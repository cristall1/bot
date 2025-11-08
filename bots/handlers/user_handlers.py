from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher
import asyncio

from database import AsyncSessionLocal
from locales import t
from states import UserStates
from services.user_service import UserService
from services.document_service import DocumentService
from services.delivery_service import DeliveryService
from services.notification_service import NotificationService
from services.shurta_service import ShurtaService
from services.user_message_service import UserMessageService
from services.statistics_service import StatisticsService
from utils.logger import logger
import asyncio
from config import settings

router = Router()


async def send_notification_to_admins_for_moderation(notification, bot):
    """
    Отправить уведомление всем администраторам для модерации
    Send notification to all admins for moderation
    """
    logger.info(f"[send_notification_to_admins_for_moderation] Начало | notification_id={notification.id}")
    try:
        # Получить всех администраторов
        async with AsyncSessionLocal() as session:
            admins = await UserService.get_all_admins(session)
            
            for admin in admins:
                try:
                    text = f"🔔 НОВОЕ УВЕДОМЛЕНИЕ НА МОДЕРАЦИЮ\n"
                    text += f"═══════════════════════════════════════\n\n"
                    text += f"Тип: {notification.type}\n"
                    text += f"Название: {notification.title}\n"
                    text += f"Описание: {notification.description}\n"
                    
                    if notification.address_text:
                        text += f"Место: {notification.address_text}\n"
                    if notification.phone:
                        text += f"Телефон: {notification.phone}\n"
                    
                    text += f"\nОт пользователя: {notification.creator_id}\n"
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_approve_notif_{notification.id}"),
                            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_notif_{notification.id}")
                        ]
                    ])
                    
                    if notification.photo_file_id:
                        await bot.send_photo(
                            chat_id=admin.telegram_id,
                            photo=notification.photo_file_id,
                            caption=text,
                            reply_markup=keyboard
                        )
                    else:
                        await bot.send_message(
                            chat_id=admin.telegram_id,
                            text=text,
                            reply_markup=keyboard
                        )
                    
                    logger.info(f"[send_notification_to_admins_for_moderation] ✅ Отправлено администратору {admin.telegram_id}")
                except Exception as e:
                    logger.error(f"[send_notification_to_admins_for_moderation] ❌ Ошибка отправки администратору {admin.telegram_id}: {str(e)}")
        
        logger.info(f"[send_notification_to_admins_for_moderation] ✅ Успешно")
    except Exception as e:
        logger.error(f"[send_notification_to_admins_for_moderation] ❌ Ошибка: {str(e)}", exc_info=True)


async def send_shurta_to_admins_for_moderation(alert, bot):
    """
    Отправить алерт Shurta всем администраторам для модерации
    Send Shurta alert to all admins for moderation
    """
    logger.info(f"[send_shurta_to_admins_for_moderation] Начало | alert_id={alert.id}")
    try:
        # Получить всех администраторов
        async with AsyncSessionLocal() as session:
            admins = await UserService.get_all_admins(session)
            
            for admin in admins:
                try:
                    text = f"🚨 НОВЫЙ АЛЕРТ SHURTA НА МОДЕРАЦИЮ\n"
                    text += f"═══════════════════════════════════════\n\n"
                    text += f"Описание: {alert.description}\n"
                    
                    if alert.address_text:
                        text += f"Место: {alert.address_text}\n"
                    elif alert.latitude and alert.longitude:
                        text += f"Координаты: {alert.latitude}, {alert.longitude}\n"
                    
                    text += f"\nОт пользователя: {alert.creator_id}\n"
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_approve_shurta_{alert.id}"),
                            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_shurta_{alert.id}")
                        ]
                    ])
                    
                    # Если есть геолокация - отправить как карту
                    if alert.latitude and alert.longitude:
                        await bot.send_location(
                            chat_id=admin.telegram_id,
                            latitude=alert.latitude,
                            longitude=alert.longitude
                        )
                    
                    if alert.photo_file_id:
                        await bot.send_photo(
                            chat_id=admin.telegram_id,
                            photo=alert.photo_file_id,
                            caption=text,
                            reply_markup=keyboard
                        )
                    else:
                        await bot.send_message(
                            chat_id=admin.telegram_id,
                            text=text,
                            reply_markup=keyboard
                        )
                    
                    logger.info(f"[send_shurta_to_admins_for_moderation] ✅ Отправлено администратору {admin.telegram_id}")
                except Exception as e:
                    logger.error(f"[send_shurta_to_admins_for_moderation] ❌ Ошибка отправки администратору {admin.telegram_id}: {str(e)}")
        
        logger.info(f"[send_shurta_to_admins_for_moderation] ✅ Успешно")
    except Exception as e:
        logger.error(f"[send_shurta_to_admins_for_moderation] ❌ Ошибка: {str(e)}", exc_info=True)


def get_language_keyboard():
    """Get language selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_RU"),
            InlineKeyboardButton(text="🇺🇿 Oʻzbekcha", callback_data="lang_UZ")
        ]
    ])
    return keyboard


def get_main_menu_keyboard(lang: str):
    """Get main menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("menu_documents", lang))],
            [KeyboardButton(text=t("menu_delivery", lang))],
            [KeyboardButton(text=t("menu_notifications", lang))],
            [KeyboardButton(text=t("menu_shurta", lang))],
            [KeyboardButton(text=t("menu_admin_contact", lang))],
            [KeyboardButton(text=t("menu_settings", lang))]
        ],
        resize_keyboard=True
    )
    return keyboard


