from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from models import Courier, User
from utils.logger import logger


class CourierService:
    """Service for courier management"""
    
    @staticmethod
    async def register_courier(
        session: AsyncSession,
        user_id: int
    ) -> Courier:
        """Register user as courier"""
        result = await session.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        courier = result.scalar_one_or_none()
        
        if courier:
            courier.status = "ACTIVE"
        else:
            courier = Courier(
                user_id=user_id,
                status="ACTIVE"
            )
            session.add(courier)
        
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.is_courier = True
        
        await session.commit()
        await session.refresh(courier)
        logger.info(f"Courier registered: user_id {user_id}")
        return courier
    
    @staticmethod
    async def get_courier(
        session: AsyncSession,
        user_id: int
    ) -> Optional[Courier]:
        """Get courier by user ID"""
        result = await session.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_couriers(
        session: AsyncSession,
        status: str = None
    ) -> List[Courier]:
        """Get all couriers"""
        query = select(Courier)
        
        if status:
            query = query.where(Courier.status == status)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_courier_status(
        session: AsyncSession,
        user_id: int,
        status: str
    ) -> Optional[Courier]:
        """Update courier status"""
        courier = await CourierService.get_courier(session, user_id)
        if not courier:
            return None
        
        courier.status = status
        await session.commit()
        await session.refresh(courier)
        logger.info(f"Courier status updated: user_id {user_id}, status {status}")
        return courier
    
    @staticmethod
    async def suspend_courier(
        session: AsyncSession,
        user_id: int
    ) -> Optional[Courier]:
        """Suspend courier"""
        return await CourierService.update_courier_status(session, user_id, "SUSPENDED")
    
    @staticmethod
    async def activate_courier(
        session: AsyncSession,
        user_id: int
    ) -> Optional[Courier]:
        """Activate courier"""
        return await CourierService.update_courier_status(session, user_id, "ACTIVE")
    
    @staticmethod
    async def remove_courier_status(
        session: AsyncSession,
        user_id: int
    ) -> bool:
        """Remove courier status"""
        courier = await CourierService.get_courier(session, user_id)
        if not courier:
            return False
        
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.is_courier = False
        
        await session.delete(courier)
        await session.commit()
        logger.info(f"Courier status removed: user_id {user_id}")
        return True
    
    @staticmethod
    async def increment_deliveries(
        session: AsyncSession,
        user_id: int
    ) -> Optional[Courier]:
        """Increment completed deliveries count"""
        courier = await CourierService.get_courier(session, user_id)
        if not courier:
            return None
        
        courier.completed_deliveries += 1
        await session.commit()
        await session.refresh(courier)
        return courier
    
    @staticmethod
    async def update_rating(
        session: AsyncSession,
        user_id: int,
        rating: float
    ) -> Optional[Courier]:
        """Update courier rating"""
        courier = await CourierService.get_courier(session, user_id)
        if not courier:
            return None
        
        courier.rating = max(1.0, min(5.0, rating))
        await session.commit()
        await session.refresh(courier)
        return courier
    
    @staticmethod
    async def get_courier_stats(session: AsyncSession) -> Dict:
        """Get courier statistics"""
        total_result = await session.execute(
            select(func.count(Courier.id))
        )
        total = total_result.scalar() or 0
        
        active_result = await session.execute(
            select(func.count(Courier.id)).where(
                Courier.status == "ACTIVE"
            )
        )
        active = active_result.scalar() or 0
        
        deliveries_result = await session.execute(
            select(func.sum(Courier.completed_deliveries))
        )
        total_deliveries = deliveries_result.scalar() or 0
        
        rating_result = await session.execute(
            select(func.avg(Courier.rating))
        )
        avg_rating = rating_result.scalar() or 5.0
        
        return {
            "total": total,
            "active": active,
            "suspended": total - active,
            "total_deliveries": int(total_deliveries),
            "average_rating": round(float(avg_rating), 2)
        }
