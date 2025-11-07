from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from models import Broadcast
from utils.logger import logger


class BroadcastService:
    """Service for broadcast management"""
    
    @staticmethod
    async def create_broadcast(
        session: AsyncSession,
        admin_id: int,
        name_ru: str,
        name_uz: str,
        message_ru: str,
        message_uz: str = None,
        photo_file_id: str = None,
        recipient_filter: str = "ALL"
    ) -> Broadcast:
        """Create new broadcast"""
        broadcast = Broadcast(
            admin_id=admin_id,
            name_ru=name_ru,
            name_uz=name_uz,
            message_ru=message_ru,
            message_uz=message_uz,
            photo_file_id=photo_file_id,
            recipient_filter=recipient_filter,
            is_sent=False,
            recipient_count=0
        )
        session.add(broadcast)
        await session.commit()
        await session.refresh(broadcast)
        logger.info(f"Broadcast created by admin {admin_id}")
        return broadcast
    
    @staticmethod
    async def mark_as_sent(
        session: AsyncSession,
        broadcast_id: int,
        recipient_count: int
    ) -> Optional[Broadcast]:
        """Mark broadcast as sent"""
        broadcast = await BroadcastService.get_broadcast(session, broadcast_id)
        if not broadcast:
            return None
        
        broadcast.is_sent = True
        broadcast.sent_at = datetime.utcnow()
        broadcast.recipient_count = recipient_count
        
        await session.commit()
        await session.refresh(broadcast)
        logger.info(f"Broadcast {broadcast_id} marked as sent to {recipient_count} users")
        return broadcast
    
    @staticmethod
    async def get_all_broadcasts(session: AsyncSession) -> List[Broadcast]:
        """Get all broadcasts"""
        query = select(Broadcast).order_by(Broadcast.sent_at.desc())
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_broadcast(session: AsyncSession, broadcast_id: int) -> Optional[Broadcast]:
        """Get broadcast by ID"""
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        return result.scalar_one_or_none()
