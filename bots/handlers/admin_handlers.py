from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from database import AsyncSessionLocal
from services.user_service import UserService
from services.category_service import CategoryService
from services.service_management import ServiceManagementService
from services.courier_service import CourierService
from services.broadcast_service import BroadcastService
from services.admin_log_service import AdminLogService
from services.inline_button_service import InlineButtonService
from services.admin_menu_service import AdminMenuService
from utils.keyboard_builder import KeyboardBuilder
from utils.validators import validate_url
from utils.parsers import ContentParser
from locales import t
from utils.logger import logger
from config import settings

router = Router()


class AdminStates(StatesGroup):
    """FSM States for admin bot"""
    category_name_ru = State()
    category_name_uz = State()
    category_desc_ru = State()
    category_desc_uz = State()
    button_text_ru = State()
    button_text_uz = State()
    button_url = State()
    broadcast_message_ru = State()
    broadcast_message_uz = State()
    user_search = State()


def is_admin(telegram_id: int) -> bool:
    """Check if user is admin"""
    return telegram_id in settings.admin_ids_list


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command for admin bot"""
    if not is_admin(message.from_user.id):
        await message.answer(t("not_authorized", "RU"))
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(
            t("admin_welcome", language),
            reply_markup=KeyboardBuilder.admin_menu_keyboard(language)
        )


@router.message(F.text.in_([t("admin_categories", "RU"), t("admin_categories", "UZ")]))
async def show_category_management(message: Message):
    """Show category management menu"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(
            t("admin_categories", language),
            reply_markup=AdminMenuService.get_category_menu(language)
        )


@router.callback_query(F.data == "cat_add")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    """Start category creation process"""
    if not is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        await callback.message.answer(t("category_name_ru", language))
        await state.set_state(AdminStates.category_name_ru)
    
    await callback.answer()


@router.message(AdminStates.category_name_ru)
async def process_category_name_ru(message: Message, state: FSMContext):
    """Process category name in Russian"""
    await state.update_data(name_ru=message.text)
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(t("category_name_uz", language))
        await state.set_state(AdminStates.category_name_uz)


@router.message(AdminStates.category_name_uz)
async def process_category_name_uz(message: Message, state: FSMContext):
    """Process category name in Uzbek and create category"""
    await state.update_data(name_uz=message.text)
    
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        category = await CategoryService.create_category(
            session,
            name_ru=data['name_ru'],
            name_uz=data['name_uz'],
            created_by_admin_id=message.from_user.id
        )
        
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="CREATE",
            entity_type="CATEGORY",
            entity_id=category.id,
            details={"name_ru": data['name_ru'], "name_uz": data['name_uz']}
        )
        
        await message.answer(
            t("category_added", language),
            reply_markup=KeyboardBuilder.admin_menu_keyboard(language)
        )
    
    await state.clear()


@router.callback_query(F.data == "cat_tree")
async def show_category_tree(callback: CallbackQuery):
    """Show category tree"""
    if not is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        tree = await CategoryService.get_category_tree(session)
        
        def format_tree(items, level=0):
            text = ""
            for item in items:
                indent = "  " * level
                status = "✅" if item["is_active"] else "❌"
                text += f"{indent}{item['icon']} {item['name_ru']} {status}\n"
                if item["children"]:
                    text += format_tree(item["children"], level + 1)
            return text
        
        tree_text = t("view_category_tree", language) + "\n\n"
        tree_text += format_tree(tree.get("tree", []))
        
        await callback.message.answer(
            tree_text or t("no_categories", language),
            reply_markup=AdminMenuService.get_category_menu(language)
        )
    
    await callback.answer()


@router.message(F.text.in_([t("admin_buttons", "RU"), t("admin_buttons", "UZ")]))
async def show_button_management(message: Message):
    """Show button management menu"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(
            t("admin_buttons", language),
            reply_markup=AdminMenuService.get_button_menu(language)
        )


@router.callback_query(F.data == "btn_list")
async def list_all_buttons(callback: CallbackQuery):
    """List all buttons"""
    if not is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        buttons = await InlineButtonService.get_all_buttons(session)
        
        if not buttons:
            await callback.message.answer(t("no_buttons", language))
            await callback.answer()
            return
        
        text = t("list_buttons", language) + "\n\n"
        for btn in buttons:
            status = "✅" if btn.is_active else "❌"
            text += f"{status} {btn.button_text_ru} → {btn.button_url}\n"
            text += f"   Category ID: {btn.category_id}\n\n"
        
        await callback.message.answer(text)
    
    await callback.answer()


@router.message(F.text.in_([t("admin_services", "RU"), t("admin_services", "UZ")]))
async def show_service_management(message: Message):
    """Show service management menu"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(
            t("admin_services", language),
            reply_markup=AdminMenuService.get_service_menu(language)
        )


