from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime
from models import MenuItem, MenuContent, MenuButton
from utils.logger import logger


class MenuService:
    """Service for managing User Bot main menu items"""

    # ═══════════════════════════════════════════════════════════════════════
    # MENU ITEM CRUD
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def get_all_menu_items(
        session: AsyncSession,
        include_inactive: bool = False
    ) -> List[MenuItem]:
        """
        Get all menu items ordered by order_index
        ALWAYS FRESH DATA - NO CACHING
        """
        stmt = select(MenuItem).options(
            selectinload(MenuItem.content),
            selectinload(MenuItem.buttons)
        ).order_by(MenuItem.order_index)
        
        if not include_inactive:
            stmt = stmt.where(MenuItem.is_active == True)
        
        result = await session.execute(stmt)
        items = result.scalars().all()
        
        logger.info(f"[MenuService] ✅ Получено {len(items)} пунктов меню (include_inactive={include_inactive})")
        return list(items)

    @staticmethod
    async def get_menu_item_by_id(
        session: AsyncSession,
        menu_item_id: int
    ) -> Optional[MenuItem]:
        """Get menu item by ID with all relations"""
        stmt = select(MenuItem).options(
            selectinload(MenuItem.content),
            selectinload(MenuItem.buttons)
        ).where(MenuItem.id == menu_item_id)
        
        result = await session.execute(stmt)
        item = result.scalar_one_or_none()
        
        if item:
            logger.info(f"[MenuService] ✅ Получен пункт меню: {item.name_ru} (ID={menu_item_id})")
        else:
            logger.warning(f"[MenuService] ⚠️ Пункт меню не найден: ID={menu_item_id}")
        
        return item

    @staticmethod
    async def create_menu_item(
        session: AsyncSession,
        name_ru: str,
        name_uz: str,
        icon: str = None,
        description_ru: str = None,
        description_uz: str = None
    ) -> MenuItem:
        """Create new menu item"""
        # Get next order_index
        stmt = select(func.max(MenuItem.order_index))
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        
        menu_item = MenuItem(
            name_ru=name_ru,
            name_uz=name_uz,
            icon=icon,
            description_ru=description_ru,
            description_uz=description_uz,
            order_index=max_order + 1,
            is_active=True
        )
        
        session.add(menu_item)
        await session.commit()
        await session.refresh(menu_item)
        
        logger.info(f"[MenuService] ✅ Создан новый пункт меню: {name_ru} (ID={menu_item.id})")
        return menu_item

    @staticmethod
    async def update_menu_item(
        session: AsyncSession,
        menu_item_id: int,
        **kwargs
    ) -> Optional[MenuItem]:
        """Update menu item fields"""
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
        if not menu_item:
            return None
        
        for key, value in kwargs.items():
            if hasattr(menu_item, key):
                setattr(menu_item, key, value)
        
        menu_item.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(menu_item)
        
        logger.info(f"[MenuService] ✅ Обновлен пункт меню: {menu_item.name_ru} (ID={menu_item_id})")
        return menu_item

    @staticmethod
    async def toggle_menu_item(
        session: AsyncSession,
        menu_item_id: int
    ) -> Optional[bool]:
        """Toggle menu item active status"""
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
        if not menu_item:
            return None
        
        menu_item.is_active = not menu_item.is_active
        await session.commit()
        
        status = "ON" if menu_item.is_active else "OFF"
        logger.info(f"[MenuService] ✅ Переключен статус пункта меню: {menu_item.name_ru} → {status}")
        return menu_item.is_active

    @staticmethod
    async def delete_menu_item(
        session: AsyncSession,
        menu_item_id: int
    ) -> bool:
        """Delete menu item (cascade deletes content and buttons)"""
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
        if not menu_item:
            return False
        
        await session.delete(menu_item)
        await session.commit()
        
        logger.info(f"[MenuService] ✅ Удален пункт меню: {menu_item.name_ru} (ID={menu_item_id})")
        return True

    @staticmethod
    async def reorder_menu_item(
        session: AsyncSession,
        menu_item_id: int,
        direction: str  # "up" or "down"
    ) -> bool:
        """Move menu item up or down"""
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
        if not menu_item:
            return False
        
        current_order = menu_item.order_index
        
        if direction == "up":
            # Find item above
            stmt = select(MenuItem).where(
                MenuItem.order_index < current_order
            ).order_by(MenuItem.order_index.desc()).limit(1)
        else:
            # Find item below
            stmt = select(MenuItem).where(
                MenuItem.order_index > current_order
            ).order_by(MenuItem.order_index.asc()).limit(1)
        
        result = await session.execute(stmt)
        swap_item = result.scalar_one_or_none()
        
        if not swap_item:
            return False
        
        # Swap order indices
        menu_item.order_index, swap_item.order_index = swap_item.order_index, menu_item.order_index
        await session.commit()
        
        logger.info(f"[MenuService] ✅ Перемещен пункт меню: {menu_item.name_ru} ({direction})")
        return True

    # ═══════════════════════════════════════════════════════════════════════
    # MENU CONTENT CRUD
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def add_text_content(
        session: AsyncSession,
        menu_item_id: int,
        text_ru: str,
        text_uz: str
    ) -> MenuContent:
        """Add text content to menu item"""
        # Get next order_index for this menu item's content
        stmt = select(func.max(MenuContent.order_index)).where(
            MenuContent.menu_item_id == menu_item_id
        )
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        
        content = MenuContent(
            menu_item_id=menu_item_id,
            content_type="TEXT",
            text_ru=text_ru,
            text_uz=text_uz,
            order_index=max_order + 1
        )
        
        session.add(content)
        await session.commit()
        await session.refresh(content)
        
        logger.info(f"[MenuService] ✅ Добавлен TEXT контент для пункта меню ID={menu_item_id}")
        return content

    @staticmethod
    async def add_photo_content(
        session: AsyncSession,
        menu_item_id: int,
        file_id: str,
        caption_ru: str = None,
        caption_uz: str = None
    ) -> MenuContent:
        """Add photo content to menu item"""
        stmt = select(func.max(MenuContent.order_index)).where(
            MenuContent.menu_item_id == menu_item_id
        )
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        
        content = MenuContent(
            menu_item_id=menu_item_id,
            content_type="PHOTO",
            file_id=file_id,
            caption_ru=caption_ru,
            caption_uz=caption_uz,
            order_index=max_order + 1
        )
        
        session.add(content)
        await session.commit()
        await session.refresh(content)
        
        logger.info(f"[MenuService] ✅ Добавлен PHOTO контент для пункта меню ID={menu_item_id}")
        return content

    @staticmethod
    async def add_pdf_content(
        session: AsyncSession,
        menu_item_id: int,
        file_id: str,
        caption_ru: str = None,
        caption_uz: str = None
    ) -> MenuContent:
        """Add PDF content to menu item"""
        stmt = select(func.max(MenuContent.order_index)).where(
            MenuContent.menu_item_id == menu_item_id
        )
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        
        content = MenuContent(
            menu_item_id=menu_item_id,
            content_type="PDF",
            file_id=file_id,
            caption_ru=caption_ru,
            caption_uz=caption_uz,
            order_index=max_order + 1
        )
        
        session.add(content)
        await session.commit()
        await session.refresh(content)
        
        logger.info(f"[MenuService] ✅ Добавлен PDF контент для пункта меню ID={menu_item_id}")
        return content

    @staticmethod
    async def add_audio_content(
        session: AsyncSession,
        menu_item_id: int,
        file_id: str,
        caption_ru: str = None,
        caption_uz: str = None
    ) -> MenuContent:
        """Add audio content to menu item"""
        stmt = select(func.max(MenuContent.order_index)).where(
            MenuContent.menu_item_id == menu_item_id
        )
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        
        content = MenuContent(
            menu_item_id=menu_item_id,
            content_type="AUDIO",
            file_id=file_id,
            caption_ru=caption_ru,
            caption_uz=caption_uz,
            order_index=max_order + 1
        )
        
        session.add(content)
        await session.commit()
        await session.refresh(content)
        
        logger.info(f"[MenuService] ✅ Добавлен AUDIO контент для пункта меню ID={menu_item_id}")
        return content

    @staticmethod
    async def add_location_content(
        session: AsyncSession,
        menu_item_id: int,
        location_type: str,
        address_text: str = None,
        latitude: float = None,
        longitude: float = None,
        geo_name: str = None,
        maps_url: str = None
    ) -> MenuContent:
        """Add location content to menu item"""
        stmt = select(func.max(MenuContent.order_index)).where(
            MenuContent.menu_item_id == menu_item_id
        )
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        
        content = MenuContent(
            menu_item_id=menu_item_id,
            content_type="LOCATION",
            location_type=location_type,
            address_text=address_text,
            latitude=latitude,
            longitude=longitude,
            geo_name=geo_name,
            maps_url=maps_url,
            order_index=max_order + 1
        )
        
        session.add(content)
        await session.commit()
        await session.refresh(content)
        
        logger.info(f"[MenuService] ✅ Добавлен LOCATION контент для пункта меню ID={menu_item_id}")
        return content

    @staticmethod
    async def delete_content(
        session: AsyncSession,
        content_id: int
    ) -> bool:
        """Delete menu content"""
        stmt = select(MenuContent).where(MenuContent.id == content_id)
        result = await session.execute(stmt)
        content = result.scalar_one_or_none()
        
        if not content:
            return False
        
        await session.delete(content)
        await session.commit()
        
        logger.info(f"[MenuService] ✅ Удален контент ID={content_id}")
        return True

    # ═══════════════════════════════════════════════════════════════════════
    # MENU BUTTON CRUD
    # ═══════════════════════════════════════════════════════════════════════

    @staticmethod
    async def add_button(
        session: AsyncSession,
        menu_item_id: int,
        button_type: str,
        text_ru: str,
        text_uz: str,
        action_type: str,
        action_data: Dict[str, Any]
    ) -> MenuButton:
        """Add button to menu item"""
        stmt = select(func.max(MenuButton.order_index)).where(
            MenuButton.menu_item_id == menu_item_id
        )
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        
        button = MenuButton(
            menu_item_id=menu_item_id,
            button_type=button_type,
            text_ru=text_ru,
            text_uz=text_uz,
            action_type=action_type,
            action_data=action_data,
            order_index=max_order + 1
        )
        
        session.add(button)
        await session.commit()
        await session.refresh(button)
        
        logger.info(f"[MenuService] ✅ Добавлена кнопка для пункта меню ID={menu_item_id}, type={button_type}, action={action_type}")
        return button

    @staticmethod
    async def delete_button(
        session: AsyncSession,
        button_id: int
    ) -> bool:
        """Delete menu button"""
        stmt = select(MenuButton).where(MenuButton.id == button_id)
        result = await session.execute(stmt)
        button = result.scalar_one_or_none()
        
        if not button:
            return False
        
        await session.delete(button)
        await session.commit()
        
        logger.info(f"[MenuService] ✅ Удалена кнопка ID={button_id}")
        return True
