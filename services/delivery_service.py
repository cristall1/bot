from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from models import Delivery, User, Courier
from utils.logger import logger


class DeliveryService:
    """Service for delivery management"""
    
    @staticmethod
    async def create_delivery(
        session: AsyncSession,
        creator_id: int,
        description: str,
        location_info: str,
        phone: str
    ) -> Delivery:
        """Create new delivery order"""
        delivery = Delivery(
            creator_id=creator_id,
            description=description,
            location_info=location_info,
            phone=phone,
            status="WAITING"
        )
        session.add(delivery)
        await session.commit()
        await session.refresh(delivery)
        logger.info(f"Delivery created by user {creator_id}")
        return delivery
    
    @staticmethod
    async def get_delivery(session: AsyncSession, delivery_id: int) -> Optional[Delivery]:
        """Get delivery by ID"""
        result = await session.execute(
            select(Delivery).where(Delivery.id == delivery_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_deliveries(session: AsyncSession) -> List[Delivery]:
        """Get all waiting deliveries"""
        query = select(Delivery).where(
            Delivery.status == "WAITING"
        ).order_by(Delivery.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_deliveries(session: AsyncSession, user_id: int) -> List[Delivery]:
        """Get deliveries created by user"""
        query = select(Delivery).where(
            Delivery.creator_id == user_id
        ).order_by(Delivery.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_courier_deliveries(session: AsyncSession, courier_id: int) -> List[Delivery]:
        """Get deliveries assigned to courier"""
        query = select(Delivery).where(
            Delivery.courier_id == courier_id
        ).order_by(Delivery.assigned_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def assign_courier(
        session: AsyncSession,
        delivery_id: int,
        courier_id: int
    ) -> Optional[Delivery]:
        """Assign courier to delivery"""
        delivery = await DeliveryService.get_delivery(session, delivery_id)
        if not delivery or delivery.status != "WAITING":
            return None
        
        delivery.courier_id = courier_id
        delivery.status = "ASSIGNED"
        delivery.assigned_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(delivery)
        logger.info(f"Delivery {delivery_id} assigned to courier {courier_id}")
        return delivery
    
    @staticmethod
    async def complete_delivery(
        session: AsyncSession,
        delivery_id: int
    ) -> Optional[Delivery]:
        """Mark delivery as completed"""
        delivery = await DeliveryService.get_delivery(session, delivery_id)
        if not delivery or delivery.status != "ASSIGNED":
            return None
        
        delivery.status = "COMPLETED"
        delivery.completed_at = datetime.utcnow()
        
        # Update courier stats
        if delivery.courier_id:
            result = await session.execute(
                select(Courier).where(Courier.user_id == delivery.courier_id)
            )
            courier = result.scalar_one_or_none()
            if courier:
                courier.completed_deliveries += 1
        
        await session.commit()
        await session.refresh(delivery)
        logger.info(f"Delivery {delivery_id} completed")
        return delivery
    
    @staticmethod
    async def reject_delivery(
        session: AsyncSession,
        delivery_id: int
    ) -> Optional[Delivery]:
        """Reject delivery"""
        delivery = await DeliveryService.get_delivery(session, delivery_id)
        if not delivery:
            return None
        
        delivery.status = "REJECTED"
        await session.commit()
        await session.refresh(delivery)
        logger.info(f"Delivery {delivery_id} rejected")
        return delivery
    
    @staticmethod
    async def cancel_delivery(
        session: AsyncSession,
        delivery_id: int,
        user_id: int
    ) -> Optional[Delivery]:
        """Cancel delivery (only creator can cancel)"""
        delivery = await DeliveryService.get_delivery(session, delivery_id)
        if not delivery or delivery.creator_id != user_id:
            return None
        
        delivery.status = "CANCELLED"
        await session.commit()
        await session.refresh(delivery)
        logger.info(f"Delivery {delivery_id} cancelled")
        return delivery
    
    @staticmethod
    async def make_courier(session: AsyncSession, user_id: int) -> Courier:
        """Make user a courier"""
        # Check if already courier
        result = await session.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            return existing
        
        # Update user status
        user_result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user:
            user.is_courier = True
        
        # Create courier record
        courier = Courier(user_id=user_id)
        session.add(courier)
        await session.commit()
        await session.refresh(courier)
        logger.info(f"User {user_id} is now a courier")
        return courier
    
    @staticmethod
    async def get_courier_stats(session: AsyncSession, user_id: int) -> Optional[dict]:
        """Get courier statistics"""
        result = await session.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        courier = result.scalar_one_or_none()
        
        if not courier:
            return None
        
        return {
            "completed_deliveries": courier.completed_deliveries,
            "rating": courier.rating,
            "status": courier.status
        }
    
    @staticmethod
    async def get_all_couriers(session: AsyncSession, active_only: bool = True) -> List[Courier]:
        """Get all couriers"""
        query = select(Courier)
        
        if active_only:
            query = query.where(Courier.status == "ACTIVE")
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def suspend_courier(session: AsyncSession, user_id: int) -> Optional[Courier]:
        """Suspend courier"""
        result = await session.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        courier = result.scalar_one_or_none()
        
        if not courier:
            return None
        
        courier.status = "SUSPENDED"
        await session.commit()
        await session.refresh(courier)
        logger.info(f"Courier {user_id} suspended")
        return courier
    
    @staticmethod
    async def activate_courier(session: AsyncSession, user_id: int) -> Optional[Courier]:
        """Activate courier"""
        result = await session.execute(
            select(Courier).where(Courier.user_id == user_id)
        )
        courier = result.scalar_one_or_none()
        
        if not courier:
            return None
        
        courier.status = "ACTIVE"
        await session.commit()
        await session.refresh(courier)
        logger.info(f"Courier {user_id} activated")
        return courier
