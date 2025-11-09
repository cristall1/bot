from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings
from bot_registry import BotRegistry


class UserBot:
    """User Bot instance"""
    
    def __init__(self):
        self.bot = Bot(token=settings.user_bot_token)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
        BotRegistry.set_user_bot(self.bot)
    
    async def start(self):
        """Start the user bot"""
        from bots.handlers.user_handlers import register_user_handlers
        register_user_handlers(self.dp)
        
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the user bot"""
        await self.bot.session.close()
        BotRegistry.set_user_bot(None)