def get_citizenship_keyboard(lang: str):
    """Get citizenship selection keyboard"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("citizenship_uz", lang), callback_data="cit_UZ")],
        [InlineKeyboardButton(text=t("citizenship_ru", lang), callback_data="cit_RU")],
        [InlineKeyboardButton(text=t("citizenship_kz", lang), callback_data="cit_KZ")],
        [InlineKeyboardButton(text=t("citizenship_kg", lang), callback_data="cit_KG")],
        [InlineKeyboardButton(text=t("back", lang), callback_data="back_main")]
    ])
    return keyboard


def get_back_keyboard(lang: str):
    """Get back button keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("to_main_menu", lang))]],
        resize_keyboard=True
    )
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        
        if not user:
            await message.answer(
                t("welcome", "RU"),
                reply_markup=get_language_keyboard()
            )
            await state.set_state(UserStates.selecting_language)
        else:
            if user.is_banned:
                await message.answer(t("banned", user.language))
                return
            
            await message.answer(
                t("main_menu", user.language),
                reply_markup=get_main_menu_keyboard(user.language)
            )


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Process language selection"""
    lang = callback.data.split("_")[1]
    
    async with AsyncSessionLocal() as session:
        user = await UserService.create_or_update_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            language=lang
        )
    
    await callback.message.edit_text(t("language_selected", lang))
    await callback.message.answer(
        t("main_menu", lang),
        reply_markup=get_main_menu_keyboard(lang)
    )
    await state.clear()
    await callback.answer()


@router.message(F.text.in_([t("menu_documents", "RU"), t("menu_documents", "UZ")]))
async def handle_documents(message: Message):
    """Handle documents menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        await message.answer(
            t("documents_title", user.language),
            reply_markup=get_citizenship_keyboard(user.language)
        )


@router.callback_query(F.data.startswith("cit_"))
async def process_citizenship_selection(callback: CallbackQuery):
    """Process citizenship selection for documents"""
    citizenship = callback.data.split("_")[1]
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        documents = await DocumentService.get_documents_by_citizenship(session, citizenship)
        
        if not documents:
            await callback.message.edit_text(
                t("no_documents", user.language),
                reply_markup=get_citizenship_keyboard(user.language)
            )
        else:
            buttons = []
            for doc in documents:
                title = doc.name_ru if user.language == "RU" else doc.name_uz
                buttons.append([InlineKeyboardButton(
                    text=title,
                    callback_data=f"doc_{doc.id}"
                )])
            buttons.append([InlineKeyboardButton(text=t("back", user.language), callback_data="back_cit")])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            await callback.message.edit_text(
                t("select_citizenship", user.language),
                reply_markup=keyboard
            )
    
    await callback.answer()


