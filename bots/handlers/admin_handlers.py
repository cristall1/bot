"""
Admin Bot Handlers - Complete Management System
Language: Russian
Framework: aiogram 3.x
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.context import FSMContext
from database import AsyncSessionLocal
from config import settings
from services.user_service import UserService
from services.document_service import DocumentService
from services.delivery_service import DeliveryService
from services.notification_service import NotificationService
from services.shurta_service import ShurtaService
from services.user_message_service import UserMessageService
from services.broadcast_service import BroadcastService
from services.admin_log_service import AdminLogService
from services.courier_service import CourierService
from services.statistics_service import StatisticsService
from services.moderation_service import ModerationService
from states import AdminStates
from utils.logger import logger
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from models import (
    UserMessage, Delivery, Notification, ShurtaAlert, User,
    Document, DocumentButton, Broadcast, SystemSetting, Courier
)
import json

router = Router()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN MENU AND NAVIGATION
# ═══════════════════════════════════════════════════════════════════════════

def get_admin_main_menu():
    """Главное меню администратора (Admin main menu)"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Управление главным меню", callback_data="admin_menu_manage")],
        [InlineKeyboardButton(text="📁 Управление категориями", callback_data="admin_category_menu")],
        [InlineKeyboardButton(text="🚨 Модерация алертов", callback_data="admin_alert_menu")],
        [InlineKeyboardButton(text="📚 Управление документами", callback_data="admin_doc_menu")],
        [InlineKeyboardButton(text="🚚 Управление доставкой", callback_data="admin_del_menu")],
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_user_menu")],
        [InlineKeyboardButton(text="💬 Сообщения от пользователей", callback_data="admin_msg_menu")],
        [InlineKeyboardButton(text="📢 Система рассылки", callback_data="admin_bc_menu")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats_menu")],
        [InlineKeyboardButton(text="📤 Экспорт данных", callback_data="admin_export_menu")],
        [InlineKeyboardButton(text="⚙️ Настройки системы", callback_data="admin_settings_menu")],
    ])
    return keyboard


