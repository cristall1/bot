from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram import Dispatcher

from database import AsyncSessionLocal
from locales import t
from states import UserStates
from services.user_service import UserService
from services.document_service import DocumentService
from services.delivery_service import DeliveryService
from services.notification_service import NotificationService
from services.shurta_service import ShurtaService
from services.user_message_service import UserMessageService
from utils.logger import logger

router = Router()


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
    logger.info(f"[cmd_start] Started | user_id={message.from_user.id}, username={message.from_user.username}")
    try:
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, message.from_user.id)
            
            if not user:
                await message.answer(
                    t("welcome", "RU"),
                    reply_markup=get_language_keyboard()
                )
                await state.set_state(UserStates.selecting_language)
                logger.info(f"[cmd_start] ✅ New user | user_id={message.from_user.id}")
            else:
                if user.is_banned:
                    await message.answer(t("banned", user.language))
                    logger.warning(f"[cmd_start] ⚠️ Banned user access | user_id={message.from_user.id}")
                    return
                
                await message.answer(
                    t("main_menu", user.language),
                    reply_markup=get_main_menu_keyboard(user.language)
                )
                logger.info(f"[cmd_start] ✅ Existing user | user_id={message.from_user.id}, lang={user.language}")
    
    except Exception as e:
        logger.error(f"[cmd_start] ❌ Error | user_id={message.from_user.id}, error={str(e)}")
        await message.answer("❌ Ошибка при запуске бота")


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
    logger.info(f"[show_document] Started | user_id={callback.from_user.id}, doc_id={callback.data}")
    try:
        doc_id = int(callback.data.split("_")[1])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user:
                logger.warning(f"[show_document] User not found | user_id={callback.from_user.id}")
                return
            
            document = await DocumentService.get_document(session, doc_id)
            if not document:
                logger.warning(f"[show_document] Document not found | doc_id={doc_id}")
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
            
            # Send content based on type
            if document.content_type == "PHOTO" and document.photo_file_id:
                await callback.message.answer_photo(
                    photo=document.photo_file_id,
                    caption=f"{title}\n\n{content}",
                    reply_markup=keyboard
                )
                logger.info(f"[show_document] ✅ Photo sent | doc_id={doc_id}")
            elif document.content_type == "TEXT":
                await callback.message.answer(
                    f"{title}\n\n{content}",
                    reply_markup=keyboard
                )
                logger.info(f"[show_document] ✅ Text sent | doc_id={doc_id}")
            elif document.content_type == "PDF" and document.pdf_file_id:
                await callback.message.answer_document(
                    document=document.pdf_file_id,
                    caption=f"{title}\n\n{content}",
                    reply_markup=keyboard
                )
                logger.info(f"[show_document] ✅ PDF sent | doc_id={doc_id}")
            elif document.content_type == "AUDIO" and document.audio_file_id:
                await callback.message.answer_audio(
                    audio=document.audio_file_id,
                    caption=f"{title}\n\n{content}",
                    reply_markup=keyboard
                )
                logger.info(f"[show_document] ✅ Audio sent | doc_id={doc_id}")
            else:
                await callback.message.answer(
                    f"{title}\n\n{content}",
                    reply_markup=keyboard
                )
                logger.info(f"[show_document] ✅ Default text sent | doc_id={doc_id}")
    
    except Exception as e:
        logger.error(f"[show_document] ❌ Error | user_id={callback.from_user.id}, error={str(e)}")
        await callback.answer("❌ Ошибка при загрузке документа", show_alert=True)
    
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
    logger.info(f"[process_delivery_phone] Started | user_id={message.from_user.id}")
    try:
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, message.from_user.id)
            if not user:
                logger.warning(f"[process_delivery_phone] User not found | user_id={message.from_user.id}")
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
        logger.info(f"[process_delivery_phone] ✅ Delivery created | delivery_id={delivery.id}")
        
        # Notify all active couriers
        couriers = await DeliveryService.get_all_couriers(session)
        notified_count = 0
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
                    notified_count += 1
                except Exception as e:
                    logger.error(f"Failed to notify courier {courier_user.telegram_id}: {e}")
        
        logger.info(f"[process_delivery_phone] ✅ Notified {notified_count} couriers | delivery_id={delivery.id}")
        
        await message.answer(
            t("delivery_created", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.clear()
    
    except Exception as e:
        logger.error(f"[process_delivery_phone] ❌ Error | user_id={message.from_user.id}, error={str(e)}")
        await message.answer("❌ Ошибка при создании заказа")
        await state.clear()


@router.callback_query(F.data.startswith("take_delivery_"))
async def take_delivery(callback: CallbackQuery):
    """Courier takes delivery"""
    logger.info(f"[take_delivery] Started | user_id={callback.from_user.id}, callback_data={callback.data}")
    try:
        delivery_id = int(callback.data.split("_")[2])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user:
                logger.warning(f"[take_delivery] User not found | user_id={callback.from_user.id}")
                return
            
            # Assign delivery
            delivery = await DeliveryService.assign_courier(session, delivery_id, user.id)
            
            if not delivery:
                await callback.answer(t("delivery_already_taken", user.language), show_alert=True)
                logger.warning(f"[take_delivery] Delivery already taken | delivery_id={delivery_id}")
                return

        # Notify creator with courier contact info
        creator = await UserService.get_user_by_id(session, delivery.creator_id)
        if creator:
            try:
                msg_text = t("delivery_accepted", creator.language)
                msg_text += f"\n\n👤 Курьер: @{user.username or user.first_name}"
                msg_text += f"\n📞 Телефон: {user.phone if user.phone else 'Не указан'}"

                await callback.bot.send_message(creator.telegram_id, msg_text)
                logger.info(f"[take_delivery] ✅ Notified creator | creator_id={creator.id}")
            except Exception as e:
                logger.error(f"[take_delivery] Failed to notify creator: {e}")

            await callback.message.edit_text(t("delivery_taken", user.language))
            logger.info(f"[take_delivery] ✅ Delivery taken | delivery_id={delivery_id}, courier_id={user.id}")
            await callback.answer()

            except Exception as e:
            logger.error(f"[take_delivery] ❌ Error | user_id={callback.from_user.id}, error={str(e)}")
            await callback.answer("❌ Ошибка при принятии заказа", show_alert=True)


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
        
        photo_url = None
        if message.photo:
            photo_url = message.photo[-1].file_id
        elif message.text != t("notifications_skip_photo", user.language):
            photo_url = None
        
        await state.update_data(photo_url=photo_url)
        
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
        
        notification = await NotificationService.create_notification(
            session,
            notification_type="PROPAJA_ODAM",
            creator_id=user.id,
            title_ru=data["name"],
            title_uz=data["name"],  # Can be the same for names
            description_ru=data["description"],
            description_uz=data["description"],  # Can be the same initially
            location_type=location_type if location_type in ["ADDRESS", "GEO", "MAPS"] else "ADDRESS",
            address_text=address_text,
            latitude=latitude,
            longitude=longitude,
            maps_url=maps_url,
            phone=data["phone"],
            photo_file_id=data.get("photo_url")
        )
        
        # Send to admin for moderation (NOT to users directly)
        await message.answer("✅ Объявление отправлено на модерацию администратору")
        logger.info(f"[process_lost_person_phone] ✅ Sent to moderation | notification_id={notification.id}")
        
        # TODO: Send notification to admins for moderation
        # This would be implemented with admin notification system
        
        await message.answer(
            t("notifications_created", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.clear()


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
        
        photo_url = None
        if message.photo:
            photo_url = message.photo[-1].file_id
        elif message.text != t("notifications_skip_photo", user.language):
            photo_url = None
        
        await state.update_data(photo_url=photo_url)
        
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
        
        notification = await NotificationService.create_notification(
            session,
            notification_type="PROPAJA_NARSA",
            creator_id=user.id,
            title_ru=data["what"],
            title_uz=data["what"],  # Can be the same for item names
            description_ru=data["description"],
            description_uz=data["description"],  # Can be the same initially
            location_type=location_type if location_type in ["ADDRESS", "GEO", "MAPS"] else "ADDRESS",
            address_text=address_text,
            latitude=latitude,
            longitude=longitude,
            maps_url=maps_url,
            phone=data["phone"],
            photo_file_id=data.get("photo_url")
        )
        
        # Send to admin for moderation (NOT to users directly)
        await message.answer("✅ Объявление отправлено на модерацию администратору")
        logger.info(f"[process_lost_item_phone] ✅ Sent to moderation | notification_id={notification.id}")
        
        # TODO: Send notification to admins for moderation
        # This would be implemented with admin notification system
        
        await message.answer(
            t("notifications_created", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.clear()


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
        
        # Notify all users
        all_users = await UserService.get_all_users(session)
        for target_user in all_users:
            if target_user.notifications_enabled and target_user.id != user.id:
                try:
                    alert_text = t("shurta_alert", target_user.language,
                                 description=data["description"],
                                 location=data["location_info"])
                    
                    if photo_file_id:
                        await message.bot.send_photo(
                            target_user.telegram_id,
                            photo=photo_file_id,
                            caption=alert_text
                        )
                    else:
                        await message.bot.send_message(
                            target_user.telegram_id,
                            alert_text
                        )
                except Exception as e:
                    logger.error(f"Failed to notify user {target_user.telegram_id}: {e}")
        
        await message.answer(
            t("shurta_created", user.language),
            reply_markup=get_main_menu_keyboard(user.language)
        )
        await state.clear()


@router.callback_query(F.data.startswith("doc_file_"))
async def handle_document_file(callback: CallbackQuery):
    """Handle document file button clicks"""
    logger.info(f"[handle_document_file] Started | callback_data={callback.data}")
    try:
        button_id = int(callback.data.split("_")[2])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Get button info
            from services.document_service import DocumentService
            button = await DocumentService.get_document_button(session, button_id)
            if not button:
                await callback.answer("❌ Кнопка не найдена", show_alert=True)
                return
            
            # Handle different file types
            if button.button_type == "PHOTO" and button.button_value:
                await callback.message.answer_photo(
                    photo=button.button_value,
                    caption=button.text_ru if user.language == "RU" else button.text_uz
                )
                logger.info(f"[handle_document_file] ✅ Photo sent | button_id={button_id}")
            elif button.button_type == "PDF" and button.button_value:
                await callback.message.answer_document(
                    document=button.button_value,
                    caption=button.text_ru if user.language == "RU" else button.text_uz
                )
                logger.info(f"[handle_document_file] ✅ PDF sent | button_id={button_id}")
            elif button.button_type == "AUDIO" and button.button_value:
                await callback.message.answer_audio(
                    audio=button.button_value,
                    caption=button.text_ru if user.language == "RU" else button.text_uz
                )
                logger.info(f"[handle_document_file] ✅ Audio sent | button_id={button_id}")
            else:
                await callback.answer("❌ Файл не найден", show_alert=True)
                logger.warning(f"[handle_document_file] No file content | button_id={button_id}")
    
    except Exception as e:
        logger.error(f"[handle_document_file] ❌ Error | {str(e)}")
        await callback.answer("❌ Ошибка при загрузке файла", show_alert=True)
    
    await callback.answer()


@router.callback_query(F.data.startswith("doc_geo_"))
async def handle_document_geo(callback: CallbackQuery):
    """Handle document geo button clicks"""
    logger.info(f"[handle_document_geo] Started | callback_data={callback.data}")
    try:
        button_id = int(callback.data.split("_")[2])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Get button info
            from services.document_service import DocumentService
            button = await DocumentService.get_document_button(session, button_id)
            if not button:
                await callback.answer("❌ Кнопка не найдена", show_alert=True)
                return
            
            # Parse coordinates from button_value (format: "lat,lng")
            if "," in button.button_value:
                try:
                    lat, lng = map(float, button.button_value.split(","))
                    await callback.message.answer_location(
                        latitude=lat,
                        longitude=lng,
                        title=button.text_ru if user.language == "RU" else button.text_uz
                    )
                    logger.info(f"[handle_document_geo] ✅ Location sent | button_id={button_id}, coords={lat},{lng}")
                except ValueError:
                    await callback.answer("❌ Неверный формат координат", show_alert=True)
                    logger.warning(f"[handle_document_geo] Invalid coords | button_id={button_id}, value={button.button_value}")
            else:
                await callback.answer("❌ Координаты не найдены", show_alert=True)
                logger.warning(f"[handle_document_geo] No coords | button_id={button_id}")
    
    except Exception as e:
        logger.error(f"[handle_document_geo] ❌ Error | {str(e)}")
        await callback.answer("❌ Ошибка при загрузке локации", show_alert=True)
    
    await callback.answer()


def register_user_handlers(dp: Dispatcher):
    """Register all user handlers"""
    dp.include_router(router)
