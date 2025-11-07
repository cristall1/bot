from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from models import Broadcast
from utils.logger import logger


class BroadcastService:
    """Service for broadcast management"""
    
    @staticmethod
    async def create_broadcast(
        session: AsyncSession,
        admin_id: int,
        message_ru: str,
        message_uz: str = None,
        photo_url: str = None,
        recipient_filter: str = "ALL",
        recipient_count: int = 0
    ) -> Broadcast:
        """Create new broadcast"""
        broadcast = Broadcast(
            admin_id=admin_id,
            message_ru=message_ru,
            message_uz=message_uz,
            photo_url=photo_url,
            recipient_filter=recipient_filter,
            recipient_count=recipient_count
        )
        session.add(broadcast)
        await session.commit()
        await session.refresh(broadcast)
        logger.info(f"Broadcast created by admin {admin_id} to {recipient_count} users")
        return broadcast
    
    @staticmethod
    async def get_all_broadcasts(session: AsyncSession) -> List[Broadcast]:
        """Get all broadcasts"""
        query = select(Broadcast).order_by(Broadcast.sent_at.desc())
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_broadcast(session: AsyncSession, broadcast_id: int) -> Broadcast:
        """Get broadcast by ID"""
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        return result.scalar_one_or_none()
