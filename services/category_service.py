"""
Сервис управления категориями - Category Management Service
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Optional, Dict, Any
from models import Category, CategoryButton
from utils.logger import logger


class CategoryService:
    """Service for category management"""
    
    @staticmethod
    async def create_category(
        session: AsyncSession,
        key: str,
        name_ru: str,
        name_uz: str,
        icon: str = None,
        parent_id: int = None,
        **kwargs
    ) -> Category:
        """
        Создать новую категорию
        Create new category
        """
        try:
            logger.info(f"[CategoryService] Создание категории: {key}")
            
            category = Category(
                key=key,
                name_ru=name_ru,
                name_uz=name_uz,
                icon=icon,
                parent_id=parent_id,
                **kwargs
            )
            
            session.add(category)
            await session.commit()
            await session.refresh(category)
            
            logger.info(f"[CategoryService] ✅ Категория создана: {category.id}")
            return category
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка создания категории: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_category(session: AsyncSession, category_id: int) -> Optional[Category]:
        """
        Получить категорию по ID
        Get category by ID
        """
        try:
            result = await session.execute(
                select(Category)
                .options(
                    selectinload(Category.children),
                    selectinload(Category.buttons)
                )
                .where(Category.id == category_id)
            )
            category = result.scalar_one_or_none()
            
            if category:
                logger.info(f"[CategoryService] Категория найдена: {category.id} - {category.name_ru}")
            else:
                logger.warning(f"[CategoryService] Категория {category_id} не найдена")
            
            return category
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка получения категории: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_category_by_key(session: AsyncSession, key: str) -> Optional[Category]:
        """
        Получить категорию по ключу
        Get category by key
        """
        try:
            result = await session.execute(
                select(Category)
                .options(
                    selectinload(Category.children),
                    selectinload(Category.buttons)
                )
                .where(Category.key == key)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка получения категории по ключу: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_all_categories(
        session: AsyncSession,
        active_only: bool = True
    ) -> List[Category]:
        """
        Получить все категории
        Get all categories
        """
        try:
            query = select(Category).options(
                selectinload(Category.children),
                selectinload(Category.buttons)
            )
            
            if active_only:
                query = query.where(Category.is_active == True)
            
            query = query.order_by(Category.order_index, Category.id)
            
            result = await session.execute(query)
            categories = result.scalars().all()
            
            logger.info(f"[CategoryService] Найдено категорий: {len(categories)}")
            return categories
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка получения категорий: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_root_categories(
        session: AsyncSession,
        active_only: bool = True
    ) -> List[Category]:
        """
        Получить корневые категории (без родителя)
        Get root categories (without parent)
        """
        try:
            query = select(Category).options(
                selectinload(Category.children),
                selectinload(Category.buttons)
            ).where(Category.parent_id == None)
            
            if active_only:
                query = query.where(Category.is_active == True)
            
            query = query.order_by(Category.order_index, Category.id)
            
            result = await session.execute(query)
            categories = result.scalars().all()
            
            logger.info(f"[CategoryService] Найдено корневых категорий: {len(categories)}")
            return categories
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка получения корневых категорий: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_subcategories(
        session: AsyncSession,
        parent_id: int,
        active_only: bool = True
    ) -> List[Category]:
        """
        Получить подкатегории
        Get subcategories
        """
        try:
            query = select(Category).options(
                selectinload(Category.children),
                selectinload(Category.buttons)
            ).where(Category.parent_id == parent_id)
            
            if active_only:
                query = query.where(Category.is_active == True)
            
            query = query.order_by(Category.order_index, Category.id)
            
            result = await session.execute(query)
            categories = result.scalars().all()
            
            logger.info(f"[CategoryService] Найдено подкатегорий для {parent_id}: {len(categories)}")
            return categories
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка получения подкатегорий: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def update_category(
        session: AsyncSession,
        category_id: int,
        **kwargs
    ) -> Optional[Category]:
        """
        Обновить категорию
        Update category
        """
        try:
            category = await CategoryService.get_category(session, category_id)
            if not category:
                logger.warning(f"[CategoryService] Категория {category_id} не найдена для обновления")
                return None
            
            for key, value in kwargs.items():
                if hasattr(category, key):
                    setattr(category, key, value)
            
            await session.commit()
            await session.refresh(category)
            
            logger.info(f"[CategoryService] ✅ Категория {category_id} обновлена")
            return category
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка обновления категории: {str(e)}", exc_info=True)
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
            category = await CategoryService.get_category(session, category_id)
            if not category:
                logger.warning(f"[CategoryService] Категория {category_id} не найдена для удаления")
                return False
            
            await session.delete(category)
            await session.commit()
            
            logger.info(f"[CategoryService] ✅ Категория {category_id} удалена")
            return True
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка удаления категории: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def toggle_category(session: AsyncSession, category_id: int) -> Optional[Category]:
        """
        Переключить активность категории (on/off)
        Toggle category active state
        """
        try:
            category = await CategoryService.get_category(session, category_id)
            if not category:
                logger.warning(f"[CategoryService] Категория {category_id} не найдена для переключения")
                return None
            
            category.is_active = not category.is_active
            await session.commit()
            await session.refresh(category)
            
            status = "включена" if category.is_active else "выключена"
            logger.info(f"[CategoryService] ✅ Категория {category_id} {status}")
            return category
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка переключения категории: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def add_button(
        session: AsyncSession,
        category_id: int,
        text_ru: str,
        text_uz: str,
        button_type: str,
        button_value: str,
        order_index: int = 0
    ) -> CategoryButton:
        """
        Добавить кнопку к категории
        Add button to category
        """
        try:
            button = CategoryButton(
                category_id=category_id,
                text_ru=text_ru,
                text_uz=text_uz,
                button_type=button_type,
                button_value=button_value,
                order_index=order_index
            )
            
            session.add(button)
            await session.commit()
            await session.refresh(button)
            
            logger.info(f"[CategoryService] ✅ Кнопка добавлена к категории {category_id}")
            return button
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка добавления кнопки: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def update_button(
        session: AsyncSession,
        button_id: int,
        **kwargs
    ) -> Optional[CategoryButton]:
        """
        Обновить кнопку категории
        Update category button
        """
        try:
            result = await session.execute(
                select(CategoryButton).where(CategoryButton.id == button_id)
            )
            button = result.scalar_one_or_none()
            if not button:
                logger.warning(f"[CategoryService] Кнопка {button_id} не найдена")
                return None
            
            for key, value in kwargs.items():
                if hasattr(button, key):
                    setattr(button, key, value)
            
            await session.commit()
            await session.refresh(button)
            
            logger.info(f"[CategoryService] ✅ Кнопка {button_id} обновлена")
            return button
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка обновления кнопки: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def delete_button(session: AsyncSession, button_id: int) -> bool:
        """
        Удалить кнопку категории
        Delete category button
        """
        try:
            result = await session.execute(
                select(CategoryButton).where(CategoryButton.id == button_id)
            )
            button = result.scalar_one_or_none()
            if not button:
                logger.warning(f"[CategoryService] Кнопка {button_id} не найдена для удаления")
                return False
            
            await session.delete(button)
            await session.commit()
            
            logger.info(f"[CategoryService] ✅ Кнопка {button_id} удалена")
            return True
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка удаления кнопки: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def ensure_default_categories(session: AsyncSession) -> List[Category]:
        """
        Убедиться, что базовые категории существуют
        Ensure that default categories exist
        """
        default_categories = [
            {"key": "talim", "name_ru": "📚 Talim", "name_uz": "📚 Talim", "icon": "📚", "order_index": 1},
            {"key": "dostavka", "name_ru": "🚚 Dostavka", "name_uz": "🚚 Dostavka", "icon": "🚚", "order_index": 2},
            {"key": "yoqolgan", "name_ru": "🔔 Yoqolgan", "name_uz": "🔔 Yoqolgan", "icon": "🔔", "order_index": 3},
            {"key": "shurta", "name_ru": "🚨 Shurta", "name_uz": "🚨 Shurta", "icon": "🚨", "order_index": 4},
            {"key": "sozlamalar", "name_ru": "⚙️ Sozlamalar", "name_uz": "⚙️ Sozlamalar", "icon": "⚙️", "order_index": 5},
            {"key": "admin", "name_ru": "💬 Admin", "name_uz": "💬 Admin", "icon": "💬", "order_index": 6},
            {"key": "settings", "name_ru": "⚙️ Settings", "name_uz": "⚙️ Settings", "icon": "⚙️", "order_index": 7},
        ]
        
        created_categories = []
        for cat_data in default_categories:
            existing = await CategoryService.get_category_by_key(session, cat_data["key"])
            if not existing:
                category = await CategoryService.create_category(
                    session,
                    key=cat_data["key"],
                    name_ru=cat_data["name_ru"],
                    name_uz=cat_data["name_uz"],
                    icon=cat_data.get("icon"),
                    order_index=cat_data.get("order_index", 0)
                )
                created_categories.append(category)
        
        if created_categories:
            logger.info(f"[CategoryService] ✅ Созданы базовые категории: {[c.key for c in created_categories]}")
        
        # Возвращаем актуальный список корневых категорий
        return await CategoryService.get_root_categories(session, active_only=False)
    
    @staticmethod
    async def get_category_tree(
        session: AsyncSession,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Получить дерево категорий со всеми уровнями
        Get category tree with all levels
        """
        try:
            root_categories = await CategoryService.get_root_categories(session, active_only=active_only)
            tree = []
            for root in root_categories:
                tree.append(CategoryService._serialize_category(root, active_only=active_only))
            return tree
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка построения дерева категорий: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def _serialize_category(category: Category, active_only: bool = True) -> Dict[str, Any]:
        """
        Сериализация категории в словарь с вложенными данными
        Serialize category to dict with nested data
        """
        children = [child for child in category.children if (child.is_active or not active_only)]
        buttons = [button for button in category.buttons if (button.is_active or not active_only)]
        
        return {
            "id": category.id,
            "key": category.key,
            "name_ru": category.name_ru,
            "name_uz": category.name_uz,
            "icon": category.icon,
            "is_active": category.is_active,
            "order_index": category.order_index,
            "content_type": category.content_type,
            "text_content_ru": category.text_content_ru,
            "text_content_uz": category.text_content_uz,
            "photo_file_id": category.photo_file_id,
            "audio_file_id": category.audio_file_id,
            "pdf_file_id": category.pdf_file_id,
            "link_url": category.link_url,
            "location_type": category.location_type,
            "location_address": category.location_address,
            "latitude": category.latitude,
            "longitude": category.longitude,
            "geo_name": category.geo_name,
            "maps_url": category.maps_url,
            "button_type": category.button_type,
            "buttons": [
                {
                    "id": button.id,
                    "text_ru": button.text_ru,
                    "text_uz": button.text_uz,
                    "button_type": button.button_type,
                    "button_value": button.button_value,
                    "order_index": button.order_index,
                    "is_active": button.is_active
                }
                for button in buttons
            ],
            "children": [
                CategoryService._serialize_category(child, active_only=active_only)
                for child in children
            ]
        }
    
    @staticmethod
    async def reorder_category(
        session: AsyncSession,
        category_id: int,
        direction: str  # "up" or "down"
    ) -> bool:
        """
        Reorder category up or down within its parent's children
        """
        try:
            category = await CategoryService.get_category(session, category_id)
            if not category:
                return False
            
            # Get siblings (categories with same parent_id)
            siblings = await CategoryService.get_subcategories(
                session, 
                category.parent_id, 
                active_only=False
            ) if category.parent_id else await CategoryService.get_root_categories(
                session,
                active_only=False
            )
            
            # Sort by order_index
            siblings = sorted(siblings, key=lambda x: x.order_index)
            current_index = next((i for i, c in enumerate(siblings) if c.id == category_id), None)
            
            if current_index is None:
                return False
            
            if direction == "up" and current_index > 0:
                # Swap with previous
                siblings[current_index].order_index, siblings[current_index - 1].order_index = \
                    siblings[current_index - 1].order_index, siblings[current_index].order_index
            elif direction == "down" and current_index < len(siblings) - 1:
                # Swap with next
                siblings[current_index].order_index, siblings[current_index + 1].order_index = \
                    siblings[current_index + 1].order_index, siblings[current_index].order_index
            else:
                return False
            
            await session.commit()
            logger.info(f"[CategoryService] ✅ Категория {category_id} перемещена {direction}")
            return True
            
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка перемещения категории: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_category_depth(session: AsyncSession, category_id: int) -> int:
        """
        Get depth level of category (0 for root, 1 for level 1, etc.)
        """
        try:
            category = await CategoryService.get_category(session, category_id)
            if not category:
                return -1
            
            depth = 0
            current = category
            while current.parent_id:
                depth += 1
                current = await CategoryService.get_category(session, current.parent_id)
                if not current:
                    break
            
            return depth
            
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка получения глубины категории: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def can_add_subcategory(session: AsyncSession, parent_id: int, max_depth: int = 4) -> bool:
        """
        Check if we can add a subcategory (respecting max depth limit)
        """
        try:
            current_depth = await CategoryService.get_category_depth(session, parent_id)
            # Depth is 0-indexed, so depth 3 means we're at level 4
            return current_depth < (max_depth - 1)
            
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка проверки возможности добавления подкатегории: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def reorder_button(
        session: AsyncSession,
        button_id: int,
        direction: str  # "up" or "down"
    ) -> bool:
        """
        Reorder button up or down within its category's buttons
        """
        try:
            result = await session.execute(
                select(CategoryButton).where(CategoryButton.id == button_id)
            )
            button = result.scalar_one_or_none()
            if not button:
                return False
            
            # Get all buttons for this category
            category = await CategoryService.get_category(session, button.category_id)
            if not category:
                return False
            
            buttons = sorted(category.buttons, key=lambda x: x.order_index)
            current_index = next((i for i, b in enumerate(buttons) if b.id == button_id), None)
            
            if current_index is None:
                return False
            
            if direction == "up" and current_index > 0:
                # Swap with previous
                buttons[current_index].order_index, buttons[current_index - 1].order_index = \
                    buttons[current_index - 1].order_index, buttons[current_index].order_index
            elif direction == "down" and current_index < len(buttons) - 1:
                # Swap with next
                buttons[current_index].order_index, buttons[current_index + 1].order_index = \
                    buttons[current_index + 1].order_index, buttons[current_index].order_index
            else:
                return False
            
            await session.commit()
            logger.info(f"[CategoryService] ✅ Кнопка {button_id} перемещена {direction}")
            return True
            
        except Exception as e:
            logger.error(f"[CategoryService] ❌ Ошибка перемещения кнопки: {str(e)}", exc_info=True)
            await session.rollback()
            raise
