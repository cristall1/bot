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
        from bots.handlers import admin_handlers
        from bots.handlers import admin_category_handlers
        from bots.handlers import admin_alert_handlers
        from bots.handlers import admin_export_handlers
        
        # Register all routers
        self.dp.include_router(admin_handlers.router)
        self.dp.include_router(admin_category_handlers.router)
        self.dp.include_router(admin_alert_handlers.router)
        self.dp.include_router(admin_export_handlers.router)
        
        await self.dp.start_polling(self.bot)
    
    async def stop(self):
        """Stop the admin bot"""
        await self.bot.session.close()
