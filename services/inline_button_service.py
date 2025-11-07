from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from models import InlineButton
from utils.logger import logger


class InlineButtonService:
    """Service for inline button management"""
    
    @staticmethod
    async def create_button(
        session: AsyncSession,
        category_id: int,
        button_text_ru: str,
        button_text_uz: str,
        button_url: str,
        button_type: str = "LINK",
        order_index: int = 0,
        created_by_admin_id: int = None
    ) -> InlineButton:
        """Create new inline button"""
        button = InlineButton(
            category_id=category_id,
            button_text_ru=button_text_ru,
            button_text_uz=button_text_uz,
            button_url=button_url,
            button_type=button_type,
            order_index=order_index,
            created_by_admin_id=created_by_admin_id
        )
        session.add(button)
        await session.commit()
        await session.refresh(button)
        logger.info(f"Button created: {button_text_ru} for category {category_id}")
        return button
    
    @staticmethod
    async def get_button(session: AsyncSession, button_id: int) -> Optional[InlineButton]:
        """Get button by ID"""
        result = await session.execute(
            select(InlineButton).where(InlineButton.id == button_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_buttons_by_category(
        session: AsyncSession,
        category_id: int,
        active_only: bool = True
    ) -> List[InlineButton]:
        """Get all buttons for a category"""
        query = select(InlineButton).where(InlineButton.category_id == category_id)
        
        if active_only:
            query = query.where(InlineButton.is_active == True)
        
        query = query.order_by(InlineButton.order_index, InlineButton.id)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_all_buttons(session: AsyncSession) -> List[InlineButton]:
        """Get all buttons"""
        result = await session.execute(
            select(InlineButton).order_by(InlineButton.category_id, InlineButton.order_index)
        )
        return result.scalars().all()
    
    @staticmethod
    async def update_button(
        session: AsyncSession,
        button_id: int,
        **kwargs
    ) -> Optional[InlineButton]:
        """Update button"""
        button = await InlineButtonService.get_button(session, button_id)
        if not button:
            return None
        
        for key, value in kwargs.items():
            if hasattr(button, key):
                setattr(button, key, value)
        
        await session.commit()
        await session.refresh(button)
        logger.info(f"Button updated: {button.button_text_ru} (ID: {button_id})")
        return button
    
    @staticmethod
    async def delete_button(session: AsyncSession, button_id: int) -> bool:
        """Delete button"""
        button = await InlineButtonService.get_button(session, button_id)
        if not button:
            return False
        
        await session.delete(button)
        await session.commit()
        logger.info(f"Button deleted: ID {button_id}")
        return True
    
    @staticmethod
    async def toggle_button(session: AsyncSession, button_id: int) -> Optional[InlineButton]:
        """Toggle button active status"""
        button = await InlineButtonService.get_button(session, button_id)
        if not button:
            return None
        
        button.is_active = not button.is_active
        await session.commit()
        await session.refresh(button)
        logger.info(f"Button toggled: {button.button_text_ru} (ID: {button_id}, Active: {button.is_active})")
        return button
    
    @staticmethod
    async def reorder_buttons(
        session: AsyncSession,
        category_id: int,
        button_ids: List[int]
    ) -> bool:
        """Reorder buttons in a category"""
        for index, button_id in enumerate(button_ids):
            button = await InlineButtonService.get_button(session, button_id)
            if button and button.category_id == category_id:
                button.order_index = index
        
        await session.commit()
        logger.info(f"Buttons reordered for category {category_id}")
        return True
