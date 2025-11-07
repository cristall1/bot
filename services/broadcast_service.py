from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict
from models import Broadcast, User
from utils.logger import logger


class BroadcastService:
    """Service for broadcast management"""
    
    @staticmethod
    async def create_broadcast(
        session: AsyncSession,
        admin_id: int,
        message_ru: str,
        message_uz: str,
        broadcast_type: str = "ALL",
        image_url: str = None
    ) -> Broadcast:
        """Create new broadcast"""
        broadcast = Broadcast(
            admin_id=admin_id,
            message_ru=message_ru,
            message_uz=message_uz,
            broadcast_type=broadcast_type,
            image_url=image_url
        )
        session.add(broadcast)
        await session.commit()
        await session.refresh(broadcast)
        logger.info(f"Broadcast created by admin {admin_id}, type: {broadcast_type}")
        return broadcast
    
    @staticmethod
    async def get_recipients(
        session: AsyncSession,
        broadcast_type: str,
        citizenship: str = None
    ) -> List[User]:
        """Get recipients based on broadcast type"""
        query = select(User).where(User.is_banned == False)
        
        if broadcast_type == "ALL":
            pass
        elif broadcast_type == "LANGUAGE_RU":
            query = query.where(User.language == "RU")
        elif broadcast_type == "LANGUAGE_UZ":
            query = query.where(User.language == "UZ")
        elif broadcast_type == "CITIZENSHIP":
            if citizenship:
                query = query.where(User.citizenship == citizenship)
        elif broadcast_type == "COURIERS_ONLY":
            query = query.where(User.is_courier == True)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def count_recipients(
        session: AsyncSession,
        broadcast_type: str,
        citizenship: str = None
    ) -> int:
        """Count recipients for broadcast"""
        recipients = await BroadcastService.get_recipients(
            session,
            broadcast_type,
            citizenship
        )
        return len(recipients)
    
    @staticmethod
    async def update_broadcast_count(
        session: AsyncSession,
        broadcast_id: int,
        count: int
    ):
        """Update broadcast recipient count"""
        result = await session.execute(
            select(Broadcast).where(Broadcast.id == broadcast_id)
        )
        broadcast = result.scalar_one_or_none()
        if broadcast:
            broadcast.total_recipients = count
            await session.commit()
    
    @staticmethod
    async def get_all_broadcasts(session: AsyncSession) -> List[Broadcast]:
        """Get all broadcasts"""
        result = await session.execute(
            select(Broadcast).order_by(Broadcast.sent_at.desc())
        )
        return result.scalars().all()
