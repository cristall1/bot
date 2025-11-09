"""
Admin Export Handlers
Export data to CSV, JSON, and SQLite formats
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
from aiogram.fsm.context import FSMContext
from database import AsyncSessionLocal
from utils.exporter import ExportService
from states import AdminStates
from models import AlertType
from utils.logger import logger
from config import settings
import os

router = Router()


@router.callback_query(F.data == "admin_export_menu")
async def show_export_menu(callback: CallbackQuery, state: FSMContext):
    """Main export menu"""
    try:
        await state.set_state(AdminStates.export_menu)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Экспорт алертов", callback_data="admin_export_alerts")],
            [InlineKeyboardButton(text="👥 Экспорт пользователей", callback_data="admin_export_users")],
            [InlineKeyboardButton(text="🚚 Экспорт доставок", callback_data="admin_export_deliveries")],
            [InlineKeyboardButton(text="💾 Дамп базы данных (SQLite)", callback_data="admin_export_database")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        text = (
            "📤 ЭКСПОРТ ДАННЫХ\n"
            "═══════════════════════════════════════\n\n"
            "Выберите что экспортировать:\n\n"
            "• CSV - табличный формат для Excel\n"
            "• JSON - структурированные данные\n"
            "• SQLite - полный дамп базы данных"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
        logger.info(f"[admin_export_menu] ✅ Админ {callback.from_user.id} открыл меню экспорта")
        
    except Exception as e:
        logger.error(f"[admin_export_menu] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки меню", show_alert=True)


@router.callback_query(F.data == "admin_export_alerts")
async def export_alerts_menu(callback: CallbackQuery, state: FSMContext):
    """Choose format for alerts export"""
    try:
        await state.set_state(AdminStates.export_format_selection)
        await state.update_data(export_type="alerts")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 CSV", callback_data="admin_export_do_alerts_csv")],
            [InlineKeyboardButton(text="📄 JSON", callback_data="admin_export_do_alerts_json")],
            [InlineKeyboardButton(text="📝 TXT", callback_data="admin_export_do_alerts_txt")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
        ])
        
        text = (
            "📋 ЭКСПОРТ АЛЕРТОВ\n"
            "═══════════════════════════════════════\n\n"
            "Выберите формат экспорта:"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[export_alerts_menu] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_export_do_alerts_csv")
async def do_export_alerts_csv(callback: CallbackQuery, state: FSMContext):
    """Export alerts to CSV"""
    try:
        await callback.message.edit_text(
            "⏳ Экспорт алертов в CSV...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            # Export to CSV
            filepath = await ExportService.export_alerts_csv(session)
        
        # Send file
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Экспорт алертов завершен!\n\n📊 CSV файл готов."
        )
        
        # Clean up
        ExportService.cleanup_export_file(filepath)
        
        # Return to menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_alerts_csv] ✅ Админ {callback.from_user.id} экспортировал алерты в CSV")
        
    except Exception as e:
        logger.error(f"[export_alerts_csv] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )


@router.callback_query(F.data == "admin_export_do_alerts_json")
async def do_export_alerts_json(callback: CallbackQuery, state: FSMContext):
    """Export alerts to JSON"""
    try:
        await callback.message.edit_text(
            "⏳ Экспорт алертов в JSON...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            # Export to JSON
            filepath = await ExportService.export_alerts_json(session)
        
        # Send file
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Экспорт алертов завершен!\n\n📄 JSON файл готов."
        )
        
        # Clean up
        ExportService.cleanup_export_file(filepath)
        
        # Return to menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_alerts_json] ✅ Админ {callback.from_user.id} экспортировал алерты в JSON")
        
    except Exception as e:
        logger.error(f"[export_alerts_json] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )


@router.callback_query(F.data == "admin_export_do_alerts_txt")
async def do_export_alerts_txt(callback: CallbackQuery, state: FSMContext):
    """Export alerts to TXT"""
    try:
        await callback.message.edit_text(
            "⏳ Экспорт алертов в TXT...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            filepath = await ExportService.export_alerts_txt(session)
        
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Экспорт алертов завершен!\n\n📝 TXT файл готов."
        )
        
        ExportService.cleanup_export_file(filepath)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_alerts_txt] ✅ Админ {callback.from_user.id} экспортировал алерты в TXT")
        
    except Exception as e:
        logger.error(f"[export_alerts_txt] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )


@router.callback_query(F.data == "admin_export_users")
async def export_users_menu(callback: CallbackQuery, state: FSMContext):
    """Choose format for users export"""
    try:
        await state.update_data(export_type="users")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 CSV", callback_data="admin_export_do_users_csv")],
            [InlineKeyboardButton(text="📝 TXT", callback_data="admin_export_do_users_txt")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
        ])
        
        text = (
            "👥 ЭКСПОРТ ПОЛЬЗОВАТЕЛЕЙ\n"
            "═══════════════════════════════════════\n\n"
            "Выберите формат экспорта:"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[export_users_menu] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_export_do_users_csv")
async def do_export_users_csv(callback: CallbackQuery, state: FSMContext):
    """Export users to CSV"""
    try:
        await callback.message.edit_text(
            "⏳ Экспорт пользователей в CSV...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            # Export to CSV
            filepath = await ExportService.export_users_csv(session)
        
        # Send file
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Экспорт пользователей завершен!\n\n📊 CSV файл готов."
        )
        
        # Clean up
        ExportService.cleanup_export_file(filepath)
        
        # Return to menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_users_csv] ✅ Админ {callback.from_user.id} экспортировал пользователей в CSV")
        
    except Exception as e:
        logger.error(f"[export_users_csv] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )


@router.callback_query(F.data == "admin_export_do_users_txt")
async def do_export_users_txt(callback: CallbackQuery, state: FSMContext):
    """Export users to TXT"""
    try:
        await callback.message.edit_text(
            "⏳ Экспорт пользователей в TXT...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            filepath = await ExportService.export_users_txt(session)
        
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Экспорт пользователей завершен!\n\n📝 TXT файл готов."
        )
        
        ExportService.cleanup_export_file(filepath)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_users_txt] ✅ Админ {callback.from_user.id} экспортировал пользователей в TXT")
        
    except Exception as e:
        logger.error(f"[export_users_txt] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )


@router.callback_query(F.data == "admin_export_deliveries")
async def export_deliveries_menu(callback: CallbackQuery, state: FSMContext):
    """Choose format for deliveries export"""
    try:
        await state.update_data(export_type="deliveries")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📊 CSV", callback_data="admin_export_do_deliveries_csv")],
            [InlineKeyboardButton(text="📝 TXT", callback_data="admin_export_do_deliveries_txt")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
        ])
        
        text = (
            "🚚 ЭКСПОРТ ДОСТАВОК\n"
            "═══════════════════════════════════════\n\n"
            "Выберите формат экспорта:"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[export_deliveries_menu] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


@router.callback_query(F.data == "admin_export_do_deliveries_csv")
async def do_export_deliveries_csv(callback: CallbackQuery, state: FSMContext):
    """Export deliveries to CSV"""
    try:
        await callback.message.edit_text(
            "⏳ Экспорт доставок в CSV...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            # Export to CSV
            filepath = await ExportService.export_deliveries_csv(session)
        
        # Send file
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Экспорт доставок завершен!\n\n📊 CSV файл готов."
        )
        
        # Clean up
        ExportService.cleanup_export_file(filepath)
        
        # Return to menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_deliveries_csv] ✅ Админ {callback.from_user.id} экспортировал доставки в CSV")
        
    except Exception as e:
        logger.error(f"[export_deliveries_csv] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )


@router.callback_query(F.data == "admin_export_do_deliveries_txt")
async def do_export_deliveries_txt(callback: CallbackQuery, state: FSMContext):
    """Export deliveries to TXT"""
    try:
        await callback.message.edit_text(
            "⏳ Экспорт доставок в TXT...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            filepath = await ExportService.export_deliveries_txt(session)
        
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Экспорт доставок завершен!\n\n📝 TXT файл готов."
        )
        
        ExportService.cleanup_export_file(filepath)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_deliveries_txt] ✅ Админ {callback.from_user.id} экспортировал доставки в TXT")
        
    except Exception as e:
        logger.error(f"[export_deliveries_txt] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )


@router.callback_query(F.data == "admin_export_database")
async def do_export_database(callback: CallbackQuery, state: FSMContext):
    """Export entire database to SQLite dump"""
    try:
        await callback.message.edit_text(
            "⏳ Создание дампа базы данных...\n\n"
            "Пожалуйста, подождите..."
        )
        
        # Export database
        filepath = await ExportService.export_database_sqlite(settings.database_url)
        
        # Send file
        file = FSInputFile(filepath)
        await callback.message.answer_document(
            document=file,
            caption="✅ Дамп базы данных готов!\n\n💾 SQLite файл содержит все таблицы и данные."
        )
        
        # Clean up
        ExportService.cleanup_export_file(filepath)
        
        # Return to menu
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню экспорта", callback_data="admin_export_menu")]
        ])
        await callback.message.edit_text(
            "✅ Файл отправлен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[export_database] ✅ Админ {callback.from_user.id} экспортировал дамп базы данных")
        
    except Exception as e:
        logger.error(f"[export_database] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка экспорта\n\n"
            "Экспорт базы данных возможен только для SQLite.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_export_menu")]
            ])
        )
