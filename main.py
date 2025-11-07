import asyncio
import sys
from database import init_db
from bots.user_bot import UserBot
from bots.admin_bot import AdminBot
from utils.logger import logger
from config import settings

# Import all models to ensure they are registered with SQLAlchemy Base
from models import (
    User, Category, CategoryContent, InlineButton, ServiceRequest,
    CourierManagement, UserPreference, AdminMessage, Broadcast,
    AdminLog, SystemSetting
)


async def seed_initial_data():
    """Seed initial categories and system settings"""
    from database import AsyncSessionLocal
    from services.category_service import CategoryService
    from models import SystemSetting
    import json
    
    async with AsyncSessionLocal() as session:
        categories = await CategoryService.get_all_categories(session, active_only=False)
        
        if not categories:
            logger.info("Seeding initial categories...")
            try:
                with open('data/categories_seed.json', 'r', encoding='utf-8') as f:
                    categories_data = json.load(f)
                
                for cat_data in categories_data:
                    category = await CategoryService.create_category(
                        session,
                        name_ru=cat_data['name_ru'],
                        name_uz=cat_data['name_uz'],
                        description_ru=cat_data.get('description_ru'),
                        description_uz=cat_data.get('description_uz'),
                        level=cat_data.get('level', 1),
                        icon=cat_data.get('icon', '📁'),
                        category_type=cat_data.get('category_type', 'GENERAL'),
                        citizenship_scope=cat_data.get('citizenship_scope'),
                        created_by_admin_id=cat_data.get('created_by_admin_id')
                    )
                    # Set order_index separately if provided
                    if 'order_index' in cat_data:
                        category.order_index = cat_data['order_index']
                        await session.commit()
                
                logger.info("Initial categories seeded successfully")
            except Exception as e:
                logger.error(f"Error seeding categories: {e}")
        
        from sqlalchemy import select
        result = await session.execute(select(SystemSetting))
        settings_exist = result.scalar_one_or_none()
        
        if not settings_exist:
            logger.info("Seeding system settings...")
            default_settings = [
                {
                    "setting_key": "SERVICE_TYPE_COURIER_ENABLED",
                    "setting_name_ru": "Курьерские услуги включены",
                    "setting_name_uz": "Kuryer xizmatlari yoqilgan",
                    "value": True
                },
                {
                    "setting_key": "SERVICE_TYPE_TUTORING_ENABLED",
                    "setting_name_ru": "Репетиторство включено",
                    "setting_name_uz": "Repetitorlik yoqilgan",
                    "value": True
                },
                {
                    "setting_key": "ALLOW_NEW_REGISTRATION",
                    "setting_name_ru": "Разрешить новые регистрации",
                    "setting_name_uz": "Yangi ro'yxatdan o'tishga ruxsat",
                    "value": True
                },
                {
                    "setting_key": "TELEGRAPH_ENABLED",
                    "setting_name_ru": "Telegraph интеграция",
                    "setting_name_uz": "Telegraph integratsiya",
                    "value": True
                },
                {
                    "setting_key": "AUTO_DELETE_EXPIRED_SERVICES",
                    "setting_name_ru": "Автоудаление старых услуг",
                    "setting_name_uz": "Eski xizmatlarni avtomatik o'chirish",
                    "value": True
                }
            ]
            
            for setting_data in default_settings:
                setting = SystemSetting(**setting_data)
                session.add(setting)
            
            await session.commit()
            logger.info("System settings seeded successfully")


async def main():
    """Main entry point"""
    logger.info("Starting bot system...")
    
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database tables created successfully")
    
    logger.info("Seeding initial data...")
    await seed_initial_data()
    logger.info("Initial data seeding completed")
    
    logger.info("Starting both bots...")
    
    user_bot = UserBot()
    admin_bot = AdminBot()
    
    try:
        await asyncio.gather(
            user_bot.start(),
            admin_bot.start()
        )
    except KeyboardInterrupt:
        logger.info("Shutting down bots...")
        await user_bot.stop()
        await admin_bot.stop()
        logger.info("Bots stopped")
    except Exception as e:
        logger.error(f"Error running bots: {e}")
        sys.exit(1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
