"""
Admin Category Management Handlers - New Admin Panel
Language: Russian (logs) / Implementation: English comments
Framework: aiogram 3.x
"""

from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from database import AsyncSessionLocal
from services.category_service import CategoryService
from services.user_service import UserService
from states import AdminStates
from utils.logger import logger

router = Router()


async def render_category_dashboard(message_obj, state: FSMContext, *, edit: bool = False):
    """
    Render the main category dashboard view
    """
    async with AsyncSessionLocal() as session:
        await CategoryService.ensure_default_categories(session)
        categories = await CategoryService.get_root_categories(session, active_only=False)
        keyboard = get_category_management_keyboard(categories)
        text = (
            "УПРАВЛЕНИЕ КАТЕГОРИЯМИ\n"
            "═══════════════════════════════════════\n\n"
            f"Всего категорий: {len(categories)}\n\n"
            "Выберите категорию для редактирования или добавьте новую:"
        )
    
    if edit:
        await message_obj.edit_text(text, reply_markup=keyboard)
    else:
        await message_obj.answer(text, reply_markup=keyboard)
    
    await state.set_state(AdminStates.category_management)
    return keyboard


def get_category_management_keyboard(categories: list, include_add_button: bool = True):
    """
    Создать клавиатуру управления категориями
    Create category management keyboard
    
    Layout:
    [on/off] [📚 Talim]           [✏️]
    [on/off] [🚚 Dostavka]        [✏️]
    ...
    [➕ Добавить категорию]
    [🔙 Назад]
    """
    keyboard_buttons = []
    
    for category in categories:
        # Иконка вкл/выкл toggle status icon
        status_icon = "✅" if category.is_active else "❌"
        toggle_button = InlineKeyboardButton(
            text=status_icon,
            callback_data=f"admin_cat_toggle_{category.id}"
        )
        
        # Название категории category name
        name_button = InlineKeyboardButton(
            text=f"{category.icon or ''} {category.name_ru}".strip(),
            callback_data=f"admin_cat_view_{category.id}"
        )
        
        # Кнопка редактирования edit button
        edit_button = InlineKeyboardButton(
            text="✏️ Edit",
            callback_data=f"admin_cat_edit_{category.id}"
        )
        
        keyboard_buttons.append([toggle_button, name_button, edit_button])
    
    if include_add_button:
        keyboard_buttons.append([
            InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_cat_add")
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


@router.callback_query(F.data == "admin_category_menu")
async def show_category_management(callback: CallbackQuery, state: FSMContext):
    """
    Показать главное меню управления категориями
    Show main category management menu
    """
    try:
        logger.info(f"[admin_category_menu] Открытие меню управления категориями admin_id={callback.from_user.id}")
        
        async with AsyncSessionLocal() as session:
            # Убедиться, что базовые категории созданы Ensure default categories exist
            await CategoryService.ensure_default_categories(session)
            
            # Получить все корневые категории Get all root categories
            categories = await CategoryService.get_root_categories(session, active_only=False)
            
            keyboard = get_category_management_keyboard(categories)
            
            await callback.message.edit_text(
                "УПРАВЛЕНИЕ КАТЕГОРИЯМИ\n"
                "═══════════════════════════════════════\n\n"
                f"Всего категорий: {len(categories)}\n\n"
                "Выберите категорию для редактирования или добавьте новую:",
                reply_markup=keyboard
            )
            
        await state.set_state(AdminStates.category_management)
        await callback.answer()
        logger.info(f"[admin_category_menu] ✅ Меню категорий показано")
    except Exception as e:
        logger.error(f"[admin_category_menu] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки категорий", show_alert=True)


@router.callback_query(F.data.startswith("admin_cat_toggle_"))
async def toggle_category(callback: CallbackQuery, state: FSMContext):
    """
    Переключить активность категории (on/off)
    Toggle category active state
    """
    try:
        category_id = int(callback.data.split("_")[-1])
        logger.info(f"[admin_cat_toggle] Переключение категории {category_id}")
        
        async with AsyncSessionLocal() as session:
            # Toggle category toggle категорию
            category = await CategoryService.toggle_category(session, category_id)
            
            if not category:
                await callback.answer("❌ Категория не найдена", show_alert=True)
                return
            
            status = "включена" if category.is_active else "выключена"
            await callback.answer(f"✅ Категория {status}")
            
            # Обновить клавиатуру Refresh keyboard
            categories = await CategoryService.get_root_categories(session, active_only=False)
            keyboard = get_category_management_keyboard(categories)
            
            try:
                await callback.message.edit_reply_markup(reply_markup=keyboard)
            except TelegramBadRequest as e:
                # If message is not modified (keyboard is the same), just ignore
                if "message is not modified" in str(e):
                    logger.info(f"[admin_cat_toggle] ⚠️ Клавиатура не изменилась, пропускаем обновление")
                else:
                    raise
            
        logger.info(f"[admin_cat_toggle] ✅ Категория {category_id} переключена: {status}")
    except Exception as e:
        logger.error(f"[admin_cat_toggle] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка переключения", show_alert=True)


@router.callback_query(F.data.startswith("admin_cat_view_"))
async def view_category(callback: CallbackQuery, state: FSMContext):
    """
    Просмотр категории и её подкатегорий
    View category and its subcategories
    """
    try:
        category_id = int(callback.data.split("_")[-1])
        logger.info(f"[admin_cat_view] Просмотр категории {category_id}")
        
        async with AsyncSessionLocal() as session:
            category = await CategoryService.get_category(session, category_id)
            
            if not category:
                await callback.answer("❌ Категория не найдена", show_alert=True)
                return
            
            # Получить подкатегории Get subcategories
            subcategories = await CategoryService.get_subcategories(session, category_id, active_only=False)
            
            # Построить текст Build text
            status = "✅ Включена" if category.is_active else "❌ Выключена"
            text = (
                f"Настройка Категории \"{category.name_ru}\"\n"
                f"═══════════════════════════════════════\n\n"
                f"Статус: {status}\n"
                f"Ключ: {category.key}\n"
                f"Иконка: {category.icon or 'нет'}\n"
            )
            
            if category.text_content_ru:
                text += f"\nТекст (RU): {category.text_content_ru[:100]}...\n"
            
            if subcategories:
                text += f"\nПодкатегорий: {len(subcategories)}\n"
            
            # Построить клавиатуру Build keyboard
            keyboard_buttons = []
            
            # Кнопки редактирования Edit buttons
            keyboard_buttons.append([
                InlineKeyboardButton(text="📝 Изменить имя", callback_data=f"admin_cat_edit_name_{category_id}")
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(text="📄 Изменить текст", callback_data=f"admin_cat_edit_text_{category_id}")
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(text="🖼️ Медиа", callback_data=f"admin_cat_edit_media_{category_id}")
            ])
            
            # Подкатегории Subcategories
            if subcategories:
                keyboard_buttons.append([
                    InlineKeyboardButton(text="📂 Управление подкатегориями", callback_data=f"admin_cat_subs_{category_id}")
                ])
            else:
                keyboard_buttons.append([
                    InlineKeyboardButton(text="➕ Добавить подкатегорию", callback_data=f"admin_cat_add_sub_{category_id}")
                ])
            
            keyboard_buttons.append([
                InlineKeyboardButton(text="🔙 Назад", callback_data="admin_category_menu")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            await callback.message.edit_text(text, reply_markup=keyboard)
            await state.update_data(current_category_id=category_id)
            
        await callback.answer()
        logger.info(f"[admin_cat_view] ✅ Категория {category_id} показана")
    except Exception as e:
        logger.error(f"[admin_cat_view] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки категории", show_alert=True)


@router.callback_query(F.data.startswith("admin_cat_edit_"))
async def edit_category(callback: CallbackQuery, state: FSMContext):
    """
    Начать редактирование категории
    Start editing category
    """
    try:
        parts = callback.data.split("_")
        category_id = int(parts[-1])
        edit_type = parts[3]  # name, text, media
        
        logger.info(f"[admin_cat_edit] Редактирование категории {category_id}, тип: {edit_type}")
        
        await state.update_data(current_category_id=category_id, edit_type=edit_type)
        
        if edit_type == "name":
            await callback.message.edit_text(
                "📝 ИЗМЕНЕНИЕ ИМЕНИ КАТЕГОРИИ\n"
                "═══════════════════════════════════════\n\n"
                "Введите новое имя категории (на русском):",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_cat_view_{category_id}")]
                ])
            )
            await state.set_state(AdminStates.category_name_input)
            
        elif edit_type == "text":
            await callback.message.edit_text(
                "📄 ИЗМЕНЕНИЕ ТЕКСТА КАТЕГОРИИ\n"
                "═══════════════════════════════════════\n\n"
                "Введите новый текст (на русском):",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_cat_view_{category_id}")]
                ])
            )
            await state.set_state(AdminStates.category_text_input)
            
        elif edit_type == "media":
            # Показать меню медиа Show media menu
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🖼️ Загрузить фото", callback_data=f"admin_cat_media_photo_{category_id}")],
                [InlineKeyboardButton(text="🎵 Загрузить аудио", callback_data=f"admin_cat_media_audio_{category_id}")],
                [InlineKeyboardButton(text="📎 Загрузить PDF", callback_data=f"admin_cat_media_pdf_{category_id}")],
                [InlineKeyboardButton(text="🔗 Добавить ссылку", callback_data=f"admin_cat_media_link_{category_id}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_cat_view_{category_id}")]
            ])
            await callback.message.edit_text(
                "🖼️ УПРАВЛЕНИЕ МЕДИА\n"
                "═══════════════════════════════════════\n\n"
                "Выберите тип медиа:",
                reply_markup=keyboard
            )
        
        await callback.answer()
    except Exception as e:
        logger.error(f"[admin_cat_edit] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(AdminStates.category_name_input)
async def process_category_name_input(message: Message, state: FSMContext):
    """
    Обработка ввода нового имени категории
    Process new category name input
    """
    try:
        data = await state.get_data()
        category_id = data.get("current_category_id")
        
        if not category_id:
            await message.answer("❌ Ошибка: категория не выбрана")
            return
        
        new_name = message.text.strip()
        logger.info(f"[category_name_input] Обновление имени категории {category_id}: {new_name}")
        
        async with AsyncSessionLocal() as session:
            category = await CategoryService.update_category(
                session,
                category_id,
                name_ru=new_name,
                name_uz=new_name  # For now, use same name for both languages
            )
            
            if not category:
                await message.answer("❌ Категория не найдена")
                return
            
            await message.answer(
                f"✅ Имя категории обновлено: {new_name}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К категории", callback_data=f"admin_cat_view_{category_id}")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin_category_menu")]
                ])
            )
            
        await state.set_state(AdminStates.category_management)
        logger.info(f"[category_name_input] ✅ Имя категории {category_id} обновлено")
    except Exception as e:
        logger.error(f"[category_name_input] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка обновления имени")