@router.callback_query(F.data.startswith("doc_"))
async def show_document(callback: CallbackQuery):
    """Show document content"""
    doc_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        document = await DocumentService.get_document(session, doc_id)
        if not document:
            return
        
        content = document.content_ru if user.language == "RU" else document.content_uz
        title = document.name_ru if user.language == "RU" else document.name_uz
        
        # Get buttons for this document
        doc_buttons = await DocumentService.get_document_buttons(session, doc_id)
        
        keyboard_buttons = []
        for btn in doc_buttons:
            btn_text = btn.text_ru if user.language == "RU" else btn.text_uz
            if btn.button_type == "LINK":
                keyboard_buttons.append([InlineKeyboardButton(text=btn_text, url=btn.button_value)])
            elif btn.button_type in ["PHOTO", "PDF", "AUDIO"]:
                keyboard_buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"doc_file_{btn.id}")])
            elif btn.button_type == "GEO":
                keyboard_buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"doc_geo_{btn.id}")])
        
        keyboard_buttons.append([InlineKeyboardButton(text=t("back", user.language), callback_data=f"cit_{document.citizenship_scope}")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        # Send photo if available
        if document.photo_file_id:
            await callback.message.answer_photo(
                photo=document.photo_file_id,
                caption=f"{title}\n\n{content}",
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(
                f"{title}\n\n{content}",
                reply_markup=keyboard
            )
    
    await callback.answer()


@router.callback_query(F.data == "back_cit")
async def back_to_citizenship(callback: CallbackQuery):
    """Back to citizenship selection"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.edit_text(
            t("documents_title", user.language),
            reply_markup=get_citizenship_keyboard(user.language)
        )
    await callback.answer()


@router.callback_query(F.data == "back_main")
async def back_to_main(callback: CallbackQuery):
    """Back to main menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            t("main_menu", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
    await callback.answer()


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


@router.callback_query(F.data == "delivery_active")
async def show_active_deliveries(callback: CallbackQuery):
    """Show active delivery orders"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Get all active deliveries (not assigned to anyone or assigned to others)
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
                btn_text = f"📦 {delivery.description[:20]}..."
                buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"view_delivery_{delivery.id}")])
            
            buttons.append([InlineKeyboardButton(text=t("back", user.language), callback_data="back_delivery_menu")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
            
            await callback.message.edit_text(
                f"{t('delivery_menu_active', user.language)}\n\n({len(deliveries)} активных)",
                reply_markup=keyboard
            )
    
    await callback.answer()


@router.callback_query(F.data.startswith("view_delivery_"))
async def view_delivery_order(callback: CallbackQuery):
    """View specific delivery order"""
    delivery_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        delivery = await DeliveryService.get_delivery(session, delivery_id)
        if not delivery:
            await callback.answer("Заказ не найден")
            return
        
        text = f"📦 Заказ #{delivery.id}\n\n"
        text += f"📝 {delivery.description}\n"
        location_display = delivery.address_text or f"{delivery.latitude},{delivery.longitude}" if delivery.latitude and delivery.longitude else delivery.maps_url or "не указано"
        text += f"📍 {location_display}\n"
        text += f"📞 {delivery.phone}\n"
        text += f"⏰ {delivery.created_at}\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("delivery_take", user.language), callback_data=f"take_delivery_{delivery.id}")],
            [InlineKeyboardButton(text=t("delivery_reject", user.language), callback_data=f"reject_delivery_{delivery.id}")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="delivery_active")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
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
    """Start delivery creation"""
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
        
        # Show location choice options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("delivery_location_text", user.language), callback_data="delivery_loc_text")],
            [InlineKeyboardButton(text=t("delivery_location_geo", user.language), callback_data="delivery_loc_geo")],
            [InlineKeyboardButton(text=t("delivery_location_maps", user.language), callback_data="delivery_loc_maps")]
        ])
        
        await message.answer(t("delivery_location_choice", user.language), reply_markup=keyboard)
        await state.set_state(UserStates.delivery_location_type)


@router.callback_query(F.data == "delivery_loc_text")
async def delivery_location_text(callback: CallbackQuery, state: FSMContext):
    """Get text location"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            "📍 Введите адрес (район/улица):",
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.delivery_location_text)
    await callback.answer()


@router.message(UserStates.delivery_location_text)
async def process_delivery_location_text(message: Message, state: FSMContext):
    """Process text location"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text, location_type="text")
        await message.answer(t("delivery_create_phone", user.language))
        await state.set_state(UserStates.delivery_phone)


@router.callback_query(F.data == "delivery_loc_geo")
async def delivery_location_geo(callback: CallbackQuery, state: FSMContext):
    """Get geolocation"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)]],
            resize_keyboard=True
        )
        await callback.message.answer("Отправьте вашу геолокацию:", reply_markup=keyboard)
        await state.set_state(UserStates.delivery_location_maps)
    await callback.answer()


@router.message(UserStates.delivery_location_maps, F.location)
async def process_delivery_location_geo(message: Message, state: FSMContext):
    """Process geolocation"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        location_str = f"{message.location.latitude},{message.location.longitude}"
        await state.update_data(location=location_str, location_type="geo")
        await message.answer(t("delivery_create_phone", user.language))
        await state.set_state(UserStates.delivery_phone)


@router.callback_query(F.data == "delivery_loc_maps")
async def delivery_location_maps(callback: CallbackQuery, state: FSMContext):
    """Get Google Maps link"""
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
    """Process Google Maps link"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text, location_type="maps")
        await message.answer(t("delivery_create_phone", user.language))
        await state.set_state(UserStates.delivery_phone)


@router.message(UserStates.delivery_location)
async def process_delivery_location(message: Message, state: FSMContext):
    """Process delivery location (deprecated, kept for compatibility)"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text)
        await message.answer(t("delivery_create_phone", user.language))
        await state.set_state(UserStates.delivery_phone)


@router.message(UserStates.delivery_phone)
async def process_delivery_phone(message: Message, state: FSMContext):
    """Process delivery phone and create order"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        data = await state.get_data()

        location_type = data.get("location_type", "ADDRESS")
        address_text = None
        latitude = None
        longitude = None
        maps_url = None

        if location_type == "geo" and data.get("location"):
            parts = data["location"].split(",")
            if len(parts) == 2:
                try:
                    latitude = float(parts[0])
                    longitude = float(parts[1])
                except ValueError:
                    address_text = data["location"]
        elif location_type == "maps":
            maps_url = data.get("location")
        else:
            address_text = data.get("location")

        delivery = await DeliveryService.create_delivery(
            session,
            creator_id=user.id,
            description=data["description"],
            location_type=location_type if location_type in ["ADDRESS", "GEO", "MAPS"] else "ADDRESS",
            address_text=address_text,
            latitude=latitude,
            longitude=longitude,
            maps_url=maps_url,
            phone=message.text
        )
        
        # Notify all active couriers
        couriers = await DeliveryService.get_all_couriers(session)
        for courier in couriers:
            courier_user = await UserService.get_user_by_id(session, courier.user_id)
            if courier_user and courier_user.notifications_enabled:
                try:
                    # Get bot instance to send message
                    from bots.user_bot import UserBot
                    bot = message.bot
                    
                    alert_text = t("delivery_alert_new", courier_user.language,
                                 description=data["description"],
                                 location=data["location"],
                                 phone=message.text)
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=t("delivery_take", courier_user.language), callback_data=f"take_delivery_{delivery.id}")],
                        [InlineKeyboardButton(text=t("delivery_reject", courier_user.language), callback_data=f"reject_delivery_{delivery.id}")]
                    ])
                    
                    await bot.send_message(
                        courier_user.telegram_id,
                        alert_text,
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"Failed to notify courier {courier_user.telegram_id}: {e}")
        
        await message.answer(
            t("delivery_created", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.clear()


@router.callback_query(F.data.startswith("take_delivery_"))
async def take_delivery(callback: CallbackQuery):
    """Courier takes delivery"""
    delivery_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        # Assign delivery
        delivery = await DeliveryService.assign_courier(session, delivery_id, user.id)
        
        if not delivery:
            await callback.answer(t("delivery_already_taken", user.language), show_alert=True)
            return
        
        # Notify creator with courier contact info
        creator = await UserService.get_user_by_id(session, delivery.creator_id)
        if creator:
            try:
                msg_text = t("delivery_accepted", creator.language)
                msg_text += f"\n\n👤 Курьер: @{user.username or user.first_name}"
                msg_text += f"\n📞 Телефон: {user.phone if user.phone else 'Не указан'}"
                
                await callback.bot.send_message(creator.telegram_id, msg_text)
            except Exception as e:
                logger.error(f"Failed to notify creator: {e}")
        
        await callback.message.edit_text(t("delivery_taken", user.language))
    
    await callback.answer()


@router.callback_query(F.data.startswith("reject_delivery_"))
async def reject_delivery(callback: CallbackQuery):
    """Courier rejects delivery"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.edit_text(t("delivery_rejected", user.language))
    
    await callback.answer()


@router.callback_query(F.data == "delivery_stats")
async def show_delivery_stats(callback: CallbackQuery):
    """Show courier statistics"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        if not user.is_courier:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("delivery_become_courier", user.language), callback_data="become_courier")]
            ])
            await callback.message.answer(
                t("delivery_stats_not_courier", user.language),
                reply_markup=keyboard
            )
        else:
            stats = await DeliveryService.get_courier_stats(session, user.id)
            if stats:
                text = f"{t('delivery_stats_title', user.language)}\n\n"
                text += t("delivery_stats_completed", user.language, count=stats["completed_deliveries"]) + "\n"
                text += t("delivery_stats_rating", user.language, rating=stats["rating"])
                
                await callback.message.answer(text)
    
    await callback.answer()


