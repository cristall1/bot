from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime

from models import MainMenuButton
from utils.logger import logger


class MainMenuService:
    """Service layer for managing main menu inline buttons"""

    # ════════════════════════════════════════════════════════════════════════
    # READ OPERATIONS
    # ════════════════════════════════════════════════════════════════════════
    @staticmethod
    async def get_active_buttons(session: AsyncSession) -> List[MainMenuButton]:
        """Return all active buttons ordered by order_index"""
        stmt = (
            select(MainMenuButton)
            .where(MainMenuButton.is_active == True)
            .order_by(MainMenuButton.order_index, MainMenuButton.id)
        )

        result = await session.execute(stmt)
        buttons = result.scalars().all()
        logger.info(
            "[MainMenuService] ✅ Загружено %s активных кнопок главного меню",
            len(buttons),
        )
        return list(buttons)

    @staticmethod
    async def get_button_by_callback(
        session: AsyncSession, callback_data: str
    ) -> Optional[MainMenuButton]:
        """Return button by callback data"""
        stmt = select(MainMenuButton).where(
            MainMenuButton.callback_data == callback_data
        )

        result = await session.execute(stmt)
        button = result.scalar_one_or_none()

        if button:
            logger.info(
                "[MainMenuService] ✅ Найдена кнопка главного меню по callback '%s' (ID=%s)",
                callback_data,
                button.id,
            )
        else:
            logger.warning(
                "[MainMenuService] ⚠️ Кнопка главного меню по callback '%s' не найдена",
                callback_data,
            )
        return button

    @staticmethod
    async def get_button_by_id(
        session: AsyncSession, button_id: int
    ) -> Optional[MainMenuButton]:
        stmt = select(MainMenuButton).where(MainMenuButton.id == button_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    # ════════════════════════════════════════════════════════════════════════
    # WRITE OPERATIONS
    # ════════════════════════════════════════════════════════════════════════
    @staticmethod
    async def create_button(
        session: AsyncSession,
        name_ru: str,
        name_uz: str,
        callback_data: str,
        icon: Optional[str] = None,
        is_active: bool = True,
    ) -> MainMenuButton:
        stmt = select(func.max(MainMenuButton.order_index))
        result = await session.execute(stmt)
        max_order = result.scalar() or 0

        button = MainMenuButton(
            name_ru=name_ru,
            name_uz=name_uz,
            icon=icon,
            callback_data=callback_data,
            order_index=max_order + 1,
            is_active=is_active,
        )
        session.add(button)
        await session.commit()
        await session.refresh(button)
        logger.info(
            "[MainMenuService] ✅ Создана кнопка главного меню %s (ID=%s)",
            name_ru,
            button.id,
        )
        return button

    @staticmethod
    async def update_button(
        session: AsyncSession,
        button_id: int,
        **kwargs,
    ) -> Optional[MainMenuButton]:
        button = await MainMenuService.get_button_by_id(session, button_id)
        if not button:
            logger.warning(
                "[MainMenuService] ⚠️ Попытка обновить отсутствующую кнопку ID=%s",
                button_id,
            )
            return None

        for field, value in kwargs.items():
            if hasattr(button, field):
                setattr(button, field, value)
        button.updated_at = datetime.utcnow()

        await session.commit()
        await session.refresh(button)
        logger.info(
            "[MainMenuService] ✅ Обновлена кнопка главного меню ID=%s",
            button_id,
        )
        return button

    @staticmethod
    async def toggle_button(
        session: AsyncSession, button_id: int
    ) -> Optional[bool]:
        button = await MainMenuService.get_button_by_id(session, button_id)
        if not button:
            return None

        button.is_active = not button.is_active
        button.updated_at = datetime.utcnow()
        await session.commit()
        logger.info(
            "[MainMenuService] ✅ Переключен статус кнопки ID=%s → %s",
            button_id,
            "ON" if button.is_active else "OFF",
        )
        return button.is_active

    @staticmethod
    async def delete_button(session: AsyncSession, button_id: int) -> bool:
        button = await MainMenuService.get_button_by_id(session, button_id)
        if not button:
            return False

        await session.delete(button)
        await session.commit()
        logger.info(
            "[MainMenuService] ✅ Удалена кнопка главного меню ID=%s",
            button_id,
        )
        return True

    @staticmethod
    async def reorder_button(
        session: AsyncSession,
        button_id: int,
        direction: str,
    ) -> bool:
        button = await MainMenuService.get_button_by_id(session, button_id)
        if not button:
            return False

        current_order = button.order_index
        if direction == "up":
            stmt = (
                select(MainMenuButton)
                .where(MainMenuButton.order_index < current_order)
                .order_by(MainMenuButton.order_index.desc())
                .limit(1)
            )
        else:
            stmt = (
                select(MainMenuButton)
                .where(MainMenuButton.order_index > current_order)
                .order_by(MainMenuButton.order_index.asc())
                .limit(1)
            )

        result = await session.execute(stmt)
        swap_button = result.scalar_one_or_none()
        if not swap_button:
            return False

        button.order_index, swap_button.order_index = (
            swap_button.order_index,
            button.order_index,
        )
        button.updated_at = datetime.utcnow()
        swap_button.updated_at = datetime.utcnow()
        await session.commit()
        logger.info(
            "[MainMenuService] ✅ Перемещена кнопка ID=%s направление=%s",
            button_id,
            direction,
        )
        return True
