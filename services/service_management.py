from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime
from models import ServiceRequest
from utils.logger import logger


class ServiceManagementService:
    """Service for managing service requests"""
    
    @staticmethod
    async def create_service_request(
        session: AsyncSession,
        user_id: int,
        service_type: str,
        title_ru: str = None,
        title_uz: str = None,
        description_ru: str = None,
        description_uz: str = None,
        **kwargs
    ) -> ServiceRequest:
        """Create new service request"""
        service = ServiceRequest(
            user_id=user_id,
            service_type=service_type,
            title_ru=title_ru,
            title_uz=title_uz,
            description_ru=description_ru,
            description_uz=description_uz,
            **kwargs
        )
        session.add(service)
        await session.commit()
        await session.refresh(service)
        logger.info(f"Service request created: {service_type} by user {user_id}")
        return service
    
    @staticmethod
    async def get_service_request(
        session: AsyncSession,
        service_id: int
    ) -> Optional[ServiceRequest]:
        """Get service request by ID"""
        result = await session.execute(
            select(ServiceRequest).where(ServiceRequest.id == service_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_pending_services(session: AsyncSession) -> List[ServiceRequest]:
        """Get all pending service requests"""
        result = await session.execute(
            select(ServiceRequest)
            .where(ServiceRequest.is_approved == False)
            .where(ServiceRequest.is_active == True)
            .order_by(ServiceRequest.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_approved_services(
        session: AsyncSession,
        service_type: str = None
    ) -> List[ServiceRequest]:
        """Get all approved service requests"""
        query = select(ServiceRequest).where(
            ServiceRequest.is_approved == True,
            ServiceRequest.is_active == True
        )
        
        if service_type:
            query = query.where(ServiceRequest.service_type == service_type)
        
        query = query.order_by(ServiceRequest.created_at.desc())
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_user_services(
        session: AsyncSession,
        user_id: int
    ) -> List[ServiceRequest]:
        """Get all services by user"""
        result = await session.execute(
            select(ServiceRequest)
            .where(ServiceRequest.user_id == user_id)
            .order_by(ServiceRequest.created_at.desc())
        )
        return result.scalars().all()
    
    @staticmethod
    async def approve_service(
        session: AsyncSession,
        service_id: int
    ) -> Optional[ServiceRequest]:
        """Approve service request"""
        service = await ServiceManagementService.get_service_request(session, service_id)
        if not service:
            return None
        
        service.is_approved = True
        await session.commit()
        await session.refresh(service)
        logger.info(f"Service approved: ID {service_id}")
        return service
    
    @staticmethod
    async def reject_service(
        session: AsyncSession,
        service_id: int
    ) -> Optional[ServiceRequest]:
        """Reject service request"""
        service = await ServiceManagementService.get_service_request(session, service_id)
        if not service:
            return None
        
        service.is_active = False
        await session.commit()
        await session.refresh(service)
        logger.info(f"Service rejected: ID {service_id}")
        return service
    
    @staticmethod
    async def delete_service(
        session: AsyncSession,
        service_id: int
    ) -> bool:
        """Delete service request"""
        service = await ServiceManagementService.get_service_request(session, service_id)
        if not service:
            return False
        
        await session.delete(service)
        await session.commit()
        logger.info(f"Service deleted: ID {service_id}")
        return True
    
    @staticmethod
    async def get_service_stats(session: AsyncSession) -> Dict:
        """Get service statistics"""
        total_result = await session.execute(select(func.count(ServiceRequest.id)))
        total = total_result.scalar()
        
        approved_result = await session.execute(
            select(func.count(ServiceRequest.id)).where(ServiceRequest.is_approved == True)
        )
        approved = approved_result.scalar()
        
        pending_result = await session.execute(
            select(func.count(ServiceRequest.id)).where(
                ServiceRequest.is_approved == False,
                ServiceRequest.is_active == True
            )
        )
        pending = pending_result.scalar()
        
        rejected = total - approved - pending
        
        return {
            "total": total,
            "approved": approved,
            "pending": pending,
            "rejected": rejected,
            "approval_rate": (approved / total * 100) if total > 0 else 0
        }
    
    @staticmethod
    async def cleanup_expired_services(session: AsyncSession) -> int:
        """Cleanup expired services (48h)"""
        now = datetime.utcnow()
        result = await session.execute(
            select(ServiceRequest).where(
                ServiceRequest.expires_at < now,
                ServiceRequest.is_active == True
            )
        )
        expired_services = result.scalars().all()
        
        count = 0
        for service in expired_services:
            service.is_active = False
            count += 1
        
        await session.commit()
        logger.info(f"Expired services cleaned up: {count}")
        return count
