from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from models import Notification
from utils.logger import logger


class NotificationService:
    """Service for notification management (lost people/items)"""
    
    @staticmethod
    async def create_notification(
        session: AsyncSession,
        notification_type: str,
        creator_id: int,
        title_ru: str,
        title_uz: str,
        description_ru: str,
        description_uz: str,
        location_type: str,
        address_text: str = None,
        latitude: float = None,
        longitude: float = None,
        geo_name: str = None,
        maps_url: str = None,
        phone: str = None,
        photo_file_id: str = None
    ) -> Notification:
        """Create new notification (requires admin approval)"""
        logger.info(f"[create_notification] Started | creator_id={creator_id}, type={notification_type}")
        try:
            notification = Notification(
                type=notification_type,
                creator_id=creator_id,
                title_ru=title_ru,
                title_uz=title_uz,
                description_ru=description_ru,
                description_uz=description_uz,
                location_type=location_type,
                address_text=address_text,
                latitude=latitude,
                longitude=longitude,
                geo_name=geo_name,
                maps_url=maps_url,
                phone=phone,
                photo_file_id=photo_file_id,
                is_approved=False,  # Requires admin approval
                is_moderated=False,
                is_active=True,
                expires_at=datetime.utcnow() + timedelta(hours=48)  # Auto-expire after 48 hours
            )
            session.add(notification)
            await session.commit()
            await session.refresh(notification)
            logger.info(f"[create_notification] ✅ Success | notification_id={notification.id}")
            return notification
        except Exception as e:
            logger.error(f"[create_notification] ❌ Error | {str(e)}")
            raise
    
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
        """Get all active and approved notifications"""
        query = select(Notification).where(
            Notification.is_active == True,
            Notification.is_approved == True,
            Notification.is_moderated == True,
            Notification.expires_at > datetime.utcnow()  # Not expired
        )
        
        if notification_type:
            query = query.where(Notification.type == notification_type)
        
        query = query.order_by(Notification.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_pending_notifications(
        session: AsyncSession,
        notification_type: str = None
    ) -> List[Notification]:
        """Get notifications pending admin approval"""
        query = select(Notification).where(
            Notification.is_active == True,
            Notification.is_approved == False,
            Notification.is_moderated == False
        )
        
        if notification_type:
            query = query.where(Notification.type == notification_type)
        
        query = query.order_by(Notification.created_at.asc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def approve_notification(
        session: AsyncSession,
        notification_id: int,
        moderator_id: int
    ) -> Optional[Notification]:
        """Approve notification (admin action)"""
        notification = await NotificationService.get_notification(session, notification_id)
        if not notification:
            return None
        
        notification.is_approved = True
        notification.is_moderated = True
        notification.moderator_id = moderator_id
        notification.moderated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(notification)
        logger.info(f"Notification {notification_id} approved by admin {moderator_id}")
        return notification
    
    @staticmethod
    async def reject_notification(
        session: AsyncSession,
        notification_id: int,
        moderator_id: int
    ) -> Optional[Notification]:
        """Reject notification (admin action)"""
        notification = await NotificationService.get_notification(session, notification_id)
        if not notification:
            return None
        
        notification.is_approved = False
        notification.is_moderated = True
        notification.moderator_id = moderator_id
        notification.moderated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(notification)
        logger.info(f"Notification {notification_id} rejected by admin {moderator_id}")
        return notification
    
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
