"""
Сервис управления контентом Web App - Web App Content Management Service
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Union
from models import WebAppCategory, WebAppCategoryItem, WebAppFile, WebAppCategoryItemType
from utils.logger import logger


class WebAppContentService:
    """Service for Web App content management"""
    
    ALLOWED_ITEM_TYPES = {item_type.value for item_type in WebAppCategoryItemType}
    
    @staticmethod
    def _normalize_item_type(item_type: Union[str, WebAppCategoryItemType]) -> str:
        if isinstance(item_type, WebAppCategoryItemType):
            return item_type.value
        if item_type is None:
            return None
        normalized = str(item_type).upper()
        if normalized not in WebAppContentService.ALLOWED_ITEM_TYPES:
            raise ValueError(f"Недопустимый тип элемента Web App: {item_type}")
        return normalized
    
    @staticmethod
    async def list_categories(
        session: AsyncSession,
        include_inactive: bool = False
    ) -> List[WebAppCategory]:
        """
        Получить список всех категорий с предзагруженными элементами
        Get all categories with preloaded items ordered by order_index
        """
        try:
            query = select(WebAppCategory).options(
                selectinload(WebAppCategory.items),
                selectinload(WebAppCategory.cover_file)
            )
            
            if not include_inactive:
                query = query.where(WebAppCategory.is_active == True)
            
            query = query.order_by(WebAppCategory.order_index, WebAppCategory.id)
            
            result = await session.execute(query)
            categories = result.scalars().all()
            
            logger.info(f"Найдено категорий Web App: {len(categories)}")
            return categories
        except Exception as e:
            logger.error(f"Ошибка получения категорий Web App: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_category(
        session: AsyncSession,
        category_id: int,
        include_inactive: bool = False
    ) -> Optional[WebAppCategory]:
        """
        Получить категорию по ID с предзагруженными элементами
        Get category by ID with preloaded items
        """
        try:
            query = select(WebAppCategory).options(
                selectinload(WebAppCategory.items),
                selectinload(WebAppCategory.cover_file)
            ).where(WebAppCategory.id == category_id)
            
            if not include_inactive:
                query = query.where(WebAppCategory.is_active == True)
            
            result = await session.execute(query)
            category = result.scalar_one_or_none()
            
            if category:
                logger.info(f"Категория Web App найдена: {category.id} - {category.title}")
            else:
                logger.warning(f"Категория Web App {category_id} не найдена")
            
            return category
        except Exception as e:
            logger.error(f"Ошибка получения категории Web App: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_category_by_slug(
        session: AsyncSession,
        slug: str,
        include_inactive: bool = False
    ) -> Optional[WebAppCategory]:
        """
        Получить категорию по slug
        Get category by slug
        """
        try:
            query = select(WebAppCategory).options(
                selectinload(WebAppCategory.items),
                selectinload(WebAppCategory.cover_file)
            ).where(WebAppCategory.slug == slug)
            
            if not include_inactive:
                query = query.where(WebAppCategory.is_active == True)
            
            result = await session.execute(query)
            category = result.scalar_one_or_none()
            
            if category:
                logger.info(f"Категория Web App найдена по slug: {slug}")
            else:
                logger.warning(f"Категория Web App со slug '{slug}' не найдена")
            
            return category
        except Exception as e:
            logger.error(f"Ошибка получения категории Web App по slug: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def create_category(
        session: AsyncSession,
        slug: str,
        title: str,
        description: str = None,
        order_index: int = 0,
        is_active: bool = True,
        cover_file_id: int = None
    ) -> WebAppCategory:
        """
        Создать новую категорию
        Create new category
        """
        try:
            logger.info(f"Создание категории Web App: {slug}")
            
            category = WebAppCategory(
                slug=slug,
                title=title,
                description=description,
                order_index=order_index,
                is_active=is_active,
                cover_file_id=cover_file_id
            )
            
            session.add(category)
            await session.commit()
            await session.refresh(category)
            
            logger.info(f"✅ Категория Web App создана: {category.id} - {category.title}")
            return category
        except Exception as e:
            logger.error(f"❌ Ошибка создания категории Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def update_category(
        session: AsyncSession,
        category_id: int,
        slug: str = None,
        title: str = None,
        description: str = None,
        order_index: int = None,
        is_active: bool = None,
        cover_file_id: int = None
    ) -> Optional[WebAppCategory]:
        """
        Обновить категорию
        Update category
        """
        try:
            category = await WebAppContentService.get_category(session, category_id, include_inactive=True)
            if not category:
                logger.warning(f"Категория Web App {category_id} не найдена для обновления")
                return None
            
            if slug is not None:
                category.slug = slug
            if title is not None:
                category.title = title
            if description is not None:
                category.description = description
            if order_index is not None:
                category.order_index = order_index
            if is_active is not None:
                category.is_active = is_active
            if cover_file_id is not None:
                category.cover_file_id = cover_file_id
            
            await session.commit()
            await session.refresh(category)
            
            logger.info(f"✅ Категория Web App {category_id} обновлена")
            return category
        except Exception as e:
            logger.error(f"❌ Ошибка обновления категории Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def delete_category(
        session: AsyncSession,
        category_id: int
    ) -> bool:
        """
        Удалить категорию
        Delete category
        """
        try:
            category = await WebAppContentService.get_category(session, category_id, include_inactive=True)
            if not category:
                logger.warning(f"Категория Web App {category_id} не найдена для удаления")
                return False
            
            await session.delete(category)
            await session.commit()
            
            logger.info(f"✅ Категория Web App {category_id} удалена")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления категории Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def add_item(
        session: AsyncSession,
        category_id: int,
        item_type: Union[str, WebAppCategoryItemType],
        text_content: str = None,
        rich_metadata: Dict = None,
        file_id: int = None,
        button_text: str = None,
        target_category_id: int = None,
        order_index: int = 0,
        is_active: bool = True
    ) -> Optional[WebAppCategoryItem]:
        """
        Добавить элемент в категорию
        Add item to category
        """
        try:
            category = await WebAppContentService.get_category(session, category_id, include_inactive=True)
            if not category:
                logger.warning(f"Категория Web App {category_id} не найдена для добавления элемента")
                return None
            
            # Normalize and validate item type
            normalized_type = WebAppContentService._normalize_item_type(item_type)
            
            logger.info(f"Добавление элемента типа {normalized_type} в категорию {category_id}")
            
            item = WebAppCategoryItem(
                category_id=category_id,
                type=normalized_type,
                text_content=text_content,
                rich_metadata=rich_metadata,
                file_id=file_id,
                button_text=button_text,
                target_category_id=target_category_id,
                order_index=order_index,
                is_active=is_active
            )
            
            session.add(item)
            await session.commit()
            await session.refresh(item)
            
            logger.info(f"✅ Элемент добавлен в категорию Web App {category_id}")
            return item
        except Exception as e:
            logger.error(f"❌ Ошибка добавления элемента в категорию Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def update_item(
        session: AsyncSession,
        item_id: int,
        item_type: Optional[Union[str, WebAppCategoryItemType]] = None,
        text_content: str = None,
        rich_metadata: Dict = None,
        file_id: int = None,
        button_text: str = None,
        target_category_id: int = None,
        order_index: int = None,
        is_active: bool = None
    ) -> Optional[WebAppCategoryItem]:
        """
        Обновить элемент категории
        Update category item
        """
        try:
            result = await session.execute(
                select(WebAppCategoryItem).where(WebAppCategoryItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            if not item:
                logger.warning(f"Элемент Web App {item_id} не найден для обновления")
                return None
            
            if item_type is not None:
                item.type = WebAppContentService._normalize_item_type(item_type)
            if text_content is not None:
                item.text_content = text_content
            if rich_metadata is not None:
                item.rich_metadata = rich_metadata
            if file_id is not None:
                item.file_id = file_id
            if button_text is not None:
                item.button_text = button_text
            if target_category_id is not None:
                item.target_category_id = target_category_id
            if order_index is not None:
                item.order_index = order_index
            if is_active is not None:
                item.is_active = is_active
            
            await session.commit()
            await session.refresh(item)
            
            logger.info(f"✅ Элемент Web App {item_id} обновлён")
            return item
        except Exception as e:
            logger.error(f"❌ Ошибка обновления элемента Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def delete_item(
        session: AsyncSession,
        item_id: int
    ) -> bool:
        """
        Удалить элемент категории
        Delete category item
        """
        try:
            result = await session.execute(
                select(WebAppCategoryItem).where(WebAppCategoryItem.id == item_id)
            )
            item = result.scalar_one_or_none()
            if not item:
                logger.warning(f"Элемент Web App {item_id} не найден для удаления")
                return False
            
            await session.delete(item)
            await session.commit()
            
            logger.info(f"✅ Элемент Web App {item_id} удалён")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления элемента Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def reorder_items(
        session: AsyncSession,
        item_order: List[Dict[str, int]]
    ) -> bool:
        """
        Переупорядочить элементы категории
        Reorder category items
        
        Args:
            item_order: List of dicts with 'id' and 'order_index' keys
        """
        try:
            logger.info(f"Переупорядочивание {len(item_order)} элементов Web App")
            
            for item_data in item_order:
                item_id = item_data.get('id')
                new_order = item_data.get('order_index')
                
                if item_id is not None and new_order is not None:
                    result = await session.execute(
                        select(WebAppCategoryItem).where(WebAppCategoryItem.id == item_id)
                    )
                    item = result.scalar_one_or_none()
                    if item:
                        item.order_index = new_order
            
            await session.commit()
            logger.info(f"✅ Элементы Web App переупорядочены")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка переупорядочивания элементов Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def create_file(
        session: AsyncSession,
        file_type: str,
        telegram_file_id: str = None,
        storage_path: str = None,
        mime_type: str = None,
        file_size: int = None,
        uploaded_by: int = None,
        original_name: str = None,
        description: str = None,
        tag: str = None,
        width: int = None,
        height: int = None
    ) -> WebAppFile:
        """
        Создать запись о файле
        Create file record
        """
        try:
            logger.info(f"Создание записи файла Web App: {file_type}")
            
            file_record = WebAppFile(
                file_type=file_type,
                telegram_file_id=telegram_file_id,
                storage_path=storage_path,
                mime_type=mime_type,
                file_size=file_size,
                uploaded_by=uploaded_by,
                original_name=original_name,
                description=description,
                tag=tag,
                width=width,
                height=height
            )
            
            session.add(file_record)
            await session.commit()
            await session.refresh(file_record)
            
            logger.info(f"✅ Запись файла Web App создана: {file_record.id}")
            return file_record
        except Exception as e:
            logger.error(f"❌ Ошибка создания записи файла Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_file(
        session: AsyncSession,
        file_id: int
    ) -> Optional[WebAppFile]:
        """
        Получить информацию о файле
        Get file information
        """
        try:
            result = await session.execute(
                select(WebAppFile).where(WebAppFile.id == file_id)
            )
            file_record = result.scalar_one_or_none()
            
            if file_record:
                logger.info(f"Файл Web App найден: {file_id}")
            else:
                logger.warning(f"Файл Web App {file_id} не найден")
            
            return file_record
        except Exception as e:
            logger.error(f"Ошибка получения файла Web App: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def resolve_file_url(file: Optional[WebAppFile]) -> Optional[str]:
        """
        Получить URL файла (telegram_file_id или storage_path)
        Resolve file URL (telegram_file_id or storage_path)
        """
        if not file:
            return None
        
        if file.telegram_file_id:
            return file.telegram_file_id
        
        if file.storage_path:
            return file.storage_path
        
        return None
    
    @staticmethod
    async def delete_file(
        session: AsyncSession,
        file_id: int,
        delete_physical: bool = True
    ) -> bool:
        """
        Удалить файл из базы данных и с диска
        Delete file from database and disk
        """
        try:
            file_record = await WebAppContentService.get_file(session, file_id)
            if not file_record:
                logger.warning(f"Файл Web App {file_id} не найден для удаления")
                return False
            
            if delete_physical and file_record.storage_path:
                try:
                    from webapp.storage import resolve_physical_path
                    physical_path = resolve_physical_path(file_record.storage_path)
                    if physical_path and physical_path.exists():
                        await asyncio.to_thread(physical_path.unlink)
                        logger.info(f"✅ Физический файл удалён: {physical_path}")
                except Exception as e:
                    logger.error(f"❌ Ошибка удаления физического файла: {str(e)}")
            
            await session.delete(file_record)
            await session.commit()
            
            logger.info(f"✅ Файл Web App {file_id} удалён из базы данных")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка удаления файла Web App: {str(e)}", exc_info=True)
            await session.rollback()
            raise