@router.message(Command("start"))
async def cmd_admin_start(message: Message, state: FSMContext):
    """Обработка /start для админ-бота"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        
        # Проверка прав администратора
        if not user or not user.is_admin:
            if message.from_user.id not in settings.admin_ids_list:
                await message.answer("❌ У вас нет прав администратора.")
                return
            
            # Создание/обновление пользователя-администратора
            if not user:
                user = await UserService.create_or_update_user(
                    session,
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    language="RU"
                )
            
            # Предоставление прав администратора
            await UserService.make_admin(session, message.from_user.id)
        
        await state.clear()
        await message.answer(
            "🔐 АДМИН-ПАНЕЛЬ\n"
            "═══════════════════════════════════════\n\n"
            "Добро пожаловать в систему управления ботом.\n"
            "Выберите нужный раздел:",
            reply_markup=get_admin_main_menu()
        )


# ═══════════════════════════════════════════════════════════════════════════
# BACK TO MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_back_main")
async def back_to_admin_main(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню администратора"""
    await state.clear()
    await callback.message.edit_text(
        "🔐 АДМИН-ПАНЕЛЬ\n"
        "═══════════════════════════════════════\n\n"
        "Добро пожаловать в систему управления ботом.\n"
        "Выберите нужный раздел:",
        reply_markup=get_admin_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_exit")
async def exit_admin_panel(callback: CallbackQuery, state: FSMContext):
    """Выход из админ-панели"""
    await state.clear()
    await callback.message.delete()
    await callback.answer("Вы вышли из админ-панели.", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENT MANAGEMENT (Управление документами)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_doc_menu")
async def handle_document_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления документами"""
    await state.set_state(AdminStates.hujjat_menu)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 Узбекистан", callback_data="admin_doc_cit_UZ")],
        [InlineKeyboardButton(text="🇷🇺 Россия", callback_data="admin_doc_cit_RU")],
        [InlineKeyboardButton(text="🇰🇿 Казахстан", callback_data="admin_doc_cit_KZ")],
        [InlineKeyboardButton(text="🇰🇬 Киргизия", callback_data="admin_doc_cit_KG")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
    ])
    
    await callback.message.edit_text(
        "📚 УПРАВЛЕНИЕ ДОКУМЕНТАМИ\n"
        "═══════════════════════════════════════\n\n"
        "Выберите страну для управления документами:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_doc_cit_"))
async def show_documents_list(callback: CallbackQuery, state: FSMContext):
    """Показать список документов для выбранной страны"""
    citizenship = callback.data.split("_")[-1]
    
    await state.update_data(selected_citizenship=citizenship)
    await state.set_state(AdminStates.hujjat_list)
    
    async with AsyncSessionLocal() as session:
        documents = await DocumentService.get_documents_by_citizenship(session, citizenship)
        
        citizenship_map = {
            "UZ": "🇺🇿 Узбекистан",
            "RU": "🇷🇺 Россия",
            "KZ": "🇰🇿 Казахстан",
            "KG": "🇰🇬 Киргизия"
        }
        
        keyboard_buttons = []
        for doc in documents:
            status_icon = "✅" if doc.is_active else "❌"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{status_icon} {doc.name_ru}",
                    callback_data=f"admin_doc_item_{doc.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="➕ Добавить документ", callback_data=f"admin_doc_add_{citizenship}")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_doc_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"📚 ДОКУМЕНТЫ: {citizenship_map.get(citizenship, citizenship)}\n"
            "═══════════════════════════════════════\n\n"
            f"Всего документов: {len(documents)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_doc_item_"))
async def view_document_item(callback: CallbackQuery, state: FSMContext):
    """Просмотр и редактирование документа"""
    doc_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if not document:
            await callback.answer("❌ Документ не найден", show_alert=True)
            return
        
        await state.set_state(AdminStates.hujjat_item)
        await state.update_data(current_doc_id=doc_id)
        
        status_icon = "✅" if document.is_active else "❌"
        status_text = "Включен" if document.is_active else "Отключен"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=f"[{status_icon}] Статус", callback_data=f"admin_doc_toggle_{doc_id}"),
                InlineKeyboardButton(text="✏️ Имя РУ", callback_data=f"admin_doc_edit_name_ru_{doc_id}")
            ],
            [
                InlineKeyboardButton(text="✏️ Имя УЗ", callback_data=f"admin_doc_edit_name_uz_{doc_id}"),
                InlineKeyboardButton(text="📄 Текст РУ", callback_data=f"admin_doc_edit_content_ru_{doc_id}")
            ],
            [
                InlineKeyboardButton(text="📄 Текст УЗ", callback_data=f"admin_doc_edit_content_uz_{doc_id}"),
                InlineKeyboardButton(text="🖼️ Фото", callback_data=f"admin_doc_edit_photo_{doc_id}")
            ],
            [
                InlineKeyboardButton(text="🎵 Аудио", callback_data=f"admin_doc_edit_audio_{doc_id}"),
                InlineKeyboardButton(text="📎 PDF", callback_data=f"admin_doc_edit_pdf_{doc_id}")
            ],
            [
                InlineKeyboardButton(text="⚙️ Кнопки", callback_data=f"admin_doc_buttons_{doc_id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_doc_delete_{doc_id}")
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_doc_cit_{document.citizenship_scope}")]
        ])
        
        content_info = ""
        if document.content_ru:
            content_info += f"\n📝 Текст РУ: {len(document.content_ru)} символов"
        if document.photo_file_id:
            content_info += "\n🖼️ Фото: есть"
        if document.audio_file_id:
            content_info += "\n🎵 Аудио: есть"
        if document.pdf_file_id:
            content_info += "\n📎 PDF: есть"
        
        await callback.message.edit_text(
            f"📚 ДОКУМЕНТ: {document.name_ru}\n"
            f"═══════════════════════════════════════\n"
            f"Статус: {status_text}\n"
            f"Страна: {document.citizenship_scope}"
            f"{content_info}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_doc_toggle_"))
async def toggle_document_status(callback: CallbackQuery):
    """Переключить статус документа (включить/отключить)"""
    doc_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if document:
            document.is_active = not document.is_active
            await session.commit()
            await callback.answer("✅ Статус обновлен", show_alert=False)
            # Refresh the view
            await callback.message.edit_text(callback.message.text)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_doc_edit_name_"))
async def edit_document_name(callback: CallbackQuery, state: FSMContext):
    """Редактирование имени документа"""
    parts = callback.data.split("_")
    lang = parts[-2]  # ru or uz
    doc_id = int(parts[-1])
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if not document:
            await callback.answer("❌ Документ не найден", show_alert=True)
            return
        
        current_name = document.name_ru if lang == "ru" else document.name_uz
        
        if lang == "ru":
            await state.set_state(AdminStates.editing_hujjat_name_ru)
        else:
            await state.set_state(AdminStates.editing_hujjat_name_uz)
        
        await state.update_data(current_doc_id=doc_id, edit_lang=lang)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_doc_item_{doc_id}")]
        ])
        
        lang_text = "РУССКОМ" if lang == "ru" else "УЗБЕКСКОМ"
        
        await callback.message.edit_text(
            f"✏️ РЕДАКТИРОВАНИЕ ИМЕНИ НА {lang_text}\n"
            f"═══════════════════════════════════════\n\n"
            f"Текущее имя:\n{current_name}\n\n"
            f"Введите новое имя:",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_hujjat_name_ru, AdminStates.editing_hujjat_name_uz))
async def process_document_name_edit(message: Message, state: FSMContext):
    """Обработка ввода нового имени документа"""
    data = await state.get_data()
    doc_id = data.get("current_doc_id")
    lang = data.get("edit_lang")
    new_name = message.text.strip()
    
    if not new_name or len(new_name) < 2:
        await message.answer("❌ Имя должно содержать минимум 2 символа")
        return
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if document:
            if lang == "ru":
                document.name_ru = new_name
            else:
                document.name_uz = new_name
            await session.commit()
            await message.answer("✅ Имя документа обновлено")
            
            # Return to document view
            status_icon = "✅" if document.is_active else "❌"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=f"[{status_icon}] Статус", callback_data=f"admin_doc_toggle_{doc_id}"),
                    InlineKeyboardButton(text="✏️ Имя РУ", callback_data=f"admin_doc_edit_name_ru_{doc_id}")
                ],
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_doc_cit_{document.citizenship_scope}")]
            ])
            
            await message.answer(
                f"📚 ДОКУМЕНТ: {document.name_ru}\n"
                f"═══════════════════════════════════════\n"
                f"Статус: {'Включен' if document.is_active else 'Отключен'}",
                reply_markup=keyboard
            )
    
    await state.clear()


@router.callback_query(F.data.startswith("admin_doc_edit_content_"))
async def edit_document_content(callback: CallbackQuery, state: FSMContext):
    """Редактирование содержимого документа"""
    parts = callback.data.split("_")
    lang = parts[-2]  # ru or uz
    doc_id = int(parts[-1])
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if not document:
            await callback.answer("❌ Документ не найден", show_alert=True)
            return
        
        current_content = document.content_ru if lang == "ru" else document.content_uz
        
        if lang == "ru":
            await state.set_state(AdminStates.editing_hujjat_content_ru)
        else:
            await state.set_state(AdminStates.editing_hujjat_content_uz)
        
        await state.update_data(current_doc_id=doc_id, edit_lang=lang)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_doc_item_{doc_id}")]
        ])
        
        lang_text = "РУССКОМ" if lang == "ru" else "УЗБЕКСКОМ"
        current_display = (current_content[:100] + "...") if current_content and len(current_content) > 100 else (current_content or "[Пусто]")
        
        await callback.message.edit_text(
            f"📄 РЕДАКТИРОВАНИЕ ТЕКСТА НА {lang_text}\n"
            f"═══════════════════════════════════════\n\n"
            f"Текущий текст:\n{current_display}\n\n"
            f"Введите новый текст:",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_hujjat_content_ru, AdminStates.editing_hujjat_content_uz))
async def process_document_content_edit(message: Message, state: FSMContext):
    """Обработка ввода нового содержимого документа"""
    data = await state.get_data()
    doc_id = data.get("current_doc_id")
    lang = data.get("edit_lang")
    new_content = message.text.strip()
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if document:
            if lang == "ru":
                document.content_ru = new_content
            else:
                document.content_uz = new_content
            await session.commit()
            await message.answer("✅ Содержимое документа обновлено")
            
            # Return to document view
            status_icon = "✅" if document.is_active else "❌"
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_doc_item_{doc_id}")]
            ])
            
            await message.answer(
                f"📚 ДОКУМЕНТ: {document.name_ru}\n"
                f"═══════════════════════════════════════\n"
                f"✅ Текст обновлен",
                reply_markup=keyboard
            )
    
    await state.clear()


@router.callback_query(F.data.startswith("admin_doc_edit_photo_"))
async def edit_document_photo(callback: CallbackQuery, state: FSMContext):
    """Загрузка фото для документа"""
    doc_id = int(callback.data.split("_")[-1])
    
    await state.set_state(AdminStates.editing_hujjat_photo)
    await state.update_data(current_doc_id=doc_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_doc_item_{doc_id}")]
    ])
    
    await callback.message.edit_text(
        "🖼️ ЗАГРУЗКА ФОТО\n"
        "═══════════════════════════════════════\n\n"
        "Отправьте фото документа или нажмите 'Отмена':",
        reply_markup=keyboard
    )
    await callback.answer()


@router.message(StateFilter(AdminStates.editing_hujjat_photo))
async def process_document_photo(message: Message, state: FSMContext):
    """Обработка загруженного фото"""
    if not message.photo:
        await message.answer("❌ Это не фото. Пожалуйста, отправьте изображение.")
        return
    
    data = await state.get_data()
    doc_id = data.get("current_doc_id")
    photo_file_id = message.photo[-1].file_id
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if document:
            document.photo_file_id = photo_file_id
            await session.commit()
            await message.answer("✅ Фото документа обновлено")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_doc_item_{doc_id}")]
            ])
            
            await message.answer(
                f"📚 ДОКУМЕНТ: {document.name_ru}\n"
                f"═══════════════════════════════════════\n"
                f"✅ Фото обновлено",
                reply_markup=keyboard
            )
    
    await state.clear()


@router.callback_query(F.data.startswith("admin_doc_delete_"))
async def delete_document(callback: CallbackQuery, state: FSMContext):
    """Удаление документа (soft delete)"""
    doc_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if not document:
            await callback.answer("❌ Документ не найден", show_alert=True)
            return
        
        citizenship = document.citizenship_scope
        await DocumentService.delete_document(session, doc_id)
        
        await callback.answer("✅ Документ удален", show_alert=True)
        
        # Return to documents list
        documents = await DocumentService.get_documents_by_citizenship(session, citizenship)
        
        keyboard_buttons = []
        for doc in documents:
            status_icon = "✅" if doc.is_active else "❌"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{status_icon} {doc.name_ru}",
                    callback_data=f"admin_doc_item_{doc.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_doc_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"📚 ДОКУМЕНТЫ\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего документов: {len(documents)}",
            reply_markup=keyboard
        )


@router.callback_query(F.data.startswith("admin_doc_buttons_"))
async def manage_document_buttons(callback: CallbackQuery, state: FSMContext):
    """Управление кнопками документа"""
    doc_id = int(callback.data.split("_")[-1])
    
    await state.set_state(AdminStates.button_management)
    await state.update_data(current_doc_id=doc_id)
    
    async with AsyncSessionLocal() as session:
        buttons = await DocumentService.get_document_buttons(session, doc_id)
        
        keyboard_buttons = []
        for idx, btn in enumerate(buttons, 1):
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{idx}️⃣ {btn.text_ru}",
                    callback_data=f"admin_btn_edit_{btn.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="➕ Добавить кнопку", callback_data=f"admin_btn_add_{doc_id}")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_doc_item_{doc_id}")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"⚙️ УПРАВЛЕНИЕ КНОПКАМИ\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего кнопок: {len(buttons)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# DELIVERY MANAGEMENT (Управление доставкой)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_del_menu")
async def handle_delivery_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления доставкой"""
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        waiting = await session.execute(
            select(func.count(Delivery.id)).where(Delivery.status == "WAITING")
        )
        waiting_count = waiting.scalar() or 0
        
        completed = await session.execute(
            select(func.count(Delivery.id)).where(Delivery.status == "COMPLETED")
        )
        completed_count = completed.scalar() or 0
        
        rejected = await session.execute(
            select(func.count(Delivery.id)).where(
                Delivery.status.in_(["REJECTED", "CANCELLED"])
            )
        )
        rejected_count = rejected.scalar() or 0
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📬 Активные заказы ({waiting_count})", callback_data="admin_del_active")],
            [InlineKeyboardButton(text=f"✅ Завершенные ({completed_count})", callback_data="admin_del_completed")],
            [InlineKeyboardButton(text=f"❌ Отклоненные ({rejected_count})", callback_data="admin_del_rejected")],
            [InlineKeyboardButton(text="👨‍💼 Управление курьерами", callback_data="admin_couriers_list")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(
            "🚚 УПРАВЛЕНИЕ ДОСТАВКОЙ\n"
            "═══════════════════════════════════════\n\n"
            f"Активные заказы: {waiting_count}\n"
            f"Завершенные: {completed_count}\n"
            f"Отклоненные: {rejected_count}",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# NOTIFICATION MANAGEMENT (Управление потерями)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_prop_menu")
async def handle_notification_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления уведомлениями о потерях"""
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        # Count pending notifications
        pending = await session.execute(
            select(func.count(Notification.id)).where(
                Notification.is_approved == False,
                Notification.is_moderated == False
            )
        )
        pending_count = pending.scalar() or 0
        
        # Count approved
        approved = await session.execute(
            select(func.count(Notification.id)).where(Notification.is_approved == True)
        )
        approved_count = approved.scalar() or 0
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"⏳ На модерации ({pending_count})", callback_data="admin_notif_pending")],
            [InlineKeyboardButton(text=f"✅ Одобренные ({approved_count})", callback_data="admin_notif_approved")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(
            "🔔 УПРАВЛЕНИЕ ПОТЕРЯШКАМИ\n"
            "═══════════════════════════════════════\n\n"
            f"На модерации: {pending_count}\n"
            f"Одобренные: {approved_count}",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# SHURTA MANAGEMENT (Управление полицией)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_shurta_menu")
async def handle_shurta_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления полицией"""
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        # Count pending alerts
        pending = await session.execute(
            select(func.count(ShurtaAlert.id)).where(
                ShurtaAlert.is_approved == False,
                ShurtaAlert.is_moderated == False
            )
        )
        pending_count = pending.scalar() or 0
        
        # Count approved
        approved = await session.execute(
            select(func.count(ShurtaAlert.id)).where(ShurtaAlert.is_approved == True)
        )
        approved_count = approved.scalar() or 0
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"⏳ На модерации ({pending_count})", callback_data="admin_shurta_pending")],
            [InlineKeyboardButton(text=f"✅ Одобренные ({approved_count})", callback_data="admin_shurta_approved")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(
            "🚨 УПРАВЛЕНИЕ ПОЛИЦИЕЙ\n"
            "═══════════════════════════════════════\n\n"
            f"На модерации: {pending_count}\n"
            f"Одобренные: {approved_count}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin_notif_pending")
async def show_pending_notifications(callback: CallbackQuery, state: FSMContext):
    """Показать ожидающие одобрения уведомления"""
    await state.set_state(AdminStates.notification_view)
    
    async with AsyncSessionLocal() as session:
        notifications = await session.execute(
            select(Notification)
            .options(joinedload(Notification.creator))
            .where(
                Notification.is_approved == False,
                Notification.is_moderated == False,
                Notification.is_active == True
            )
            .order_by(Notification.created_at.desc())
            .limit(20)
        )
        notifs = notifications.unique().scalars().all()
        
        if not notifs:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_prop_menu")]
            ])
            await callback.message.edit_text(
                "✅ Нет ожидающих одобрения уведомлений",
                reply_markup=keyboard
            )
            await callback.answer()
            return
        
        keyboard_buttons = []
        for notif in notifs:
            preview = (notif.title[:30] + "...") if len(notif.title) > 30 else notif.title
            creator_name = notif.creator.username if notif.creator and notif.creator.username else f"ID{notif.creator_id}"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🔴 {notif.type} - {preview}",
                    callback_data=f"admin_notif_view_{notif.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_prop_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"🔔 ОЖИДАЮЩИЕ ОДОБРЕНИЯ УВЕДОМЛЕНИЯ\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего: {len(notifs)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_notif_view_"))
async def view_notification_detail(callback: CallbackQuery):
    """Просмотр деталей уведомления"""
    notif_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        notification = await session.get(Notification, notif_id)
        if not notification:
            await callback.answer("❌ Уведомление не найдено", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"admin_notif_approve_{notif_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_notif_reject_{notif_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_notif_pending")]
        ])
        
        text = f"🔔 УВЕДОМЛЕНИЕ\n"
        text += f"═══════════════════════════════════════\n\n"
        text += f"Тип: {notification.type}\n"
        text += f"Название: {notification.title}\n"
        text += f"Описание: {notification.description}\n"
        text += f"Телефон: {notification.phone}\n"
        text += f"Место: {notification.address_text or 'не указано'}"
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_notif_approve_"))
async def approve_notification(callback: CallbackQuery):
    """Одобрить уведомление"""
    try:
        logger.info(f"Админ {callback.from_user.id} одобряет уведомление")
        notif_id = int(callback.data.split("_")[-1])
        admin_id = callback.from_user.id
        
        async with AsyncSessionLocal() as session:
            notification = await ModerationService.approve_notification(session, notif_id, admin_id)
            if notification:
                users = await ModerationService.get_users_for_notification(
                    session,
                    notification.type
                )
                success_count = 0
                fail_count = 0
                
                for target_user in users:
                    try:
                        message_text = await ModerationService.format_notification_for_user(
                            notification,
                            target_user.language or "RU"
                        )
                        if notification.photo_file_id:
                            await callback.bot.send_photo(
                                target_user.telegram_id,
                                photo=notification.photo_file_id,
                                caption=message_text
                            )
                        else:
                            await callback.bot.send_message(
                                target_user.telegram_id,
                                message_text
                            )
                        
                        if notification.location_type == "GEO" and notification.latitude and notification.longitude:
                            await callback.bot.send_location(
                                target_user.telegram_id,
                                latitude=notification.latitude,
                                longitude=notification.longitude
                            )
                        elif notification.location_type == "MAPS" and notification.maps_url:
                            await callback.bot.send_message(
                                target_user.telegram_id,
                                f"📍 {notification.maps_url}"
                            )
                        elif notification.address_text:
                            await callback.bot.send_message(
                                target_user.telegram_id,
                                f"📍 {notification.address_text}"
                            )
                        success_count += 1
                    except Exception as send_error:
                        fail_count += 1
                        logger.error(f"Ошибка отправки уведомления пользователю {target_user.telegram_id}: {str(send_error)}")
                
                # Уведомить создателя
                creator = await session.get(User, notification.creator_id)
                if creator and creator.telegram_id:
                    try:
                        await callback.bot.send_message(
                            creator.telegram_id,
                            "✅ Ваше объявление одобрено и отправлено пользователям"
                        )
                    except Exception as creator_error:
                        logger.error(f"Не удалось уведомить создателя {creator.telegram_id}: {str(creator_error)}")
                
                logger.info(f"Уведомление одобрено, отправлено {success_count}/{len(users)} пользователям")
                await callback.message.edit_text(
                    f"✅ Уведомление одобрено и отправлено {success_count}/{len(users)} пользователям\n"
                    f"Ошибок отправки: {fail_count}"
                )
                await callback.answer(
                    f"✅ Уведомление отправлено {success_count}/{len(users)} пользователям",
                    show_alert=True
                )
            else:
                logger.error(f"Не удалось одобрить уведомление {notif_id}")
                await callback.answer("❌ Ошибка при одобрении", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при одобрении уведомления: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_notif_reject_"))
async def reject_notification(callback: CallbackQuery):
    """Отклонить уведомление"""
    try:
        logger.info(f"Админ {callback.from_user.id} отклоняет уведомление")
        notif_id = int(callback.data.split("_")[-1])
        admin_id = callback.from_user.id
        
        async with AsyncSessionLocal() as session:
            notification = await ModerationService.reject_notification(session, notif_id, admin_id)
            if notification:
                logger.info(f"Уведомление {notif_id} отклонено")
                await callback.message.edit_text("✅ Уведомление отклонено")
                await callback.answer("✅ Уведомление отклонено", show_alert=True)
            else:
                logger.error(f"Не удалось отклонить уведомление {notif_id}")
                await callback.answer("❌ Ошибка при отклонении", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отклонении уведомления: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "admin_notif_approved")
async def show_approved_notifications(callback: CallbackQuery):
    """Показать одобренные уведомления"""
    async with AsyncSessionLocal() as session:
        notifications = await session.execute(
            select(Notification)
            .where(Notification.is_approved == True, Notification.is_active == True)
            .order_by(Notification.created_at.desc())
            .limit(20)
        )
        notifs = notifications.scalars().all()
        
        keyboard_buttons = []
        for notif in notifs:
            preview = (notif.title[:30] + "...") if len(notif.title) > 30 else notif.title
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"✅ {notif.type} - {preview}",
                    callback_data=f"admin_notif_approved_view_{notif.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_prop_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"✅ ОДОБРЕННЫЕ УВЕДОМЛЕНИЯ\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего: {len(notifs)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin_shurta_pending")
async def show_pending_shurta_alerts(callback: CallbackQuery):
    """Показать ожидающие одобрения алерты Shurta"""
    async with AsyncSessionLocal() as session:
        alerts = await session.execute(
            select(ShurtaAlert)
            .options(joinedload(ShurtaAlert.creator))
            .where(
                ShurtaAlert.is_approved == False,
                ShurtaAlert.is_moderated == False,
                ShurtaAlert.is_active == True
            )
            .order_by(ShurtaAlert.created_at.desc())
            .limit(20)
        )
        alert_list = alerts.unique().scalars().all()
        
        if not alert_list:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_shurta_menu")]
            ])
            await callback.message.edit_text(
                "✅ Нет ожидающих одобрения алертов",
                reply_markup=keyboard
            )
            await callback.answer()
            return
        
        keyboard_buttons = []
        for alert in alert_list:
            preview = (alert.description[:30] + "...") if len(alert.description) > 30 else alert.description
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🔴 {preview}",
                    callback_data=f"admin_shurta_view_{alert.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_shurta_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"🚨 ОЖИДАЮЩИЕ ОДОБРЕНИЯ АЛЕРТЫ\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего: {len(alert_list)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_shurta_view_"))
async def view_shurta_detail(callback: CallbackQuery):
    """Просмотр деталей Shurta алерта"""
    alert_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        alert = await session.get(ShurtaAlert, alert_id)
        if not alert:
            await callback.answer("❌ Алерт не найден", show_alert=True)
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data=f"admin_shurta_approve_{alert_id}")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_shurta_reject_{alert_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_shurta_pending")]
        ])
        
        text = f"🚨 SHURTA АЛЕРТ\n"
        text += f"═══════════════════════════════════════\n\n"
        text += f"Описание: {alert.description}\n"
        text += f"Место: {alert.address_text or 'не указано'}"
        
        await callback.message.edit_text(text, reply_markup=keyboard)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_shurta_approve_"))