@router.callback_query(F.data == "become_courier")
async def become_courier(callback: CallbackQuery):
    """User becomes courier"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await DeliveryService.make_courier(session, user.id)
        await callback.message.answer(t("delivery_courier_registered", user.language))
    
    await callback.answer()


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
        
        await UserMessageService.create_message(session, user.id, message.text)
        await message.answer(
            t("admin_contact_sent", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.clear()


@router.message(F.text.in_([t("menu_settings", "RU"), t("menu_settings", "UZ")]))
async def handle_settings(message: Message):
    """Handle settings menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        notif_status = t("settings_notifications_on", user.language) if user.notifications_enabled else t("settings_notifications_off", user.language)
        
        text = f"{t('settings_title', user.language)}\n\n"
        text += f"{t('settings_language', user.language)}: {'Русский' if user.language == 'RU' else 'Oʻzbekcha'}\n"
        text += f"{t('settings_notifications', user.language)}: {notif_status}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("settings_change_language", user.language), callback_data="settings_lang")],
            [InlineKeyboardButton(text=t("settings_toggle_notifications", user.language), callback_data="settings_notif")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
        ])
        
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "settings_lang")
async def change_language(callback: CallbackQuery):
    """Change language setting"""
    await callback.message.answer(
        t("choose_language", "RU"),
        reply_markup=get_language_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "settings_notif")
async def toggle_notifications(callback: CallbackQuery):
    """Toggle notifications"""
    async with AsyncSessionLocal() as session:
        user = await UserService.toggle_notifications(session, callback.from_user.id)
        if not user:
            return
        
        if user.notifications_enabled:
            await callback.message.answer(t("settings_notifications_enabled", user.language))
        else:
            await callback.message.answer(t("settings_notifications_disabled", user.language))
    
    await callback.answer()


@router.message(F.text.in_([t("menu_notifications", "RU"), t("menu_notifications", "UZ")]))
async def handle_notifications(message: Message):
    """Handle notifications menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("notifications_menu_lost_person", user.language), callback_data="notif_person")],
            [InlineKeyboardButton(text=t("notifications_menu_lost_item", user.language), callback_data="notif_item")],
            [InlineKeyboardButton(text=t("back", user.language), callback_data="back_main")]
        ])
        
        await message.answer(
            t("notifications_title", user.language),
            reply_markup=keyboard
        )


@router.callback_query(F.data == "notif_person")
async def start_lost_person(callback: CallbackQuery, state: FSMContext):
    """Start lost person notification"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            t("notifications_lost_person_name", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.notification_person_name)
    await callback.answer()


@router.message(UserStates.notification_person_name)
async def process_lost_person_name(message: Message, state: FSMContext):
    """Process lost person name"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(name=message.text)
        await message.answer(t("notifications_lost_person_desc", user.language))
        await state.set_state(UserStates.notification_person_desc)


@router.message(UserStates.notification_person_desc)
async def process_lost_person_desc(message: Message, state: FSMContext):
    """Process lost person description"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(description=message.text)
        
        skip_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=t("notifications_skip_photo", user.language))]],
            resize_keyboard=True
        )
        await message.answer(t("notifications_lost_person_photo", user.language), reply_markup=skip_keyboard)
        await state.set_state(UserStates.notification_person_photo)


