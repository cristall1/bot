from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from models import ShurtaAlert
from utils.logger import logger


class ShurtaService:
    """Service for police alert management"""
    
    @staticmethod
    async def create_alert(
        session: AsyncSession,
        creator_id: int,
        description: str,
        location_info: str,
        google_maps_url: str = None,
        coordinates: str = None,
        photo_url: str = None
    ) -> ShurtaAlert:
        """Create new police alert"""
        alert = ShurtaAlert(
            creator_id=creator_id,
            description=description,
            location_info=location_info,
            google_maps_url=google_maps_url,
            coordinates=coordinates,
            photo_url=photo_url
        )
        session.add(alert)
        await session.commit()
        await session.refresh(alert)
        logger.info(f"Shurta alert created by user {creator_id}")
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
        """Get all active alerts"""
        query = select(ShurtaAlert).where(
            ShurtaAlert.is_active == True
        ).order_by(ShurtaAlert.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
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
