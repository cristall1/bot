"""
Сервис очереди модерации - Moderation Queue Service
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime
from models import ModerationQueue, Notification, ShurtaAlert, Delivery, User
from utils.logger import logger


class ModerationQueueService:
    """Сервис для управления очередью модерации"""
    
    @staticmethod
    async def add_to_queue(
        session: AsyncSession,
        entity_type: str,
        entity_id: int,
        user_id: int,
        admin_message_id: int = None
    ) -> ModerationQueue:
        """
        Добавить элемент в очередь модерации
        Add item to moderation queue
        """
        try:
            logger.info(f"[ModerationQueue] Добавление в очередь: {entity_type} #{entity_id}")
            
            queue_item = ModerationQueue(
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                admin_message_id=admin_message_id,
                status="PENDING"
            )
            
            session.add(queue_item)
            await session.commit()
            await session.refresh(queue_item)
            
            logger.info(f"[ModerationQueue] ✅ Элемент добавлен в очередь: {queue_item.id}")
            return queue_item
        except Exception as e:
            logger.error(f"[ModerationQueue] ❌ Ошибка добавления в очередь: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_pending_items(
        session: AsyncSession,
        entity_type: str = None
    ) -> List[ModerationQueue]:
        """
        Получить все элементы, ожидающие модерации
        Get all items pending moderation
        """
        try:
            query = select(ModerationQueue).options(
                joinedload(ModerationQueue.user)
            ).where(ModerationQueue.status == "PENDING")
            
            if entity_type:
                query = query.where(ModerationQueue.entity_type == entity_type)
            
            query = query.order_by(ModerationQueue.created_at.asc())
            
            result = await session.execute(query)
            items = result.scalars().all()
            
            logger.info(f"[ModerationQueue] Найдено элементов на модерации: {len(items)}")
            return items
        except Exception as e:
            logger.error(f"[ModerationQueue] ❌ Ошибка получения очереди: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def approve_item(
        session: AsyncSession,
        queue_id: int,
        moderator_id: int,
        comment: str = None
    ) -> Optional[ModerationQueue]:
        """
        Одобрить элемент
        Approve item
        """
        try:
            result = await session.execute(
                select(ModerationQueue)
                .options(joinedload(ModerationQueue.user))
                .where(ModerationQueue.id == queue_id)
            )
            queue_item = result.scalar_one_or_none()
            
            if not queue_item:
                logger.warning(f"[ModerationQueue] Элемент {queue_id} не найден")
                return None
            
            queue_item.status = "APPROVED"
            queue_item.moderator_id = moderator_id
            queue_item.moderator_comment = comment
            queue_item.moderated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(queue_item)
            
            logger.info(f"[ModerationQueue] ✅ Элемент {queue_id} одобрен модератором {moderator_id}")
            return queue_item
        except Exception as e:
            logger.error(f"[ModerationQueue] ❌ Ошибка одобрения элемента: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def reject_item(
        session: AsyncSession,
        queue_id: int,
        moderator_id: int,
        comment: str = None
    ) -> Optional[ModerationQueue]:
        """
        Отклонить элемент
        Reject item
        """
        try:
            result = await session.execute(
                select(ModerationQueue)
                .options(joinedload(ModerationQueue.user))
                .where(ModerationQueue.id == queue_id)
            )
            queue_item = result.scalar_one_or_none()
            
            if not queue_item:
                logger.warning(f"[ModerationQueue] Элемент {queue_id} не найден")
                return None
            
            queue_item.status = "REJECTED"
            queue_item.moderator_id = moderator_id
            queue_item.moderator_comment = comment
            queue_item.moderated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(queue_item)
            
            logger.info(f"[ModerationQueue] ❌ Элемент {queue_id} отклонён модератором {moderator_id}")
            return queue_item
        except Exception as e:
            logger.error(f"[ModerationQueue] ❌ Ошибка отклонения элемента: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_queue_item_by_entity(
        session: AsyncSession,
        entity_type: str,
        entity_id: int
    ) -> Optional[ModerationQueue]:
        """
        Получить элемент очереди по типу и ID сущности
        Get queue item by entity type and ID
        """
        try:
            result = await session.execute(
                select(ModerationQueue)
                .options(joinedload(ModerationQueue.user))
                .where(
                    ModerationQueue.entity_type == entity_type,
                    ModerationQueue.entity_id == entity_id
                )
                .order_by(ModerationQueue.created_at.desc())
            )
            return result.scalars().first()
        except Exception as e:
            logger.error(f"[ModerationQueue] ❌ Ошибка получения элемента очереди: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_statistics(session: AsyncSession) -> dict:
        """
        Получить статистику очереди модерации
        Get moderation queue statistics
        """
        try:
            from sqlalchemy import func
            
            result = await session.execute(
                select(
                    ModerationQueue.entity_type,
                    ModerationQueue.status,
                    func.count(ModerationQueue.id).label("count")
                )
                .group_by(ModerationQueue.entity_type, ModerationQueue.status)
            )
            
            stats = {}
            for row in result.all():
                entity_type = row[0]
                status = row[1]
                count = row[2]
                
                if entity_type not in stats:
                    stats[entity_type] = {}
                stats[entity_type][status] = count
            
            logger.info(f"[ModerationQueue] Статистика очереди: {stats}")
            return stats
        except Exception as e:
            logger.error(f"[ModerationQueue] ❌ Ошибка получения статистики: {str(e)}", exc_info=True)
            raise
