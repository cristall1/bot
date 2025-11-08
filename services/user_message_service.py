from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
from models import UserMessage
from utils.logger import logger


class UserMessageService:
    """Service for user messages to admin"""
    
    @staticmethod
    async def create_message(
        session: AsyncSession,
        user_id: int,
        message_text: str
    ) -> UserMessage:
        """Create new message from user to admin"""
        message = UserMessage(
            user_id=user_id,
            message_text=message_text
        )
        session.add(message)
        await session.commit()
        await session.refresh(message)
        logger.info(f"User message created by user {user_id}")
        return message
    
    @staticmethod
    async def get_message(session: AsyncSession, message_id: int) -> Optional[UserMessage]:
        """Get message by ID"""
        result = await session.execute(
            select(UserMessage)
            .options(joinedload(UserMessage.user))
            .where(UserMessage.id == message_id)
        )
        return result.unique().scalar_one_or_none()
    
    @staticmethod
    async def get_all_messages(
        session: AsyncSession,
        unread_only: bool = False
    ) -> List[UserMessage]:
        """Get all messages"""
        query = select(UserMessage).options(joinedload(UserMessage.user))
        
        if unread_only:
            query = query.where(UserMessage.is_read == False)
        
        query = query.order_by(UserMessage.created_at.desc())
        
        result = await session.execute(query)
        return result.unique().scalars().all()
    
    @staticmethod
    async def get_user_messages(session: AsyncSession, user_id: int) -> List[UserMessage]:
        """Get messages from specific user"""
        query = select(UserMessage).where(
            UserMessage.user_id == user_id
        ).order_by(UserMessage.created_at.desc())
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def mark_as_read(
        session: AsyncSession,
        message_id: int
    ) -> Optional[UserMessage]:
        """Mark message as read"""
        message = await UserMessageService.get_message(session, message_id)
        if not message:
            return None
        
        message.is_read = True
        await session.commit()
        await session.refresh(message)
        return message
    
    @staticmethod
    async def reply_to_message(
        session: AsyncSession,
        message_id: int,
        admin_id: int,
        reply_text: str
    ) -> Optional[UserMessage]:
        """Reply to user message"""
        message = await UserMessageService.get_message(session, message_id)
        if not message:
            return None
        
        message.admin_reply = reply_text
        message.admin_id = admin_id
        message.replied_at = datetime.utcnow()
        message.is_read = True
        
        await session.commit()
        await session.refresh(message)
        logger.info(f"Admin {admin_id} replied to message {message_id}")
        return message
    
    @staticmethod
    async def delete_message(session: AsyncSession, message_id: int) -> bool:
        """Delete message"""
        message = await UserMessageService.get_message(session, message_id)
        if not message:
            return False
        
        await session.delete(message)
        await session.commit()
        logger.info(f"Message {message_id} deleted")
        return True
    
    @staticmethod
    async def get_unread_count(session: AsyncSession) -> int:
        """Get count of unread messages"""
        result = await session.execute(
            select(func.count(UserMessage.id)).where(UserMessage.is_read == False)
        )
        return result.scalar()
