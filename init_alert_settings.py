"""
Initialize system settings for the 11 alert types
Run this once after database migration
"""

import asyncio
from database import AsyncSessionLocal
from models import SystemSetting, AlertType
from sqlalchemy import select
from utils.logger import logger


ALERT_SETTINGS = {
    AlertType.PROPAJA_ODAM: {
        "name_ru": "Пропал человек",
        "name_uz": "Odam yo'qoldi"
    },
    AlertType.PROPAJA_NARSA: {
        "name_ru": "Пропала вещь",
        "name_uz": "Narsa yo'qoldi"
    },
    AlertType.SHURTA: {
        "name_ru": "Полиция",
        "name_uz": "Politsiya"
    },
    AlertType.DOSTAVKA: {
        "name_ru": "Доставка",
        "name_uz": "Yetkazib berish"
    },
    AlertType.ISH_TAKLIFNOMASI: {
        "name_ru": "Вакансия",
        "name_uz": "Ish taklifnomasi"
    },
    AlertType.UY_UYICHA: {
        "name_ru": "Жилье",
        "name_uz": "Uy-joy"
    },
    AlertType.TADBIR: {
        "name_ru": "Мероприятие",
        "name_uz": "Tadbir"
    },
    AlertType.FAVQULODDA: {
        "name_ru": "Чрезвычайное происшествие",
        "name_uz": "Favqulodda holat"
    },
    AlertType.SOTISH: {
        "name_ru": "Продажа",
        "name_uz": "Sotish"
    },
    AlertType.XIZMAT: {
        "name_ru": "Услуга",
        "name_uz": "Xizmat"
    },
    AlertType.ELON: {
        "name_ru": "Объявление",
        "name_uz": "E'lon"
    }
}


async def init_alert_settings():
    """Initialize alert type settings"""
    async with AsyncSessionLocal() as session:
        logger.info("🔧 Инициализация настроек системы алертов...")
        
        created_count = 0
        updated_count = 0
        
        for alert_type, names in ALERT_SETTINGS.items():
            setting_key = f"alert_{alert_type.value.lower()}"
            
            # Check if setting exists
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.setting_key == setting_key)
            )
            setting = result.scalar_one_or_none()
            
            if setting:
                # Update existing
                setting.setting_name_ru = names["name_ru"]
                setting.setting_name_uz = names["name_uz"]
                updated_count += 1
                logger.info(f"  ✏️ Обновлена настройка: {setting_key}")
            else:
                # Create new
                setting = SystemSetting(
                    setting_key=setting_key,
                    setting_name_ru=names["name_ru"],
                    setting_name_uz=names["name_uz"],
                    value=True  # Enabled by default
                )
                session.add(setting)
                created_count += 1
                logger.info(f"  ✅ Создана настройка: {setting_key}")
        
        # Also add document and delivery settings if not exist
        other_settings = [
            {
                "key": "documents_enabled",
                "name_ru": "Документы (Hujjat Yordami)",
                "name_uz": "Hujjatlar (Hujjat Yordami)"
            },
            {
                "key": "delivery_enabled",
                "name_ru": "Доставка (Dostavka)",
                "name_uz": "Yetkazib berish (Dostavka)"
            }
        ]
        
        for setting_data in other_settings:
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.setting_key == setting_data["key"])
            )
            setting = result.scalar_one_or_none()
            
            if not setting:
                setting = SystemSetting(
                    setting_key=setting_data["key"],
                    setting_name_ru=setting_data["name_ru"],
                    setting_name_uz=setting_data["name_uz"],
                    value=True
                )
                session.add(setting)
                created_count += 1
                logger.info(f"  ✅ Создана настройка: {setting_data['key']}")
        
        await session.commit()
        
        logger.info(f"\n✅ Инициализация завершена!")
        logger.info(f"  📝 Создано: {created_count}")
        logger.info(f"  ✏️ Обновлено: {updated_count}")
        logger.info(f"  📊 Всего: {len(ALERT_SETTINGS) + len(other_settings)}")


if __name__ == "__main__":
    asyncio.run(init_alert_settings())
