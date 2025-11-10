"""Init script for dynamic menu"""
import asyncio
from database import AsyncSessionLocal
from services.dynamic_menu_service import DynamicMenuService, MenuFilterService, MenuFilterOptionService
from utils.logger import logger


async def init_dynamic_menu():
    """Инициализация главного меню"""
    async with AsyncSessionLocal() as session:
        existing = await DynamicMenuService.get_all_menus(session, active_only=False)
        if existing:
            logger.info(f"[InitDynamicMenu] ℹ️ Уже существует {len(existing)} пунктов меню")
            return
        
        # TALIM
        logger.info("[InitDynamicMenu] 📚 Создание TALIM")
        talim = await DynamicMenuService.create_menu(session, "📚 TALIM", "📚 Ta'lim", "📚")
        
        # Фильтр Гражданство для TALIM
        citizenship_filter = await MenuFilterService.create_filter(session, talim.id, "Гражданство", "Fuqarolik")
        await MenuFilterOptionService.create_option(session, citizenship_filter.id, "Узбекистан", "O'zbekiston", "🇺🇿")
        await MenuFilterOptionService.create_option(session, citizenship_filter.id, "Россия", "Rossiya", "🇷🇺")
        await MenuFilterOptionService.create_option(session, citizenship_filter.id, "Казахстан", "Qozog'iston", "🇰🇿")
        
        # DOSTAVKA
        logger.info("[InitDynamicMenu] 🚚 Создание DOSTAVKA")
        await DynamicMenuService.create_menu(session, "🚚 DOSTAVKA", "🚚 Yetkazib berish", "🚚")
        
        logger.info("[InitDynamicMenu] ✅ Инициализация завершена")


if __name__ == "__main__":
    asyncio.run(init_dynamic_menu())