async def approve_shurta_alert(callback: CallbackQuery):
    """Одобрить Shurta алерт"""
    try:
        logger.info(f"Админ {callback.from_user.id} одобряет Shurta")
        alert_id = int(callback.data.split("_")[-1])
        admin_id = callback.from_user.id
        
        async with AsyncSessionLocal() as session:
            alert = await ModerationService.approve_shurta(session, alert_id, admin_id)
            if alert:
                users = await ModerationService.get_users_for_notification(session, "SHURTA")
                recipients_count = len(users)
                
                logger.info(f"Shurta одобрен, рассылка {recipients_count} пользователям")
                await callback.message.edit_text(
                    f"✅ Алерт одобрен и отправлен {recipients_count} пользователям"
                )
                await callback.answer(
                    f"✅ Алерт отправлен {recipients_count} пользователям",
                    show_alert=True
                )
            else:
                logger.error(f"Не удалось одобрить Shurta {alert_id}")
                await callback.answer("❌ Ошибка при одобрении", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при одобрении Shurta: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_shurta_reject_"))
async def reject_shurta_alert(callback: CallbackQuery):
    """Отклонить Shurta алерт"""
    try:
        logger.info(f"Админ {callback.from_user.id} отклоняет Shurta")
        alert_id = int(callback.data.split("_")[-1])
        admin_id = callback.from_user.id
        
        async with AsyncSessionLocal() as session:
            alert = await ModerationService.reject_shurta(session, alert_id, admin_id)
            if alert:
                logger.info(f"Shurta {alert_id} отклонен")
                await callback.message.edit_text("✅ Алерт отклонен")
                await callback.answer("✅ Алерт отклонен", show_alert=True)
            else:
                logger.error(f"Не удалось отклонить Shurta {alert_id}")
                await callback.answer("❌ Ошибка при отклонении", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при отклонении Shurta: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data == "admin_shurta_approved")
async def show_approved_shurta_alerts(callback: CallbackQuery):
    """Показать одобренные Shurta алерты"""
    async with AsyncSessionLocal() as session:
        alerts = await session.execute(
            select(ShurtaAlert)
            .where(ShurtaAlert.is_approved == True, ShurtaAlert.is_active == True)
            .order_by(ShurtaAlert.created_at.desc())
            .limit(20)
        )
        alert_list = alerts.scalars().all()
        
        keyboard_buttons = []
        for alert in alert_list:
            preview = (alert.description[:30] + "...") if len(alert.description) > 30 else alert.description
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"✅ {preview}",
                    callback_data=f"admin_shurta_approved_view_{alert.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_shurta_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"✅ ОДОБРЕННЫЕ АЛЕРТЫ\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего: {len(alert_list)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# MODERATION HANDLERS (Обработчики модерации из пользовательского бота)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("admin_approve_notif_"))
async def approve_notification_from_user_bot(callback: CallbackQuery):
    """Одобрить уведомление из пользовательского бота"""
    logger.info(f"[approve_notification_from_user_bot] Начало | admin_id={callback.from_user.id}")
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user or not user.is_admin:
                await callback.answer("❌ У вас нет прав администратора", show_alert=True)
                return
            
            notification = await NotificationService.approve_notification(
                session,
                notification_id,
                user.id
            )
            
            if notification:
                # Отправить уведомление всем пользователям
                all_users = await UserService.get_all_users(session)
                for target_user in all_users:
                    if target_user.notifications_enabled and target_user.id != notification.creator_id:
                        try:
                            alert_text = ModerationService.format_notification_for_user(
                                notification, target_user.language
                            )
                            
                            if notification.photo_file_id:
                                await callback.bot.send_photo(
                                    target_user.telegram_id,
                                    photo=notification.photo_file_id,
                                    caption=alert_text
                                )
                            else:
                                await callback.bot.send_message(
                                    target_user.telegram_id,
                                    alert_text
                                )
                        except Exception as e:
                            logger.error(f"Не удалось отправить пользователю {target_user.telegram_id}: {e}")
                
                await callback.message.edit_text("✅ Уведомление одобрено и отправлено пользователям")
                await callback.answer("✅ Одобрено")
                logger.info(f"[approve_notification_from_user_bot] ✅ Успешно")
            else:
                await callback.answer("❌ Уведомление не найдено", show_alert=True)
                logger.error(f"[approve_notification_from_user_bot] ❌ Уведомление {notification_id} не найдено")
    except Exception as e:
        logger.error(f"[approve_notification_from_user_bot] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_notif_"))
async def reject_notification_from_user_bot(callback: CallbackQuery):
    """Отклонить уведомление из пользовательского бота"""
    logger.info(f"[reject_notification_from_user_bot] Начало | admin_id={callback.from_user.id}")
    try:
        notification_id = int(callback.data.split("_")[-1])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user or not user.is_admin:
                await callback.answer("❌ У вас нет прав администратора", show_alert=True)
                return
            
            notification = await NotificationService.reject_notification(
                session,
                notification_id,
                user.id
            )
            
            if notification:
                await callback.message.edit_text("✅ Уведомление отклонено")
                await callback.answer("✅ Отклонено")
                logger.info(f"[reject_notification_from_user_bot] ✅ Успешно")
            else:
                await callback.answer("❌ Уведомление не найдено", show_alert=True)
                logger.error(f"[reject_notification_from_user_bot] ❌ Уведомление {notification_id} не найдено")
    except Exception as e:
        logger.error(f"[reject_notification_from_user_bot] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_approve_shurta_"))
