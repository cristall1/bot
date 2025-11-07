from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from database import AsyncSessionLocal
from services.user_service import UserService
from services.category_service import CategoryService
from services.service_management import ServiceManagementService
from services.courier_service import CourierService
from services.inline_button_service import InlineButtonService
from utils.keyboard_builder import KeyboardBuilder
from utils.helpers import get_citizenship_name
from locales import t
from utils.logger import logger

router = Router()


class UserStates(StatesGroup):
    """FSM States for user bot"""
    choosing_language = State()
    choosing_citizenship = State()
    browsing_categories = State()
    requesting_service = State()
    service_title = State()
    service_description = State()
    service_contact = State()
    contacting_admin = State()
    searching = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        
        if not user:
            await message.answer(
                t("welcome", "RU") + "\n\n" + t("welcome_desc", "RU") + "\n\n" + t("welcome_capabilities", "RU"),
                reply_markup=KeyboardBuilder.language_keyboard()
            )
            await state.set_state(UserStates.choosing_language)
        else:
            if user.is_banned:
                await message.answer(t("user_banned", user.language))
                return
            
            user.last_active = __import__('datetime').datetime.utcnow()
            await session.commit()
            
            await message.answer(
                t("main_menu", user.language),
                reply_markup=KeyboardBuilder.main_menu_keyboard(user.language)
            )
            await state.clear()


@router.callback_query(F.data.startswith("lang_"))
async def process_language_selection(callback: CallbackQuery, state: FSMContext):
    """Process language selection"""
    language = callback.data.split("_")[1]
    await state.update_data(language=language)
    
    await callback.message.edit_text(
        t("language_selected", language) + "\n\n" + t("choose_citizenship", language),
        reply_markup=KeyboardBuilder.citizenship_keyboard(language)
    )
    await state.set_state(UserStates.choosing_citizenship)
    await callback.answer()


@router.callback_query(F.data.startswith("citizenship_"))
async def process_citizenship_selection(callback: CallbackQuery, state: FSMContext):
    """Process citizenship selection"""
    citizenship = callback.data.split("_")[1]
    user_data = await state.get_data()
    language = user_data.get("language", "RU")
    
    async with AsyncSessionLocal() as session:
        user = await UserService.create_or_update_user(
            session,
            telegram_id=callback.from_user.id,
            username=callback.from_user.username,
            first_name=callback.from_user.first_name,
            language=language,
            citizenship=citizenship
        )
        
        citizenship_name = get_citizenship_name(citizenship, language)
        await callback.message.edit_text(
            t("citizenship_selected", language, citizenship=citizenship_name) + "\n\n" +
            t("registration_complete", language)
        )
        
        await callback.message.answer(
            t("main_menu", language),
            reply_markup=KeyboardBuilder.main_menu_keyboard(language)
        )
    
    await state.clear()
    await callback.answer()


@router.message(F.text.in_([t("menu_categories", "RU"), t("menu_categories", "UZ")]))
async def show_categories(message: Message):
    """Show root categories"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        categories = await CategoryService.get_root_categories(
            session,
            active_only=True,
            citizenship=user.citizenship
        )
        
        if not categories:
            await message.answer(t("no_categories", user.language))
            return
        
        buttons = []
        for cat in categories:
            name = cat.name_ru if user.language == "RU" else cat.name_uz
            buttons.append({
                "text": f"{cat.icon} {name}",
                "callback_data": f"cat_{cat.id}"
            })
        
        buttons.append({"text": t("btn_back", user.language), "callback_data": "main_menu"})
        
        await message.answer(
            t("select_category", user.language),
            reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=2)
        )


@router.callback_query(F.data.startswith("cat_"))
async def show_category_content(callback: CallbackQuery):
    """Show category content and subcategories"""
    category_id = int(callback.data.split("_")[1])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user or user.is_banned:
            return
        
        category = await CategoryService.get_category(session, category_id)
        if not category or not category.is_active:
            await callback.answer(t("error", user.language))
            return
        
        name = category.name_ru if user.language == "RU" else category.name_uz
        desc = category.description_ru if user.language == "RU" else category.description_uz
        
        text = f"{category.icon} **{name}**\n\n"
        if desc:
            text += f"{desc}\n\n"
        
        content = await CategoryService.get_category_content(session, category_id)
        if content:
            for item in content:
                content_text = item.content_ru if user.language == "RU" else item.content_uz
                if content_text:
                    text += f"{content_text}\n\n"
        
        subcategories = await CategoryService.get_subcategories(
            session,
            category_id,
            active_only=True,
            citizenship=user.citizenship
        )
        
        buttons = []
        
        if subcategories:
            for subcat in subcategories:
                subcat_name = subcat.name_ru if user.language == "RU" else subcat.name_uz
                buttons.append({
                    "text": f"{subcat.icon} {subcat_name}",
                    "callback_data": f"cat_{subcat.id}"
                })
        
        inline_buttons = await InlineButtonService.get_buttons_by_category(
            session,
            category_id,
            active_only=True
        )
        
        for btn in inline_buttons:
            btn_text = btn.button_text_ru if user.language == "RU" else btn.button_text_uz
            buttons.append({
                "text": btn_text,
                "url": btn.button_url
            })
        
        buttons.append({"text": t("btn_back", user.language), "callback_data": f"cat_parent_{category.parent_id}" if category.parent_id else "categories"})
        
        await callback.message.edit_text(
            text,
            reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=2),
            parse_mode="Markdown"
        )
    
    await callback.answer()


@router.message(F.text.in_([t("menu_courier", "RU"), t("menu_courier", "UZ")]))
async def show_courier_info(message: Message):
    """Show courier system information"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        courier = await CourierService.get_courier(session, user.id)
        
        if courier and courier.is_courier:
            text = t("already_courier", user.language) + "\n\n"
            text += t("courier_rating", user.language, rating=courier.rating) + "\n"
            text += t("courier_deliveries", user.language, count=courier.completed_deliveries) + "\n"
            if courier.cairo_zone:
                text += t("courier_zone", user.language, zone=courier.cairo_zone) + "\n"
            text += t("courier_status", user.language, status=courier.courier_status)
            
            buttons = [
                {"text": t("courier_active", user.language), "callback_data": "courier_deliveries"},
                {"text": t("courier_stats", user.language), "callback_data": "courier_stats"}
            ]
        else:
            text = t("courier_title", user.language) + "\n\n"
            text += t("courier_desc", user.language) + "\n\n"
            text += t("courier_benefits", user.language) + "\n\n"
            text += t("courier_requirements", user.language) + "\n\n"
            text += t("courier_zones", user.language)
            
            buttons = [
                {"text": t("accept_courier_terms", user.language), "callback_data": "become_courier"}
            ]
        
        buttons.append({"text": t("btn_back", user.language), "callback_data": "main_menu"})
        
        await message.answer(
            text,
            reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=1)
        )


