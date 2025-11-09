"""
Web App Categories API Routes
Provides read-only endpoints for category listing and details
"""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from models import User, WebAppCategory
from services.webapp_content_service import WebAppContentService
from utils.logger import logger
from webapp.auth import get_current_user, get_db_session

router = APIRouter(prefix="/webapp", tags=["webapp-categories"])


class WebAppFileOut(BaseModel):
    id: int
    file_type: str
    file_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None

    class Config:
        from_attributes = True


class WebAppCategoryItemOut(BaseModel):
    id: int
    type: str
    text_content: Optional[str] = None
    rich_metadata: Optional[dict] = None
    file: Optional[WebAppFileOut] = None
    button_text: Optional[str] = None
    target_category_id: Optional[int] = None
    order_index: int
    is_active: bool

    class Config:
        from_attributes = True


class WebAppCategoryOut(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    order_index: int
    is_active: bool
    items_count: int = 0

    class Config:
        from_attributes = True


class WebAppCategoryDetailOut(BaseModel):
    id: int
    slug: str
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    order_index: int
    is_active: bool
    items: List[WebAppCategoryItemOut]

    class Config:
        from_attributes = True


def build_file_url(file_record) -> Optional[str]:
    """Build absolute file URL from file record"""
    if not file_record:
        return None

    if file_record.telegram_file_id:
        return file_record.telegram_file_id

    if file_record.storage_path:
        storage_path = file_record.storage_path.lstrip("/")
        base_url = settings.webapp_public_url.rstrip("/")

        if storage_path.startswith("webapp/static/"):
            return f"{base_url}/{storage_path}"

        return f"{base_url}/webapp/static/{storage_path}"

    return None


def serialize_category(
    category: WebAppCategory,
    *,
    include_items: bool,
    include_inactive_items: bool
) -> Union[WebAppCategoryOut, WebAppCategoryDetailOut]:
    """Convert ORM category to response model"""
    cover_url = build_file_url(category.cover_file) if category.cover_file else None

    serialized_items: List[WebAppCategoryItemOut] = []
    for item in category.items:
        if not include_inactive_items and not item.is_active:
            continue

        file_data = None
        if item.file:
            file_data = WebAppFileOut(
                id=item.file.id,
                file_type=item.file.file_type,
                file_url=build_file_url(item.file),
                mime_type=item.file.mime_type,
                file_size=item.file.file_size
            )

        serialized_items.append(
            WebAppCategoryItemOut(
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
        )

    if include_items:
        ordered_items = sorted(serialized_items, key=lambda x: x.order_index)
        return WebAppCategoryDetailOut(
            id=category.id,
            slug=category.slug,
            title=category.title,
            description=category.description,
            cover_url=cover_url,
            order_index=category.order_index,
            is_active=category.is_active,
            items=ordered_items
        )

    items_count = len(category.items) if include_inactive_items else len(serialized_items)
    return WebAppCategoryOut(
        id=category.id,
        slug=category.slug,
        title=category.title,
        description=category.description,
        cover_url=cover_url,
        order_index=category.order_index,
        is_active=category.is_active,
        items_count=items_count
    )


@router.get("/categories", response_model=List[WebAppCategoryOut])
async def list_categories(
    include_inactive: bool = False,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Получить список категорий
    Get list of categories
    
    Query params:
    - include_inactive: Include inactive categories (admin only)
    
    Returns list of categories with minimal fields sorted by order_index.
    """
    try:
        effective_include_inactive = include_inactive and user.is_admin
        
        if include_inactive and not user.is_admin:
            logger.warning(f"Пользователь {user.telegram_id} попытался получить неактивные категории без прав администратора")
        
        categories = await WebAppContentService.list_categories(
            session=session,
            include_inactive=effective_include_inactive
        )
        
        result = [
            serialize_category(
                category,
                include_items=False,
                include_inactive_items=effective_include_inactive
            )
            for category in categories
        ]
        
        logger.info(f"✅ Получен список категорий: {len(result)} категорий для пользователя {user.telegram_id}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения списка категорий: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка получения списка категорий")


@router.get("/category/{category_id}", response_model=WebAppCategoryDetailOut)
async def get_category(
    category_id: int,
    include_inactive: bool = False,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """
    Получить детали категории с элементами
    Get category details with items
    
    Path params:
    - category_id: ID категории
    
    Query params:
    - include_inactive: Include inactive items (admin only)
    
    Returns full category details including ordered active items.
    """
    try:
        effective_include_inactive = include_inactive and user.is_admin
        
        if include_inactive and not user.is_admin:
            logger.warning(f"Пользователь {user.telegram_id} попытался получить неактивные элементы без прав администратора")
        
        category = await WebAppContentService.get_category(
            session=session,
            category_id=category_id,
            include_inactive=effective_include_inactive
        )
        
        if not category:
            logger.warning(f"❌ Категория {category_id} не найдена для пользователя {user.telegram_id}")
            raise HTTPException(status_code=404, detail="Категория не найдена")
        
        result = serialize_category(
            category,
            include_items=True,
            include_inactive_items=effective_include_inactive
        )
        
        logger.info(f"✅ Получена категория {category_id} для пользователя {user.telegram_id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Ошибка получения категории {category_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Ошибка получения категории")
