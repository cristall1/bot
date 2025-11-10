"""
User Bot Handlers - Comprehensive Implementation
Aiogram 3.x | RU/UZ Localization | 11 Alert Types | Category Navigation
"""

from aiogram import Router, F, Dispatcher
from aiogram.filters import Command
from aiogram.types import (
    Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
)
from aiogram.fsm.context import FSMContext
import asyncio
import re

from database import AsyncSessionLocal
from locales import t
from states import UserStates
from services.user_service import UserService
from services.category_service import CategoryService
from services.delivery_service import DeliveryService
from services.alert_service import AlertService
from services.user_message_service import UserMessageService
from services.statistics_service import StatisticsService
from services.geolocation_service import GeolocationService
from models import AlertType, User
from utils.logger import logger
from utils.message_helpers import send_menu_auto_delete, delete_message_later
from config import settings
from bot_registry import get_admin_bot, get_user_bot

router = Router()

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

async def send_alert_to_admins_for_moderation(alert):
    """
    Отправить алерт всем администраторам для модерации через ADMIN BOT
    Send alert to all admins for moderation via ADMIN BOT
    
    ИСПРАВЛЕНИЕ: Теперь отправляется через Admin Bot, а НЕ через User Bot!
    FIX: Now sends via Admin Bot, NOT User Bot!
    """
    admin_bot = get_admin_bot()
    if not admin_bot:
        logger.error(f"[send_alert_to_admins] ❌ Admin Bot не доступен!")
        return
    
    logger.info(f"[send_alert_to_admins] Начало | alert_id={alert.id} type={alert.alert_type.value}")
    try:
        async with AsyncSessionLocal() as session:
            admins = await UserService.get_all_admins(session)
            
            for admin in admins:
                try:
                    # Alert type emoji mapping
                    type_emojis = {
                        AlertType.SHURTA: "🚨",
                        AlertType.MISSING_PERSON: "👤",
                        AlertType.LOST_ITEM: "📦",
                        AlertType.SCAM_WARNING: "⚠️",
                        AlertType.MEDICAL_EMERGENCY: "🏥",
                        AlertType.ACCOMMODATION_NEEDED: "🏠",
                        AlertType.RIDE_SHARING: "🚗",
                        AlertType.JOB_POSTING: "💼",
                        AlertType.LOST_DOCUMENT: "📄",
                        AlertType.EVENT_ANNOUNCEMENT: "🎉",
                        AlertType.COURIER_NEEDED: "📦"
                    }
                    
                    emoji = type_emojis.get(alert.alert_type, "📝")
                    
                    text = f"{emoji} НОВЫЙ АЛЕРТ НА МОДЕРАЦИЮ\n"
                    text += f"═══════════════════════════════════════\n\n"
                    text += f"Тип: {alert.alert_type.value}\n"
                    
                    if alert.title:
                        text += f"Заголовок: {alert.title}\n"
                    text += f"Описание: {alert.description}\n"
                    
                    if alert.phone:
                        text += f"Телефон: {alert.phone}\n"
                    
                    if alert.address_text:
                        text += f"Адрес: {alert.address_text}\n"
                    elif alert.latitude and alert.longitude:
                        text += f"Координаты: {alert.latitude}, {alert.longitude}\n"
                    elif alert.maps_url:
                        text += f"Карта: {alert.maps_url}\n"
                    
                    text += f"\nОт пользователя: {alert.creator_id}\n"
                    text += f"ID алерта: {alert.id}\n"
                    
                    # 2-ROW BUTTON LAYOUT (COMPACT)
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_alert_approve_{alert.id}"),
                            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_alert_reject_{alert.id}")
                        ]
                    ])
                    
                    # Send location if available
                    if alert.latitude and alert.longitude:
                        await admin_bot.send_location(
                            chat_id=admin.telegram_id,
                            latitude=alert.latitude,
                            longitude=alert.longitude
                        )
                    
                    # Send photo or text via ADMIN BOT
                    if alert.photo_file_id:
                        msg = await admin_bot.send_photo(
                            chat_id=admin.telegram_id,
                            photo=alert.photo_file_id,
                            caption=text,
                            reply_markup=keyboard
                        )
                    else:
                        msg = await admin_bot.send_message(
                            chat_id=admin.telegram_id,
                            text=text,
                            reply_markup=keyboard
                        )
                    
                    # Store message_id for later deletion after moderation
                    async with AsyncSessionLocal() as mod_session:
                        from models import ModerationQueue
                        from sqlalchemy import select, update
                        
                        # Update moderation queue with message_id
                        stmt = (
                            update(ModerationQueue)
                            .where(ModerationQueue.entity_type == "ALERT")
                            .where(ModerationQueue.entity_id == alert.id)
                            .values(admin_message_id=msg.message_id)
                        )
                        await mod_session.execute(stmt)
                        await mod_session.commit()
                    
                    logger.info(f"[send_alert_to_admins] ✅ Отправлено администратору {admin.telegram_id} через Admin Bot")
                except Exception as e:
                    logger.error(f"[send_alert_to_admins] ❌ Ошибка отправки администратору {admin.telegram_id}: {str(e)}")
        
        logger.info(f"[send_alert_to_admins] ✅ Успешно")
    except Exception as e:
        logger.error(f"[send_alert_to_admins] ❌ Ошибка: {str(e)}", exc_info=True)