@router.message(AdminStates.category_text_input)
async def process_category_text_input(message: Message, state: FSMContext):
    """
    Обработка ввода нового текста категории
    Process new category text input
    """
    try:
        data = await state.get_data()
        category_id = data.get("current_category_id")
        
        if not category_id:
            await message.answer("❌ Ошибка: категория не выбрана")
            return
        
        new_text = message.text.strip()
        logger.info(f"[category_text_input] Обновление текста категории {category_id}")
        
        async with AsyncSessionLocal() as session:
            category = await CategoryService.update_category(
                session,
                category_id,
                text_content_ru=new_text,
                text_content_uz=new_text,  # For now, use same text for both languages
                content_type="TEXT"
            )
            
            if not category:
                await message.answer("❌ Категория не найдена")
                return
            
            await message.answer(
                f"✅ Текст категории обновлён",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К категории", callback_data=f"admin_cat_view_{category_id}")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin_category_menu")]
                ])
            )
            
        await state.set_state(AdminStates.category_management)
        logger.info(f"[category_text_input] ✅ Текст категории {category_id} обновлён")
    except Exception as e:
        logger.error(f"[category_text_input] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка обновления текста")


@router.callback_query(F.data.startswith("admin_cat_media_photo_"))
async def prepare_photo_upload(callback: CallbackQuery, state: FSMContext):
    """
    Подготовка к загрузке фото
    Prepare for photo upload
    """
    try:
        category_id = int(callback.data.split("_")[-1])
        await state.update_data(current_category_id=category_id, media_type="photo")
        
        await callback.message.edit_text(
            "🖼️ ЗАГРУЗКА ФОТО\n"
            "═══════════════════════════════════════\n\n"
            "Отправьте фото для категории:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_cat_edit_media_{category_id}")]
            ])
        )
        
        await state.set_state(AdminStates.category_photo_upload)
        await callback.answer()
    except Exception as e:
        logger.error(f"[prepare_photo_upload] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(AdminStates.category_photo_upload, F.photo)
async def process_photo_upload(message: Message, state: FSMContext):
    """
    Обработка загруженного фото
    Process uploaded photo
    """
    try:
        data = await state.get_data()
        category_id = data.get("current_category_id")
        
        if not category_id:
            await message.answer("❌ Ошибка: категория не выбрана")
            return
        
        photo_file_id = message.photo[-1].file_id
        logger.info(f"[category_photo_upload] Загрузка фото для категории {category_id}")
        
        async with AsyncSessionLocal() as session:
            category = await CategoryService.update_category(
                session,
                category_id,
                photo_file_id=photo_file_id,
                content_type="PHOTO"
            )
            
            if not category:
                await message.answer("❌ Категория не найдена")
                return
            
            await message.answer(
                "✅ Фото загружено",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 К категории", callback_data=f"admin_cat_view_{category_id}")],
                    [InlineKeyboardButton(text="🏠 Главное меню", callback_data="admin_category_menu")]
                ])
            )
            
        await state.set_state(AdminStates.category_management)
        logger.info(f"[category_photo_upload] ✅ Фото загружено для категории {category_id}")
    except Exception as e:
        logger.error(f"[category_photo_upload] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка загрузки фото")


@router.callback_query(F.data == "admin_cat_add")
async def start_add_category(callback: CallbackQuery, state: FSMContext):
    """
    Начать добавление новой категории
    Start adding new category
    """
    try:
        logger.info(f"[admin_cat_add] Начало добавления новой категории")
        
        await callback.message.edit_text(
            "➕ ДОБАВЛЕНИЕ НОВОЙ КАТЕГОРИИ\n"
            "═══════════════════════════════════════\n\n"
            "Шаг 1/3: Назовите имя категории:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_category_menu")]
            ])
        )
        
        await state.set_state(AdminStates.category_name_input)
        await state.update_data(is_new_category=True)
        await callback.answer()
    except Exception as e:
        logger.error(f"[admin_cat_add] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


def register_category_handlers(dp):
    """Register category management handlers"""
    dp.include_router(router)
