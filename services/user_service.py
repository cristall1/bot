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
    async def get_or_create_debug_user(
        session: AsyncSession,
        telegram_id: int,
        username: str = "debug_user",
        first_name: str = "Debug",
        language: str = "RU"
    ) -> User:
        """Get or create a debug user with admin rights for local development."""
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            updated = False
            if not user.is_admin:
                user.is_admin = True
                updated = True
            if user.is_banned:
                user.is_banned = False
                updated = True
            if language and user.language != language:
                user.language = language
                updated = True
            if username and user.username != username:
                user.username = username
                updated = True
            if first_name and user.first_name != first_name:
                user.first_name = first_name
                updated = True
            if updated:
                await session.commit()
                await session.refresh(user)
                logger.info(f"Debug user updated: {telegram_id}")
            return user
        
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language=language,
            is_admin=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Debug user created: {telegram_id}")
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
    async def get_all_admins(session: AsyncSession) -> List[User]:
        """Get all active administrators"""
        query = select(User).where(
            User.is_admin == True,
            User.is_banned == False
        )
        result = await session.execute(query)
        admins = result.scalars().all()
        logger.info(f"Загружено {len(admins)} администраторов для уведомлений")
        return admins
    
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
        query: str,
        limit: int = 20
    ) -> List[User]:
        """Search users by username, first name, phone or telegram ID"""
        from sqlalchemy import or_
        
        like_query = f"%{query}%"
        filters = [
            User.username.ilike(like_query),
            User.first_name.ilike(like_query)
        ]
        
        if query.isdigit():
            filters.append(User.telegram_id == int(query))
        
        # Add phone search if query looks like a phone number
        if len(query) >= 4:
            filters.append(User.phone.ilike(like_query))
        
        search_query = select(User).where(
            or_(*filters)
        ).order_by(User.last_active.desc()).limit(limit)
        
        result = await session.execute(search_query)
        users = result.scalars().all()
        logger.info(f"Поиск пользователей по запросу '{query}' найдено {len(users)}")
        return users
    
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