def get_language_keyboard():
    """Get language selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_RU"),
            InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang_UZ")
        ]
    ])
    return keyboard


async def get_main_menu_inline_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Get main menu INLINE keyboard from database (ALWAYS FRESH DATA)"""
    from services.main_menu_service import MainMenuService
    
    async with AsyncSessionLocal() as session:
        buttons = await MainMenuService.get_active_buttons(session)
        
        # Build inline keyboard
        keyboard_buttons = []
        
        # WebApp button first if HTTPS
        webapp_url = settings.webapp_url or settings.webapp_public_url
        if webapp_url and webapp_url.startswith("https://"):
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=t("menu_webapp", lang),
                    web_app=WebAppInfo(url=webapp_url)
                )
            ])
        
        # Add database buttons
        for btn in buttons:
            btn_text = f"{btn.icon} {btn.name_ru}" if lang == "RU" else f"{btn.icon} {btn.name_uz}"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=btn_text,
                    callback_data=btn.callback_data
                )
            ])
        
        # Fallback defaults if DB empty
        if not buttons:
            default_buttons = [
                ("🚚", t("menu_delivery", lang), "menu_delivery"),
                ("🚨", t("alert_menu_title", lang), "menu_alert"),
                ("📞", t("menu_admin_contact", lang), "menu_message_admin"),
                ("⚙️", t("menu_settings", lang), "menu_settings"),
            ]
            for icon, text_label, callback in default_buttons:
                keyboard_buttons.append([
                    InlineKeyboardButton(text=f"{icon} {text_label}", callback_data=callback)
                ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


def get_back_keyboard(lang: str):
    """Get back button keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("to_main_menu", lang))]],
        resize_keyboard=True
    )
    return keyboard


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    # Simple validation: starts with + and has 10-15 digits
    pattern = r'^\+?\d{10,15}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))


def validate_google_maps_url(url: str) -> bool:
    """Validate Google Maps URL"""
    patterns = [
        r'https?://maps\.google\.com',
        r'https?://www\.google\.com/maps',
        r'https?://goo\.gl/maps'
    ]
    return any(re.search(pattern, url) for pattern in patterns)


# ==============================================================================
# START & LANGUAGE SELECTION
# ==============================================================================

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command - NOW WITH INLINE KEYBOARD"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        
        if not user:
            await message.answer(
                t("welcome", "RU"),
                reply_markup=get_language_keyboard()
            )
            await state.set_state(UserStates.selecting_language)
            logger.info(f"[cmd_start] 👤 Новый пользователь {message.from_user.id}")
        else:
            if user.is_banned:
                await message.answer(t("banned", user.language))
                logger.info(f"[cmd_start] 🚫 Заблокированный пользователь {message.from_user.id}")
                return
            
            # Ensure preferences are present (handles legacy users)
            await AlertService.ensure_user_alert_preferences(session, user.id)
            
            # SHOW INLINE KEYBOARD MENU
            menu_keyboard = await get_main_menu_inline_keyboard(user.language)
            await message.answer(
                t("main_menu", user.language),
                reply_markup=menu_keyboard
            )
            
            await StatisticsService.track_activity(
                session,
                user.id,
                "WEBAPP_OPEN",
                {"source": "main_menu", "url": settings.webapp_url or settings.webapp_public_url}
            )
            logger.info(f"[cmd_start] ✅ Пользователь {message.from_user.id} вернулся в главное меню")


@router.message(Command("webapp"))
async def cmd_webapp(message: Message):
    """Provide direct access to the WebApp button"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        lang = user.language if user else "RU"
        
        if user and user.is_banned:
            await message.answer(t("banned", lang))
            return
        
        webapp_text = f"{t('webapp_title', lang)}\n\n{t('webapp_description', lang)}"
        menu_keyboard = await get_main_menu_inline_keyboard(lang)
        await message.answer(
            webapp_text,
            reply_markup=menu_keyboard
        )
        
        if user:
            await StatisticsService.track_activity(
                session,
                user.id,
                "WEBAPP_OPEN",
                {"source": "command", "url": settings.webapp_url or settings.webapp_public_url}
            )
        logger.info(f"[cmd_webapp] ✅ Пользователь {message.from_user.id} открыл WebApp")


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Process language selection WITH ONBOARDING"""
    lang = callback.data.split("_")[1]
    
    async with AsyncSessionLocal() as session:
        user = await UserService.create_or_update_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            language=lang
        )
        
        # Ensure user has alert preferences with ALL ENABLED BY DEFAULT
        await AlertService.ensure_user_alert_preferences(session, user.id)
        
        # SHOW ONBOARDING MESSAGE
        onboarding_text_ru = """
✅ Язык выбран!

═══════════════════════════════════════
🔔 ОЗНАКОМЛЕНИЕ С БОТОМ
═══════════════════════════════════════

По умолчанию ВЫ ПОЛУЧАЕТЕ уведомления о:

🚨 Полиции (SHURTA)
👤 Пропавших людях
📦 Потерянных вещах
⚠️ Предупреждениях о мошенничестве
🏥 Медицинской помощи
🏠 Жилье
🚗 Совместных поездках
💼 Предложениях работы
📄 Потерянных документах
🎉 Событиях

Вы можете изменить настройки в любое время:
[⚙️ Настройки] → [🔔 Уведомления]
"""
        
        onboarding_text_uz = """
✅ Til tanlandi!

═══════════════════════════════════════
🔔 BOT HAQIDA MA'LUMOT
═══════════════════════════════════════

Standart bo'yicha SIZ BILDIRISHNOMALAR olasiz:

🚨 Politsiya (SHURTA)
👤 Yo'qolgan odamlar
📦 Yo'qolgan narsalar
⚠️ Firibgarlik haqida ogohlantirishlar
🏥 Tibbiy yordam
🏠 Uy-joy
🚗 Birgalikda sayohat
💼 Ish takliflari
📄 Yo'qolgan hujjatlar
🎉 Tadbirlar

Sozlamalarni istalgan vaqtda o'zgartirishingiz mumkin:
[⚙️ Sozlamalar] → [🔔 Bildirishnomalar]
"""
        
        onboarding_text = onboarding_text_ru if lang == "RU" else onboarding_text_uz
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👍 Понятно" if lang == "RU" else "👍 Tushunarli", callback_data="onboarding_understood")],
            [InlineKeyboardButton(text="⚙️ Настроить сейчас" if lang == "RU" else "⚙️ Hozir sozlash", callback_data="menu_settings")]
        ])
        
        await callback.message.edit_text(onboarding_text, reply_markup=keyboard)
        
        await StatisticsService.track_activity(
            session,
            user.id,
            "LANGUAGE_SELECTED",
            {"language": lang}
        )
        logger.info(f"[language_selection] ✅ Пользователь {callback.from_user.id} выбрал язык {lang}")
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "onboarding_understood")
async def onboarding_complete(callback: CallbackQuery):
    """Complete onboarding and show main menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        menu_keyboard = await get_main_menu_inline_keyboard(user.language)
        await callback.message.edit_text(
            t("main_menu", user.language),
            reply_markup=menu_keyboard
        )
        logger.info(f"[onboarding] ✅ Пользователь {user.id} завершил онбординг")
    
    await callback.answer()


# ==============================================================================
# MAIN MENU INLINE KEYBOARD HANDLERS
# ==============================================================================

@router.callback_query(F.data == "back_main")
async def back_to_main_menu(callback: CallbackQuery):
    """Return to main menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        menu_keyboard = await get_main_menu_inline_keyboard(user.language)
        await callback.message.edit_text(
            t("main_menu", user.language),
            reply_markup=menu_keyboard
        )
    await callback.answer()


@router.callback_query(F.data == "menu_delivery")
async def menu_delivery_handler(callback: CallbackQuery):
    """Handle delivery menu button from main menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user or user.is_banned:
            return
        
        # Check if user is courier
        if user.is_courier:
            # Show courier menu
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("delivery_menu_create", user.language), callback_data="delivery_create")],
                [InlineKeyboardButton(text=t("delivery_menu_active", user.language), callback_data="delivery_active")],
                [InlineKeyboardButton(text=t("delivery_menu_my_stats", user.language), callback_data="delivery_stats")],
                [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
            ])
        else:
            # Show options: become courier or order delivery
            text_ru = """
🚚 ДОСТАВКА
═════════════════

Вы не зарегистрированы как курьер.

Что вы хотите?
"""
            text_uz = """
🚚 YETKAZIB BERISH
═════════════════

Siz kuryer sifatida ro'yxatdan o'tmagansiz.

Nima qilmoqchisiz?
"""
            text = text_ru if user.language == "RU" else text_uz
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Стать курьером" if user.language == "RU" else "✅ Kuryer bo'lish", callback_data="become_courier")],
                [InlineKeyboardButton(text="📦 Заказать доставку" if user.language == "RU" else "📦 Yetkazishni buyurtma qilish", callback_data="delivery_create")],
                [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
            ])
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            return
        
        await callback.message.edit_text(
            t("delivery_title", user.language),
            reply_markup=keyboard
        )
        logger.info(f"[menu_delivery] ✅ Пользователь {user.id} открыл меню доставки")
    await callback.answer()


