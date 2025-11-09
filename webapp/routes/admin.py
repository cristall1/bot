"""
Admin API Routes for Web App Content Management
Provides CRUD operations for categories and items (admin-only)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from models import (
    User,
    WebAppCategory,
    WebAppCategoryItem,
    WebAppCategoryItemType,
)
from services.webapp_content_service import WebAppContentService
from utils.logger import logger
from webapp.auth import require_admin_user, get_db_session
from webapp.routes.categories import (
    WebAppCategoryDetailOut,
    WebAppCategoryItemOut,
    WebAppFileOut,
    build_file_url,
    serialize_category,
)

router = APIRouter(prefix="/webapp", tags=["webapp-admin"])


# Request Schemas

class CategoryCreateRequest(BaseModel):
    """Schema for creating a new category"""
    slug: str = Field(..., min_length=1, max_length=100, description="Unique URL slug")
    title: str = Field(..., min_length=1, max_length=255, description="Category title")
    description: Optional[str] = Field(None, description="Category description")
    order_index: Optional[int] = Field(None, ge=0, description="Display order (auto-assigned if not provided)")
    is_active: bool = Field(True, description="Active status")
    cover_file_id: Optional[int] = Field(None, description="Cover image file ID")


class CategoryUpdateRequest(BaseModel):
    """Schema for updating a category"""
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    cover_file_id: Optional[int] = None
    items_order: Optional[List[int]] = Field(
        None,
        description="Optional list of item IDs to reorder as part of the update"
    )


class ItemCreateRequest(BaseModel):
    """Schema for creating a new category item"""
    type: str = Field(..., description="Item type (TEXT, IMAGE, DOCUMENT, LINK, VIDEO, BUTTON)")
    text_content: Optional[str] = Field(None, description="Text content or caption")
    rich_metadata: Optional[dict] = Field(None, description="Rich metadata for complex items")
    file_id: Optional[int] = Field(None, description="File ID for media items")
    button_text: Optional[str] = Field(None, max_length=255, description="Button text (required for BUTTON type)")
    target_category_id: Optional[int] = Field(None, description="Target category for navigation (required for BUTTON type)")
    order_index: Optional[int] = Field(None, ge=0, description="Display order (auto-assigned if not provided)")
    is_active: bool = Field(True, description="Active status")

    @validator('type')
    def validate_type(cls, v):
        """Validate item type"""
        v_upper = v.upper()
        allowed_types = {item_type.value for item_type in WebAppCategoryItemType}
        if v_upper not in allowed_types:
            raise ValueError(f"Invalid item type. Must be one of: {', '.join(allowed_types)}")
        return v_upper

    @validator('button_text')
    def validate_button_text(cls, v, values):
        """Validate button text is provided for BUTTON type"""
        if 'type' in values and values['type'] == 'BUTTON':
            if not v or not v.strip():
                raise ValueError("button_text is required for BUTTON type items")
        return v

    @validator('target_category_id')
    def validate_target_category(cls, v, values):
        """Validate target_category_id is provided for BUTTON type"""
        if 'type' in values and values['type'] == 'BUTTON':
            if v is None:
                raise ValueError("target_category_id is required for BUTTON type items")
        return v


class ItemUpdateRequest(BaseModel):
    """Schema for updating a category item"""
    type: Optional[str] = Field(None, description="Item type")
    text_content: Optional[str] = None
    rich_metadata: Optional[dict] = None
    file_id: Optional[int] = None
    button_text: Optional[str] = Field(None, max_length=255)
    target_category_id: Optional[int] = None
    order_index: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None

    @validator('type')
    def validate_type(cls, v):
        """Validate item type"""
        if v is not None:
            v_upper = v.upper()
            allowed_types = {item_type.value for item_type in WebAppCategoryItemType}
            if v_upper not in allowed_types:
                raise ValueError(f"Invalid item type. Must be one of: {', '.join(allowed_types)}")
            return v_upper
        return v


class ItemReorderRequest(BaseModel):
    """Schema for reordering items"""
    item_ids: List[int] = Field(..., description="List of item IDs in desired order")


async def _prepare_reorder_data(
    *,
    session: AsyncSession,
    category_id: int,
    item_ids: List[int]
) -> List[dict]:
    """Validate and prepare reorder payload"""
    if not item_ids:
        logger.warning(f"❌ Пустой список элементов для переупорядочивания в категории {category_id}")
        raise HTTPException(status_code=400, detail="Список элементов для переупорядочивания не может быть пустым")
    if len(set(item_ids)) != len(item_ids):
        logger.warning(f"❌ Найдены дубликаты в items_order для категории {category_id}: {item_ids}")
        raise HTTPException(status_code=400, detail="Список item_ids содержит дубликаты")

    result = await session.execute(
        select(WebAppCategoryItem).where(
            WebAppCategoryItem.id.in_(item_ids),
            WebAppCategoryItem.category_id == category_id
        )
    )
    existing_items = result.scalars().all()
    existing_ids = {item.id for item in existing_items}

    invalid_ids = set(item_ids) - existing_ids
    if invalid_ids:
        logger.warning(f"❌ Элементы {invalid_ids} не найдены в категории {category_id}")
        raise HTTPException(
            status_code=400,
            detail=f"Элементы с ID {sorted(invalid_ids)} не найдены в указанной категории"
        )

    return [
        {"id": item_id, "order_index": idx}
        for idx, item_id in enumerate(item_ids)
    ]


async def _apply_reorder_data(
    *,
    session: AsyncSession,
    category_id: int,
    reorder_data: List[dict]
) -> int:
    """Persist items reordering"""
    success = await WebAppContentService.reorder_items(
        session=session,
        item_order=reorder_data
    )

    if not success:
        logger.error(f"❌ Ошибка применения порядка элементов в категории {category_id}")
        raise HTTPException(status_code=500, detail="Ошибка переупорядочивания элементов")

    return len(reorder_data)


# Admin Category Endpoints

@router.post("/category", response_model=WebAppCategoryDetailOut)
async def create_category(
    data: CategoryCreateRequest,
    user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Создать новую категорию (только администратор)
    Create new category (admin only)
    """
    try:
        # Validate cover_file_id if provided
        if data.cover_file_id:
            file_record = await WebAppContentService.get_file(session, data.cover_file_id)
            if not file_record:
                logger.warning(f"❌ Файл обложки {data.cover_file_id} не найден")
                raise HTTPException(status_code=400, detail=f"Файл обложки с ID {data.cover_file_id} не существует")
        
        # Auto-assign order_index if not provided
        order_index = data.order_index
        if order_index is None:
            # Get max order_index and add 1
            result = await session.execute(
                select(func.max(WebAppCategory.order_index))
            )
            max_order = result.scalar()
            order_index = 0 if max_order is None else max_order + 1
        
        # Create category
        category = await WebAppContentService.create_category(
            session=session,
            slug=data.slug,
            title=data.title,
            description=data.description,
            order_index=order_index,
            is_active=data.is_active,
            cover_file_id=data.cover_file_id
        )
        
        # Reload with relationships
        category = await WebAppContentService.get_category(
            session=session,
            category_id=category.id,
            include_inactive=True
        )
        
        result = serialize_category(
            category,
            include_items=True,
            include_inactive_items=True
        )
        
        logger.info(f"✅ Администратор {user.telegram_id} создал категорию {category.id} - {category.title}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка создания категории: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания категории: {str(e)}")