@router.message(UserStates.notification_person_photo)
async def process_lost_person_photo(message: Message, state: FSMContext):
    """Process lost person photo"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        photo_file_id = None
        if message.photo:
            photo_file_id = message.photo[-1].file_id
        elif message.text != t("notifications_skip_photo", user.language):
            photo_file_id = None
        
        await state.update_data(photo_file_id=photo_file_id)
        
        # Show location choice options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("notifications_location_text", user.language), callback_data="notif_person_loc_text")],
            [InlineKeyboardButton(text=t("notifications_location_geo", user.language), callback_data="notif_person_loc_geo")],
            [InlineKeyboardButton(text=t("notifications_location_maps", user.language), callback_data="notif_person_loc_maps")]
        ])
        
        await message.answer(t("notifications_location_choice", user.language), reply_markup=keyboard)
        await state.set_state(UserStates.notification_person_location_choice)


@router.callback_query(F.data == "notif_person_loc_text")
async def notif_person_location_text(callback: CallbackQuery, state: FSMContext):
    """Get text location for lost person"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            "📍 Введите адрес (район/улица):",
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.notification_person_location_text)
    await callback.answer()


@router.message(UserStates.notification_person_location_text)
async def process_notif_person_location_text(message: Message, state: FSMContext):
    """Process text location for lost person"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text, location_type="text")
        await message.answer(t("notifications_lost_person_phone", user.language))
        await state.set_state(UserStates.notification_person_phone)


@router.callback_query(F.data == "notif_person_loc_geo")
async def notif_person_location_geo(callback: CallbackQuery, state: FSMContext):
    """Get geolocation for lost person"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)]],
            resize_keyboard=True
        )
        await callback.message.answer("Отправьте геолокацию:", reply_markup=keyboard)
        await state.set_state(UserStates.notification_person_location_maps)
    await callback.answer()


@router.message(UserStates.notification_person_location_maps, F.location)
async def process_notif_person_location_geo(message: Message, state: FSMContext):
    """Process geolocation for lost person"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        location_str = f"{message.location.latitude},{message.location.longitude}"
        await state.update_data(location=location_str, location_type="geo")
        await message.answer(t("notifications_lost_person_phone", user.language))
        await state.set_state(UserStates.notification_person_phone)


@router.callback_query(F.data == "notif_person_loc_maps")
async def notif_person_location_maps(callback: CallbackQuery, state: FSMContext):
    """Get Google Maps link for lost person"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            "🗺 Введите Google Maps ссылку:",
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.notification_person_location_maps)
    await callback.answer()


@router.message(UserStates.notification_person_location_maps, ~F.location)
async def process_notif_person_location_maps(message: Message, state: FSMContext):
    """Process Google Maps link for lost person"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text, location_type="maps")
        await message.answer(t("notifications_lost_person_phone", user.language))
        await state.set_state(UserStates.notification_person_phone)


@router.message(UserStates.notification_person_location)
async def process_lost_person_location(message: Message, state: FSMContext):
    """Process lost person location (deprecated, kept for compatibility)"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text)
        await message.answer(t("notifications_lost_person_phone", user.language))
        await state.set_state(UserStates.notification_person_phone)


@router.message(UserStates.notification_person_phone)
async def process_lost_person_phone(message: Message, state: FSMContext):
    """Process lost person phone and create notification"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        data = await state.get_data()
        
        location_type = data.get("location_type", "ADDRESS")
        address_text = None
        latitude = None
        longitude = None
        maps_url = None
        
        if location_type == "geo" and data.get("location"):
            parts = data["location"].split(",")
            if len(parts) == 2:
                try:
                    latitude = float(parts[0])
                    longitude = float(parts[1])
                except ValueError:
                    address_text = data["location"]
        elif location_type == "maps":
            maps_url = data.get("location")
        else:
            address_text = data.get("location")
        
        try:
            logger.info(f"Пользователь {user.id} создает уведомление о потере человека")
            
    logger.info(f"[process_lost_person_phone] Начало | user_id={message.from_user.id}")
    try:
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, message.from_user.id)
            if not user:
                logger.warning(f"[process_lost_person_phone] Пользователь не найден")
                return
            
            data = await state.get_data()
            
            location_type = data.get("location_type", "ADDRESS")
            address_text = None
            latitude = None
            longitude = None
            maps_url = None
            
            if location_type == "geo" and data.get("location"):
                parts = data["location"].split(",")
                if len(parts) == 2:
                    try:
                        latitude = float(parts[0])
                        longitude = float(parts[1])
                    except ValueError:
                        address_text = data["location"]
            elif location_type == "maps":
                maps_url = data.get("location")
            else:
                address_text = data.get("location")
            
            # Создать уведомление с is_approved=False (требует модерации)
            notification = await NotificationService.create_notification(
                session,
                notification_type="PROPAJA_ODAM",
                creator_id=user.id,
                title=data["name"],
                description=data["description"],
                location_type=location_type if location_type in ["ADDRESS", "GEO", "MAPS"] else "ADDRESS",
                address_text=address_text,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                phone=message.text,
                photo_file_id=data.get("photo_file_id")
            )
            
            # Отправить сообщение пользователю о том, что заявка на модерации
            success_msg = await message.answer(
                "✅ Объявление отправлено на модерацию",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            
            # Записать активность для статистики
            await StatisticsService.track_activity(
                session,
                user.id,
                "NOTIFICATION_CREATED",
                {"type": "PROPAJA_ODAM", "notification_id": notification.id}
            )
            
            logger.info(f"Уведомление {notification.id} создано и отправлено на модерацию")
            
            # Удалить сообщение через 10 секунд
            await asyncio.sleep(10)
            try:
                await success_msg.delete()
            except Exception as e:
                logger.error(f"Не удалось удалить сообщение: {str(e)}")
            
            await state.clear()
        except Exception as e:
            logger.error(f"Ошибка при создании уведомления: {str(e)}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка при создании объявления. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            await state.clear()
            # Отправить уведомление администраторам для модерации
            await send_notification_to_admins_for_moderation(notification, message.bot)
            
            # Отправить подтверждение пользователю
            confirm_msg = await message.answer(
                "✅ Объявление отправлено на модерацию\n⏳ Сообщение удалится через 10 секунд",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            
            # Авто-удаление через 10 секунд
            await asyncio.sleep(10)
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=confirm_msg.message_id
                )
                logger.info(f"[process_lost_person_phone] ✅ Сообщение удалено через 10 секунд")
            except Exception as e:
                logger.warning(f"[process_lost_person_phone] Не удалось удалить сообщение: {str(e)}")
            
            await state.clear()
            logger.info(f"[process_lost_person_phone] ✅ Успешно создано уведомление")
    except Exception as e:
        logger.error(f"[process_lost_person_phone] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при создании объявления. Попробуйте позже.")


@router.callback_query(F.data == "notif_item")
async def start_lost_item(callback: CallbackQuery, state: FSMContext):
    """Start lost item notification"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            t("notifications_lost_item_what", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.notification_item_what)
    await callback.answer()