@router.callback_query(F.data == "menu_alert")
async def menu_alert_handler(callback: CallbackQuery, state: FSMContext):
    """Handle alert creation button from main menu"""
    # Redirect to alert type selection
    await show_alert_type_selection(callback, state)


@router.callback_query(F.data == "menu_message_admin")
async def menu_message_admin_handler(callback: CallbackQuery, state: FSMContext):
    """Handle message admin button from main menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user or user.is_banned:
            return
        
        await callback.message.answer(
            t("admin_contact_prompt", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.admin_contact_message)
        logger.info(f"[menu_message_admin] ✅ Пользователь {user.id} начал писать админу")
    await callback.answer()


@router.callback_query(F.data == "menu_settings")
async def menu_settings_handler(callback: CallbackQuery):
    """Handle settings button from main menu"""
    await show_settings_menu(callback)


# ==============================================================================
# CATEGORY NAVIGATION (4 LEVELS)
# ==============================================================================

@router.message(F.text.in_([t("menu_documents", "RU"), t("menu_documents", "UZ")]))
async def handle_documents_categories(message: Message, state: FSMContext):
    """Handle documents menu - show root categories"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        # Get root categories
        categories = await CategoryService.get_root_categories(session, active_only=True)
        
        if not categories:
            await message.answer(t("category_no_content", user.language))
            return
        
        buttons = []
        for cat in categories:
            cat_name = cat.name_ru if user.language == "RU" else cat.name_uz
            icon = cat.icon or "📁"
            buttons.append([InlineKeyboardButton(
                text=f"{icon} {cat_name}",
                callback_data=f"cat_{cat.id}"
            )])
        
        buttons.append([InlineKeyboardButton(text=t("category_main_menu", user.language), callback_data="back_main")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            t("category_select", user.language),
            reply_markup=keyboard
        )
        
        await state.set_state(UserStates.browsing_categories)
        logger.info(f"[documents_categories] ✅ Пользователь {message.from_user.id} открыл категории")


@router.callback_query(F.data.startswith("cat_"))
async def show_category_content(callback: CallbackQuery, state: FSMContext):
    """Show category content or subcategories"""
    cat_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        category = await CategoryService.get_category(session, cat_id)
        if not category:
            await callback.answer("❌ Категория не найдена", show_alert=True)
            return
        
        # Get subcategories
        subcategories = await CategoryService.get_subcategories(session, cat_id, active_only=True)
        
        cat_name = category.name_ru if user.language == "RU" else category.name_uz
        
        # If has subcategories, show them
        if subcategories:
            buttons = []
            for sub in subcategories:
                sub_name = sub.name_ru if user.language == "RU" else sub.name_uz
                icon = sub.icon or "📄"
                buttons.append([InlineKeyboardButton(
                    text=f"{icon} {sub_name}",
                    callback_data=f"cat_{sub.id}"
                )])
            
            # Back button to parent or main
            if category.parent_id:
                buttons.append([InlineKeyboardButton(text=t("category_back", user.language), callback_data=f"cat_{category.parent_id}")])
            else:
                buttons.append([InlineKeyboardButton(text=t("category_main_menu", user.language), callback_data="back_main")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await callback.message.edit_text(
                f"{cat_name}\n\n{t('category_select', user.language)}",
                reply_markup=keyboard
            )
        else:
            # Show content
            text_content = category.text_content_ru if user.language == "RU" else category.text_content_uz
            content_text = f"{cat_name}\n\n{text_content or t('category_no_content', user.language)}"
            
            # Build keyboard with buttons
            buttons = []
            
            # Add category buttons (links, etc.)
            for btn in category.buttons:
                btn_text = btn.text_ru if user.language == "RU" else btn.text_uz
                if btn.button_type == "LINK":
                    buttons.append([InlineKeyboardButton(text=btn_text, url=btn.button_value)])
                elif btn.button_type == "CALLBACK":
                    buttons.append([InlineKeyboardButton(text=btn_text, callback_data=btn.button_value)])
                elif btn.button_type == "GEO":
                    # Handle geolocation button
                    buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"cat_geo_{btn.id}")])
            
            # Back button
            if category.parent_id:
                buttons.append([InlineKeyboardButton(text=t("category_back", user.language), callback_data=f"cat_{category.parent_id}")])
            else:
                buttons.append([InlineKeyboardButton(text=t("category_main_menu", user.language), callback_data="back_main")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            # Send based on content type
            if category.content_type == "PHOTO" and category.photo_file_id:
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=category.photo_file_id,
                    caption=content_text,
                    reply_markup=keyboard
                )
            elif category.content_type == "AUDIO" and category.audio_file_id:
                await callback.message.delete()
                await callback.message.answer_audio(
                    audio=category.audio_file_id,
                    caption=content_text,
                    reply_markup=keyboard
                )
            elif category.content_type == "PDF" and category.pdf_file_id:
                await callback.message.delete()
                await callback.message.answer_document(
                    document=category.pdf_file_id,
                    caption=content_text,
                    reply_markup=keyboard
                )
            elif category.content_type == "LOCATION" and category.latitude and category.longitude:
                await callback.message.delete()
                await callback.message.answer_location(
                    latitude=category.latitude,
                    longitude=category.longitude
                )
                await callback.message.answer(content_text, reply_markup=keyboard)
            else:
                await callback.message.edit_text(content_text, reply_markup=keyboard)
        
        await StatisticsService.track_activity(
            session,
            user.id,
            "CATEGORY_VIEW",
            {"category_id": cat_id, "category_name": cat_name}
        )
        logger.info(f"[category_content] ✅ Пользователь {user.id} открыл категорию {cat_id}")
    
    await callback.answer()


@router.callback_query(F.data.startswith("cat_geo_"))
async def send_category_geolocation(callback: CallbackQuery):
    """Send geolocation from category button"""
    btn_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        from models import CategoryButton
        
        result = await session.execute(
            select(CategoryButton).where(CategoryButton.id == btn_id)
        )
        button = result.scalar_one_or_none()
        
        if button and button.button_value:
            # Parse coordinates from button_value (format: "lat,lon")
            try:
                lat_str, lon_str = button.button_value.split(",")
                latitude = float(lat_str)
                longitude = float(lon_str)
                
                await callback.message.answer_location(latitude=latitude, longitude=longitude)
                logger.info(f"[cat_geo] ✅ Отправлена геолокация {latitude},{longitude}")
            except Exception as e:
                logger.error(f"[cat_geo] ❌ Ошибка парсинга координат: {str(e)}")
                await callback.answer("❌ Ошибка получения координат", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    """Back to main menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            t("main_menu", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        
        await state.clear()
        logger.info(f"[back_main] ✅ Пользователь {user.id} вернулся в главное меню")
    await callback.answer()


# ==============================================================================
# UNIFIED ALERT CREATION (11 TYPES)
# ==============================================================================

@router.message(F.text.in_([t("alert_menu_title", "RU"), t("alert_menu_title", "UZ")]))
async def start_alert_creation(message: Message, state: FSMContext):
    """Start alert creation - show type selection"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        # Build type selection keyboard - 2 COLUMNS layout, exclude COURIER_NEEDED
        from utils.message_helpers import build_keyboard_2_columns
        
        buttons = []
        for alert_type in AlertType:
            # EXCLUDE COURIER_NEEDED from user UI (delivery is managed separately)
            if alert_type == AlertType.COURIER_NEEDED:
                continue
            
            type_key = f"alert_type_{alert_type.value.lower()}"
            type_text = t(type_key, user.language)
            buttons.append(InlineKeyboardButton(
                text=type_text,
                callback_data=f"alert_create_{alert_type.value}"
            ))
        
        # Build 2-column keyboard with back button
        back_button = InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")
        keyboard = build_keyboard_2_columns(buttons, back_button=back_button)
        
        await message.answer(
            t("alert_select_type", user.language),
            reply_markup=keyboard
        )
        
        await state.set_state(UserStates.alert_type_selection)
        logger.info(f"[start_alert] ✅ Пользователь {user.id} начал создание алерта")


@router.callback_query(F.data.startswith("alert_create_"))
async def select_alert_type(callback: CallbackQuery, state: FSMContext):
    """Select alert type and start gathering info"""
    alert_type_str = callback.data.split("alert_create_")[1]
    alert_type = AlertType(alert_type_str)
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Check if alert type is enabled
        is_enabled = await AlertService.check_alert_type_enabled(session, alert_type)
        if not is_enabled:
            await callback.answer("❌ Этот тип алертов временно отключен", show_alert=True)
            return
        
        # Store alert type in state
        await state.update_data(alert_type=alert_type)
        
        # Determine if title is needed (for some types)
        needs_title = alert_type in [
            AlertType.MISSING_PERSON,  # Name
            AlertType.LOST_ITEM,  # What
            AlertType.JOB_POSTING,  # Job title
            AlertType.ACCOMMODATION_NEEDED,  # Property name
            AlertType.EVENT_ANNOUNCEMENT,  # Event name
            AlertType.LOST_DOCUMENT  # Document name
        ]
        
        if needs_title:
            await callback.message.answer(
                t("alert_title_prompt", user.language),
                reply_markup=get_back_keyboard(user.language)
            )
            await state.set_state(UserStates.alert_title)
        else:
            # Skip to description
            await callback.message.answer(
                t("alert_description_prompt", user.language),
                reply_markup=get_back_keyboard(user.language)
            )
            await state.set_state(UserStates.alert_description)
        
        logger.info(f"[select_alert_type] ✅ Пользователь {user.id} выбрал тип {alert_type.value}")
    
    await callback.answer()


@router.message(UserStates.alert_title)
async def process_alert_title(message: Message, state: FSMContext):
    """Process alert title"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        await state.update_data(title=message.text)
        await message.answer(
            t("alert_description_prompt", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.alert_description)
        logger.info(f"[alert_title] ✅ Пользователь {user.id} указал заголовок")


@router.message(UserStates.alert_description)
async def process_alert_description(message: Message, state: FSMContext):
    """Process alert description"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        await state.update_data(description=message.text)
        
        # Determine if phone is needed
        data = await state.get_data()
        alert_type = data.get("alert_type")
        
        needs_phone = alert_type in [
            AlertType.MISSING_PERSON,
            AlertType.LOST_ITEM,
            AlertType.JOB_POSTING,
            AlertType.ACCOMMODATION_NEEDED,
            AlertType.RIDE_SHARING,
            AlertType.LOST_DOCUMENT
        ]
        
        if needs_phone:
            await message.answer(
                t("alert_phone_prompt", user.language),
                reply_markup=get_back_keyboard(user.language)
            )
            await state.set_state(UserStates.alert_phone)
        else:
            # Skip to location choice
            await show_location_choice(message, state, user.language)


@router.message(UserStates.alert_phone)
async def process_alert_phone(message: Message, state: FSMContext):
    """Process alert phone number"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        # Validate phone
        if not validate_phone_number(message.text):
            await message.answer(
                f"❌ {t('invalid_input', user.language)}\n\nФормат: +998901234567",
                reply_markup=get_back_keyboard(user.language)
            )
            return
        
        await state.update_data(phone=message.text)
        await show_location_choice(message, state, user.language)


async def show_location_choice(message: Message, state: FSMContext, lang: str):
    """Show location input choice"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("notifications_location_text", lang), callback_data="alert_loc_text")],
        [InlineKeyboardButton(text=t("notifications_location_geo", lang), callback_data="alert_loc_geo")],
        [InlineKeyboardButton(text=t("notifications_location_maps", lang), callback_data="alert_loc_maps")],
        [InlineKeyboardButton(text=t("notifications_skip_photo", lang), callback_data="alert_skip_location")]
    ])
    
    await message.answer(
        t("alert_location_prompt", lang),
        reply_markup=keyboard
    )
    await state.set_state(UserStates.alert_location_choice)
    logger.info(f"[show_location_choice] ✅ Показан выбор локации")


