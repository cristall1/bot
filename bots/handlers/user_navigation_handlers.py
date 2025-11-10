"""
User Bot Navigation - ONE MESSAGE SYSTEM
Навигация по меню, фильтрам, категориям в одном сообщении
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from database import AsyncSessionLocal
from services.dynamic_menu_service import DynamicMenuService, MenuFilterService
from services.category_service import CategoryService
from utils.logger import logger

router = Router()

# State storage для навигации
user_nav_state = {}  # {user_id: {message_id: int, menu_id: int, filter_option_id: int, category_id: int}}


async def build_main_menu_keyboard(user_id: int, lang: str) -> ReplyKeyboardMarkup:
    """Построить главное меню (KEYBOARD)"""
    async with AsyncSessionLocal() as session:
        menus = await DynamicMenuService.get_all_menus(session, active_only=True)
    
    buttons = []
    for menu in menus:
        name = menu.name_ru if lang == "RU" else menu.name_uz
        icon = menu.icon or ""
        buttons.append([KeyboardButton(text=f"{icon} {name}".strip())])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


async def build_menu_view(menu_id: int, filter_option_id: int = None, lang: str = "RU") -> tuple[str, InlineKeyboardMarkup]:
    """Построить вид меню с фильтрами и категориями"""
    async with AsyncSessionLocal() as session:
        menu = await DynamicMenuService.get_menu_by_id(session, menu_id)
        if not menu:
            return "❌ Меню не найдено", InlineKeyboardMarkup(inline_keyboard=[])
        
        # Заголовок
        name = menu.name_ru if lang == "RU" else menu.name_uz
        icon = menu.icon or ""
        text = f"{icon} {name}\n"
        text += "═════════════════════════════════════\n\n"
        
        # Фильтры
        if menu.filters:
            text += "🔍 ФИЛЬТРЫ:\n"
            filter_buttons = []
            for filter_obj in menu.filters:
                if filter_obj.is_active and filter_obj.options:
                    row = []
                    for option in filter_obj.options:
                        if option.is_active:
                            opt_name = option.name_ru if lang == "RU" else option.name_uz
                            opt_icon = option.icon or ""
                            # Выделяем выбранный фильтр
                            if filter_option_id == option.id:
                                opt_name = f"✓ {opt_name}"
                            row.append(InlineKeyboardButton(
                                text=f"{opt_icon} {opt_name}".strip(),
                                callback_data=f"nav_filter_{menu_id}_{option.id}"
                            ))
                    if row:
                        filter_buttons.append(row)
            text += "\n"
        
        # Категории
        categories = await CategoryService.get_categories_by_menu(
            session, menu_id, filter_option_id=filter_option_id, parent_category_id=None
        )
        
        if categories:
            text += "📚 КАТЕГОРИИ:\n"
            category_buttons = []
            for cat in categories:
                cat_name = cat.name_ru if lang == "RU" else cat.name_uz
                cat_icon = cat.icon or ""
                category_buttons.append([InlineKeyboardButton(
                    text=f"{cat_icon} {cat_name}".strip(),
                    callback_data=f"nav_cat_{cat.id}"
                )])
        else:
            text += "📚 КАТЕГОРИИ:\nПока нет категорий.\n"
            category_buttons = []
        
        text += "\n═════════════════════════════════════"
        
        # Собираем клавиатуру
        keyboard = filter_buttons + category_buttons
        keyboard.append([InlineKeyboardButton(text="🔙 Главное меню", callback_data="nav_main")])
        
        return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


async def build_category_view(category_id: int, lang: str = "RU") -> tuple[str, InlineKeyboardMarkup]:
    """Построить вид категории с контентом"""
    async with AsyncSessionLocal() as session:
        category = await CategoryService.get_category(session, category_id)
        if not category:
            return "❌ Категория не найдена", InlineKeyboardMarkup(inline_keyboard=[])
        
        # Заголовок с breadcrumb
        cat_name = category.name_ru if lang == "RU" else category.name_uz
        cat_icon = category.icon or ""
        text = f"{cat_icon} {cat_name}\n"
        text += "═════════════════════════════════════\n\n"
        
        # Контент
        if category.content:
            text += "📄 СОДЕРЖИМОЕ:\n"
            for content in category.content:
                if content.content_type == "text":
                    content_text = content.text_ru if lang == "RU" else content.text_uz
                    text += f"{content_text}\n\n"
                elif content.content_type == "location":
                    loc_title = content.location_title_ru if lang == "RU" else content.location_title_uz
                    text += f"📍 {loc_title}\n"
                    text += f"Координаты: {content.latitude}, {content.longitude}\n\n"
        
        # Подкатегории
        if category.subcategories:
            text += "📂 ПОДКАТЕГОРИИ:\n"
            subcat_buttons = []
            for subcat in category.subcategories:
                if subcat.is_active:
                    subcat_name = subcat.name_ru if lang == "RU" else subcat.name_uz
                    subcat_icon = subcat.icon or ""
                    subcat_buttons.append([InlineKeyboardButton(
                        text=f"{subcat_icon} {subcat_name}".strip(),
                        callback_data=f"nav_cat_{subcat.id}"
                    )])
        else:
            subcat_buttons = []
        
        # Кнопки категории
        action_buttons = []
        if category.buttons:
            for btn in category.buttons:
                if btn.is_active:
                    btn_text = btn.text_ru if lang == "RU" else btn.text_uz
                    if btn.button_type == "url" and btn.action_data:
                        action_buttons.append([InlineKeyboardButton(
                            text=btn_text,
                            url=btn.action_data.get("url")
                        )])
                    elif btn.button_type == "next_category" and btn.action_data:
                        next_cat_id = btn.action_data.get("category_id")
                        action_buttons.append([InlineKeyboardButton(
                            text=btn_text,
                            callback_data=f"nav_cat_{next_cat_id}"
                        )])
        
        text += "\n═════════════════════════════════════"
        
        # Собираем клавиатуру
        keyboard = subcat_buttons + action_buttons
        
        # Кнопка назад
        if category.parent_category_id:
            keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"nav_cat_{category.parent_category_id}")])
        else:
            keyboard.append([InlineKeyboardButton(text="🔙 К меню", callback_data=f"nav_menu_{category.main_menu_id}")])
        
        return text, InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.message(F.text.contains("TALIM") | F.text.contains("Ta'lim"))
async def handle_talim_menu(message: Message):
    """Обработка кнопки TALIM"""
    user_id = message.from_user.id
    lang = "RU"  # TODO: получить из базы
    
    async with AsyncSessionLocal() as session:
        menus = await DynamicMenuService.get_all_menus(session)
        talim_menu = next((m for m in menus if "TALIM" in m.name_ru.upper()), None)
        
        if not talim_menu:
            await message.answer("❌ Меню TALIM не найдено")
            return
        
        text, markup = await build_menu_view(talim_menu.id, lang=lang)
        sent = await message.answer(text, reply_markup=markup)
        
        # Сохраняем state
        user_nav_state[user_id] = {
            'message_id': sent.message_id,
            'menu_id': talim_menu.id
        }


@router.message(F.text.contains("DOSTAVKA") | F.text.contains("Yetkazib"))
async def handle_dostavka_menu(message: Message):
    """Обработка кнопки DOSTAVKA"""
    user_id = message.from_user.id
    lang = "RU"
    
    async with AsyncSessionLocal() as session:
        menus = await DynamicMenuService.get_all_menus(session)
        dostavka_menu = next((m for m in menus if "DOSTAVKA" in m.name_ru.upper()), None)
        
        if not dostavka_menu:
            await message.answer("❌ Меню DOSTAVKA не найдено")
            return
        
        text, markup = await build_menu_view(dostavka_menu.id, lang=lang)
        sent = await message.answer(text, reply_markup=markup)
        
        user_nav_state[user_id] = {
            'message_id': sent.message_id,
            'menu_id': dostavka_menu.id
        }


@router.callback_query(F.data.startswith("nav_filter_"))
async def handle_filter_selection(callback: CallbackQuery):
    """Обработка выбора фильтра"""
    user_id = callback.from_user.id
    lang = "RU"
    
    parts = callback.data.split("_")
    menu_id = int(parts[2])
    filter_option_id = int(parts[3])
    
    # Обновляем вид меню с фильтром
    text, markup = await build_menu_view(menu_id, filter_option_id=filter_option_id, lang=lang)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    # Обновляем state
    if user_id in user_nav_state:
        user_nav_state[user_id]['filter_option_id'] = filter_option_id
    
    await callback.answer()


@router.callback_query(F.data.startswith("nav_cat_"))
async def handle_category_selection(callback: CallbackQuery):
    """Обработка выбора категории"""
    user_id = callback.from_user.id
    lang = "RU"
    
    category_id = int(callback.data.split("_")[2])
    
    # Показываем категорию
    text, markup = await build_category_view(category_id, lang=lang)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    # Обновляем state
    if user_id in user_nav_state:
        user_nav_state[user_id]['category_id'] = category_id
    
    await callback.answer()


@router.callback_query(F.data.startswith("nav_menu_"))
async def handle_back_to_menu(callback: CallbackQuery):
    """Вернуться к меню"""
    user_id = callback.from_user.id
    lang = "RU"
    
    menu_id = int(callback.data.split("_")[2])
    
    text, markup = await build_menu_view(menu_id, lang=lang)
    
    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise
    
    await callback.answer()


@router.callback_query(F.data == "nav_main")
async def handle_back_to_main(callback: CallbackQuery):
    """Вернуться в главное меню"""
    user_id = callback.from_user.id
    
    # Удаляем сообщение навигации
    try:
        await callback.message.delete()
    except:
        pass
    
    # Очищаем state
    if user_id in user_nav_state:
        del user_nav_state[user_id]
    
    await callback.answer("✅ Вернулись в главное меню")
