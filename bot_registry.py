"""
Bot Registry - Global bot instances for cross-bot communication
"""
from typing import Optional
from aiogram import Bot


class BotRegistry:
    """Global registry for bot instances"""
    _user_bot: Optional[Bot] = None
    _admin_bot: Optional[Bot] = None
    
    @classmethod
    def set_user_bot(cls, bot: Bot):
        """Set user bot instance"""
        cls._user_bot = bot
    
    @classmethod
    def set_admin_bot(cls, bot: Bot):
        """Set admin bot instance"""
        cls._admin_bot = bot
    
    @classmethod
    def get_user_bot(cls) -> Optional[Bot]:
        """Get user bot instance"""
        return cls._user_bot
    
    @classmethod
    def get_admin_bot(cls) -> Optional[Bot]:
        """Get admin bot instance"""
        return cls._admin_bot


# Convenience functions
def get_user_bot() -> Optional[Bot]:
    """Get user bot instance"""
    return BotRegistry.get_user_bot()


def get_admin_bot() -> Optional[Bot]:
    """Get admin bot instance"""
    return BotRegistry.get_admin_bot()