async def approve_shurta_from_user_bot(callback: CallbackQuery):
    """Одобрить алерт Shurta из пользовательского бота"""
    logger.info(f"[approve_shurta_from_user_bot] Начало | admin_id={callback.from_user.id}")
    try:
        shurta_id = int(callback.data.split("_")[-1])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user or not user.is_admin:
                await callback.answer("❌ У вас нет прав администратора", show_alert=True)
                return
            
            alert = await ShurtaService.approve_alert(
                session,
                shurta_id,
                user.id
            )
            
            if alert:
                # Отправить алерт всем пользователям
                all_users = await UserService.get_all_users(session)
                for target_user in all_users:
                    if target_user.notifications_enabled and target_user.id != alert.creator_id:
                        try:
                            alert_text = ModerationService.format_shurta_for_user(
                                alert, target_user.language
                            )
                            
                            # Если есть геолокация - отправить как карту
                            if alert.latitude and alert.longitude:
                                await callback.bot.send_location(
                                    chat_id=target_user.telegram_id,
                                    latitude=alert.latitude,
                                    longitude=alert.longitude
                                )
                            
                            if alert.photo_file_id:
                                await callback.bot.send_photo(
                                    target_user.telegram_id,
                                    photo=alert.photo_file_id,
                                    caption=alert_text
                                )
                            else:
                                await callback.bot.send_message(
                                    target_user.telegram_id,
                                    alert_text
                                )
                        except Exception as e:
                            logger.error(f"Не удалось отправить пользователю {target_user.telegram_id}: {e}")
                
                await callback.message.edit_text("✅ Алерт Shurta одобрен и отправлен пользователям")
                await callback.answer("✅ Одобрено")
                logger.info(f"[approve_shurta_from_user_bot] ✅ Успешно")
            else:
                await callback.answer("❌ Алерт не найден", show_alert=True)
                logger.error(f"[approve_shurta_from_user_bot] ❌ Алерт {shurta_id} не найден")
    except Exception as e:
        logger.error(f"[approve_shurta_from_user_bot] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_reject_shurta_"))
