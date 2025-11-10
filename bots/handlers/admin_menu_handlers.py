"""
Admin Menu Management Handlers - ONE MESSAGE SYSTEM
Complete rewrite for managing User Bot main menu
Language: Russian
Framework: aiogram 3.x
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from database import AsyncSessionLocal
from services.menu_service import MenuService
from services.admin_log_service import AdminLogService
from states import AdminStates
from utils.logger import logger
from typing import Dict, Any

router = Router()

# ═══════════════════════════════════════════════════════════════════════════
# STATE STORAGE (In-Memory - Simple Implementation)
# ═══════════════════════════════════════════════════════════════════════════

admin_temp_data: Dict[int, Dict[str, Any]] = {}


def get_temp_data(admin_id: int) -> Dict[str, Any]:
    """Get temporary data for admin"""
    if admin_id not in admin_temp_data:
        admin_temp_data[admin_id] = {}
    return admin_temp_data[admin_id]


def clear_temp_data(admin_id: int):
    """Clear temporary data for admin"""
    if admin_id in admin_temp_data:
        admin_temp_data[admin_id] = {}


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 1: MAIN MENU LIST
# ═══════════════════════════════════════════════════════════════════════════

async def build_menu_management_view(admin_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Build main menu management page (ALWAYS FRESH DATA)"""
    async with AsyncSessionLocal() as session:
        menu_items = await MenuService.get_all_menu_items(session, include_inactive=True)
    
    text = "🔧 УПРАВЛЕНИЕ МЕНЮ USER BOT\n"
    text += "═══════════════════════════════════════\n\n"
    text += "Пункты меню:\n\n"
    
    keyboard_rows = []
    
    if not menu_items:
        text += "Пока нет пунктов меню.\n"
    else:
        for item in menu_items:
            status_icon = "✅" if item.is_active else "❌"
            icon = item.icon or "📝"
            
            text += f"{status_icon} {icon} {item.name_ru}\n"
            
            # Each item has: Toggle | Edit | Delete buttons
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"🔄 {status_icon}",
                    callback_data=f"menu_toggle_{item.id}"
                ),
                InlineKeyboardButton(
                    text=item.name_ru[:20],
                    callback_data=f"menu_view_{item.id}"
                ),
                InlineKeyboardButton(
                    text="✏️",
                    callback_data=f"menu_edit_{item.id}"
                ),
                InlineKeyboardButton(
                    text="🗑️",
                    callback_data=f"menu_delete_{item.id}"
                )
            ])
    
    # Add New and Back buttons
    keyboard_rows.append([
        InlineKeyboardButton(text="➕ Добавить пункт меню", callback_data="menu_add_new")
    ])
    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Назад в главное меню", callback_data="admin_back_main")
    ])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    return text, markup


@router.callback_query(F.data == "admin_menu_manage")
async def show_menu_management(callback: CallbackQuery, state: FSMContext):
    """Show menu management main page"""
    await state.set_state(AdminStates.menu_management)
    clear_temp_data(callback.from_user.id)
    
    text, markup = await build_menu_management_view(callback.from_user.id)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()
    logger.info(f"[MenuManagement] 👤 Admin {callback.from_user.id} открыл управление меню")


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 5: TOGGLE ON/OFF
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_toggle_"))
async def toggle_menu_item(callback: CallbackQuery, state: FSMContext):
    """Toggle menu item ON/OFF"""
    menu_item_id = int(callback.data.split("_")[2])
    
    async with AsyncSessionLocal() as session:
        new_status = await MenuService.toggle_menu_item(session, menu_item_id)
        
        if new_status is not None:
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="TOGGLE_MENU_ITEM",
                entity_type="MENU_ITEM",
                entity_id=menu_item_id,
                details={"new_status": new_status}
            )
    
    # Refresh the view (ONE MESSAGE)
    text, markup = await build_menu_management_view(callback.from_user.id)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    status_text = "ON" if new_status else "OFF"
    await callback.answer(f"✅ Статус изменен: {status_text}")


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 2: VIEW/EDIT MENU ITEM
# ═══════════════════════════════════════════════════════════════════════════

