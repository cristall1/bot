from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
from models import ShurtaAlert
from utils.logger import logger


class ShurtaService:
    """Service for police alert management"""
    
    @staticmethod
    async def create_alert(
        session: AsyncSession,
        creator_id: int,
        description: str,
        location_type: str,
        address_text: str = None,
        latitude: float = None,
        longitude: float = None,
        geo_name: str = None,
        maps_url: str = None,
        photo_file_id: str = None
    ) -> ShurtaAlert:
        """Create new police alert (requires admin approval)"""
        alert = ShurtaAlert(
            creator_id=creator_id,
            description=description,
            location_type=location_type,
            address_text=address_text,
            latitude=latitude,
            longitude=longitude,
            geo_name=geo_name,
            maps_url=maps_url,
            photo_file_id=photo_file_id,
            is_approved=False,  # Requires admin approval
            is_moderated=False,
            expires_at=datetime.utcnow() + timedelta(hours=48)  # Auto-expire after 48 hours
        )
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        logger.info(f"Shurta alert created by user {creator_id} (pending approval)")
        return alert
    
    @staticmethod
    async def get_alert(session: AsyncSession, alert_id: int) -> Optional[ShurtaAlert]:
        """Get alert by ID"""
        result = await session.execute(
            select(ShurtaAlert).where(ShurtaAlert.id == alert_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_alerts(session: AsyncSession) -> List[ShurtaAlert]:
        """Get all active and approved alerts (not expired)"""
        query = select(ShurtaAlert).where(
            ShurtaAlert.is_active == True,
            ShurtaAlert.is_approved == True,
            ShurtaAlert.is_moderated == True,
            ShurtaAlert.expires_at > datetime.utcnow()  # Not expired
        ).order_by(ShurtaAlert.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_pending_alerts(session: AsyncSession) -> List[ShurtaAlert]:
        """Get alerts pending admin approval"""
        query = select(ShurtaAlert).where(
            ShurtaAlert.is_active == True,
            ShurtaAlert.is_approved == False,
            ShurtaAlert.is_moderated == False
        ).order_by(ShurtaAlert.created_at.asc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def approve_alert(
        session: AsyncSession,
        alert_id: int,
        moderator_id: int
    ) -> Optional[ShurtaAlert]:
        """Approve alert (admin action)"""
        alert = await ShurtaService.get_alert(session, alert_id)
        if not alert:
            return None
        
        alert.is_approved = True
        alert.is_moderated = True
        alert.moderator_id = moderator_id
        alert.moderated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(alert)
        logger.info(f"Shurta alert {alert_id} approved by admin {moderator_id}")
        return alert
    
    @staticmethod
    async def reject_alert(
        session: AsyncSession,
        alert_id: int,
        moderator_id: int
    ) -> Optional[ShurtaAlert]:
        """Reject alert (admin action)"""
        alert = await ShurtaService.get_alert(session, alert_id)
        if not alert:
            return None
        
        alert.is_approved = False
        alert.is_moderated = True
        alert.moderator_id = moderator_id
        alert.moderated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(alert)
        logger.info(f"Shurta alert {alert_id} rejected by admin {moderator_id}")
        return alert
    
    @staticmethod
    async def get_all_alerts(session: AsyncSession) -> List[ShurtaAlert]:
        """Get all alerts (including inactive)"""
        query = select(ShurtaAlert).order_by(ShurtaAlert.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_alerts(session: AsyncSession, user_id: int) -> List[ShurtaAlert]:
        """Get alerts created by user"""
        query = select(ShurtaAlert).where(
            ShurtaAlert.creator_id == user_id
        ).order_by(ShurtaAlert.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def deactivate_alert(
        session: AsyncSession,
        alert_id: int
    ) -> Optional[ShurtaAlert]:
        """Deactivate alert"""
        alert = await ShurtaService.get_alert(session, alert_id)
        if not alert:
            return None
        
        alert.is_active = False
        await session.commit()
        await session.refresh(alert)
        logger.info(f"Shurta alert {alert_id} deactivated")
        return alert
    
    @staticmethod
    async def delete_alert(session: AsyncSession, alert_id: int) -> bool:
        """Delete alert"""
        alert = await ShurtaService.get_alert(session, alert_id)
        if not alert:
            return False
        
        await session.delete(alert)
        await session.commit()
        logger.info(f"Shurta alert {alert_id} deleted")
        return True
    
    @staticmethod
    async def get_alert_stats(session: AsyncSession) -> dict:
        """Get alert statistics"""
        total_result = await session.execute(
            select(func.count(ShurtaAlert.id))
        )
        total = total_result.scalar()
        
        active_result = await session.execute(
            select(func.count(ShurtaAlert.id)).where(ShurtaAlert.is_active == True)
        )
        active = active_result.scalar()
        
        return {
            "total": total,
            "active": active
        }