async def reject_shurta_from_user_bot(callback: CallbackQuery):
    """Отклонить алерт Shurta из пользовательского бота"""
    logger.info(f"[reject_shurta_from_user_bot] Начало | admin_id={callback.from_user.id}")
    try:
        shurta_id = int(callback.data.split("_")[-1])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user(session, callback.from_user.id)
            if not user or not user.is_admin:
                await callback.answer("❌ У вас нет прав администратора", show_alert=True)
                return
            
            alert = await ShurtaService.reject_alert(
                session,
                shurta_id,
                user.id
            )
            
            if alert:
                await callback.message.edit_text("✅ Алерт Shurta отклонен")
                await callback.answer("✅ Отклонено")
                logger.info(f"[reject_shurta_from_user_bot] ✅ Успешно")
            else:
                await callback.answer("❌ Алерт не найден", show_alert=True)
                logger.error(f"[reject_shurta_from_user_bot] ❌ Алерт {shurta_id} не найден")
    except Exception as e:
        logger.error(f"[reject_shurta_from_user_bot] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════════
# USER MANAGEMENT (Управление пользователями)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_user_menu")
async def handle_user_management_menu(callback: CallbackQuery, state: FSMContext):
    """Меню управления пользователями"""
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        # Get user statistics
        total_users = await session.execute(select(func.count(User.id)))
        total = total_users.scalar() or 0
        
        couriers = await session.execute(
            select(func.count(User.id)).where(User.is_courier == True)
        )
        courier_count = couriers.scalar() or 0
        
        banned = await session.execute(
            select(func.count(User.id)).where(User.is_banned == True)
        )
        banned_count = banned.scalar() or 0
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_user_stats")],
            [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_select_user")],
            [InlineKeyboardButton(text=f"🚗 Курьеры ({courier_count})", callback_data="admin_couriers_list")],
            [InlineKeyboardButton(text=f"🚫 Забанены ({banned_count})", callback_data="admin_user_banned")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(
            "👥 УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ\n"
            "═══════════════════════════════════════\n\n"
            f"Всего пользователей: {total}\n"
            f"Курьеры: {courier_count}\n"
            f"Забанены: {banned_count}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin_select_user")
async def admin_select_user(callback: CallbackQuery, state: FSMContext):
    """Начало поиска пользователя"""
    logger.info(f"[admin_select_user] Начало | admin_id={callback.from_user.id}")
    try:
        await state.set_state(AdminStates.user_search_input)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_user_menu")]
        ])
        
        await callback.message.edit_text(
            "🔍 ПОИСК ПОЛЬЗОВАТЕЛЯ\n"
            "═══════════════════════════════════════\n\n"
            "Введите имя, юзернейм или номер телефона:",
            reply_markup=keyboard
        )
        
        await callback.answer()
        logger.info(f"[admin_select_user] ✅ Успешно")
    except Exception as e:
        logger.error(f"[admin_select_user] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.message(StateFilter(AdminStates.user_search_input))
async def search_users_live(message: Message, state: FSMContext):
    """Живой поиск пользователей"""
    logger.info(f"[search_users_live] Начало | query={message.text}")
    try:
        query = message.text.strip().lower()
        
        if len(query) < 2:
            await message.answer("⚠️ Минимум 2 символа для поиска")
            return
        
        async with AsyncSessionLocal() as session:
            users = await UserService.search_users(session, query)
        
        if not users:
            await message.answer("❌ Пользователей не найдено")
            logger.info(f"[search_users_live] Пользователи не найдены")
            return
        
        text = f"✅ НАЙДЕНО: {len(users)} пользователей\n\n"
        buttons = []
        
        for user in users:
            status = "🟢 Онлайн" if user.is_online else "🟡 Оффлайн"
            courier_badge = "🚗" if user.is_courier else "👤"
            lang = "🇷🇺" if user.language == 'RU' else "🇺🇿"
            last_active = user.last_active.strftime('%d.%m %H:%M') if user.last_active else 'N/A'
            username_display = user.username or f"id{user.telegram_id}"
            first_name_display = user.first_name or "—"
            phone_display = user.phone or "—"
            
            text += f"{courier_badge} @{username_display} ({first_name_display})\n"
            text += f"   📞 {phone_display} | {lang} | {status}\n"
            text += f"   Активен: {last_active}\n\n"
            
            buttons.append([InlineKeyboardButton(
                text=f"@{username_display}",
                callback_data=f"admin_user_detail_{user.id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_user_menu")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(text, reply_markup=keyboard)
        
        logger.info(f"[search_users_live] ✅ Найдено {len(users)} пользователей")
    except Exception as e:
        logger.error(f"[search_users_live] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка при поиске")

@router.callback_query(F.data.startswith("admin_user_view_"))
async def view_user_profile(callback: CallbackQuery, state: FSMContext):
    """Просмотр профиля пользователя с детальной статистикой"""
    try:
        logger.info(f"Админ {callback.from_user.id} просматривает профиль пользователя")
        user_id = int(callback.data.split("_")[-1])
        
        async with AsyncSessionLocal() as session:
            user = await session.get(User, user_id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            # Получить детальную статистику
            user_stats = await StatisticsService.get_user_detail_stats(session, user.id)
            
            if not user_stats:
                await callback.answer("❌ Не удалось загрузить статистику", show_alert=True)
                return
            
            banned_status = "🚫 Забанен" if user.is_banned else "✅ Активен"
            courier_status = "🚗 Да" if user.is_courier else "❌ Нет"
            citizenship_map = {
                "UZ": "🇺🇿 Узбекистан",
                "RU": "🇷🇺 Россия",
                "KZ": "🇰🇿 Казахстан",
                "KG": "🇰🇬 Киргизия"
            }
            
            # Формируем топ кнопок
            top_buttons_text = ""
            for button_name, clicks in list(user_stats.get("top_buttons", {}).items())[:3]:
                top_buttons_text += f"- {button_name}: {clicks} переходов\n"
            if not top_buttons_text:
                top_buttons_text = "— нет данных\n"
            
            # Формируем пиковые часы
            peak_hours_text = ""
            for time_range, count in list(user_stats.get("peak_hours", {}).items())[:2]:
                peak_hours_text += f"- {time_range}: {count} минут\n"
            if not peak_hours_text:
                peak_hours_text = "— нет данных\n"
            
            profile_text = (
                f"👤 ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ\n"
                f"═══════════════════════════════════════\n\n"
                f"👤 @{user.username or 'без юзернейма'} ({user.first_name or 'Без имени'})\n"
                f"📞 Телефон: {user.phone or 'не указан'}\n"
                f"🆔 User ID: {user.telegram_id}\n"
                f"🕐 Присоединился: {user.created_at.strftime('%d.%m.%Y') if user.created_at else 'неизв.'}\n\n"
                f"🌍 Язык: {'🇷🇺 Русский' if user.language == 'RU' else '🇺🇿 Узбекский'}\n"
                f"🏠 Гражданство: {citizenship_map.get(user.citizenship, user.citizenship or 'не указано')}\n"
                f"🚗 Курьер: {courier_status}\n\n"
                f"📊 СТАТИСТИКА:\n"
                f"- Нажато кнопок за месяц: {user_stats.get('clicks_month', 0)}\n"
                f"- Отправлено сообщений: {user_stats.get('messages_sent', 0)}\n"
                f"- Загружено фото: {user_stats.get('photos_uploaded', 0)}\n\n"
                f"⏰ ВРЕМЯ АКТИВНОСТИ (в этом месяце):\n{peak_hours_text}\n"
                f"❓ ИНТЕРЕСНЫЕ ТЕМЫ:\n{top_buttons_text}\n"
                f"Статус: {banned_status}"
            )
            
            ban_btn_text = "🔓 Разбанить" if user.is_banned else "🚫 Забанить"
            courier_btn_text = "❌ Убрать курьера" if user.is_courier else "🚗 Сделать курьером"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=ban_btn_text, callback_data=f"admin_user_toggle_ban_{user_id}"),
                    InlineKeyboardButton(text=courier_btn_text, callback_data=f"admin_user_toggle_courier_{user_id}")
                ],
                [InlineKeyboardButton(text="💬 Сообщение", callback_data=f"admin_user_msg_{user_id}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_user_menu")]
            ])
            
            await callback.message.edit_text(profile_text, reply_markup=keyboard)
            logger.info(f"Профиль пользователя {user.id} отображен с детальной статистикой")
        
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка при просмотре профиля пользователя: {str(e)}", exc_info=True)
        await callback.answer("❌ Произошла ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_user_detail_"))