@router.message(UserStates.notification_item_what)
async def process_lost_item_what(message: Message, state: FSMContext):
    """Process lost item what"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(what=message.text)
        await message.answer(t("notifications_lost_item_desc", user.language))
        await state.set_state(UserStates.notification_item_desc)


@router.message(UserStates.notification_item_desc)
async def process_lost_item_desc(message: Message, state: FSMContext):
    """Process lost item description"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(description=message.text)
        
        skip_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=t("notifications_skip_photo", user.language))]],
            resize_keyboard=True
        )
        await message.answer(t("notifications_lost_item_photo", user.language), reply_markup=skip_keyboard)
        await state.set_state(UserStates.notification_item_photo)


@router.message(UserStates.notification_item_photo)
async def process_lost_item_photo(message: Message, state: FSMContext):
    """Process lost item photo"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        photo_file_id = None
        if message.photo:
            photo_file_id = message.photo[-1].file_id
        elif message.text != t("notifications_skip_photo", user.language):
            photo_file_id = None
        
        await state.update_data(photo_file_id=photo_file_id)
        
        # Show location choice options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("notifications_location_text", user.language), callback_data="notif_item_loc_text")],
            [InlineKeyboardButton(text=t("notifications_location_geo", user.language), callback_data="notif_item_loc_geo")],
            [InlineKeyboardButton(text=t("notifications_location_maps", user.language), callback_data="notif_item_loc_maps")]
        ])
        
        await message.answer(t("notifications_location_choice", user.language), reply_markup=keyboard)
        await state.set_state(UserStates.notification_item_location_choice)


@router.callback_query(F.data == "notif_item_loc_text")
async def notif_item_location_text(callback: CallbackQuery, state: FSMContext):
    """Get text location for lost item"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            "📍 Введите адрес (район/улица):",
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.notification_item_location_text)
    await callback.answer()


@router.message(UserStates.notification_item_location_text)
async def process_notif_item_location_text(message: Message, state: FSMContext):
    """Process text location for lost item"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text, location_type="text")
        await message.answer(t("notifications_lost_item_phone", user.language))
        await state.set_state(UserStates.notification_item_phone)


@router.callback_query(F.data == "notif_item_loc_geo")
async def notif_item_location_geo(callback: CallbackQuery, state: FSMContext):
    """Get geolocation for lost item"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📍 Отправить локацию", request_location=True)]],
            resize_keyboard=True
        )
        await callback.message.answer("Отправьте геолокацию:", reply_markup=keyboard)
        await state.set_state(UserStates.notification_item_location_maps)
    await callback.answer()


@router.message(UserStates.notification_item_location_maps, F.location)
async def process_notif_item_location_geo(message: Message, state: FSMContext):
    """Process geolocation for lost item"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        location_str = f"{message.location.latitude},{message.location.longitude}"
        await state.update_data(location=location_str, location_type="geo")
        await message.answer(t("notifications_lost_item_phone", user.language))
        await state.set_state(UserStates.notification_item_phone)


@router.callback_query(F.data == "notif_item_loc_maps")
async def notif_item_location_maps(callback: CallbackQuery, state: FSMContext):
    """Get Google Maps link for lost item"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(
            "🗺 Введите Google Maps ссылку:",
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.notification_item_location_maps)
    await callback.answer()


@router.message(UserStates.notification_item_location_maps, ~F.location)
async def process_notif_item_location_maps(message: Message, state: FSMContext):
    """Process Google Maps link for lost item"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text, location_type="maps")
        await message.answer(t("notifications_lost_item_phone", user.language))
        await state.set_state(UserStates.notification_item_phone)


@router.message(UserStates.notification_item_location)
async def process_lost_item_location(message: Message, state: FSMContext):
    """Process lost item location (deprecated, kept for compatibility)"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location=message.text)
        await message.answer(t("notifications_lost_item_phone", user.language))
        await state.set_state(UserStates.notification_item_phone)


