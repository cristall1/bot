"""
Инициализация категорий в базе данных
Initialize categories in database
"""

import asyncio
from database import init_db, AsyncSessionLocal
from services.category_service import CategoryService
from utils.logger import logger


async def initialize_categories():
    """Initialize default categories in the database"""
    try:
        logger.info("[init_categories] Инициализация базы данных...")
        await init_db()
        
        logger.info("[init_categories] Создание базовых категорий...")
        async with AsyncSessionLocal() as session:
            categories = await CategoryService.ensure_default_categories(session)
            logger.info(f"[init_categories] ✅ Создано/обновлено категорий: {len(categories)}")
            
            for cat in categories:
                logger.info(f"  - {cat.icon} {cat.name_ru} (is_active={cat.is_active})")
        
        logger.info("[init_categories] ✅ Инициализация завершена успешно")
    except Exception as e:
        logger.error(f"[init_categories] ❌ Ошибка инициализации: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(initialize_categories())