@router.callback_query(F.data == "alert_loc_text")
async def alert_location_text(callback: CallbackQuery, state: FSMContext):
    """Get text location"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            t("shurta_location_input", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.alert_location_text)
    await callback.answer()


@router.message(UserStates.alert_location_text)
async def process_alert_location_text(message: Message, state: FSMContext):
    """Process text location"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        await state.update_data(
            location_type="ADDRESS",
            address_text=message.text
        )
        
        # Ask for photo
        await ask_for_photo(message, state, user.language)


@router.callback_query(F.data == "alert_loc_geo")
async def alert_location_geo(callback: CallbackQuery, state: FSMContext):
    """Get geolocation"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)],
                     [KeyboardButton(text=t("to_main_menu", user.language))]],
            resize_keyboard=True
        )
        await callback.message.answer(
            t("shurta_location_geo_input", user.language),
            reply_markup=keyboard
        )
        await state.set_state(UserStates.alert_location_geo)
    await callback.answer()


@router.message(UserStates.alert_location_geo, F.location)
async def process_alert_location_geo(message: Message, state: FSMContext):
    """Process geolocation"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(
            location_type="GEO",
            latitude=message.location.latitude,
            longitude=message.location.longitude,
            geo_name=f"{message.location.latitude:.6f}, {message.location.longitude:.6f}"
        )
        
        # Ask for photo
        await ask_for_photo(message, state, user.language)


@router.callback_query(F.data == "alert_loc_maps")
async def alert_location_maps(callback: CallbackQuery, state: FSMContext):
    """Get Google Maps link"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            t("shurta_location_maps_input", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.alert_location_maps)
    await callback.answer()


@router.message(UserStates.alert_location_maps, ~F.location)
async def process_alert_location_maps(message: Message, state: FSMContext):
    """Process Google Maps link"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        # Validate Google Maps URL
        if not validate_google_maps_url(message.text):
            await message.answer(
                f"❌ {t('invalid_input', user.language)}\n\nПример: https://maps.google.com/?q=41.2995,69.2401",
                reply_markup=get_back_keyboard(user.language)
            )
            return
        
        # Try to parse coordinates from URL
        parsed = GeolocationService.parse_google_maps_url(message.text)
        if parsed and parsed.get("type") == "COORDINATES":
            await state.update_data(
                location_type="GEO",
                latitude=parsed["latitude"],
                longitude=parsed["longitude"],
                maps_url=message.text
            )
        else:
            await state.update_data(
                location_type="MAPS",
                maps_url=message.text
            )
        
        # Ask for photo
        await ask_for_photo(message, state, user.language)


