"""Dynamic Menu Service"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime
from models import MainMenu, MenuFilter, MenuFilterOption, Category
from utils.logger import logger


class DynamicMenuService:
    @staticmethod
    async def get_all_menus(session: AsyncSession, active_only: bool = True) -> List[MainMenu]:
        stmt = select(MainMenu).options(
            selectinload(MainMenu.filters).selectinload(MenuFilter.options),
            selectinload(MainMenu.categories)
        ).order_by(MainMenu.order_index)
        if active_only:
            stmt = stmt.where(MainMenu.is_active == True)
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())
    
    @staticmethod
    async def get_menu_by_id(session: AsyncSession, menu_id: int) -> Optional[MainMenu]:
        stmt = select(MainMenu).options(
            selectinload(MainMenu.filters).selectinload(MenuFilter.options),
            selectinload(MainMenu.categories)
        ).where(MainMenu.id == menu_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def create_menu(session: AsyncSession, name_ru: str, name_uz: str, icon: str = None) -> MainMenu:
        stmt = select(func.max(MainMenu.order_index))
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        menu = MainMenu(name_ru=name_ru, name_uz=name_uz, icon=icon, order_index=max_order + 1)
        session.add(menu)
        await session.commit()
        await session.refresh(menu)
        logger.info(f"[DynamicMenuService] ✅ Создано меню: {name_ru}")
        return menu
    
    @staticmethod
    async def toggle_menu(session: AsyncSession, menu_id: int) -> Optional[bool]:
        menu = await DynamicMenuService.get_menu_by_id(session, menu_id)
        if not menu:
            return None
        menu.is_active = not menu.is_active
        menu.updated_at = datetime.utcnow()
        await session.commit()
        return menu.is_active
    
    @staticmethod
    async def delete_menu(session: AsyncSession, menu_id: int) -> bool:
        menu = await DynamicMenuService.get_menu_by_id(session, menu_id)
        if not menu:
            return False
        await session.delete(menu)
        await session.commit()
        return True


class MenuFilterService:
    @staticmethod
    async def create_filter(session: AsyncSession, main_menu_id: int, name_ru: str, name_uz: str) -> MenuFilter:
        stmt = select(func.max(MenuFilter.order_index)).where(MenuFilter.main_menu_id == main_menu_id)
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        filter_obj = MenuFilter(main_menu_id=main_menu_id, name_ru=name_ru, name_uz=name_uz, order_index=max_order + 1)
        session.add(filter_obj)
        await session.commit()
        await session.refresh(filter_obj)
        logger.info(f"[MenuFilterService] ✅ Создан фильтр: {name_ru}")
        return filter_obj
    
    @staticmethod
    async def get_filter_by_id(session: AsyncSession, filter_id: int) -> Optional[MenuFilter]:
        stmt = select(MenuFilter).options(selectinload(MenuFilter.options)).where(MenuFilter.id == filter_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_filter(session: AsyncSession, filter_id: int) -> bool:
        filter_obj = await MenuFilterService.get_filter_by_id(session, filter_id)
        if not filter_obj:
            return False
        await session.delete(filter_obj)
        await session.commit()
        return True


class MenuFilterOptionService:
    @staticmethod
    async def create_option(session: AsyncSession, filter_id: int, name_ru: str, name_uz: str, icon: str = None) -> MenuFilterOption:
        stmt = select(func.max(MenuFilterOption.order_index)).where(MenuFilterOption.filter_id == filter_id)
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        option = MenuFilterOption(filter_id=filter_id, name_ru=name_ru, name_uz=name_uz, icon=icon, order_index=max_order + 1)
        session.add(option)
        await session.commit()
        await session.refresh(option)
        logger.info(f"[MenuFilterOptionService] ✅ Создана опция: {name_ru}")
        return option
    
    @staticmethod
    async def get_option_by_id(session: AsyncSession, option_id: int) -> Optional[MenuFilterOption]:
        stmt = select(MenuFilterOption).where(MenuFilterOption.id == option_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def delete_option(session: AsyncSession, option_id: int) -> bool:
        option = await MenuFilterOptionService.get_option_by_id(session, option_id)
        if not option:
            return False
        await session.delete(option)
        await session.commit()
        return True


class CategoryContentService:
    @staticmethod
    async def create_content(session: AsyncSession, category_id: int, content_type: str, **kwargs) -> 'CategoryContent':
        from models import CategoryContent
        stmt = select(func.max(CategoryContent.order_index)).where(CategoryContent.category_id == category_id)
        result = await session.execute(stmt)
        max_order = result.scalar() or 0
        content = CategoryContent(category_id=category_id, content_type=content_type, order_index=max_order + 1, **kwargs)
        session.add(content)
        await session.commit()
        await session.refresh(content)
        logger.info(f"[CategoryContentService] ✅ Создан контент: {content_type}")
        return content
    
    @staticmethod
    async def delete_content(session: AsyncSession, content_id: int) -> bool:
        from models import CategoryContent
        stmt = select(CategoryContent).where(CategoryContent.id == content_id)
        result = await session.execute(stmt)
        content = result.scalar_one_or_none()
        if not content:
            return False
        await session.delete(content)
        await session.commit()
        return True
