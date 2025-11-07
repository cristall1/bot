import asyncio
import sys
from database import init_db
from bots.user_bot import UserBot
from bots.admin_bot import AdminBot
from utils.logger import logger
from config import settings

# Import all models to ensure they are registered with SQLAlchemy Base
from models import (
    User, Document, DocumentButton, Delivery, Notification,
    ShurtaAlert, UserMessage, Broadcast, TelegraphArticle,
    Courier, SystemSetting, AdminLog
)


async def seed_initial_data():
    """Seed initial documents and system settings"""
    from database import AsyncSessionLocal
    from models import Document, SystemSetting
    from sqlalchemy import select
    
    async with AsyncSessionLocal() as session:
        # Check if documents already exist
        result = await session.execute(select(Document))
        documents_exist = result.scalars().first()
        
        if not documents_exist:
            logger.info("Seeding initial documents...")
            try:
                initial_documents = [
                    {
                        "citizenship_scope": "UZ",
                        "name_ru": "Получение рекомендации (Xitob)",
                        "name_uz": "Xitob (tavsiyanoma) olish",
                        "content_ru": "Полная информация о получении рекомендации для граждан Узбекистана...",
                        "content_uz": "O'zbekiston fuqarolari uchun tavsiyanoma olish haqida to'liq ma'lumot...",
                        "order_index": 1
                    },
                    {
                        "citizenship_scope": "UZ",
                        "name_ru": "Подача документов в Аль-Азхар",
                        "name_uz": "Al-Azhar ga hujjat topshirish",
                        "content_ru": "Инструкция по подаче документов для граждан Узбекистана...",
                        "content_uz": "O'zbekiston fuqarolari uchun hujjat topshirish bo'yicha ko'rsatma...",
                        "order_index": 2
                    },
                    {
                        "citizenship_scope": "UZ",
                        "name_ru": "Онлайн регистрация",
                        "name_uz": "Onlayn ro'yxatdan o'tish",
                        "content_ru": "Как пройти онлайн регистрацию для граждан Узбекистана...",
                        "content_uz": "O'zbekiston fuqarolari uchun onlayn ro'yxatdan o'tish...",
                        "order_index": 3
                    },
                    {
                        "citizenship_scope": "RU",
                        "name_ru": "Получение рекомендации (Xitob)",
                        "name_uz": "Xitob (tavsiyanoma) olish",
                        "content_ru": "Полная информация о получении рекомендации для граждан России...",
                        "content_uz": "Rossiya fuqarolari uchun tavsiyanoma olish haqida to'liq ma'lumot...",
                        "order_index": 1
                    },
                    {
                        "citizenship_scope": "KZ",
                        "name_ru": "Получение рекомендации (Xitob)",
                        "name_uz": "Xitob (tavsiyanoma) olish",
                        "content_ru": "Полная информация о получении рекомендации для граждан Казахстана...",
                        "content_uz": "Qozog'iston fuqarolari uchun tavsiyanoma olish haqida to'liq ma'lumot...",
                        "order_index": 1
                    },
                    {
                        "citizenship_scope": "KG",
                        "name_ru": "Получение рекомендации (Xitob)",
                        "name_uz": "Xitob (tavsiyanoma) olish",
                        "content_ru": "Полная информация о получении рекомендации для граждан Кыргызстана...",
                        "content_uz": "Qirg'iziston fuqarolari uchun tavsiyanoma olish haqida to'liq ma'lumot...",
                        "order_index": 1
                    }
                ]
                
                for doc_data in initial_documents:
                    document = Document(**doc_data)
                    session.add(document)
                
                await session.commit()
                logger.info("Initial documents seeded successfully")
            except Exception as e:
                logger.error(f"Error seeding documents: {e}")
        
        # Check if system settings exist
        result = await session.execute(select(SystemSetting))
        settings_exist = result.scalars().first()
        
        if not settings_exist:
            logger.info("Seeding system settings...")
            default_settings = [
                {
                    "setting_key": "DOCUMENTS_ENABLED",
                    "setting_name_ru": "Раздел Документы включен",
                    "setting_name_uz": "Hujjatlar bo'limi yoqilgan",
                    "value": True
                },
                {
                    "setting_key": "DELIVERY_ENABLED",
                    "setting_name_ru": "Раздел Доставка включен",
                    "setting_name_uz": "Dostavka bo'limi yoqilgan",
                    "value": True
                },
                {
                    "setting_key": "NOTIFICATIONS_ENABLED",
                    "setting_name_ru": "Раздел Уведомления включен",
                    "setting_name_uz": "Xabarnoma bo'limi yoqilgan",
                    "value": True
                },
                {
                    "setting_key": "SHURTA_ENABLED",
                    "setting_name_ru": "Раздел Полиция включен",
                    "setting_name_uz": "Shurta bo'limi yoqilgan",
                    "value": True
                },
                {
                    "setting_key": "ALLOW_NEW_ORDERS",
                    "setting_name_ru": "Разрешить новые заказы доставки",
                    "setting_name_uz": "Yangi zakaz yaratishga ruxsat",
                    "value": True
                },
                {
                    "setting_key": "REQUIRE_COURIER_VERIFICATION",
                    "setting_name_ru": "Требовать верификацию курьера",
                    "setting_name_uz": "Kuryerni tekshirishni talab qilish",
                    "value": False
                },
                {
                    "setting_key": "AUTO_DELETE_OLD_NOTIFICATIONS",
                    "setting_name_ru": "Автоудаление старых уведомлений (>30 дней)",
                    "setting_name_uz": "Eski xabarlarni avtomatik o'chirish (>30 kun)",
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