@router.callback_query(F.data == "alert_skip_location")
async def skip_alert_location(callback: CallbackQuery, state: FSMContext):
    """Skip location"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Ask for photo
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("alert_skip_photo", user.language), callback_data="alert_skip_photo")]
        ])
        
        await callback.message.answer(
            t("alert_photo_prompt", user.language),
            reply_markup=keyboard
        )
        await state.set_state(UserStates.alert_photo)
    await callback.answer()


async def ask_for_photo(message: Message, state: FSMContext, lang: str):
    """Ask for optional photo"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("alert_skip_photo", lang), callback_data="alert_skip_photo")]
    ])
    
    await message.answer(
        t("alert_photo_prompt", lang),
        reply_markup=keyboard
    )
    await state.set_state(UserStates.alert_photo)


@router.message(UserStates.alert_photo, F.photo)
async def process_alert_photo(message: Message, state: FSMContext):
    """Process alert photo"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        # Get largest photo
        photo = message.photo[-1]
        await state.update_data(photo_file_id=photo.file_id)
        
        # Create alert
        await create_alert_from_state(message, state, user, session)


@router.callback_query(F.data == "alert_skip_photo")
async def skip_alert_photo(callback: CallbackQuery, state: FSMContext):
    """Skip photo and create alert"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Create alert
        await create_alert_from_state(callback.message, state, user, session)
    
    await callback.answer()


async def create_alert_from_state(message: Message, state: FSMContext, user, session):
    """Create alert from FSM state data"""
    data = await state.get_data()
    
    try:
        # Create alert
        alert = await AlertService.create_alert(
            session,
            alert_type=data.get("alert_type"),
            creator_id=user.id,
            title=data.get("title"),
            description=data.get("description"),
            phone=data.get("phone"),
            photo_file_id=data.get("photo_file_id"),
            location_type=data.get("location_type"),
            address_text=data.get("address_text"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            geo_name=data.get("geo_name"),
            maps_url=data.get("maps_url"),
            expires_hours=48  # Default expiration
        )
        
        # Send to admins for moderation via ADMIN BOT
        asyncio.create_task(send_alert_to_admins_for_moderation(alert))
        
        # Confirm to user with auto-delete after 30 sec
        msg = await message.answer(
            t("alert_created", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        # Auto-delete confirmation after 30 seconds
        asyncio.create_task(delete_message_later(message.bot, message.chat.id, msg.message_id, 30))
        
        await StatisticsService.track_activity(
            session,
            user.id,
            "ALERT_CREATED",
            {"alert_id": alert.id, "alert_type": alert.alert_type.value}
        )
        
        logger.info(f"[create_alert] ✅ Пользователь {user.id} создал алерт #{alert.id} типа {alert.alert_type.value}")
        
    except Exception as e:
        logger.error(f"[create_alert] ❌ Ошибка создания алерта: {str(e)}", exc_info=True)
        await message.answer(
            t("error", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
    
    await state.clear()


async def notify_couriers_about_delivery(delivery, session):
    """
    Notify all active couriers about new delivery order
    Sends notification via User Bot with order details and action buttons
    """
    user_bot = get_user_bot()
    if not user_bot:
        logger.error("[notify_couriers] ❌ User Bot не доступен!")
        return
    
    try:
        # Get all active couriers
        from sqlalchemy import select
        from models import User
        result = await session.execute(
            select(User).where(
                User.is_courier == True,
                User.is_banned == False
            )
        )
        couriers = result.scalars().all()
        
        if not couriers:
            logger.info("[notify_couriers] ⚠️ Нет активных курьеров")
            return
        
        # Format location info
        location_text = ""
        if delivery.address_text:
            location_text = f"\n📍 Откуда: {delivery.address_text}"
        elif delivery.latitude and delivery.longitude:
            location_text = f"\n📍 Координаты: {delivery.latitude:.6f}, {delivery.longitude:.6f}"
        elif delivery.geo_name:
            location_text = f"\n📍 Место: {delivery.geo_name}"
        
        sent_count = 0
        failed_count = 0
        
        for courier in couriers:
            try:
                text_ru = f"""
🚚 НОВЫЙ ЗАКАЗ #{delivery.id}

Что доставить: {delivery.description}
{location_text}

📞 Телефон заказчика: {delivery.phone}
⏰ Создан: {delivery.created_at.strftime('%d.%m.%Y %H:%M')}

Хотите взять этот заказ?
"""
                
                text_uz = f"""
🚚 YANGI BUYURTMA #{delivery.id}

Nima yetkazish: {delivery.description}
{location_text}

📞 Buyurtmachi telefoni: {delivery.phone}
⏰ Yaratilgan: {delivery.created_at.strftime('%d.%m.%Y %H:%M')}

Ushbu buyurtmani qabul qilmoqchimisiz?
"""
                
                text = text_ru if courier.language == "RU" else text_uz
                
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ Взять заказ" if courier.language == "RU" else "✅ Qabul qilish",
                            callback_data=f"accept_delivery_{delivery.id}"
                        ),
                        InlineKeyboardButton(
                            text="❌ Отклонить" if courier.language == "RU" else "❌ Rad etish",
                            callback_data=f"decline_delivery_{delivery.id}"
                        )
                    ]
                ])
                
                # Send location first if available
                if delivery.latitude and delivery.longitude:
                    try:
                        await user_bot.send_location(
                            chat_id=courier.telegram_id,
                            latitude=delivery.latitude,
                            longitude=delivery.longitude
                        )
                    except Exception as loc_error:
                        logger.error(f"[notify_couriers] ❌ Ошибка отправки локации курьеру {courier.telegram_id}: {str(loc_error)}")
                
                # Send notification
                await user_bot.send_message(
                    chat_id=courier.telegram_id,
                    text=text,
                    reply_markup=keyboard
                )
                
                sent_count += 1
                logger.info(f"[notify_couriers] ✅ Уведомление отправлено курьеру {courier.telegram_id}")
                
            except Exception as courier_error:
                failed_count += 1
                logger.error(f"[notify_couriers] ❌ Ошибка отправки курьеру {courier.telegram_id}: {str(courier_error)}")
        
        logger.info(f"[notify_couriers] ✅ Завершено: отправлено={sent_count}, ошибок={failed_count}")
        
    except Exception as e:
        logger.error(f"[notify_couriers] ❌ Критическая ошибка: {str(e)}", exc_info=True)


@router.callback_query(F.data.startswith("accept_delivery_"))
async def courier_accept_delivery(callback: CallbackQuery):
    """Courier accepts delivery order"""
    delivery_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user or not user.is_courier:
            await callback.answer("❌ Только курьеры могут принимать заказы", show_alert=True)
            return
        
        # Try to assign delivery
        delivery = await DeliveryService.assign_courier(session, delivery_id, user.id)
        
        if delivery:
            await callback.answer("✅ Заказ принят!" if user.language == "RU" else "✅ Buyurtma qabul qilindi!", show_alert=True)
            
            # Update message to show it's taken
            taken_text_ru = f"""
✅ ЗАКАЗ ПРИНЯТ

Вы приняли заказ #{delivery.id}

Что доставить: {delivery.description}
📞 Телефон: {delivery.phone}

Свяжитесь с заказчиком для уточнения деталей.
"""
            taken_text_uz = f"""
✅ BUYURTMA QABUL QILINDI

Siz #{delivery.id} buyurtmani qabul qildingiz

Nima yetkazish: {delivery.description}
📞 Telefon: {delivery.phone}

Tafsilotlar uchun buyurtmachi bilan bog'laning.
"""
            
            taken_text = taken_text_ru if user.language == "RU" else taken_text_uz
            
            try:
                await callback.message.edit_text(taken_text)
            except Exception:
                pass
            
            # Notify customer
            try:
                user_bot = get_user_bot()
                customer_text_ru = f"""
✅ Ваш заказ #{delivery.id} принят курьером!

Курьер свяжется с вами в ближайшее время.
"""
                customer_text_uz = f"""
✅ Sizning #{delivery.id} buyurtmangiz kuryer tomonidan qabul qilindi!

Kuryer tez orada siz bilan bog'lanadi.
"""
                
                from sqlalchemy import select
                from models import User
                result = await session.execute(
                    select(User).where(User.id == delivery.creator_id)
                )
                customer = result.scalar_one_or_none()
                
                if customer:
                    customer_text = customer_text_ru if customer.language == "RU" else customer_text_uz
                    await user_bot.send_message(
                        chat_id=customer.telegram_id,
                        text=customer_text
                    )
            except Exception as notify_error:
                logger.error(f"[accept_delivery] ❌ Ошибка уведомления заказчика: {str(notify_error)}")
            
            logger.info(f"[accept_delivery] ✅ Курьер {user.id} принял доставку {delivery_id}")
        else:
            await callback.answer("❌ Заказ уже принят другим курьером" if user.language == "RU" else "❌ Buyurtma boshqa kuryer tomonidan qabul qilingan", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("decline_delivery_"))
async def courier_decline_delivery(callback: CallbackQuery):
    """Courier declines delivery order"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.answer("Заказ отклонен" if user.language == "RU" else "Buyurtma rad etildi")
        
        try:
            await callback.message.delete()
        except Exception:
            pass
    
    await callback.answer()


# ==============================================================================
# DELIVERY MENU (EXISTING FUNCTIONALITY WITH INLINE UPDATES)
# ==============================================================================

@router.message(F.text.in_([t("menu_delivery", "RU"), t("menu_delivery", "UZ")]))
async def handle_delivery(message: Message):
    """Handle delivery menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("delivery_menu_create", user.language), callback_data="delivery_create")],
            [InlineKeyboardButton(text=t("delivery_menu_active", user.language), callback_data="delivery_active")],
            [InlineKeyboardButton(text=t("delivery_menu_my_stats", user.language), callback_data="delivery_stats")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
        ])
        
        await message.answer(
            t("delivery_title", user.language),
            reply_markup=keyboard
        )
        logger.info(f"[delivery_menu] ✅ Пользователь {user.id} открыл меню доставки")