@router.message(UserStates.notification_item_phone)
async def process_lost_item_phone(message: Message, state: FSMContext):
    """Process lost item phone and create notification"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        data = await state.get_data()
        
        location_type = data.get("location_type", "ADDRESS")
        address_text = None
        latitude = None
        longitude = None
        maps_url = None
        
        if location_type == "geo" and data.get("location"):
            parts = data["location"].split(",")
            if len(parts) == 2:
                try:
                    latitude = float(parts[0])
                    longitude = float(parts[1])
                except ValueError:
                    address_text = data["location"]
        elif location_type == "maps":
            maps_url = data.get("location")
        else:
            address_text = data.get("location")
        
        try:
            logger.info(f"Пользователь {user.id} создает уведомление о потере вещи")
            
    logger.info(f"[process_lost_item_phone] Начало | user_id={message.from_user.id}")
    try:
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, message.from_user.id)
            if not user:
                logger.warning(f"[process_lost_item_phone] Пользователь не найден")
                return
            
            data = await state.get_data()
            
            location_type = data.get("location_type", "ADDRESS")
            address_text = None
            latitude = None
            longitude = None
            maps_url = None
            
            if location_type == "geo" and data.get("location"):
                parts = data["location"].split(",")
                if len(parts) == 2:
                    try:
                        latitude = float(parts[0])
                        longitude = float(parts[1])
                    except ValueError:
                        address_text = data["location"]
            elif location_type == "maps":
                maps_url = data.get("location")
            else:
                address_text = data.get("location")
            
            # Создать уведомление с is_approved=False (требует модерации)
            notification = await NotificationService.create_notification(
                session,
                notification_type="PROPAJA_NARSA",
                creator_id=user.id,
                title=data["what"],
                description=data["description"],
                location_type=location_type if location_type in ["ADDRESS", "GEO", "MAPS"] else "ADDRESS",
                address_text=address_text,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                phone=message.text,
                photo_file_id=data.get("photo_file_id")
            )
            
            # Отправить сообщение пользователю о том, что заявка на модерации
            success_msg = await message.answer(
                "✅ Объявление отправлено на модерацию",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            
            # Записать активность для статистики
            await StatisticsService.track_activity(
                session,
                user.id,
                "NOTIFICATION_CREATED",
                {"type": "PROPAJA_NARSA", "notification_id": notification.id}
            )
            
            logger.info(f"Уведомление {notification.id} создано и отправлено на модерацию")
            
            # Удалить сообщение через 10 секунд
            await asyncio.sleep(10)
            try:
                await success_msg.delete()
            except Exception as e:
                logger.error(f"Не удалось удалить сообщение: {str(e)}")
            
            await state.clear()
        except Exception as e:
            logger.error(f"Ошибка при создании уведомления: {str(e)}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка при создании объявления. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            await state.clear()
            # Отправить уведомление администраторам для модерации
            await send_notification_to_admins_for_moderation(notification, message.bot)
            
            # Подтверждение пользователю с автоудалением
            confirm_msg = await message.answer(
                "✅ Объявление отправлено на модерацию\n⏳ Сообщение удалится через 10 секунд",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            
            await asyncio.sleep(10)
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=confirm_msg.message_id
                )
                logger.info(f"[process_lost_item_phone] ✅ Сообщение удалено через 10 секунд")
            except Exception as e:
                logger.warning(f"[process_lost_item_phone] Не удалось удалить сообщение: {str(e)}")
            
            await state.clear()
            logger.info(f"[process_lost_item_phone] ✅ Успешно создано уведомление")
    except Exception as e:
        logger.error(f"[process_lost_item_phone] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при создании объявления. Попробуйте позже.")


@router.message(F.text.in_([t("menu_shurta", "RU"), t("menu_shurta", "UZ")]))
async def handle_shurta(message: Message, state: FSMContext):
    """Handle shurta (police) alerts"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        await message.answer(
            t("shurta_description", user.language),
            reply_markup=get_back_keyboard(user.language)
        )
        await state.set_state(UserStates.shurta_description)


@router.message(UserStates.shurta_description)
async def process_shurta_description(message: Message, state: FSMContext):
    """Process shurta description"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(description=message.text)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("shurta_location_maps", user.language), callback_data="shurta_maps")],
            [InlineKeyboardButton(text=t("shurta_location_geo", user.language), callback_data="shurta_geo")],
            [InlineKeyboardButton(text=t("shurta_location_text", user.language), callback_data="shurta_text")]
        ])
        
        await message.answer(
            t("shurta_location_choice", user.language),
            reply_markup=keyboard
        )
        await state.set_state(UserStates.shurta_location_type)


@router.callback_query(F.data == "shurta_text")
async def shurta_text_location(callback: CallbackQuery, state: FSMContext):
    """Text address for shurta"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(t("shurta_location_input", user.language))
        await state.set_state(UserStates.shurta_location_text)
    await callback.answer()


@router.message(UserStates.shurta_location_text)
async def process_shurta_location_text(message: Message, state: FSMContext):
    """Process shurta text location"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location_info=message.text)
        
        skip_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=t("notifications_skip_photo", user.language))]],
            resize_keyboard=True
        )
        await message.answer(t("shurta_photo", user.language), reply_markup=skip_keyboard)
        await state.set_state(UserStates.shurta_photo)


@router.callback_query(F.data == "shurta_geo")
async def shurta_geo_location(callback: CallbackQuery, state: FSMContext):
    """Geolocation for shurta"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(t("shurta_location_geo_input", user.language))
        await state.set_state(UserStates.shurta_location_geo)
    await callback.answer()