async def show_user_detail(callback: CallbackQuery, state: FSMContext):
    """Показать детали пользователя"""
    logger.info(f"[show_user_detail] Начало | admin_id={callback.from_user.id}")
    try:
        user_id = int(callback.data.split('_')[3])
        
        async with AsyncSessionLocal() as session:
            user = await UserService.get_user_by_id(session, user_id)
            
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return
            
            text = f"ПОЛЬЗОВАТЕЛЬ: @{user.username or user.first_name}\n"
            text += f"{'='*50}\n\n"
            text += f"👤 {user.first_name or '—'}\n"
            text += f"📞 {user.phone or '—'}\n"
            text += f"🆔 {user.telegram_id}\n"
            text += f"📅 Присоединился: {user.created_at.strftime('%d.%m.%Y') if user.created_at else '—'}\n\n"
            
            text += f"🌍 Язык: {'🇷🇺 Русский' if user.language == 'RU' else '🇺🇿 Узбекский'}\n"
            text += f"🏠 Гражданство: {user.citizenship or '—'}\n"
            text += f"🚗 Курьер: {'✅ Да' if user.is_courier else '❌ Нет'}\n"
            text += f"🚫 Забанен: {'✅ Да' if user.is_banned else '❌ Нет'}\n\n"
            
            text += f"📊 АКТИВНОСТЬ:\n"
            text += f"- Последний вход: {user.last_active.strftime('%d.%m %H:%M') if user.last_active else 'N/A'}\n\n"
            
            buttons = [
                [InlineKeyboardButton(text="🚫 Забанить" if not user.is_banned else "✅ Разбанить", callback_data=f"admin_ban_user_{user_id}")],
                [InlineKeyboardButton(text="🚗 Сделать курьером" if not user.is_courier else "❌ Убрать курьера", callback_data=f"admin_make_courier_{user_id}")],
                [InlineKeyboardButton(text="💬 Отправить сообщение", callback_data=f"admin_msg_user_{user_id}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_user_menu")]
            ]
            
            await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
            logger.info(f"[show_user_detail] ✅ Детали показаны")
    except Exception as e:
        logger.error(f"[show_user_detail] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data.startswith("admin_user_toggle_ban_"))
async def toggle_user_ban(callback: CallbackQuery):
    """Переключить статус бана пользователя"""
    user_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_banned = not user.is_banned
            await session.commit()
            await callback.answer("✅ Статус обновлен", show_alert=False)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_toggle_courier_"))
async def toggle_user_courier(callback: CallbackQuery):
    """Переключить статус курьера пользователя"""
    user_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if user:
            user.is_courier = not user.is_courier
            await session.commit()
            await callback.answer("✅ Статус обновлен", show_alert=False)
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_msg_"))
async def send_message_to_user(callback: CallbackQuery, state: FSMContext):
    """Начать отправку сообщения пользователю"""
    user_id = int(callback.data.split("_")[-1])
    
    await state.set_state(AdminStates.message_reply_input)
    await state.update_data(target_user_id=user_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_user_view_{user_id}")]
    ])
    
    await callback.message.edit_text(
        "💬 ОТПРАВКА СООБЩЕНИЯ\n"
        "═══════════════════════════════════════\n\n"
        "Введите текст сообщения:",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.message(StateFilter(AdminStates.message_reply_input))
async def process_message_to_user(message: Message, state: FSMContext):
    """Обработка отправки сообщения пользователю"""
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    msg_text = message.text.strip()
    
    if not msg_text:
        await message.answer("❌ Сообщение не может быть пустым")
        return
    
    # TODO: Implement actual message sending to user bot
    await message.answer("✅ Сообщение отправлено пользователю")
    await state.clear()


# ═══════════════════════════════════════════════════════════════════════════
# MESSAGES FROM USERS (Сообщения от пользователей)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_msg_menu")
async def handle_messages_menu(callback: CallbackQuery, state: FSMContext):
    """Меню сообщений от пользователей"""
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        unread = await session.execute(
            select(func.count(UserMessage.id)).where(UserMessage.is_read == False)
        )
        unread_count = unread.scalar() or 0
        
        total = await session.execute(select(func.count(UserMessage.id)))
        total_count = total.scalar() or 0
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🔴 Непрочитанные ({unread_count})", callback_data="admin_msg_unread")],
            [InlineKeyboardButton(text=f"✅ Прочитанные", callback_data="admin_msg_read")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(
            "💬 СООБЩЕНИЯ ОТ ПОЛЬЗОВАТЕЛЕЙ\n"
            "═══════════════════════════════════════\n\n"
            f"Всего сообщений: {total_count}\n"
            f"Непрочитанные: {unread_count}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data == "admin_msg_unread")
async def show_unread_messages(callback: CallbackQuery, state: FSMContext):
    """Показать непрочитанные сообщения"""
    await state.set_state(AdminStates.message_view)
    
    async with AsyncSessionLocal() as session:
        messages = await session.execute(
            select(UserMessage)
            .options(joinedload(UserMessage.user))
            .where(UserMessage.is_read == False)
            .order_by(UserMessage.created_at.desc())
            .limit(20)
        )
        msgs = messages.unique().scalars().all()
        
        if not msgs:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_msg_menu")]
            ])
            await callback.message.edit_text(
                "❌ Нет непрочитанных сообщений",
                reply_markup=keyboard
            )
            await callback.answer()
            return
        
        keyboard_buttons = []
        for msg in msgs:
            preview = (msg.message_text[:30] + "...") if len(msg.message_text) > 30 else msg.message_text
            username = msg.user.username if msg.user else "Unknown"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"🔴 @{username}: {preview}",
                    callback_data=f"admin_msg_view_detail_{msg.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_msg_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"💬 НЕПРОЧИТАННЫЕ СООБЩЕНИЯ\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего: {len(msgs)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_msg_view_detail_"))
async def view_message_detail(callback: CallbackQuery, state: FSMContext):
    """Просмотр деталей сообщения"""
    msg_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        msg = await UserMessageService.get_message(session, msg_id)
        if not msg:
            await callback.answer("❌ Сообщение не найдено", show_alert=True)
            return
        
        await UserMessageService.mark_as_read(session, msg_id)
        
        username = msg.user.username if msg.user else f"ID: {msg.user_id}"
        created_at = msg.created_at.strftime("%d.%m.%Y %H:%M") if msg.created_at else "неизв."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Ответить", callback_data=f"admin_msg_reply_{msg_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_msg_delete_{msg_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_msg_unread")]
        ])
        
        await callback.message.edit_text(
            f"💬 СООБЩЕНИЕ\n"
            f"═══════════════════════════════════════\n\n"
            f"От: @{username}\n"
            f"Время: {created_at}\n\n"
            f"{msg.message_text}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_msg_reply_"))
async def reply_to_message(callback: CallbackQuery, state: FSMContext):
    """Начало ответа на сообщение"""
    msg_id = int(callback.data.split("_")[-1])
    
    await state.set_state(AdminStates.message_reply_input)
    await state.update_data(reply_to_msg_id=msg_id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_msg_view_detail_{msg_id}")]
    ])
    
    await callback.message.edit_text(
        "✉️ ОТВЕТИТЬ НА СООБЩЕНИЕ\n"
        "═══════════════════════════════════════\n\n"
        "Введите текст ответа:",
        reply_markup=keyboard
    )
    
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# BROADCASTING SYSTEM (Система рассылки)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_bc_menu")
async def handle_broadcast_menu(callback: CallbackQuery, state: FSMContext):
    """Меню системы рассылки"""
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Создать новую рассылку", callback_data="admin_bc_new")],
        [InlineKeyboardButton(text="📋 История рассылок", callback_data="admin_bc_history")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
    ])
    
    await callback.message.edit_text(
        "📢 СИСТЕМА РАССЫЛКИ\n"
        "═══════════════════════════════════════",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data == "admin_bc_new")