@router.callback_query(F.data == "delivery_active")
async def show_active_deliveries(callback: CallbackQuery):
    """Show active delivery orders with inline updates"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Get active deliveries with fresh query
        deliveries = await DeliveryService.get_active_deliveries(session)
        
        if not deliveries:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("back", user.language), callback_data="back_delivery_menu")]
            ])
            await callback.message.edit_text(
                t("delivery_no_active", user.language),
                reply_markup=keyboard
            )
        else:
            buttons = []
            for delivery in deliveries:
                btn_text = f"📦 {delivery.description[:30]}..."
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_delivery_{delivery.id}")])
            
            buttons.append([InlineKeyboardButton(text=t("back", user.language), callback_data="back_delivery_menu")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await callback.message.edit_text(
                f"{t('delivery_menu_active', user.language)}\n\n📊 Всего активных: {len(deliveries)}",
                reply_markup=keyboard
            )
        
        logger.info(f"[delivery_active] ✅ Пользователь {user.id} просмотрел активные доставки")
    
    await callback.answer()


@router.callback_query(F.data.startswith("view_delivery_"))
async def view_delivery_order(callback: CallbackQuery):
    """View specific delivery order with location"""
    delivery_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        delivery = await DeliveryService.get_delivery(session, delivery_id)
        if not delivery:
            await callback.answer("❌ Заказ не найден", show_alert=True)
            return
        
        # Build detailed text
        text = f"📦 Заказ #{delivery.id}\n\n"
        text += f"📝 {delivery.description}\n"
        text += f"📞 {delivery.phone}\n"
        text += f"⏰ Создан: {delivery.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
        
        # Format location
        location_info = GeolocationService.format_location_for_display(
            location_type=delivery.location_type or "ADDRESS",
            address_text=delivery.address_text,
            latitude=delivery.latitude,
            longitude=delivery.longitude,
            geo_name=delivery.geo_name,
            maps_url=delivery.maps_url
        )
        text += location_info
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("delivery_take", user.language), callback_data=f"take_delivery_{delivery.id}")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="delivery_active")]
        ])
        
        # If has coordinates, send location first
        if delivery.latitude and delivery.longitude:
            try:
                await callback.message.answer_location(
                    latitude=delivery.latitude,
                    longitude=delivery.longitude
                )
            except Exception as e:
                logger.error(f"[view_delivery] ❌ Ошибка отправки локации: {str(e)}")
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        logger.info(f"[view_delivery] ✅ Пользователь {user.id} просмотрел доставку {delivery_id}")
    
    await callback.answer()


@router.callback_query(F.data.startswith("take_delivery_"))
async def take_delivery_order(callback: CallbackQuery):
    """Take delivery order (atomic update)"""
    delivery_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Atomically assign delivery
        delivery = await DeliveryService.assign_courier(session, delivery_id, user.id)
        
        if delivery:
            await callback.answer(t("delivery_taken", user.language), show_alert=True)
            
            # Notify creator
            creator_text = t("delivery_accepted", user.language if delivery.creator else "RU")
            try:
                await callback.message.bot.send_message(
                    chat_id=delivery.creator.telegram_id,
                    text=creator_text
                )
            except Exception as e:
                logger.error(f"[take_delivery] ❌ Ошибка уведомления создателя: {str(e)}")
            
            # Refresh list
            await show_active_deliveries(callback)
            logger.info(f"[take_delivery] ✅ Пользователь {user.id} взял доставку {delivery_id}")
        else:
            await callback.answer(t("delivery_already_taken", user.language), show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data == "back_delivery_menu")
async def back_to_delivery_menu(callback: CallbackQuery):
    """Back to delivery menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("delivery_menu_create", user.language), callback_data="delivery_create")],
            [InlineKeyboardButton(text=t("delivery_menu_active", user.language), callback_data="delivery_active")],
            [InlineKeyboardButton(text=t("delivery_menu_my_stats", user.language), callback_data="delivery_stats")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
        ])
        
        await callback.message.edit_text(
            t("delivery_title", user.language),
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data == "delivery_create")
async def start_delivery_creation(callback: CallbackQuery, state: FSMContext):
    """Start delivery creation (reusing existing flow)"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            t("delivery_create_desc", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.delivery_description)
    await callback.answer()


@router.callback_query(F.data == "delivery_stats")
async def show_delivery_stats(callback: CallbackQuery):
    """Show delivery statistics"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Get stats from DeliveryService
        stats = await DeliveryService.get_courier_stats(session, user.id)
        
        text = f"📊 {t('delivery_stats_title', user.language)}\n\n"
        
        if stats:
            text += f"✅ Выполнено: {stats.get('completed_deliveries', 0)}\n"
            text += f"⭐ Рейтинг: {stats.get('rating', 5.0):.1f}/5.0\n"
            text += f"📊 Статус: {stats.get('status', 'ACTIVE')}\n"
        else:
            text += t("delivery_stats_not_courier", user.language)
            text += "\n\n"
            
            # Offer to become courier
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("delivery_become_courier", user.language), callback_data="become_courier")],
                [InlineKeyboardButton(text=t("back", user.language), callback_data="back_delivery_menu")]
            ])
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer()
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("back", user.language), callback_data="back_delivery_menu")]
        ])
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data == "become_courier")
async def register_as_courier(callback: CallbackQuery):
    """Register user as courier"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        from services.courier_service import CourierService
        
        courier = await CourierService.register_courier(session, user.id)
        
        if courier:
            await callback.answer(t("delivery_courier_registered", user.language), show_alert=True)
            logger.info(f"[become_courier] ✅ Пользователь {user.id} стал курьером")
        
        # Refresh stats
        await show_delivery_stats(callback)


# ==============================================================================
# DELIVERY CREATION FLOW (EXISTING)
# ==============================================================================

@router.message(UserStates.delivery_description)
async def process_delivery_description(message: Message, state: FSMContext):
    """Process delivery description"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        await state.update_data(description=message.text)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("delivery_location_text", user.language), callback_data="delivery_loc_text")],
            [InlineKeyboardButton(text=t("delivery_location_geo", user.language), callback_data="delivery_loc_geo")],
            [InlineKeyboardButton(text=t("delivery_location_maps", user.language), callback_data="delivery_loc_maps")]
        ])
        
        await message.answer(t("delivery_location_choice", user.language), reply_markup=keyboard)
        await state.set_state(UserStates.delivery_location_type)


