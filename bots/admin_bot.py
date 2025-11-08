from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import settings


class AdminBot:
    """Admin Bot instance"""
    
    def __init__(self):
        self.bot = Bot(token=settings.admin_bot_token)
        self.storage = MemoryStorage()
        self.dp = Dispatcher(storage=self.storage)
    
    async def start(self):
        """Start the admin bot"""
        from bots.handlers.admin_handlers import register_admin_handlers
        from bots.handlers.admin_category_handlers import register_category_handlers
        
        register_admin_handlers(self.dp)
        register_category_handlers(self.dp)
        
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the admin bot"""
        await self.bot.session.close()