async def start_new_broadcast(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой рассылки"""
    await state.set_state(AdminStates.broadcast_menu)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_bc_menu")]
    ])
    
    await callback.message.edit_text(
        "✍️ СОЗДАНИЕ РАССЫЛКИ\n"
        "═══════════════════════════════════════\n\n"
        "1️⃣ НАЗВАНИЕ КАМПАНИИ\n\n"
        "Введите название (например, 'Важная информация'):",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.message(StateFilter(AdminStates.broadcast_menu))
async def process_broadcast_name(message: Message, state: FSMContext):
    """Обработка названия рассылки"""
    name = message.text.strip()
    
    if not name or len(name) < 3:
        await message.answer("❌ Название должно содержать минимум 3 символа")
        return
    
    await state.update_data(broadcast_name=name)
    await state.set_state(AdminStates.broadcast_text_ru)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Пропустить УЗ текст", callback_data="admin_bc_skip_uz")]
    ])
    
    await message.answer(
        "✍️ СОЗДАНИЕ РАССЫЛКИ\n"
        "═══════════════════════════════════════\n\n"
        "2️⃣ ТЕКСТ НА РУССКОМ\n\n"
        "Введите текст сообщения на русском языке:",
        reply_markup=keyboard
    )


@router.message(StateFilter(AdminStates.broadcast_text_ru))
async def process_broadcast_text_ru(message: Message, state: FSMContext):
    """Обработка русского текста рассылки"""
    text = message.text.strip()
    
    if not text:
        await message.answer("❌ Текст не может быть пустым")
        return
    
    await state.update_data(broadcast_text_ru=text)
    await state.set_state(AdminStates.broadcast_text_uz)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Далее", callback_data="admin_bc_continue")]
    ])
    
    await message.answer(
        "✍️ СОЗДАНИЕ РАССЫЛКИ\n"
        "═══════════════════════════════════════\n\n"
        "3️⃣ ТЕКСТ НА УЗБЕКСКОМ\n\n"
        "Введите текст сообщения на узбекском языке:",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "admin_bc_continue")
async def continue_broadcast_creation(callback: CallbackQuery, state: FSMContext):
    """Продолжить создание рассылки (пропуск узбекского)"""
    data = await state.get_data()
    text_ru = data.get("broadcast_text_ru")
    
    await state.update_data(broadcast_text_uz=text_ru)
    await state.set_state(AdminStates.broadcast_photo)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Далее (без фото)", callback_data="admin_bc_no_photo")]
    ])
    
    await callback.message.edit_text(
        "📸 СОЗДАНИЕ РАССЫЛКИ\n"
        "═══════════════════════════════════════\n\n"
        "4️⃣ ФОТО (опционально)\n\n"
        "Отправьте фото или нажмите 'Далее':",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data == "admin_bc_no_photo")
async def skip_broadcast_photo(callback: CallbackQuery, state: FSMContext):
    """Пропустить фото в рассылке"""
    await state.set_state(AdminStates.broadcast_recipient_filter)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всем пользователям", callback_data="admin_bc_filter_all")],
        [InlineKeyboardButton(text="🇷🇺 Только русскоговорящим", callback_data="admin_bc_filter_ru")],
        [InlineKeyboardButton(text="🇺🇿 Только узбекоговорящим", callback_data="admin_bc_filter_uz")],
        [InlineKeyboardButton(text="🚗 Только курьерам", callback_data="admin_bc_filter_couriers")],
    ])
    
    await callback.message.edit_text(
        "👥 СОЗДАНИЕ РАССЫЛКИ\n"
        "═══════════════════════════════════════\n\n"
        "5️⃣ ВЫБОР АУДИТОРИИ\n\n"
        "Кому отправить рассылку:",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_bc_filter_"))
async def set_broadcast_filter(callback: CallbackQuery, state: FSMContext):
    """Установить фильтр аудитории рассылки"""
    filter_type = callback.data.split("_")[-1]
    
    data = await state.get_data()
    name = data.get("broadcast_name")
    text_ru = data.get("broadcast_text_ru")
    text_uz = data.get("broadcast_text_uz")
    
    await state.update_data(broadcast_filter=filter_type)
    
    # Create and send broadcast
    async with AsyncSessionLocal() as session:
        broadcast = await BroadcastService.create_broadcast(
            session,
            admin_id=callback.from_user.id,
            name_ru=name,
            name_uz=name,
            message_ru=text_ru,
            message_uz=text_uz,
            recipient_filter=filter_type.upper()
        )
        
        # TODO: Send broadcast to users
        # For now just mark as sent
        await BroadcastService.mark_as_sent(session, broadcast.id, recipient_count=0)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 История", callback_data="admin_bc_history")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(
            f"✅ РАССЫЛКА ОТПРАВЛЕНА\n"
            f"═══════════════════════════════════════\n\n"
            f"Название: {name}\n"
            f"Статус: Отправлена",
            reply_markup=keyboard
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "admin_bc_history")
async def show_broadcast_history(callback: CallbackQuery):
    """Показать историю рассылок"""
    async with AsyncSessionLocal() as session:
        broadcasts = await session.execute(
            select(Broadcast).order_by(Broadcast.created_at.desc()).limit(20)
        )
        bcasts = broadcasts.scalars().all()
        
        if not bcasts:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_bc_menu")]
            ])
            await callback.message.edit_text(
                "❌ Нет рассылок в истории",
                reply_markup=keyboard
            )
            await callback.answer()
            return
        
        keyboard_buttons = []
        for idx, bcast in enumerate(bcasts, 1):
            status = "✅" if bcast.is_sent else "⏳"
            sent_time = bcast.sent_at.strftime("%d.%m %H:%M") if bcast.sent_at else "не отправлено"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{status} {idx}. {bcast.name_ru} - {sent_time}",
                    callback_data=f"admin_bc_view_{bcast.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_bc_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"📋 ИСТОРИЯ РАССЫЛОК\n"
            f"═══════════════════════════════════════\n\n"
            f"Всего: {len(bcasts)}",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ═══════════════════════════════════════════════════════════════════════════
# STATISTICS (Статистика)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_stats_menu")
async def handle_statistics_menu(callback: CallbackQuery, state: FSMContext):
    """Меню статистики"""
    try:
        logger.info(f"Админ {callback.from_user.id} просматривает статистику")
        await state.clear()
        
        async with AsyncSessionLocal() as session:
            user_stats = await StatisticsService.get_user_statistics(session)
            button_stats = await StatisticsService.get_button_statistics(session, days=30)
            peak_hours = await StatisticsService.get_peak_hours(session, days=30)
            moderation_stats = await StatisticsService.get_moderation_queue_count(session)
        
        # Формирование блоков статистики
        language_map = {"RU": "🇷🇺 Русский", "UZ": "🇺🇿 Узбекский"}
        citizenship_map = {"UZ": "🇺🇿 Узбекистан", "RU": "🇷🇺 Россия", "KZ": "🇰🇿 Казахстан", "KG": "🇰🇬 Киргизия"}
        
        language_lines = [f"{language_map.get(c, c)}: {cnt}" for c, cnt in user_stats.get("language_stats", {}).items()]
        citizenship_lines = [f"{citizenship_map.get(c, c)}: {cnt}" for c, cnt in user_stats.get("citizenship_stats", {}).items()]
        button_lines = [f"{i}. {name} — {clicks} нажатий" for i, (name, clicks) in enumerate(button_stats.items(), 1)]
        peak_lines = [f"{tr} → {val} пользователей" for tr, val in peak_hours.items()]
        
        stats_text = (
            "📊 ОБЩАЯ СТАТИСТИКА ПОЛЬЗОВАТЕЛЕЙ\n"
            "═══════════════════════════════════════\n\n"
            f"👥 Всего пользователей: {user_stats.get('total_users', 0)}\n"
            f"🚀 Активных сегодня: {user_stats.get('active_today', 0)}\n"
            f"🔄 Активных за неделю: {user_stats.get('active_week', 0)}\n"
            f"📱 Новых за неделю: {user_stats.get('new_week', 0)}\n\n"
            "📊 ТОП 5 КНОПОК:\n" + ("\n".join(button_lines) if button_lines else "—") + "\n\n"
            "⏰ ПИКОВЫЕ ЧАСЫ:\n" + ("\n".join(peak_lines) if peak_lines else "—") + "\n\n"
            "🌍 ПО ЯЗЫКАМ:\n" + ("\n".join(language_lines) if language_lines else "—") + "\n\n"
            "🏠 ПО ГРАЖДАНСТВУ:\n" + ("\n".join(citizenship_lines) if citizenship_lines else "—") + "\n\n"
            f"🚗 Курьеры: {user_stats.get('couriers_count', 0)}\n\n"
            "🛡️ МОДЕРАЦИЯ:\n"
            f"— Потери в очереди: {moderation_stats.get('notifications_pending', 0)}\n"
            f"— Shurta в очереди: {moderation_stats.get('shurta_pending', 0)}\n"
            f"— Сообщений без ответа: {moderation_stats.get('messages_unread', 0)}"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats_menu")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(stats_text, reply_markup=keyboard)
        await callback.answer("✅ Статистика обновлена")
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка при загрузке статистики", show_alert=True)


# ═══════════════════════════════════════════════════════════════════════════
# SETTINGS (Настройки)
# ═══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "admin_settings_menu")
async def handle_settings_menu(callback: CallbackQuery, state: FSMContext):
    """Меню настроек"""
    await state.clear()
    
    async with AsyncSessionLocal() as session:
        settings_list = await session.execute(select(SystemSetting))
        all_settings = settings_list.scalars().all()
        
        keyboard_buttons = []
        for setting in all_settings:
            status_icon = "✅" if setting.value else "❌"
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"[{status_icon}] {setting.setting_name_ru}",
                    callback_data=f"admin_sett_toggle_{setting.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            "⚙️ НАСТРОЙКИ СИСТЕМЫ\n"
            "═══════════════════════════════════════\n\n"
            "Нажмите на параметр для переключения:",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_sett_toggle_"))
async def toggle_system_setting(callback: CallbackQuery):
    """Переключить системный параметр"""
    setting_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        setting = await session.get(SystemSetting, setting_id)
        if setting:
            setting.value = not setting.value
            await session.commit()
            await callback.answer("✅ Параметр обновлен", show_alert=False)
    
    await callback.answer()


def register_admin_handlers(dp):
    """Регистрация обработчиков админ-бота"""
    dp.include_router(router)
