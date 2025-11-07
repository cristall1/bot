from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from models import Notification
from utils.logger import logger


class NotificationService:
    """Service for notification management (lost people/items)"""
    
    @staticmethod
    async def create_notification(
        session: AsyncSession,
        notification_type: str,
        creator_id: int,
        title: str,
        description: str,
        location: str,
        phone: str,
        photo_url: str = None
    ) -> Notification:
        """Create new notification"""
        notification = Notification(
            type=notification_type,
            creator_id=creator_id,
            title=title,
            description=description,
            location=location,
            phone=phone,
            photo_url=photo_url
        )
        session.add(notification)
        await session.commit()
        await session.refresh(notification)
        logger.info(f"Notification created: {notification_type} by user {creator_id}")
        return notification
    
    @staticmethod
    async def get_notification(session: AsyncSession, notification_id: int) -> Optional[Notification]:
        """Get notification by ID"""
        result = await session.execute(
            select(Notification).where(Notification.id == notification_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_notifications(
        session: AsyncSession,
        notification_type: str = None
    ) -> List[Notification]:
        """Get all active notifications"""
        query = select(Notification).where(Notification.is_active == True)
        
        if notification_type:
            query = query.where(Notification.type == notification_type)
        
        query = query.order_by(Notification.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_notifications(
        session: AsyncSession,
        user_id: int
    ) -> List[Notification]:
        """Get notifications created by user"""
        query = select(Notification).where(
            Notification.creator_id == user_id
        ).order_by(Notification.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def deactivate_notification(
        session: AsyncSession,
        notification_id: int,
        user_id: int = None
    ) -> Optional[Notification]:
        """Deactivate notification (only creator or admin)"""
        notification = await NotificationService.get_notification(session, notification_id)
        if not notification:
            return None
        
        # If user_id is provided, check ownership
        if user_id and notification.creator_id != user_id:
            return None
        
        notification.is_active = False
        await session.commit()
        await session.refresh(notification)
        logger.info(f"Notification {notification_id} deactivated")
        return notification
    
    @staticmethod
    async def delete_notification(
        session: AsyncSession,
        notification_id: int
    ) -> bool:
        """Delete notification"""
        notification = await NotificationService.get_notification(session, notification_id)
        if not notification:
            return False
        
        await session.delete(notification)
        await session.commit()
        logger.info(f"Notification {notification_id} deleted")
        return True
    
    @staticmethod
    async def get_notification_stats(session: AsyncSession) -> dict:
        """Get notification statistics"""
        total_result = await session.execute(
            select(func.count(Notification.id))
        )
        total = total_result.scalar()
        
        active_result = await session.execute(
            select(func.count(Notification.id)).where(Notification.is_active == True)
        )
        active = active_result.scalar()
        
        lost_person_result = await session.execute(
            select(func.count(Notification.id)).where(
                Notification.type == "PROPAJA_ODAM",
                Notification.is_active == True
            )
        )
        lost_person = lost_person_result.scalar()
        
        lost_item_result = await session.execute(
            select(func.count(Notification.id)).where(
                Notification.type == "PROPAJA_NARSA",
                Notification.is_active == True
            )
        )
        lost_item = lost_item_result.scalar()
        
        return {
            "total": total,
            "active": active,
            "lost_person": lost_person,
            "lost_item": lost_item
        }