@router.callback_query(F.data == "svc_pending")
async def show_pending_services(callback: CallbackQuery):
    """Show pending service requests"""
    if not is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        services = await ServiceManagementService.get_pending_services(session)
        
        if not services:
            await callback.message.answer(t("no_pending_services", language))
            await callback.answer()
            return
        
        for service in services[:5]:
            text = f"🏢 **{service.service_type}**\n\n"
            text += f"Title: {service.title_ru}\n"
            text += f"Description: {service.description_ru}\n"
            text += f"User ID: {service.user_id}\n"
            
            buttons = [
                {"text": t("approve_service", language), "callback_data": f"svc_approve_{service.id}"},
                {"text": t("reject_service", language), "callback_data": f"svc_reject_{service.id}"}
            ]
            
            await callback.message.answer(
                text,
                reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=2),
                parse_mode="Markdown"
            )
    
    await callback.answer()


@router.callback_query(F.data.startswith("svc_approve_"))
async def approve_service(callback: CallbackQuery):
    """Approve service request"""
    if not is_admin(callback.from_user.id):
        return
    
    service_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        service = await ServiceManagementService.approve_service(session, service_id)
        
        if service:
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="APPROVE",
                entity_type="SERVICE",
                entity_id=service_id
            )
            
            await callback.message.edit_text(t("service_approved_admin", language))
    
    await callback.answer()


@router.callback_query(F.data.startswith("svc_reject_"))
async def reject_service(callback: CallbackQuery):
    """Reject service request"""
    if not is_admin(callback.from_user.id):
        return
    
    service_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        service = await ServiceManagementService.reject_service(session, service_id)
        
        if service:
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="REJECT",
                entity_type="SERVICE",
                entity_id=service_id
            )
            
            await callback.message.edit_text(t("service_rejected_admin", language))
    
    await callback.answer()


@router.message(F.text.in_([t("admin_users", "RU"), t("admin_users", "UZ")]))
async def show_user_management(message: Message):
    """Show user management menu"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        stats = await UserService.get_user_stats(session)
        
        text = t("stats_users", language) + "\n\n"
        text += t("total_users", language, count=stats["total"]) + "\n"
        text += t("users_today", language, count=stats["today"]) + "\n"
        text += t("users_by_language", language, ru=stats["by_language"]["RU"], uz=stats["by_language"]["UZ"]) + "\n"
        text += t("users_by_citizenship", language, 
                  uz=stats["by_citizenship"]["UZ"],
                  ru=stats["by_citizenship"]["RU"],
                  kz=stats["by_citizenship"]["KZ"],
                  kg=stats["by_citizenship"]["KG"]) + "\n"
        
        await message.answer(
            text,
            reply_markup=AdminMenuService.get_user_menu(language)
        )


@router.message(F.text.in_([t("admin_couriers", "RU"), t("admin_couriers", "UZ")]))
async def show_courier_management(message: Message):
    """Show courier management"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        stats = await CourierService.get_courier_stats(session)
        
        text = t("stats_couriers", language) + "\n\n"
        text += t("total_couriers", language, count=stats["total"]) + "\n"
        text += t("active_couriers", language, count=stats["active"]) + "\n"
        text += t("total_deliveries", language, count=stats["total_deliveries"]) + "\n"
        text += t("average_rating", language, rating=stats["average_rating"]) + "\n"
        
        await message.answer(
            text,
            reply_markup=AdminMenuService.get_courier_menu(language)
        )


