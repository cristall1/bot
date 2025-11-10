"""
Admin Dynamic Menu Handlers - ONE MESSAGE SYSTEM
Управление главным меню, фильтрами, категориями
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from database import AsyncSessionLocal
from services.dynamic_menu_service import DynamicMenuService, MenuFilterService, MenuFilterOptionService
from services.category_service import CategoryService
from services.admin_log_service import AdminLogService
from states import AdminStates
from utils.logger import logger

router = Router()

# State storage
admin_menu_state = {}  # {admin_id: {message_id: int, context: dict}}


async def build_menu_list_view() -> tuple[str, InlineKeyboardMarkup]:
    """Список всех пунктов меню"""
    async with AsyncSessionLocal() as session:
        menus = await DynamicMenuService.get_all_menus(session, active_only=False)
    
    text = "🔧 УПРАВЛЕНИЕ ГЛАВНЫМ МЕНЮ\n"
    text += "═══════════════════════════════════════\n\n"
    
    keyboard = []
    
    for menu in menus:
        status = "✅" if menu.is_active else "❌"
        icon = menu.icon or "📝"
        text += f"{status} {icon} {menu.name_ru}\n"
        
        keyboard.append([
            InlineKeyboardButton(text=f"✏️ {menu.name_ru[:15]}", callback_data=f"adm_menu_edit_{menu.id}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"adm_menu_del_{menu.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="➕ Добавить меню", callback_data="adm_menu_add")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")])
    
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


async def build_menu_edit_view(menu_id: int) -> tuple[str, InlineKeyboardMarkup]:
    """Редактирование пункта меню"""
    async with AsyncSessionLocal() as session:
        menu = await DynamicMenuService.get_menu_by_id(session, menu_id)
        if not menu:
            return "❌ Меню не найдено", InlineKeyboardMarkup(inline_keyboard=[])
        
        filters = await MenuFilterService.get_filters_for_menu(session, menu_id, active_only=False)
        categories = await CategoryService.get_categories_by_menu(session, menu_id, active_only=False)
    
    status = "✅ ON" if menu.is_active else "❌ OFF"
    
    text = f"✏️ РЕДАКТИРОВАНИЕ: {menu.name_ru}\n"
    text += "═══════════════════════════════════════\n\n"
    text += f"📝 NAME (RU): {menu.name_ru}\n"
    text += f"📝 NAME (UZ): {menu.name_uz}\n"
    text += f"🔄 STATUS: {status}\n\n"
    
    text += "🔍 ФИЛЬТРЫ:\n"
    if filters:
        for f in filters:
            text += f"  • {f.name_ru} ({len(f.options)} опций)\n"
    else:
        text += "  (нет фильтров)\n"
    text += "\n"
    
    text += "📚 КАТЕГОРИИ:\n"
    if categories:
        for c in categories:
            text += f"  • {c.icon or ''} {c.name_ru}\n"
    else:
        text += "  (нет категорий)\n"
    
    keyboard = [
        [
            InlineKeyboardButton(text="✏️ Изменить имя (RU)", callback_data=f"adm_menu_name_ru_{menu_id}"),
            InlineKeyboardButton(text="✏️ Изменить имя (UZ)", callback_data=f"adm_menu_name_uz_{menu_id}")
        ],
        [
            InlineKeyboardButton(text=f"🔄 Toggle {status}", callback_data=f"adm_menu_toggle_{menu_id}")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить фильтр", callback_data=f"adm_filter_add_{menu_id}")
        ],
        [
            InlineKeyboardButton(text="➕ Добавить категорию", callback_data=f"adm_cat_add_{menu_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="adm_menu_list")
        ]
    ]
    
    return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "admin_dynamic_menu")
async def show_menu_management(callback: CallbackQuery, state: FSMContext):
    """Показать управление меню"""
    await state.set_state(AdminStates.menu_management)
    
    text, markup = await build_menu_list_view()
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    await callback.answer()
    logger.info(f"[AdminDynamicMenu] 👤 Admin {callback.from_user.id} открыл управление меню")


@router.callback_query(F.data.startswith("adm_menu_edit_"))
async def edit_menu(callback: CallbackQuery):
    """Редактировать меню"""
    menu_id = int(callback.data.split("_")[3])
    
    text, markup = await build_menu_edit_view(menu_id)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    await callback.answer()


@router.callback_query(F.data.startswith("adm_menu_toggle_"))
async def toggle_menu(callback: CallbackQuery):
    """Переключить статус меню"""
    menu_id = int(callback.data.split("_")[3])
    
    async with AsyncSessionLocal() as session:
        new_status = await DynamicMenuService.toggle_menu(session, menu_id)
        
        await AdminLogService.log_action(
            session,
            admin_id=callback.from_user.id,
            action="TOGGLE_MENU",
            entity_type="MAIN_MENU",
            entity_id=menu_id,
            details={"new_status": new_status}
        )
    
    text, markup = await build_menu_edit_view(menu_id)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    status_text = "ON" if new_status else "OFF"
    await callback.answer(f"✅ Статус: {status_text}")


@router.callback_query(F.data.startswith("adm_menu_del_"))
async def delete_menu(callback: CallbackQuery):
    """Удалить меню"""
    menu_id = int(callback.data.split("_")[3])
    
    async with AsyncSessionLocal() as session:
        success = await DynamicMenuService.delete_menu(session, menu_id)
        
        if success:
            await AdminLogService.log_action(
                session,
                admin_id=callback.from_user.id,
                action="DELETE_MENU",
                entity_type="MAIN_MENU",
                entity_id=menu_id
            )
    
    text, markup = await build_menu_list_view()
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    await callback.answer("✅ Меню удалено")


@router.callback_query(F.data == "adm_menu_list")
async def back_to_menu_list(callback: CallbackQuery):
    """Вернуться к списку меню"""
    text, markup = await build_menu_list_view()
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    await callback.answer()


@router.callback_query(F.data.startswith("adm_filter_add_"))
async def start_add_filter(callback: CallbackQuery, state: FSMContext):
    """Начать добавление фильтра"""
    menu_id = int(callback.data.split("_")[3])
    
    await state.update_data(menu_id=menu_id, message_id=callback.message.message_id)
    await state.set_state(AdminStates.adding_filter_name_ru)
    
    text = "➕ ДОБАВЛЕНИЕ ФИЛЬТРА\n"
    text += "═══════════════════════════════════════\n\n"
    text += "Шаг 1/3: Введите имя фильтра (RU):\n"
    text += "(например: Гражданство)"
    
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=f"adm_menu_edit_{menu_id}")]]
    
    try:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    await callback.answer()


@router.message(AdminStates.adding_filter_name_ru)
async def receive_filter_name_ru(message: Message, state: FSMContext):
    """Получить имя фильтра (RU)"""
    data = await state.get_data()
    await state.update_data(filter_name_ru=message.text)
    await state.set_state(AdminStates.adding_filter_name_uz)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    text = "➕ ДОБАВЛЕНИЕ ФИЛЬТРА\n"
    text += "═══════════════════════════════════════\n\n"
    text += f"✅ Имя (RU): {message.text}\n\n"
    text += "Шаг 2/3: Введите имя фильтра (UZ):\n"
    text += "(например: Fuqarolik)"
    
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=f"adm_menu_edit_{data['menu_id']}")]]
    
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['message_id'],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except:
        pass


@router.message(AdminStates.adding_filter_name_uz)
async def receive_filter_name_uz(message: Message, state: FSMContext):
    """Получить имя фильтра (UZ)"""
    data = await state.get_data()
    await state.update_data(filter_name_uz=message.text)
    await state.set_state(AdminStates.adding_filter_options)
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    text = "➕ ДОБАВЛЕНИЕ ФИЛЬТРА\n"
    text += "═══════════════════════════════════════\n\n"
    text += f"✅ Имя (RU): {data['filter_name_ru']}\n"
    text += f"✅ Имя (UZ): {message.text}\n\n"
    text += "Шаг 3/3: Введите варианты через запятую (RU|UZ):\n"
    text += "(например: Узбекистан|O'zbekiston, Россия|Rossiya)"
    
    keyboard = [[InlineKeyboardButton(text="❌ Отмена", callback_data=f"adm_menu_edit_{data['menu_id']}")]]
    
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['message_id'],
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except:
        pass


@router.message(AdminStates.adding_filter_options)
async def receive_filter_options(message: Message, state: FSMContext):
    """Получить опции фильтра"""
    data = await state.get_data()
    
    # Удаляем сообщение пользователя
    try:
        await message.delete()
    except:
        pass
    
    # Создаем фильтр и опции
    async with AsyncSessionLocal() as session:
        filter_obj = await MenuFilterService.create_filter(
            session,
            main_menu_id=data['menu_id'],
            name_ru=data['filter_name_ru'],
            name_uz=data['filter_name_uz']
        )
        
        # Парсим опции
        options_text = message.text.split(",")
        for opt_text in options_text:
            opt_text = opt_text.strip()
            if "|" in opt_text:
                opt_ru, opt_uz = opt_text.split("|")
                await MenuFilterOptionService.create_option(
                    session,
                    filter_id=filter_obj.id,
                    name_ru=opt_ru.strip(),
                    name_uz=opt_uz.strip()
                )
        
        await AdminLogService.log_action(
            session,
            admin_id=message.from_user.id,
            action="CREATE_FILTER",
            entity_type="MENU_FILTER",
            entity_id=filter_obj.id
        )
    
    await state.clear()
    
    # Показываем меню
    text, markup = await build_menu_edit_view(data['menu_id'])
    
    try:
        await message.bot.edit_message_text(
            text=text,
            chat_id=message.chat.id,
            message_id=data['message_id'],
            reply_markup=markup
        )
    except:
        pass