@router.put("/category/{category_id}", response_model=WebAppCategoryDetailOut)
async def update_category(
    category_id: int,
    data: CategoryUpdateRequest,
    user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Обновить категорию (только администратор)
    Update category (admin only)
    """
    try:
        # Check if category exists
        category = await WebAppContentService.get_category(
            session=session,
            category_id=category_id,
            include_inactive=True
        )
        if not category:
            logger.warning(f"❌ Категория {category_id} не найдена")
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        # Validate cover_file_id if provided
        if data.cover_file_id is not None:
            file_record = await WebAppContentService.get_file(session, data.cover_file_id)
            if not file_record:
                logger.warning(f"❌ Файл обложки {data.cover_file_id} не найден")
                raise HTTPException(status_code=400, detail=f"Файл обложки с ID {data.cover_file_id} не существует")
        
        # Update category
        await WebAppContentService.update_category(
            session=session,
            category_id=category_id,
            slug=data.slug,
            title=data.title,
            description=data.description,
            order_index=data.order_index,
            is_active=data.is_active,
            cover_file_id=data.cover_file_id
        )
        
        # Optionally reorder items if provided
        if data.items_order is not None and len(data.items_order) > 0:
            reorder_data = await _prepare_reorder_data(
                session=session,
                category_id=category_id,
                item_ids=data.items_order
            )
            count = await _apply_reorder_data(
                session=session,
                category_id=category_id,
                reorder_data=reorder_data
            )
            logger.info(f"✅ Переупорядочено {count} элементов в категории {category_id}")
        
        # Reload with relationships
        updated_category = await WebAppContentService.get_category(
            session=session,
            category_id=category_id,
            include_inactive=True
        )
        
        result = serialize_category(
            updated_category,
            include_items=True,
            include_inactive_items=True
        )
        
        logger.info(f"✅ Администратор {user.telegram_id} обновил категорию {category_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка обновления категории {category_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления категории: {str(e)}")


@router.delete("/category/{category_id}")
async def delete_category(
    category_id: int,
    hard_delete: bool = False,
    user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Удалить категорию (только администратор)
    Delete category (admin only)
    
    Query params:
    - hard_delete: If true, permanently delete. If false, soft delete (set inactive)
    """
    try:
        # Check if category exists
        category = await WebAppContentService.get_category(
            session=session,
            category_id=category_id,
            include_inactive=True
        )
        if not category:
            logger.warning(f"❌ Категория {category_id} не найдена")
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        if hard_delete:
            # Permanently delete
            success = await WebAppContentService.delete_category(
                session=session,
                category_id=category_id
            )
            if success:
                logger.info(f"✅ Администратор {user.telegram_id} удалил категорию {category_id} (hard delete)")
                return {"success": True, "message": "Категория удалена", "deleted": True}
        else:
            # Soft delete - set inactive
            await WebAppContentService.update_category(
                session=session,
                category_id=category_id,
                is_active=False
            )
            logger.info(f"✅ Администратор {user.telegram_id} деактивировал категорию {category_id}")
            return {"success": True, "message": "Категория деактивирована", "deleted": False}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка удаления категории {category_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления категории: {str(e)}")


# Admin Item Endpoints

@router.post("/category/{category_id}/items", response_model=WebAppCategoryItemOut)
async def create_item(
    category_id: int,
    data: ItemCreateRequest,
    user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Создать новый элемент в категории (только администратор)
    Create new item in category (admin only)
    """
    try:
        # Check if category exists
        category = await WebAppContentService.get_category(
            session=session,
            category_id=category_id,
            include_inactive=True
        )
        if not category:
            logger.warning(f"❌ Категория {category_id} не найдена")
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        # Validate file_id if provided
        if data.file_id:
            file_record = await WebAppContentService.get_file(session, data.file_id)
            if not file_record:
                logger.warning(f"❌ Файл {data.file_id} не найден")
                raise HTTPException(status_code=400, detail=f"Файл с ID {data.file_id} не существует")
        
        # Validate target_category_id if provided
        if data.target_category_id is not None:
            target_category = await WebAppContentService.get_category(
                session=session,
                category_id=data.target_category_id,
                include_inactive=True
            )
            if not target_category:
                logger.warning(f"❌ Целевая категория {data.target_category_id} не найдена")
                raise HTTPException(status_code=400, detail=f"Целевая категория с ID {data.target_category_id} не существует")
        
        # Auto-assign order_index if not provided
        order_index = data.order_index
        if order_index is None:
            # Get max order_index in this category and add 1
            result = await session.execute(
                select(func.max(WebAppCategoryItem.order_index)).where(
                    WebAppCategoryItem.category_id == category_id
                )
            )
            max_order = result.scalar()
            order_index = 0 if max_order is None else max_order + 1
        
        # Create item
        item = await WebAppContentService.add_item(
            session=session,
            category_id=category_id,
            item_type=data.type,
            text_content=data.text_content,
            rich_metadata=data.rich_metadata,
            file_id=data.file_id,
            button_text=data.button_text,
            target_category_id=data.target_category_id,
            order_index=order_index,
            is_active=data.is_active
        )
        
        # Reload to get relationships
        result = await session.execute(
            select(WebAppCategoryItem)
            .options(selectinload(WebAppCategoryItem.file))
            .where(WebAppCategoryItem.id == item.id)
        )
        item = result.scalar_one()
        
        # Serialize
        file_data = None
        if item.file:
            file_data = WebAppFileOut(
                id=item.file.id,
                file_type=item.file.file_type,
                file_url=build_file_url(item.file),
                mime_type=item.file.mime_type,
                file_size=item.file.file_size
            )
        
        response = WebAppCategoryItemOut(
            id=item.id,
            type=item.type,
            text_content=item.text_content,
            rich_metadata=item.rich_metadata,
            file=file_data,
            button_text=item.button_text,
            target_category_id=item.target_category_id,
            order_index=item.order_index,
            is_active=item.is_active
        )
        
        logger.info(f"✅ Администратор {user.telegram_id} создал элемент {item.id} в категории {category_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка создания элемента в категории {category_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка создания элемента: {str(e)}")


@router.put("/category/{category_id}/items/{item_id}", response_model=WebAppCategoryItemOut)
async def update_item(
    category_id: int,
    item_id: int,
    data: ItemUpdateRequest,
    user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Обновить элемент категории (только администратор)
    Update category item (admin only)
    """
    try:
        # Check if item exists and belongs to category
        result = await session.execute(
            select(WebAppCategoryItem).where(
                WebAppCategoryItem.id == item_id,
                WebAppCategoryItem.category_id == category_id
            )
        )
        item = result.scalar_one_or_none()
        
        if not item:
            logger.warning(f"❌ Элемент {item_id} не найден в категории {category_id}")
            raise HTTPException(status_code=404, detail="Элемент не найден в указанной категории")
        
        # Validate file_id if provided
        if data.file_id is not None:
            file_record = await WebAppContentService.get_file(session, data.file_id)
            if not file_record:
                logger.warning(f"❌ Файл {data.file_id} не найден")
                raise HTTPException(status_code=400, detail=f"Файл с ID {data.file_id} не существует")
        
        # Validate target_category_id if provided
        if data.target_category_id is not None:
            target_category = await WebAppContentService.get_category(
                session=session,
                category_id=data.target_category_id,
                include_inactive=True
            )
            if not target_category:
                logger.warning(f"❌ Целевая категория {data.target_category_id} не найдена")
                raise HTTPException(status_code=400, detail=f"Целевая категория с ID {data.target_category_id} не существует")
        
        # Determine final state after update
        final_type = data.type or item.type
        final_button_text = item.button_text if data.button_text is None else data.button_text
        final_target_category_id = item.target_category_id if data.target_category_id is None else data.target_category_id
        
        if final_type == "BUTTON":
            if not final_button_text or not final_button_text.strip():
                logger.warning(f"❌ Некорректный текст кнопки для элемента {item_id}")
                raise HTTPException(status_code=400, detail="Для кнопки необходимо указать текст кнопки")
            if final_target_category_id is None:
                logger.warning(f"❌ Не указан target_category_id для кнопки {item_id}")
                raise HTTPException(status_code=400, detail="Для кнопки необходимо указать целевую категорию")
            # Ensure target category exists (even if unchanged)
            target_category = await WebAppContentService.get_category(
                session=session,
                category_id=final_target_category_id,
                include_inactive=True
            )
            if not target_category:
                logger.warning(f"❌ Целевая категория {final_target_category_id} не найдена для кнопки {item_id}")
                raise HTTPException(status_code=400, detail="Целевая категория для кнопки не существует")
        
        # Update item
        updated_item = await WebAppContentService.update_item(
            session=session,
            item_id=item_id,
            item_type=data.type,
            text_content=data.text_content,
            rich_metadata=data.rich_metadata,
            file_id=data.file_id,
            button_text=data.button_text,
            target_category_id=data.target_category_id,
            order_index=data.order_index,
            is_active=data.is_active
        )
        
        # Reload to get relationships
        result = await session.execute(
            select(WebAppCategoryItem)
            .options(selectinload(WebAppCategoryItem.file))
            .where(WebAppCategoryItem.id == item_id)
        )
        updated_item = result.scalar_one()
        
        # Serialize
        file_data = None
        if updated_item.file:
            file_data = WebAppFileOut(
                id=updated_item.file.id,
                file_type=updated_item.file.file_type,
                file_url=build_file_url(updated_item.file),
                mime_type=updated_item.file.mime_type,
                file_size=updated_item.file.file_size
            )
        
        response = WebAppCategoryItemOut(
            id=updated_item.id,
            type=updated_item.type,
            text_content=updated_item.text_content,
            rich_metadata=updated_item.rich_metadata,
            file=file_data,
            button_text=updated_item.button_text,
            target_category_id=updated_item.target_category_id,
            order_index=updated_item.order_index,
            is_active=updated_item.is_active
        )
        
        logger.info(f"✅ Администратор {user.telegram_id} обновил элемент {item_id} в категории {category_id}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка обновления элемента {item_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка обновления элемента: {str(e)}")


@router.delete("/category/{category_id}/items/{item_id}")
async def delete_item(
    category_id: int,
    item_id: int,
    hard_delete: bool = False,
    user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Удалить элемент категории (только администратор)
    Delete category item (admin only)
    
    Query params:
    - hard_delete: If true, permanently delete. If false, soft delete (set inactive)
    """
    try:
        # Check if item exists and belongs to category
        result = await session.execute(
            select(WebAppCategoryItem).where(
                WebAppCategoryItem.id == item_id,
                WebAppCategoryItem.category_id == category_id
            )
        )
        item = result.scalar_one_or_none()
        
        if not item:
            logger.warning(f"❌ Элемент {item_id} не найден в категории {category_id}")
            raise HTTPException(status_code=404, detail="Элемент не найден в указанной категории")
        
        if hard_delete:
            # Permanently delete
            success = await WebAppContentService.delete_item(
                session=session,
                item_id=item_id
            )
            if success:
                logger.info(f"✅ Администратор {user.telegram_id} удалил элемент {item_id} (hard delete)")
                return {"success": True, "message": "Элемент удалён", "deleted": True}
        else:
            # Soft delete - set inactive
            await WebAppContentService.update_item(
                session=session,
                item_id=item_id,
                is_active=False
            )
            logger.info(f"✅ Администратор {user.telegram_id} деактивировал элемент {item_id}")
            return {"success": True, "message": "Элемент деактивирован", "deleted": False}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка удаления элемента {item_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка удаления элемента: {str(e)}")


@router.post("/category/{category_id}/items/reorder", response_model=List[WebAppCategoryItemOut])
async def reorder_items(
    category_id: int,
    data: ItemReorderRequest,
    user: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Переупорядочить элементы категории (только администратор)
    Reorder category items (admin only)
    
    Accepts array of item IDs in desired order. Each item will be assigned
    an order_index based on its position in the array (0, 1, 2, ...).
    """
    try:
        # Check if category exists
        category = await WebAppContentService.get_category(
            session=session,
            category_id=category_id,
            include_inactive=True
        )
        if not category:
            logger.warning(f"❌ Категория {category_id} не найдена")
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        # Apply reordering using helper
        reorder_data = await _prepare_reorder_data(
            session=session,
            category_id=category_id,
            item_ids=data.item_ids
        )
        count = await _apply_reorder_data(
            session=session,
            category_id=category_id,
            reorder_data=reorder_data
        )
        
        # Get updated category with items
        updated_category = await WebAppContentService.get_category(
            session=session,
            category_id=category_id,
            include_inactive=True
        )
        serialized_category = serialize_category(
            updated_category,
            include_items=True,
            include_inactive_items=True
        )
        items = sorted(serialized_category.items, key=lambda item: item.order_index)
        
        logger.info(f"✅ Администратор {user.telegram_id} переупорядочил {count} элементов в категории {category_id}")
        return items
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка переупорядочивания элементов категории {category_id}: {str(e)}", exc_info=True)
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка переупорядочивания элементов: {str(e)}")