@router.callback_query(F.data == "delivery_loc_text")
async def delivery_location_text(callback: CallbackQuery, state: FSMContext):
    """Get text location for delivery"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            "📍 Введите адрес доставки:",
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.delivery_location_text)
    await callback.answer()


@router.message(UserStates.delivery_location_text)
async def process_delivery_location_text(message: Message, state: FSMContext):
    """Process text location for delivery"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        await state.update_data(
            location_type="ADDRESS",
            address_text=message.text
        )
        
        await message.answer(t("delivery_create_phone", user.language))
        await state.set_state(UserStates.delivery_phone)


@router.callback_query(F.data == "delivery_loc_geo")
async def delivery_location_geo(callback: CallbackQuery, state: FSMContext):
    """Get geolocation for delivery"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)],
                     [KeyboardButton(text=t("to_main_menu", user.language))]],
            resize_keyboard=True
        )
        await callback.message.answer(
            "📍 Отправьте вашу геолокацию:",
            reply_markup=keyboard
        )
        await state.set_state(UserStates.delivery_location_geo)
    await callback.answer()


@router.message(UserStates.delivery_location_geo, F.location)
async def process_delivery_location_geo(message: Message, state: FSMContext):
    """Process geolocation for delivery"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(
            location_type="GEO",
            latitude=message.location.latitude,
            longitude=message.location.longitude,
            geo_name=f"{message.location.latitude:.6f}, {message.location.longitude:.6f}"
        )
        
        await message.answer(t("delivery_create_phone", user.language))
        await state.set_state(UserStates.delivery_phone)


@router.callback_query(F.data == "delivery_loc_maps")
async def delivery_location_maps(callback: CallbackQuery, state: FSMContext):
    """Get Google Maps link for delivery"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            "🗺 Введите Google Maps ссылку:",
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.delivery_location_maps)
    await callback.answer()


@router.message(UserStates.delivery_location_maps, ~F.location)
async def process_delivery_location_maps(message: Message, state: FSMContext):
    """Process Google Maps link for delivery"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        # Parse coordinates if possible
        parsed = GeolocationService.parse_google_maps_url(message.text)
        if parsed and parsed.get("type") == "COORDINATES":
            await state.update_data(
                location_type="GEO",
                latitude=parsed["latitude"],
                longitude=parsed["longitude"],
                maps_url=message.text
            )
        else:
            await state.update_data(
                location_type="MAPS",
                maps_url=message.text
            )
        
        await message.answer(t("delivery_create_phone", user.language))
        await state.set_state(UserStates.delivery_phone)


@router.message(UserStates.delivery_phone)
async def process_delivery_phone(message: Message, state: FSMContext):
    """Process delivery phone and create order"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        # Validate phone
        if not validate_phone_number(message.text):
            await message.answer(
                f"❌ {t('invalid_input', user.language)}\n\nФормат: +998901234567"
            )
            return
        
        data = await state.get_data()
        
        try:
            # Create delivery
            delivery = await DeliveryService.create_delivery(
                session,
                creator_id=user.id,
                description=data.get("description"),
                location_type=data.get("location_type", "ADDRESS"),
                address_text=data.get("address_text"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                geo_name=data.get("geo_name"),
                maps_url=data.get("maps_url"),
                phone=message.text
            )
            
            await message.answer(
                t("delivery_created", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            
            await StatisticsService.track_activity(
                session,
                user.id,
                "DELIVERY_CREATED",
                {"delivery_id": delivery.id}
            )
            
            logger.info(f"[delivery_created] ✅ Пользователь {user.id} создал доставку {delivery.id}")
            
            # NOTIFY ALL ACTIVE COURIERS ABOUT NEW DELIVERY
            asyncio.create_task(notify_couriers_about_delivery(delivery, session))
            
        except Exception as e:
            logger.error(f"[delivery_phone] ❌ Ошибка создания доставки: {str(e)}", exc_info=True)
            await message.answer(t("error", user.language))
        
        await state.clear()


# ==============================================================================
# ADMIN MESSAGING
# ==============================================================================

@router.message(F.text.in_([t("menu_admin_contact", "RU"), t("menu_admin_contact", "UZ")]))
async def handle_admin_contact(message: Message, state: FSMContext):
    """Handle admin contact"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        await message.answer(
            t("admin_contact_prompt", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.admin_contact_message)
        logger.info(f"[admin_contact] ✅ Пользователь {user.id} начал писать админу")


