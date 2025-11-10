"""
Initialize default main menu buttons
Run this once to populate main_menu_buttons table
"""
import asyncio
from database import AsyncSessionLocal
from services.main_menu_service import MainMenuService
from utils.logger import logger


async def init_main_menu_buttons():
    """Initialize default main menu inline buttons"""
    async with AsyncSessionLocal() as session:
        # Check if buttons already exist
        buttons = await MainMenuService.get_active_buttons(session)
        if buttons:
            logger.info("✅ Main menu buttons already exist, skipping initialization")
            return

        logger.info("📋 Creating default main menu buttons...")

        # Create default buttons
        await MainMenuService.create_button(
            session,
            name_ru="🚚 Доставка",
            name_uz="🚚 Yetkazib berish",
            callback_data="menu_delivery",
            icon="🚚",
        )

        await MainMenuService.create_button(
            session,
            name_ru="🚨 Создать алерт",
            name_uz="🚨 Alert yaratish",
            callback_data="menu_alert",
            icon="🚨",
        )

        await MainMenuService.create_button(
            session,
            name_ru="📞 Написать админу",
            name_uz="📞 Adminga yozish",
            callback_data="menu_message_admin",
            icon="📞",
        )

        await MainMenuService.create_button(
            session,
            name_ru="⚙️ Настройки",
            name_uz="⚙️ Sozlamalar",
            callback_data="menu_settings",
            icon="⚙️",
        )

        logger.info("✅ Default main menu buttons created successfully!")


if __name__ == "__main__":
    asyncio.run(init_main_menu_buttons())