@router.callback_query(F.data == "become_courier")
async def register_as_courier(callback: CallbackQuery):
    """Register user as courier"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if not user or user.is_banned:
            return
        
        await CourierService.register_courier(session, user.id)
        
        await callback.message.edit_text(
            t("courier_registered", user.language),
            reply_markup=KeyboardBuilder.back_button(user.language, "main_menu")
        )
    
    await callback.answer()


@router.message(F.text.in_([t("menu_services", "RU"), t("menu_services", "UZ")]))
async def show_services(message: Message):
    """Show available services"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        services = await ServiceManagementService.get_approved_services(session)
        
        if not services:
            await message.answer(t("no_services", user.language))
            return
        
        text = t("services_list", user.language) + "\n\n"
        
        for service in services[:10]:
            title = service.title_ru if user.language == "RU" else service.title_uz
            desc = service.description_ru if user.language == "RU" else service.description_uz
            text += f"🏢 **{title}**\n{desc[:100]}...\n\n"
        
        buttons = [
            {"text": t("service_request", user.language), "callback_data": "request_service"},
            {"text": t("my_services", user.language), "callback_data": "my_services"}
        ]
        
        await message.answer(
            text,
            reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=2),
            parse_mode="Markdown"
        )


@router.message(F.text.in_([t("menu_settings", "RU"), t("menu_settings", "UZ")]))
async def show_settings(message: Message):
    """Show user settings"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        text = t("settings", user.language) + "\n\n"
        text += t("settings_language", user.language) + f" {user.language}\n"
        text += t("settings_citizenship", user.language) + f" {get_citizenship_name(user.citizenship, user.language)}\n"
        notif_status = t("notifications_enabled", user.language) if user.notifications_enabled else t("notifications_disabled", user.language)
        text += t("settings_notifications", user.language) + f" {notif_status}\n"
        
        buttons = [
            {"text": t("change_language", user.language), "callback_data": "change_language"},
            {"text": t("toggle_notifications", user.language), "callback_data": "toggle_notifications"}
        ]
        
        await message.answer(
            text,
            reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=2)
        )


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: CallbackQuery):
    """Toggle user notifications"""
    async with AsyncSessionLocal() as session:
        user = await UserService.toggle_notifications(session, callback.from_user.id)
        if user:
            await callback.answer(t("settings_updated", user.language))
            
            text = t("settings", user.language) + "\n\n"
            text += t("settings_language", user.language) + f" {user.language}\n"
            text += t("settings_citizenship", user.language) + f" {get_citizenship_name(user.citizenship, user.language)}\n"
            notif_status = t("notifications_enabled", user.language) if user.notifications_enabled else t("notifications_disabled", user.language)
            text += t("settings_notifications", user.language) + f" {notif_status}\n"
            
            buttons = [
                {"text": t("change_language", user.language), "callback_data": "change_language"},
                {"text": t("toggle_notifications", user.language), "callback_data": "toggle_notifications"}
            ]
            
            await callback.message.edit_text(
                text,
                reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=2)
            )


@router.message(F.text.in_([t("menu_help", "RU"), t("menu_help", "UZ")]))
async def show_help(message: Message):
    """Show help information"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        if not user or user.is_banned:
            return
        
        await message.answer(
            t("help_text", user.language),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Return to main menu"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        if user:
            await callback.message.answer(
                t("main_menu", user.language),
                reply_markup=KeyboardBuilder.main_menu_keyboard(user.language)
            )
    await callback.answer()


def register_user_handlers(dp):
    """Register all user handlers"""
    dp.include_router(router)
    logger.info("User handlers registered")