@router.message(UserStates.admin_contact_message)
async def process_admin_message(message: Message, state: FSMContext):
    """Process message to admin"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        if message.text == t("to_main_menu", user.language):
            await state.clear()
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )
            return
        
        # Save message
        user_message = await UserMessageService.create_message(
            session,
            user_id=user.id,
            message_text=message.text
        )
        
        # Notify admins
        admins = await UserService.get_all_admins(session)
        for admin in admins:
            try:
                text = f"💬 НОВОЕ СООБЩЕНИЕ ОТ ПОЛЬЗОВАТЕЛЯ\n"
                text += f"═══════════════════════════════════════\n\n"
                text += f"От: {user.first_name or user.username or user.telegram_id}\n"
                text += f"ID: {user.telegram_id}\n\n"
                text += f"Сообщение:\n{message.text}"
                
                await message.bot.send_message(
                    chat_id=admin.telegram_id,
                    text=text
                )
            except Exception as e:
                logger.error(f"[admin_message] ❌ Ошибка отправки админу {admin.telegram_id}: {str(e)}")
        
        await message.answer(
            t("admin_contact_sent", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        
        await StatisticsService.track_activity(
            session,
            user.id,
            "MESSAGE_TO_ADMIN",
            {"message_id": user_message.id}
        )
        
        logger.info(f"[admin_message] ✅ Пользователь {user.id} отправил сообщение админу")
        
        await state.clear()


# ==============================================================================
# SETTINGS MENU WITH PER-ALERT PREFERENCES
# ==============================================================================

@router.message(F.text.in_([t("menu_settings", "RU"), t("menu_settings", "UZ")]))
async def handle_settings(message: Message):
    """Handle settings menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        notif_status = t("settings_notifications_on", user.language) if user.notifications_enabled else t("settings_notifications_off", user.language)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("settings_change_language", user.language), callback_data="settings_language")],
            [InlineKeyboardButton(text=f"{t('settings_notifications', user.language)}: {notif_status}", callback_data="settings_toggle_notif")],
            [InlineKeyboardButton(text=t("settings_alert_preferences", user.language), callback_data="settings_alert_prefs")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
        ])
        
        text = f"{t('settings_title', user.language)}\n\n"
        text += f"🌐 {t('settings_language', user.language)}: {user.language}\n"
        text += f"🔔 {t('settings_notifications', user.language)}: {notif_status}"
        
        await message.answer(text, reply_markup=keyboard)
        logger.info(f"[settings] ✅ Пользователь {user.id} открыл настройки")


@router.callback_query(F.data == "settings_language")
async def change_language_callback(callback: CallbackQuery):
    """Change language"""
    await callback.message.edit_text(
        t("choose_language", "RU"),
        reply_markup=get_language_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings_toggle_notif")
async def toggle_notifications_callback(callback: CallbackQuery):
    """Toggle global notifications"""
    async with AsyncSessionLocal() as session:
        user = await UserService.toggle_notifications(session, callback.from_user.id)
        
        if user:
            status_msg = t("settings_notifications_enabled", user.language) if user.notifications_enabled else t("settings_notifications_disabled", user.language)
            await callback.answer(status_msg, show_alert=True)
            
            # Refresh settings menu
            notif_status = t("settings_notifications_on", user.language) if user.notifications_enabled else t("settings_notifications_off", user.language)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("settings_change_language", user.language), callback_data="settings_language")],
                [InlineKeyboardButton(text=f"{t('settings_notifications', user.language)}: {notif_status}", callback_data="settings_toggle_notif")],
                [InlineKeyboardButton(text=t("settings_alert_preferences", user.language), callback_data="settings_alert_prefs")],
                [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
            ])
            
            text = f"{t('settings_title', user.language)}\n\n"
            text += f"🌐 {t('settings_language', user.language)}: {user.language}\n"
            text += f"🔔 {t('settings_notifications', user.language)}: {notif_status}"
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            logger.info(f"[toggle_notif] ✅ Пользователь {user.id} изменил настройки уведомлений: {user.notifications_enabled}")


@router.callback_query(F.data == "settings_alert_prefs")
async def show_alert_preferences(callback: CallbackQuery, state: FSMContext):
    """Show per-alert type preferences"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Get user preferences
        prefs = await AlertService.get_user_preferences(session, user.id)
        
        # Build keyboard with all 11 alert types
        buttons = []
        for alert_type in AlertType:
            is_enabled = prefs.get(alert_type, True)
            status_icon = t("alert_pref_enabled", user.language) if is_enabled else t("alert_pref_disabled", user.language)
            
            type_key = f"alert_type_{alert_type.value.lower()}"
            type_text = t(type_key, user.language)
            
            buttons.append([InlineKeyboardButton(
                text=f"{status_icon} {type_text}",
                callback_data=f"toggle_pref_{alert_type.value}"
            )])
        
        buttons.append([InlineKeyboardButton(text=t("back", user.language), callback_data="back_settings")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(
            t("settings_alert_prefs_title", user.language),
            reply_markup=keyboard
        )
        
        await state.set_state(UserStates.settings_alert_preferences)
        logger.info(f"[alert_prefs] ✅ Пользователь {user.id} открыл настройки типов алертов")
    
    await callback.answer()


@router.callback_query(F.data.startswith("toggle_pref_"))
async def toggle_alert_preference(callback: CallbackQuery):
    """Toggle specific alert type preference"""
    alert_type_str = callback.data.split("toggle_pref_")[1]
    alert_type = AlertType(alert_type_str)
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Get current preference
        prefs = await AlertService.get_user_preferences(session, user.id)
        current_value = prefs.get(alert_type, True)
        
        # Toggle it
        await AlertService.update_user_preference(
            session,
            user_id=user.id,
            alert_type=alert_type,
            is_enabled=not current_value
        )
        
        # Refresh preferences display
        prefs = await AlertService.get_user_preferences(session, user.id)
        
        buttons = []
        for at in AlertType:
            is_enabled = prefs.get(at, True)
            status_icon = t("alert_pref_enabled", user.language) if is_enabled else t("alert_pref_disabled", user.language)
            
            type_key = f"alert_type_{at.value.lower()}"
            type_text = t(type_key, user.language)
            
            buttons.append([InlineKeyboardButton(
                text=f"{status_icon} {type_text}",
                callback_data=f"toggle_pref_{at.value}"
            )])
        
        buttons.append([InlineKeyboardButton(text=t("back", user.language), callback_data="back_settings")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await callback.message.edit_text(
            t("settings_alert_prefs_title", user.language),
            reply_markup=keyboard
        )
        
        await StatisticsService.track_activity(
            session,
            user.id,
            "ALERT_PREF_TOGGLE",
            {"alert_type": alert_type.value, "enabled": not current_value}
        )
        
        logger.info(f"[toggle_pref] ✅ Пользователь {user.id} изменил предпочтение {alert_type.value}: {not current_value}")
    
    await callback.answer()


@router.callback_query(F.data == "back_settings")
async def back_to_settings(callback: CallbackQuery, state: FSMContext):
    """Back to settings menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        notif_status = t("settings_notifications_on", user.language) if user.notifications_enabled else t("settings_notifications_off", user.language)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("settings_change_language", user.language), callback_data="settings_language")],
            [InlineKeyboardButton(text=f"{t('settings_notifications', user.language)}: {notif_status}", callback_data="settings_toggle_notif")],
            [InlineKeyboardButton(text=t("settings_alert_preferences", user.language), callback_data="settings_alert_prefs")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
        ])
        
        text = f"{t('settings_title', user.language)}\n\n"
        text += f"🌐 {t('settings_language', user.language)}: {user.language}\n"
        text += f"🔔 {t('settings_notifications', user.language)}: {notif_status}"
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.clear()
    
    await callback.answer()


# ==============================================================================
# STATISTICS TRACKING
# ==============================================================================

# Statistics are tracked inline throughout all handlers using:
# await StatisticsService.track_activity(session, user.id, activity_type, activity_data)



# ==============================================================================
# HANDLER REGISTRATION
# ==============================================================================

def register_user_handlers(dp: Dispatcher):
    """Register all user handlers"""
    dp.include_router(router)