@router.message(F.text.in_([t("admin_broadcast", "RU"), t("admin_broadcast", "UZ")]))
async def show_broadcast_menu(message: Message):
    """Show broadcast menu"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(
            t("admin_broadcast", language),
            reply_markup=AdminMenuService.get_broadcast_menu(language)
        )


@router.callback_query(F.data == "bc_create")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Start broadcast creation"""
    if not is_admin(callback.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        await callback.message.answer(t("broadcast_message_ru", language))
        await state.set_state(AdminStates.broadcast_message_ru)
    
    await callback.answer()


@router.message(AdminStates.broadcast_message_ru)
async def process_broadcast_message_ru(message: Message, state: FSMContext):
    """Process broadcast message in Russian"""
    await state.update_data(message_ru=message.text)
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(t("broadcast_message_uz", language))
        await state.set_state(AdminStates.broadcast_message_uz)


@router.message(AdminStates.broadcast_message_uz)
async def process_broadcast_message_uz(message: Message, state: FSMContext):
    """Process broadcast message in Uzbek"""
    await state.update_data(message_uz=message.text)
    
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        buttons = [
            {"text": t("broadcast_all", language), "callback_data": "bc_send_ALL"},
            {"text": t("broadcast_language_ru", language), "callback_data": "bc_send_LANGUAGE_RU"},
            {"text": t("broadcast_language_uz", language), "callback_data": "bc_send_LANGUAGE_UZ"},
            {"text": t("broadcast_couriers", language), "callback_data": "bc_send_COURIERS_ONLY"}
        ]
        
        await message.answer(
            t("broadcast_filter", language),
            reply_markup=KeyboardBuilder.inline_keyboard(buttons, row_width=2)
        )


@router.callback_query(F.data.startswith("bc_send_"))
async def send_broadcast(callback: CallbackQuery, state: FSMContext):
    """Send broadcast"""
    if not is_admin(callback.from_user.id):
        return
    
    broadcast_type = callback.data.split("_", 2)[2]
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        recipients = await BroadcastService.get_recipients(session, broadcast_type)
        count = len(recipients)
        
        await callback.message.answer(
            t("broadcast_recipients", language, count=count),
            reply_markup=KeyboardBuilder.confirm_keyboard(language, "bc_confirm", "bc_cancel")
        )
        
        await state.update_data(broadcast_type=broadcast_type)
    
    await callback.answer()


@router.callback_query(F.data == "bc_confirm")
async def confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Confirm and send broadcast"""
    if not is_admin(callback.from_user.id):
        return
    
    data = await state.get_data()
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, callback.from_user.id)
        language = user.language if user else "RU"
        
        broadcast = await BroadcastService.create_broadcast(
            session,
            admin_id=callback.from_user.id,
            message_ru=data['message_ru'],
            message_uz=data['message_uz'],
            broadcast_type=data['broadcast_type']
        )
        
        recipients = await BroadcastService.get_recipients(session, data['broadcast_type'])
        
        await BroadcastService.update_broadcast_count(session, broadcast.id, len(recipients))
        
        await AdminLogService.log_action(
            session,
            admin_id=callback.from_user.id,
            action="CREATE",
            entity_type="BROADCAST",
            entity_id=broadcast.id,
            details={"type": data['broadcast_type'], "recipients": len(recipients)}
        )
        
        await callback.message.edit_text(
            t("broadcast_sent", language, count=len(recipients))
        )
    
    await state.clear()
    await callback.answer()


@router.message(F.text.in_([t("admin_stats", "RU"), t("admin_stats", "UZ")]))
async def show_statistics(message: Message):
    """Show statistics"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        user_stats = await UserService.get_user_stats(session)
        service_stats = await ServiceManagementService.get_service_stats(session)
        courier_stats = await CourierService.get_courier_stats(session)
        
        text = "📊 **" + t("admin_stats", language) + "**\n\n"
        
        text += "👥 " + t("stats_users", language) + "\n"
        text += t("total_users", language, count=user_stats["total"]) + "\n\n"
        
        text += "🏢 " + t("stats_services", language) + "\n"
        text += t("services_total", language, count=service_stats["total"]) + "\n"
        text += t("services_approved", language, count=service_stats["approved"]) + "\n"
        text += t("services_pending", language, count=service_stats["pending"]) + "\n\n"
        
        text += "🚚 " + t("stats_couriers", language) + "\n"
        text += t("total_couriers", language, count=courier_stats["total"]) + "\n"
        text += t("total_deliveries", language, count=courier_stats["total_deliveries"]) + "\n"
        
        await message.answer(text, parse_mode="Markdown")


@router.message(F.text.in_([t("admin_parse", "RU"), t("admin_parse", "UZ")]))
async def parse_content(message: Message):
    """Parse result.json content"""
    if not is_admin(message.from_user.id):
        return
    
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        language = user.language if user else "RU"
        
        await message.answer(t("parse_progress", language))
        
        parser = ContentParser("result.json")
        success = parser.export_to_json()
        
        if success:
            parsed = parser.parse_all()
            text = t("parse_complete", language) + "\n\n"
            text += t("parse_found", language,
                     dirassa=len(parsed.get("dirassa", {}).get("general", [])),
                     alazhar=len(parsed.get("alazhar", {}).get("general", [])),
                     contacts=len(parsed.get("contacts", [])))
            
            await message.answer(text)
        else:
            await message.answer(t("error_occurred", language))


def register_admin_handlers(dp):
    """Register all admin handlers"""
    dp.include_router(router)
    logger.info("Admin handlers registered")
