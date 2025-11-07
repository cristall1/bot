from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from models import AdminLog
from utils.logger import logger


class AdminLogService:
    """Service for admin action logging"""
    
    @staticmethod
    async def log_action(
        session: AsyncSession,
        admin_id: int,
        action: str,
        entity_type: str,
        entity_id: int = None,
        details: Dict = None
    ) -> AdminLog:
        """Log admin action"""
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details
        )
        session.add(log)
        await session.commit()
        await session.refresh(log)
        logger.info(f"Admin action logged: {action} on {entity_type} by admin {admin_id}")
        return log
    
    @staticmethod
    async def get_logs(
        session: AsyncSession,
        admin_id: int = None,
        entity_type: str = None,
        action: str = None,
        limit: int = 100
    ) -> List[AdminLog]:
        """Get admin logs with filters"""
        query = select(AdminLog)
        
        if admin_id:
            query = query.where(AdminLog.admin_id == admin_id)
        if entity_type:
            query = query.where(AdminLog.entity_type == entity_type)
        if action:
            query = query.where(AdminLog.action == action)
        
        query = query.order_by(AdminLog.created_at.desc()).limit(limit)
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_recent_logs(
        session: AsyncSession,
        hours: int = 24,
        limit: int = 50
    ) -> List[AdminLog]:
        """Get recent logs within specified hours"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await session.execute(
            select(AdminLog)
            .where(AdminLog.created_at >= cutoff)
            .order_by(AdminLog.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_log_by_id(
        session: AsyncSession,
        log_id: int
    ) -> Optional[AdminLog]:
        """Get specific log by ID"""
        result = await session.execute(
            select(AdminLog).where(AdminLog.id == log_id)
        )
        return result.scalar_one_or_none()
