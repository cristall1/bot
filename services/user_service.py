from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from models import User
from utils.logger import logger


class UserService:
    """Service for user management"""
    
    @staticmethod
    async def create_or_update_user(
        session: AsyncSession,
        telegram_id: int,
        username: str = None,
        first_name: str = None,
        language: str = "RU",
        citizenship: str = None
    ) -> User:
        """Create or update user"""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.username = username
            user.first_name = first_name
            user.last_active = datetime.utcnow()
            if language:
                user.language = language
            if citizenship:
                user.citizenship = citizenship
        else:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language=language,
                citizenship=citizenship
            )
            session.add(user)
            logger.info(f"New user created: {telegram_id}")
        
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def get_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Get user by telegram ID"""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by database ID"""
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_users(
        session: AsyncSession,
        language: str = None,
        citizenship: str = None,
        is_courier: bool = None,
        is_banned: bool = None
    ) -> List[User]:
        """Get all users with filters"""
        query = select(User)
        
        if language:
            query = query.where(User.language == language)
        if citizenship:
            query = query.where(User.citizenship == citizenship)
        if is_courier is not None:
            query = query.where(User.is_courier == is_courier)
        if is_banned is not None:
            query = query.where(User.is_banned == is_banned)
        
        result = await session.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def ban_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Ban user"""
        user = await UserService.get_user(session, telegram_id)
        if not user:
            return None
        
        user.is_banned = True
        await session.commit()
        await session.refresh(user)
        logger.info(f"User banned: {telegram_id}")
        return user
    
    @staticmethod
    async def unban_user(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Unban user"""
        user = await UserService.get_user(session, telegram_id)
        if not user:
            return None
        
        user.is_banned = False
        await session.commit()
        await session.refresh(user)
        logger.info(f"User unbanned: {telegram_id}")
        return user
    
    @staticmethod
    async def make_admin(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Make user admin"""
        user = await UserService.get_user(session, telegram_id)
        if not user:
            return None
        
        user.is_admin = True
        await session.commit()
        await session.refresh(user)
        logger.info(f"User made admin: {telegram_id}")
        return user
    
    @staticmethod
    async def remove_admin(session: AsyncSession, telegram_id: int) -> Optional[User]:
        """Remove admin rights"""
        user = await UserService.get_user(session, telegram_id)
        if not user:
            return None
        
        user.is_admin = False
        await session.commit()
        await session.refresh(user)
        logger.info(f"Admin removed: {telegram_id}")
        return user
    
    @staticmethod
    async def get_user_stats(session: AsyncSession) -> Dict:
        """Get user statistics"""
        total_result = await session.execute(select(func.count(User.id)))
        total = total_result.scalar()
        
        today = datetime.utcnow().date()
        today_result = await session.execute(
            select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
        )
        today_count = today_result.scalar()
        
        ru_result = await session.execute(
            select(func.count(User.id)).where(User.language == "RU")
        )
        ru_count = ru_result.scalar()
        
        uz_result = await session.execute(
            select(func.count(User.id)).where(User.language == "UZ")
        )
        uz_count = uz_result.scalar()
        
        citizenship_stats = {}
        for cit in ["UZ", "RU", "KZ", "KG"]:
            result = await session.execute(
                select(func.count(User.id)).where(User.citizenship == cit)
            )
            citizenship_stats[cit] = result.scalar()
        
        couriers_result = await session.execute(
            select(func.count(User.id)).where(User.is_courier == True)
        )
        couriers = couriers_result.scalar()
        
        banned_result = await session.execute(
            select(func.count(User.id)).where(User.is_banned == True)
        )
        banned = banned_result.scalar()
        
        return {
            "total": total,
            "today": today_count,
            "by_language": {"RU": ru_count, "UZ": uz_count},
            "by_citizenship": citizenship_stats,
            "couriers": couriers,
            "banned": banned
        }
    
    @staticmethod
    async def search_users(
        session: AsyncSession,
        query: str
    ) -> List[User]:
        """Search users by telegram_id, username, or first_name"""
        search_query = select(User).where(
            (User.username.ilike(f"%{query}%")) |
            (User.first_name.ilike(f"%{query}%")) |
            (User.telegram_id == int(query) if query.isdigit() else False)
        )
        result = await session.execute(search_query)
        return result.scalars().all()
    
    @staticmethod
    async def update_user_language(
        session: AsyncSession,
        telegram_id: int,
        language: str
    ) -> Optional[User]:
        """Update user language"""
        user = await UserService.get_user(session, telegram_id)
        if not user:
            return None
        
        user.language = language
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def update_user_citizenship(
        session: AsyncSession,
        telegram_id: int,
        citizenship: str
    ) -> Optional[User]:
        """Update user citizenship"""
        user = await UserService.get_user(session, telegram_id)
        if not user:
            return None
        
        user.citizenship = citizenship
        await session.commit()
        await session.refresh(user)
        return user
    
    @staticmethod
    async def toggle_notifications(
        session: AsyncSession,
        telegram_id: int
    ) -> Optional[User]:
        """Toggle user notifications"""
        user = await UserService.get_user(session, telegram_id)
        if not user:
            return None
        
        user.notifications_enabled = not user.notifications_enabled
        await session.commit()
        await session.refresh(user)
        return user