async def build_menu_item_edit_view(admin_id: int, menu_item_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Build menu item editing view (ALWAYS FRESH DATA)"""
    async with AsyncSessionLocal() as session:
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
    
    if not menu_item:
        return "❌ Пункт меню не найден", InlineKeyboardMarkup(inline_keyboard=[])
    
    icon = menu_item.icon or "📝"
    status = "✅ ON" if menu_item.is_active else "❌ OFF"
    
    text = f"✏️ РЕДАКТИРОВАНИЕ МЕНЮ: {icon} {menu_item.name_ru}\n"
    text += "═══════════════════════════════════════\n\n"
    
    text += f"📝 Название (RU): {menu_item.name_ru}\n"
    text += f"📝 Название (UZ): {menu_item.name_uz}\n"
    text += f"📝 Иконка: {icon}\n"
    text += f"🔄 Статус: {status}\n"
    
    if menu_item.description_ru:
        text += f"\n📋 Описание (RU):\n{menu_item.description_ru[:100]}\n"
    if menu_item.description_uz:
        text += f"📋 Описание (UZ):\n{menu_item.description_uz[:100]}\n"
    
    text += "\n────────────────────────────────────\n"
    text += "СОДЕРЖИМОЕ:\n\n"
    
    keyboard_rows = []
    
    # Basic info editing buttons
    keyboard_rows.append([
        InlineKeyboardButton(text="✏️ Название (RU)", callback_data=f"menu_edit_name_ru_{menu_item_id}"),
        InlineKeyboardButton(text="✏️ Название (UZ)", callback_data=f"menu_edit_name_uz_{menu_item_id}")
    ])
    keyboard_rows.append([
        InlineKeyboardButton(text="✏️ Иконка", callback_data=f"menu_edit_icon_{menu_item_id}"),
        InlineKeyboardButton(text=f"🔄 {status}", callback_data=f"menu_toggle_{menu_item_id}")
    ])
    keyboard_rows.append([
        InlineKeyboardButton(text="✏️ Описание", callback_data=f"menu_edit_desc_{menu_item_id}")
    ])
    
    # Show content items
    if menu_item.content:
        for idx, content in enumerate(menu_item.content, 1):
            content_icon = {
                "TEXT": "📝",
                "PHOTO": "🖼️",
                "PDF": "📎",
                "AUDIO": "🎵",
                "LOCATION": "📍"
            }.get(content.content_type, "📄")
            
            content_label = f"{content.content_type}"
            if content.content_type == "TEXT":
                preview = (content.text_ru or "")[:30]
                content_label = f"Text: {preview}..."
            elif content.content_type in ["PHOTO", "PDF", "AUDIO"]:
                content_label = f"{content.content_type}"
            elif content.content_type == "LOCATION":
                content_label = f"Location: {content.geo_name or 'Coordinates'}"
            
            text += f"{idx}️⃣ {content_icon} {content_label}\n"
            
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"🗑️ Удалить {content_icon} #{idx}",
                    callback_data=f"menu_del_content_{content.id}_{menu_item_id}"
                )
            ])
    else:
        text += "Нет контента.\n"
    
    # Show buttons
    if menu_item.buttons:
        text += "\nКНОПКИ:\n\n"
        for idx, button in enumerate(menu_item.buttons, 1):
            btn_type_icon = "🔘" if button.button_type == "INLINE" else "⌨️"
            action_icon = {
                "OPEN_URL": "🔗",
                "SEND_TEXT": "📝",
                "SEND_PHOTO": "🖼️",
                "SEND_PDF": "📎",
                "SEND_AUDIO": "🎵",
                "SEND_LOCATION": "📍"
            }.get(button.action_type, "➡️")
            
            text += f"{idx}️⃣ {btn_type_icon} {button.text_ru} {action_icon}\n"
            
            keyboard_rows.append([
                InlineKeyboardButton(
                    text=f"🗑️ Удалить кнопку #{idx}",
                    callback_data=f"menu_del_button_{button.id}_{menu_item_id}"
                )
            ])
    
    text += "\n────────────────────────────────────\n"
    text += "ДОБАВИТЬ:\n"
    
    # Add content buttons
    keyboard_rows.append([
        InlineKeyboardButton(text="➕ Текст", callback_data=f"menu_add_text_{menu_item_id}"),
        InlineKeyboardButton(text="➕ Фото", callback_data=f"menu_add_photo_{menu_item_id}")
    ])
    keyboard_rows.append([
        InlineKeyboardButton(text="➕ PDF", callback_data=f"menu_add_pdf_{menu_item_id}"),
        InlineKeyboardButton(text="➕ Аудио", callback_data=f"menu_add_audio_{menu_item_id}")
    ])
    keyboard_rows.append([
        InlineKeyboardButton(text="➕ Локация", callback_data=f"menu_add_location_{menu_item_id}"),
        InlineKeyboardButton(text="➕ Кнопка", callback_data=f"menu_add_button_{menu_item_id}")
    ])
    
    # Back button
    keyboard_rows.append([
        InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_menu_manage")
    ])
    
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    return text, markup


@router.callback_query(F.data.startswith("menu_edit_"))
async def edit_menu_item(callback: CallbackQuery, state: FSMContext):
    """Show menu item editing page"""
    menu_item_id = int(callback.data.split("_")[-1])
    
    await state.set_state(AdminStates.menu_item_editing)
    await state.update_data(menu_item_id=menu_item_id)
    
    text, markup = await build_menu_item_edit_view(callback.from_user.id, menu_item_id)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()


@router.callback_query(F.data.startswith("menu_view_"))
async def view_menu_item(callback: CallbackQuery, state: FSMContext):
    """View menu item (same as edit for now)"""
    await edit_menu_item(callback, state)


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 3: EDIT NAME (RU/UZ)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_edit_name_ru_"))
async def start_edit_name_ru(callback: CallbackQuery, state: FSMContext):
    """Start editing name RU"""
    menu_item_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
    
    if not menu_item:
        await callback.answer("❌ Пункт меню не найден", show_alert=True)
        return
    
    await state.set_state(AdminStates.menu_item_name_ru)
    await state.update_data(menu_item_id=menu_item_id, message_id=callback.message.message_id)
    
    text = f"✏️ ИЗМЕНИТЬ НАЗВАНИЕ (RU)\n"
    text += "═══════════════════════════════════════\n\n"
    text += f"Текущее название: {menu_item.name_ru}\n\n"
    text += "Введите новое название на русском:"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()


@router.message(StateFilter(AdminStates.menu_item_name_ru))
async def process_name_ru(message: Message, state: FSMContext):
    """Process new name RU"""
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    
    new_name = message.text.strip()
    
    async with AsyncSessionLocal() as session:
        await MenuService.update_menu_item(session, menu_item_id, name_ru=new_name)
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="UPDATE_MENU_ITEM_NAME_RU",
            entity_type="MENU_ITEM",
            entity_id=menu_item_id,
            details={"name_ru": new_name}
        )
    
    # Delete user's message
    try:
        await message.delete()
    except:
        pass
    
    # Update the ONE message
    await state.set_state(AdminStates.menu_item_editing)
    
    text, markup = await build_menu_item_edit_view(message.from_user.id, menu_item_id)
    text = f"✅ Название (RU) обновлено!\n\n{text}"
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(F.data.startswith("menu_edit_name_uz_"))
async def start_edit_name_uz(callback: CallbackQuery, state: FSMContext):
    """Start editing name UZ"""
    menu_item_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
    
    if not menu_item:
        await callback.answer("❌ Пункт меню не найден", show_alert=True)
        return
    
    await state.set_state(AdminStates.menu_item_name_uz)
    await state.update_data(menu_item_id=menu_item_id, message_id=callback.message.message_id)
    
    text = f"✏️ ИЗМЕНИТЬ НАЗВАНИЕ (UZ)\n"
    text += "═══════════════════════════════════════\n\n"
    text += f"Текущее название: {menu_item.name_uz}\n\n"
    text += "Введите новое название на узбекском:"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()


@router.message(StateFilter(AdminStates.menu_item_name_uz))
async def process_name_uz(message: Message, state: FSMContext):
    """Process new name UZ"""
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    
    new_name = message.text.strip()
    
    async with AsyncSessionLocal() as session:
        await MenuService.update_menu_item(session, menu_item_id, name_uz=new_name)
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="UPDATE_MENU_ITEM_NAME_UZ",
            entity_type="MENU_ITEM",
            entity_id=menu_item_id,
            details={"name_uz": new_name}
        )
    
    try:
        await message.delete()
    except:
        pass
    
    await state.set_state(AdminStates.menu_item_editing)
    
    text, markup = await build_menu_item_edit_view(message.from_user.id, menu_item_id)
    text = f"✅ Название (UZ) обновлено!\n\n{text}"
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 4: EDIT ICON
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_edit_icon_"))
async def start_edit_icon(callback: CallbackQuery, state: FSMContext):
    """Start editing icon"""
    menu_item_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
    
    if not menu_item:
        await callback.answer("❌ Пункт меню не найден", show_alert=True)
        return
    
    await state.set_state(AdminStates.menu_item_icon)
    await state.update_data(menu_item_id=menu_item_id, message_id=callback.message.message_id)
    
    current_icon = menu_item.icon or "нет"
    
    text = f"✏️ ИЗМЕНИТЬ ИКОНКУ\n"
    text += "═══════════════════════════════════════\n\n"
    text += f"Текущая иконка: {current_icon}\n\n"
    text += "Введите новую иконку (эмодзи):"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()


@router.message(StateFilter(AdminStates.menu_item_icon))
async def process_icon(message: Message, state: FSMContext):
    """Process new icon"""
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    
    new_icon = message.text.strip()
    
    async with AsyncSessionLocal() as session:
        await MenuService.update_menu_item(session, menu_item_id, icon=new_icon)
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="UPDATE_MENU_ITEM_ICON",
            entity_type="MENU_ITEM",
            entity_id=menu_item_id,
            details={"icon": new_icon}
        )
    
    try:
        await message.delete()
    except:
        pass
    
    await state.set_state(AdminStates.menu_item_editing)
    
    text, markup = await build_menu_item_edit_view(message.from_user.id, menu_item_id)
    text = f"✅ Иконка обновлена: {new_icon}\n\n{text}"
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


# ═══════════════════════════════════════════════════════════════════════════
# EDIT DESCRIPTION
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_edit_desc_"))
async def start_edit_description(callback: CallbackQuery, state: FSMContext):
    """Start editing description"""
    menu_item_id = int(callback.data.split("_")[-1])
    
    await state.set_state(AdminStates.menu_item_description_ru)
    await state.update_data(menu_item_id=menu_item_id, message_id=callback.message.message_id)
    
    text = f"✏️ ИЗМЕНИТЬ ОПИСАНИЕ\n"
    text += "═══════════════════════════════════════\n\n"
    text += "Введите описание на РУССКОМ (или пропустите):"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=f"menu_skip_desc_ru_{menu_item_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    
    await callback.answer()


@router.message(StateFilter(AdminStates.menu_item_description_ru))
async def process_description_ru(message: Message, state: FSMContext):
    """Process description RU"""
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    
    description_ru = message.text.strip()
    
    # Save to temp data and ask for UZ
    get_temp_data(message.from_user.id)["description_ru"] = description_ru
    
    try:
        await message.delete()
    except:
        pass
    
    await state.set_state(AdminStates.menu_item_description_uz)
    
    text = f"✏️ ИЗМЕНИТЬ ОПИСАНИЕ\n"
    text += "═══════════════════════════════════════\n\n"
    text += f"Описание (RU): ✅ Сохранено\n\n"
    text += "Введите описание на УЗБЕКСКОМ (или пропустите):"
    
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=f"menu_skip_desc_uz_{menu_item_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.message(StateFilter(AdminStates.menu_item_description_uz))
async def process_description_uz(message: Message, state: FSMContext):
    """Process description UZ"""
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    
    temp_data = get_temp_data(message.from_user.id)
    description_ru = temp_data.get("description_ru", "")
    description_uz = message.text.strip()
    
    async with AsyncSessionLocal() as session:
        await MenuService.update_menu_item(
            session,
            menu_item_id,
            description_ru=description_ru,
            description_uz=description_uz
        )
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="UPDATE_MENU_ITEM_DESCRIPTION",
            entity_type="MENU_ITEM",
            entity_id=menu_item_id,
            details={"description_ru": description_ru, "description_uz": description_uz}
        )
    
    try:
        await message.delete()
    except:
        pass
    
    clear_temp_data(message.from_user.id)
    await state.set_state(AdminStates.menu_item_editing)
    
    text, markup = await build_menu_item_edit_view(message.from_user.id, menu_item_id)
    text = f"✅ Описание обновлено!\n\n{text}"
    
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(F.data.startswith("menu_skip_desc_"))
async def skip_description(callback: CallbackQuery, state: FSMContext):
    """Skip description input"""
    parts = callback.data.split("_")
    lang = parts[3]  # ru or uz
    menu_item_id = int(parts[4])
    
    if lang == "ru":
        # Skip RU, go to UZ
        get_temp_data(callback.from_user.id)["description_ru"] = ""
        
        await state.set_state(AdminStates.menu_item_description_uz)
        
        text = f"✏️ ИЗМЕНИТЬ ОПИСАНИЕ\n"
        text += "═══════════════════════════════════════\n\n"
        text += "Описание (RU): ⏭️ Пропущено\n\n"
        text += "Введите описание на УЗБЕКСКОМ (или пропустите):"
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=f"menu_skip_desc_uz_{menu_item_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
        ])
        
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        
        await callback.answer()
    else:
        # Skip UZ, save and return
        temp_data = get_temp_data(callback.from_user.id)
        description_ru = temp_data.get("description_ru", "")
        
        async with AsyncSessionLocal() as session:
            await MenuService.update_menu_item(
                session,
                menu_item_id,
                description_ru=description_ru,
                description_uz=""
            )
        
        clear_temp_data(callback.from_user.id)
        await state.set_state(AdminStates.menu_item_editing)
        
        text, markup = await build_menu_item_edit_view(callback.from_user.id, menu_item_id)
        text = f"✅ Описание обновлено!\n\n{text}"
        
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        
        await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 6: ADD TEXT CONTENT
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_add_text_"))
async def start_add_text_content(callback: CallbackQuery, state: FSMContext):
    """Start adding text content (RU -> UZ)"""
    menu_item_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminStates.menu_add_text_ru)
    await state.update_data(menu_item_id=menu_item_id, message_id=callback.message.message_id)
    clear_temp_data(callback.from_user.id)
    
    text = (
        "➕ ДОБАВИТЬ ТЕКСТ\n"
        "═══════════════════════════════════════\n\n"
        "Введите текст на РУССКОМ языке:\n"
        "(Можно несколько абзацев)"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.message(StateFilter(AdminStates.menu_add_text_ru))
async def process_text_ru(message: Message, state: FSMContext):
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    temp = get_temp_data(message.from_user.id)
    temp["text_ru"] = message.text.strip()
    
    try:
        await message.delete()
    except:
        pass
    
    await state.set_state(AdminStates.menu_add_text_uz)
    text = (
        "➕ ДОБАВИТЬ ТЕКСТ\n"
        "═══════════════════════════════════════\n\n"
        "Текст (RU): ✅ Сохранён\n\n"
        "Введите текст на УЗБЕКСКОМ языке:\n"
        "(Можно несколько абзацев)"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.message(StateFilter(AdminStates.menu_add_text_uz))
async def finalize_text_content(message: Message, state: FSMContext):
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    temp = get_temp_data(message.from_user.id)
    text_ru = temp.get("text_ru", "")
    text_uz = message.text.strip()
    
    async with AsyncSessionLocal() as session:
        content = await MenuService.add_text_content(session, menu_item_id, text_ru, text_uz)
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="ADD_MENU_TEXT_CONTENT",
            entity_type="MENU_CONTENT",
            entity_id=content.id,
            details={"menu_item_id": menu_item_id}
        )
    try:
        await message.delete()
    except:
        pass
    clear_temp_data(message.from_user.id)
    await state.set_state(AdminStates.menu_item_editing)
    text, markup = await build_menu_item_edit_view(message.from_user.id, menu_item_id)
    text = "✅ Текст добавлен!\n\n" + text
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 7: ADD PHOTO/PDF/AUDIO CONTENT
# ═══════════════════════════════════════════════════════════════════════════

async def prompt_photo_caption(message, message_id, menu_item_id, step_text):
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=f"menu_skip_photo_caption_ru_{menu_item_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text=step_text,
        reply_markup=markup
    )


@router.callback_query(F.data.startswith("menu_add_photo_"))
async def start_add_photo(callback: CallbackQuery, state: FSMContext):
    menu_item_id = int(callback.data.split("_")[-1])
    await state.set_state(AdminStates.menu_add_photo)
    await state.update_data(menu_item_id=menu_item_id, message_id=callback.message.message_id)
    clear_temp_data(callback.from_user.id)
    text = (
        "➕ ДОБАВИТЬ PHOTO\n"
        "═══════════════════════════════════════\n\n"
        "Отправьте фото (JPG/PNG/WebP, до 10MB):"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.message(StateFilter(AdminStates.menu_add_photo))
async def handle_photo_upload(message: Message, state: FSMContext):
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    if not message.photo:
        await message.reply("❌ Пожалуйста, отправьте фото.")
        return
    file_id = message.photo[-1].file_id
    temp = get_temp_data(message.from_user.id)
    temp["photo_file_id"] = file_id
    try:
        await message.delete()
    except:
        pass
    await state.set_state(AdminStates.menu_add_photo_caption_ru)
    text = (
        "➕ ДОБАВИТЬ PHOTO\n"
        "═══════════════════════════════════════\n\n"
        "Фото загружено: ✅\n\n"
        "Введите подпись на РУССКОМ (или пропустите):"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=f"menu_skip_photo_caption_ru_{menu_item_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.message(StateFilter(AdminStates.menu_add_photo_caption_ru))
async def process_photo_caption_ru(message: Message, state: FSMContext):
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    temp = get_temp_data(message.from_user.id)
    temp["caption_ru"] = message.text.strip()
    try:
        await message.delete()
    except:
        pass
    await state.set_state(AdminStates.menu_add_photo_caption_uz)
    text = (
        "➕ ДОБАВИТЬ PHOTO\n"
        "═══════════════════════════════════════\n\n"
        "Подпись (RU): ✅\n\n"
        "Введите подпись на УЗБЕКСКОМ (или пропустите):"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=f"menu_skip_photo_caption_uz_{menu_item_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
    ])
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.message(StateFilter(AdminStates.menu_add_photo_caption_uz))
async def finalize_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    menu_item_id = data.get("menu_item_id")
    message_id = data.get("message_id")
    temp = get_temp_data(message.from_user.id)
    caption_ru = temp.get("caption_ru")
    caption_uz = message.text.strip()
    file_id = temp.get("photo_file_id")
    async with AsyncSessionLocal() as session:
        content = await MenuService.add_photo_content(session, menu_item_id, file_id, caption_ru, caption_uz)
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="ADD_MENU_PHOTO",
            entity_type="MENU_CONTENT",
            entity_id=content.id,
            details={"menu_item_id": menu_item_id}
        )
    try:
        await message.delete()
    except:
        pass
    clear_temp_data(message.from_user.id)
    await state.set_state(AdminStates.menu_item_editing)
    text, markup = await build_menu_item_edit_view(message.from_user.id, menu_item_id)
    text = "✅ Фото добавлено!\n\n" + text
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.callback_query(F.data.startswith("menu_skip_photo_caption_"))
async def skip_photo_caption(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    lang = parts[4]
    menu_item_id = int(parts[5])
    await state.update_data(menu_item_id=menu_item_id)
    data = await state.get_data()
    message_id = data.get("message_id", callback.message.message_id)
    temp = get_temp_data(callback.from_user.id)
    if lang == "ru":
        temp["caption_ru"] = None
        await state.set_state(AdminStates.menu_add_photo_caption_uz)
        text = (
            "➕ ДОБАВИТЬ PHOTO\n"
            "═══════════════════════════════════════\n\n"
            "Подпись (RU): ⏭️ Пропущено\n\n"
            "Введите подпись на УЗБЕКСКОМ (или пропустите):"
        )
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Пропустить", callback_data=f"menu_skip_photo_caption_uz_{menu_item_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"menu_edit_{menu_item_id}")]
        ])
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()
    else:
        temp["caption_uz"] = None
        file_id = temp.get("photo_file_id")
        caption_ru = temp.get("caption_ru")
        async with AsyncSessionLocal() as session:
            content = await MenuService.add_photo_content(session, menu_item_id, file_id, caption_ru, None)
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="ADD_MENU_PHOTO",
                entity_type="MENU_CONTENT",
                entity_id=content.id,
                details={"menu_item_id": menu_item_id}
            )
        clear_temp_data(callback.from_user.id)
        await state.set_state(AdminStates.menu_item_editing)
        text, markup = await build_menu_item_edit_view(callback.from_user.id, menu_item_id)
        text = "✅ Фото добавлено!\n\n" + text
        try:
            await callback.message.edit_text(text, reply_markup=markup)
        except TelegramBadRequest as e:
            if "message is not modified" not in str(e):
                raise
        await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# DELETE CONTENT/BUTTON
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_del_content_"))
async def delete_content(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    content_id = int(parts[3])
    menu_item_id = int(parts[4])
    async with AsyncSessionLocal() as session:
        success = await MenuService.delete_content(session, content_id)
        if success:
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="DELETE_MENU_CONTENT",
                entity_type="MENU_CONTENT",
                entity_id=content_id,
                details={"menu_item_id": menu_item_id}
            )
    text, markup = await build_menu_item_edit_view(callback.from_user.id, menu_item_id)
    text = "✅ Контент удалён!\n\n" + text
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer("✅ Контент удалён")


@router.callback_query(F.data.startswith("menu_del_button_"))
async def delete_button(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    button_id = int(parts[3])
    menu_item_id = int(parts[4])
    async with AsyncSessionLocal() as session:
        success = await MenuService.delete_button(session, button_id)
        if success:
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="DELETE_MENU_BUTTON",
                entity_type="MENU_BUTTON",
                entity_id=button_id,
                details={"menu_item_id": menu_item_id}
            )
    text, markup = await build_menu_item_edit_view(callback.from_user.id, menu_item_id)
    text = "✅ Кнопка удалена!\n\n" + text
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer("✅ Кнопка удалена")


# ═══════════════════════════════════════════════════════════════════════════
# DELETE MENU ITEM
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_delete_"))
async def confirm_delete_menu_item(callback: CallbackQuery, state: FSMContext):
    menu_item_id = int(callback.data.split("_")[2])
    async with AsyncSessionLocal() as session:
        menu_item = await MenuService.get_menu_item_by_id(session, menu_item_id)
    if not menu_item:
        await callback.answer("❌ Пункт меню не найден", show_alert=True)
        return
    text = (
        f"❌ УДАЛИТЬ ПУНКТ МЕНЮ?\n"
        f"═══════════════════════════════════════\n\n"
        f"Вы уверены, что хотите удалить:\n"
        f"{menu_item.icon or '📝'} {menu_item.name_ru}\n\n"
        f"⚠️ Это действие необратимо!\n"
        f"Весь контент и кнопки также будут удалены."
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"menu_delete_confirm_{menu_item_id}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu_manage")
        ]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.callback_query(F.data.startswith("menu_delete_confirm_"))
async def execute_delete_menu_item(callback: CallbackQuery, state: FSMContext):
    menu_item_id = int(callback.data.split("_")[3])
    async with AsyncSessionLocal() as session:
        success = await MenuService.delete_menu_item(session, menu_item_id)
        if success:
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="DELETE_MENU_ITEM",
                entity_type="MENU_ITEM",
                entity_id=menu_item_id
            )
    text, markup = await build_menu_management_view(callback.from_user.id)
    text = "✅ Пункт меню удалён!\n\n" + text
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer("✅ Удалено")


# ═══════════════════════════════════════════════════════════════════════════
# FEATURE 10: CREATE NEW MENU ITEM
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "menu_add_new")
async def start_create_menu_item(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.menu_create_name_ru)
    await state.update_data(message_id=callback.message.message_id)
    clear_temp_data(callback.from_user.id)
    text = (
        "➕ ДОБАВИТЬ НОВЫЙ ПУНКТ МЕНЮ\n"
        "═══════════════════════════════════════\n\n"
        "Шаг 1/3: Введите название на РУССКОМ:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu_manage")]
    ])
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise
    await callback.answer()


@router.message(StateFilter(AdminStates.menu_create_name_ru))
async def process_create_name_ru(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    temp = get_temp_data(message.from_user.id)
    temp["name_ru"] = message.text.strip()
    try:
        await message.delete()
    except:
        pass
    await state.set_state(AdminStates.menu_create_name_uz)
    text = (
        "➕ ДОБАВИТЬ НОВЫЙ ПУНКТ МЕНЮ\n"
        "═══════════════════════════════════════\n\n"
        f"Название (RU): ✅ {temp['name_ru']}\n\n"
        "Шаг 2/3: Введите название на УЗБЕКСКОМ:"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu_manage")]
    ])
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.message(StateFilter(AdminStates.menu_create_name_uz))
async def process_create_name_uz(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    temp = get_temp_data(message.from_user.id)
    temp["name_uz"] = message.text.strip()
    try:
        await message.delete()
    except:
        pass
    await state.set_state(AdminStates.menu_create_icon)
    text = (
        "➕ ДОБАВИТЬ НОВЫЙ ПУНКТ МЕНЮ\n"
        "═══════════════════════════════════════\n\n"
        f"Название (RU): ✅ {temp['name_ru']}\n"
        f"Название (UZ): ✅ {temp['name_uz']}\n\n"
        "Шаг 3/3: Введите иконку (эмодзи):"
    )
    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu_manage")]
    ])
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


@router.message(StateFilter(AdminStates.menu_create_icon))
async def finalize_create_menu_item(message: Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("message_id")
    temp = get_temp_data(message.from_user.id)
    icon = message.text.strip()
    name_ru = temp.get("name_ru")
    name_uz = temp.get("name_uz")
    async with AsyncSessionLocal() as session:
        menu_item = await MenuService.create_menu_item(
            session,
            name_ru=name_ru,
            name_uz=name_uz,
            icon=icon
        )
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="CREATE_MENU_ITEM",
            entity_type="MENU_ITEM",
            entity_id=menu_item.id,
            details={"name_ru": name_ru, "name_uz": name_uz, "icon": icon}
        )
    try:
        await message.delete()
    except:
        pass
    clear_temp_data(message.from_user.id)
    await state.set_state(AdminStates.menu_management)
    text, markup = await build_menu_management_view(message.from_user.id)
    text = f"✅ Новый пункт меню создан: {icon} {name_ru}\n\n" + text
    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=text,
            reply_markup=markup
        )
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e):
            raise


# ═══════════════════════════════════════════════════════════════════════════
# STUB HANDLERS FOR OTHER CONTENT TYPES (PDF, AUDIO, LOCATION, BUTTON)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("menu_add_pdf_"))
async def placeholder_add_pdf(callback: CallbackQuery):
    await callback.answer("📎 Функция добавления PDF будет реализована далее", show_alert=True)


@router.callback_query(F.data.startswith("menu_add_audio_"))
async def placeholder_add_audio(callback: CallbackQuery):
    await callback.answer("🎵 Функция добавления Аудио будет реализована далее", show_alert=True)


@router.callback_query(F.data.startswith("menu_add_location_"))
async def placeholder_add_location(callback: CallbackQuery):
    await callback.answer("📍 Функция добавления Локации будет реализована далее", show_alert=True)


@router.callback_query(F.data.startswith("menu_add_button_"))
async def placeholder_add_button(callback: CallbackQuery):
    await callback.answer("➕ Функция добавления Кнопки будет реализована далее", show_alert=True)