@router.message(UserStates.shurta_location_geo, F.location)
async def process_shurta_location_geo(message: Message, state: FSMContext):
    """Process shurta geolocation"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        location_str = f"{message.location.latitude},{message.location.longitude}"
        await state.update_data(location_info=location_str, location_type="geo")
        
        skip_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=t("notifications_skip_photo", user.language))]],
            resize_keyboard=True
        )
        await message.answer(t("shurta_photo", user.language), reply_markup=skip_keyboard)
        await state.set_state(UserStates.shurta_photo)


@router.callback_query(F.data == "shurta_maps")
async def shurta_maps_location(callback: CallbackQuery, state: FSMContext):
    """Google Maps link for shurta"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user:
            return
        
        await callback.message.answer(t("shurta_location_maps_input", user.language))
        await state.set_state(UserStates.shurta_location_maps)
    await callback.answer()


@router.message(UserStates.shurta_location_maps, ~F.location)
async def process_shurta_location_maps(message: Message, state: FSMContext):
    """Process shurta Google Maps link"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        await state.update_data(location_info=message.text, location_type="maps")
        
        skip_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=t("notifications_skip_photo", user.language))]],
            resize_keyboard=True
        )
        await message.answer(t("shurta_photo", user.language), reply_markup=skip_keyboard)
        await state.set_state(UserStates.shurta_photo)


@router.message(UserStates.shurta_photo)
async def process_shurta_photo(message: Message, state: FSMContext):
    """Process shurta photo and create alert"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user:
            return
        
        photo_file_id = None
        if message.photo:
            photo_file_id = message.photo[-1].file_id
        
        data = await state.get_data()
        
        location_type = data.get("location_type", "ADDRESS")
        address_text = None
        latitude = None
        longitude = None
        maps_url = None
        
        if location_type == "geo" and data.get("location_info"):
            parts = data["location_info"].split(",")
            if len(parts) == 2:
                try:
                    latitude = float(parts[0])
                    longitude = float(parts[1])
                except ValueError:
                    address_text = data["location_info"]
        elif location_type == "maps":
            maps_url = data.get("location_info")
        else:
            address_text = data.get("location_info")
        
        try:
            logger.info(f"Пользователь {user.id} создает Shurta-уведомление")
            
    logger.info(f"[process_shurta_photo] Начало | user_id={message.from_user.id}")
    try:
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, message.from_user.id)
            if not user:
                logger.warning(f"[process_shurta_photo] Пользователь не найден")
                return
            
            photo_file_id = None
            if message.photo:
                photo_file_id = message.photo[-1].file_id
            
            data = await state.get_data()
            
            location_type = data.get("location_type", "ADDRESS")
            address_text = None
            latitude = None
            longitude = None
            maps_url = None
            
            if location_type == "geo" and data.get("location_info"):
                parts = data["location_info"].split(",")
                if len(parts) == 2:
                    try:
                        latitude = float(parts[0])
                        longitude = float(parts[1])
                    except ValueError:
                        address_text = data["location_info"]
            elif location_type == "maps":
                maps_url = data.get("location_info")
            else:
                address_text = data.get("location_info")
            
            # Создать алерт с is_approved=False (требует модерации)
            alert = await ShurtaService.create_alert(
                session,
                creator_id=user.id,
                description=data["description"],
                location_type=location_type if location_type in ["ADDRESS", "GEO", "MAPS"] else "ADDRESS",
                address_text=address_text,
                latitude=latitude,
                longitude=longitude,
                maps_url=maps_url,
                photo_file_id=photo_file_id
            )
            
            success_msg = await message.answer(
                "✅ Объявление отправлено на модерацию",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            
            await StatisticsService.track_activity(
                session,
                user.id,
                "SHURTA_CREATED",
                {"alert_id": alert.id}
            )
            
            logger.info(f"Shurta {alert.id} создан и отправлен на модерацию")
            
            await asyncio.sleep(10)
            try:
                await success_msg.delete()
            except Exception as e:
                logger.error(f"Не удалось удалить сообщение: {str(e)}")
            
            await state.clear()
        except Exception as e:
            logger.error(f"Ошибка при создании Shurta: {str(e)}", exc_info=True)
            await message.answer(
                "❌ Произошла ошибка при создании объявления. Попробуйте позже.",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            await state.clear()
            # Отправить алерт администраторам для модерации
            await send_shurta_to_admins_for_moderation(alert, message.bot)
            
            # Подтверждение пользователю с автоудалением
            confirm_msg = await message.answer(
                "✅ Алерт отправлен на модерацию\n⏳ Сообщение удалится через 10 секунд",
                reply_markup=get_main_menu_keyboard(user.language)
            )
            
            await asyncio.sleep(10)
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=confirm_msg.message_id
                )
                logger.info(f"[process_shurta_photo] ✅ Сообщение удалено через 10 секунд")
            except Exception as e:
                logger.warning(f"[process_shurta_photo] Не удалось удалить сообщение: {str(e)}")
            
            await state.clear()
            logger.info(f"[process_shurta_photo] ✅ Успешно создан алерт Shurta")
    except Exception as e:
        logger.error(f"[process_shurta_photo] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при создании алерта. Попробуйте позже.")


def register_user_handlers(dp: Dispatcher):
    """Register all user handlers"""
    dp.include_router(router)
