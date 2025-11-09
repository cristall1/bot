import asyncio
import sys
import uvicorn
from database import init_db
from bots.user_bot import UserBot
from bots.admin_bot import AdminBot
from utils.logger import logger
from config import settings
from webapp.server import create_app

# Import all models to ensure they are registered with SQLAlchemy Base
from models import (
    User, Document, DocumentButton, Delivery, Notification,
    ShurtaAlert, UserMessage, Broadcast, TelegraphArticle,
    Courier, SystemSetting, AdminLog, WebAppCategory,
    WebAppCategoryItem, WebAppCategoryItemType, WebAppFile
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
        
        # Seed initial Web App content
        result = await session.execute(select(WebAppCategory))
        webapp_categories_exist = result.scalars().first()
        
        if not webapp_categories_exist:
            logger.info("Seeding initial Web App content...")
            try:
                # Create example category
                example_category = WebAppCategory(
                    slug="welcome",
                    title="Добро пожаловать",
                    description="Вводная категория с информацией о боте",
                    order_index=1,
                    is_active=True
                )
                session.add(example_category)
                await session.commit()
                await session.refresh(example_category)
                
                # Add text item to the category
                text_item = WebAppCategoryItem(
                    category_id=example_category.id,
                    type="TEXT",
                    text_content="Добро пожаловать в наш бот! Здесь вы найдете полезную информацию и сервисы.",
                    order_index=1,
                    is_active=True
                )
                session.add(text_item)
                await session.commit()
                
                logger.info("Initial Web App content seeded successfully")
            except Exception as e:
                logger.error(f"Error seeding Web App content: {e}")


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
    webapp_app = create_app()

    uvicorn_config = uvicorn.Config(
        app=webapp_app,
        host=settings.webapp_host,
        port=settings.webapp_port,
        log_config=None,
        loop="asyncio"
    )
    webapp_server = uvicorn.Server(uvicorn_config)

    async def start_webapp_server():
        logger.info(
            "Запускаем веб-сервер: "
            f"{settings.webapp_public_url} (host={settings.webapp_host}, port={settings.webapp_port})"
        )
        try:
            await webapp_server.serve()
        finally:
            logger.info("Веб-сервер остановлен")

    tasks = [
        asyncio.create_task(user_bot.start(), name="user-bot"),
        asyncio.create_task(admin_bot.start(), name="admin-bot"),
        asyncio.create_task(start_webapp_server(), name="webapp-server")
    ]

    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки, завершаем работу сервисов...")
    except Exception as e:
        logger.error(f"Ошибка при работе сервисов: {e}")
        raise
    finally:
        webapp_server.should_exit = True
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("Останавливаем ботов...")
        await user_bot.stop()
        await admin_bot.stop()
        logger.info("Боты остановлены")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
