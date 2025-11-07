from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from models import User, Notification, ShurtaAlert, Broadcast
from utils.logger import logger


class SmartNotificationService:
    """Service for smart notifications and broadcasting"""
    
    @staticmethod
    async def check_duplicate_notification(
        session: AsyncSession,
        user_id: int,
        title: str,
        description: str,
        time_window_hours: int = 1
    ) -> bool:
        """Check if user already sent similar notification within time window"""
        time_threshold = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        result = await session.execute(
            select(Notification).where(
                and_(
                    Notification.creator_id == user_id,
                    or_(
                        Notification.title.ilike(f"%{title}%"),
                        Notification.description.ilike(f"%{description}%")
                    ),
                    Notification.created_at > time_threshold
                )
            )
        )
        
        duplicates = result.scalars().all()
        return len(duplicates) > 0
    
    @staticmethod
    async def validate_notification_content(
        title: str,
        description: str,
        phone: str
    ) -> Dict[str, Any]:
        """Validate notification content"""
        errors = []
        
        if not title or len(title.strip()) < 3:
            errors.append("Title must be at least 3 characters")
        
        if not description or len(description.strip()) < 10:
            errors.append("Description must be at least 10 characters")
        
        if not phone or len(phone.strip()) < 5:
            errors.append("Phone number is required")
        
        # Check for spam patterns
        spam_keywords = ["spam", "advertisement", "реклама", "рекламу"]
        text_lower = (title + " " + description).lower()
        
        for keyword in spam_keywords:
            if keyword in text_lower:
                errors.append(f"Spam content detected: {keyword}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    async def get_target_audience(
        session: AsyncSession,
        filter_type: str = "ALL",
        citizenship: str = None,
        language: str = None
    ) -> List[User]:
        """Get target audience for broadcasting"""
        query = select(User).where(User.is_banned == False)
        
        # Apply filters
        if filter_type == "RU":
            query = query.where(User.language == "RU")
        elif filter_type == "UZ":
            query = query.where(User.language == "UZ")
        elif filter_type == "COURIERS":
            query = query.where(User.is_courier == True)
        elif filter_type.startswith("CITIZENSHIP_"):
            citizenship_filter = filter_type.replace("CITIZENSHIP_", "")
            query = query.where(User.citizenship == citizenship_filter)
        
        if citizenship:
            query = query.where(User.citizenship == citizenship)
        
        if language:
            query = query.where(User.language == language)
        
        # Only users with notifications enabled
        query = query.where(User.notifications_enabled == True)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def send_broadcast_with_progress(
        session: AsyncSession,
        bot,
        broadcast_id: int,
        message_ru: str,
        message_uz: str = None,
        photo_file_id: str = None,
        recipient_filter: str = "ALL",
        rate_limit: float = 0.08  # 80ms delay between messages
    ) -> Dict[str, Any]:
        """Send broadcast with rate limiting and progress tracking"""
        import asyncio
        
        # Get target audience
        recipients = await SmartNotificationService.get_target_audience(
            session, recipient_filter
        )
        
        total_recipients = len(recipients)
        successful_sends = 0
        failed_sends = 0
        
        logger.info(f"Starting broadcast to {total_recipients} recipients")
        
        for i, user in enumerate(recipients):
            try:
                # Choose appropriate language
                message_text = message_uz if user.language == "UZ" and message_uz else message_ru
                
                if photo_file_id:
                    await bot.send_photo(
                        chat_id=user.telegram_id,
                        photo=photo_file_id,
                        caption=message_text
                    )
                else:
                    await bot.send_message(
                        chat_id=user.telegram_id,
                        text=message_text
                    )
                
                successful_sends += 1
                
                # Rate limiting
                if i < total_recipients - 1:  # Don't delay after last message
                    await asyncio.sleep(rate_limit)
                
                # Progress update every 50 messages
                if (i + 1) % 50 == 0:
                    progress = ((i + 1) / total_recipients) * 100
                    logger.info(f"Broadcast progress: {i + 1}/{total_recipients} ({progress:.1f}%)")
                    
            except Exception as e:
                failed_sends += 1
                logger.error(f"Failed to send broadcast to user {user.telegram_id}: {e}")
        
        # Update broadcast record
        from services.broadcast_service import BroadcastService
        await BroadcastService.mark_as_sent(
            session, broadcast_id, successful_sends
        )
        
        result = {
            "total": total_recipients,
            "successful": successful_sends,
            "failed": failed_sends,
            "success_rate": (successful_sends / total_recipients * 100) if total_recipients > 0 else 0
        }
        
        logger.info(f"Broadcast completed: {result}")
        return result
    
    @staticmethod
    async def cleanup_expired_notifications(session: AsyncSession) -> Dict[str, int]:
        """Clean up expired notifications and alerts"""
        now = datetime.utcnow()
        
        # Clean expired notifications
        expired_notifications_query = select(Notification).where(
            and_(
                Notification.expires_at < now,
                Notification.is_active == True
            )
        )
        notif_result = await session.execute(expired_notifications_query)
        expired_notifications = notif_result.scalars().all()
        
        for notification in expired_notifications:
            notification.is_active = False
        
        # Clean expired shurta alerts
        expired_alerts_query = select(ShurtaAlert).where(
            and_(
                ShurtaAlert.expires_at < now,
                ShurtaAlert.is_active == True
            )
        )
        alert_result = await session.execute(expired_alerts_query)
        expired_alerts = alert_result.scalars().all()
        
        for alert in expired_alerts:
            alert.is_active = False
        
        await session.commit()
        
        return {
            "notifications_cleaned": len(expired_notifications),
            "alerts_cleaned": len(expired_alerts)
        }
    
    @staticmethod
    async def get_notification_stats(session: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive notification statistics"""
        from sqlalchemy import func
        
        # Total notifications
        total_notifs = await session.execute(select(func.count(Notification.id)))
        total_notifications = total_notifs.scalar()
        
        # Active notifications
        active_notifs = await session.execute(
            select(func.count(Notification.id)).where(
                and_(
                    Notification.is_active == True,
                    Notification.is_approved == True
                )
            )
        )
        active_notifications = active_notifs.scalar()
        
        # Pending notifications
        pending_notifs = await session.execute(
            select(func.count(Notification.id)).where(
                and_(
                    Notification.is_active == True,
                    Notification.is_approved == False,
                    Notification.is_moderated == False
                )
            )
        )
        pending_notifications = pending_notifs.scalar()
        
        # Total alerts
        total_alerts = await session.execute(select(func.count(ShurtaAlert.id)))
        total_shurta_alerts = total_alerts.scalar()
        
        # Active alerts
        active_alerts = await session.execute(
            select(func.count(ShurtaAlert.id)).where(
                and_(
                    ShurtaAlert.is_active == True,
                    ShurtaAlert.is_approved == True
                )
            )
        )
        active_shurta_alerts = active_alerts.scalar()
        
        # Pending alerts
        pending_alerts = await session.execute(
            select(func.count(ShurtaAlert.id)).where(
                and_(
                    ShurtaAlert.is_active == True,
                    ShurtaAlert.is_approved == False,
                    ShurtaAlert.is_moderated == False
                )
            )
        )
        pending_shurta_alerts = pending_alerts.scalar()
        
        return {
            "notifications": {
                "total": total_notifications,
                "active": active_notifications,
                "pending": pending_notifications
            },
            "shurta_alerts": {
                "total": total_shurta_alerts,
                "active": active_shurta_alerts,
                "pending": pending_shurta_alerts
            }
        }