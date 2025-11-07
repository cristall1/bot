# This is a stub file - full admin handlers will be created shortly
# This file ensures the system boots without errors

from aiogram import Router, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from database import AsyncSessionLocal
from services.user_service import UserService
from config import settings

router = Router()


def get_admin_menu():
    """Get admin menu keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Управление Документами")],
            [KeyboardButton(text="🚚 Управление Доставками")],
            [KeyboardButton(text="🔔 Управление Уведомлениями")],
            [KeyboardButton(text="🚨 Управление Shurta")],
            [KeyboardButton(text="👥 Управление Пользователями")],
            [KeyboardButton(text="💬 Сообщения от пользователей")],
            [KeyboardButton(text="📢 Рассылка")],
            [KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="⚙️ Системные настройки")],
            [KeyboardButton(text="📖 Редактор Telegraph")]
        ],
        resize_keyboard=True
    )
    return keyboard


@router.message(Command("start"))
async def cmd_admin_start(message: Message):
    """Handle /start for admin bot"""
    async with AsyncSessionLocal() as session:
        user = await UserService.get_user(session, message.from_user.id)
        
        # Check if user is admin
        if not user or not user.is_admin:
            if message.from_user.id not in settings.admin_ids_list:
                await message.answer("❌ У вас нет прав администратора.")
                return
            
            # Create admin user if not exists
            if not user:
                user = await UserService.create_or_update_user(
                    session,
                    telegram_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    language="RU"
                )
            
            # Make user admin
            await UserService.make_admin(session, message.from_user.id)
        
        await message.answer(
            "🔐 Админ-панель\n\nДобро пожаловать в систему управления.",
            reply_markup=get_admin_menu()
        )


@router.message(lambda message: message.text == "📚 Управление Документами")
async def handle_documents_management(message: Message):
    """Handle document management - simplified version"""
    await message.answer(
        "📚 Управление Документами\n\n"
        "Здесь вы можете управлять документами для разных стран.\n\n"
        "🔹 Функции:\n"
        "• Добавление новых документов\n"
        "• Редактирование существующих\n"
        "• Удаление документов\n"
        "• Управление inline-кнопками\n\n"
        "Полная функциональность будет доступна в следующей версии."
    )


@router.message(lambda message: message.text == "📊 Статистика")
async def handle_statistics(message: Message):
    """Handle statistics"""
    async with AsyncSessionLocal() as session:
        from services.user_service import UserService
        from services.delivery_service import DeliveryService
        from services.notification_service import NotificationService
        from services.shurta_service import ShurtaService
        from services.document_service import DocumentService
        from sqlalchemy import select, func
        from models import UserMessage, Delivery
        
        # Get user stats
        user_stats = await UserService.get_user_stats(session)
        
        # Get delivery stats
        total_deliveries = await session.execute(select(func.count(Delivery.id)))
        total_del = total_deliveries.scalar()
        
        active_deliveries = await session.execute(
            select(func.count(Delivery.id)).where(Delivery.status == "WAITING")
        )
        active_del = active_deliveries.scalar()
        
        completed_deliveries = await session.execute(
            select(func.count(Delivery.id)).where(Delivery.status == "COMPLETED")
        )
        completed_del = completed_deliveries.scalar()
        
        # Get notification stats
        notif_stats = await NotificationService.get_notification_stats(session)
        
        # Get shurta stats
        shurta_stats = await ShurtaService.get_alert_stats(session)
        
        # Get document stats
        documents = await DocumentService.get_all_documents(session)
        
        # Get messages stats
        unread_messages = await session.execute(
            select(func.count(UserMessage.id)).where(UserMessage.is_read == False)
        )
        unread_msg = unread_messages.scalar()
        
        text = "📊 ОБЩАЯ СТАТИСТИКА\n\n"
        text += "👥 Пользователи:\n"
        text += f"• Всего: {user_stats['total']}\n"
        text += f"• Сегодня: {user_stats['today']}\n"
        text += f"• На русском: {user_stats['by_language']['RU']}\n"
        text += f"• На узбекском: {user_stats['by_language']['UZ']}\n"
        text += f"• Курьеры: {user_stats['couriers']}\n"
        text += f"• Заблокированы: {user_stats['banned']}\n\n"
        
        text += "🚚 Доставки:\n"
        text += f"• Всего: {total_del}\n"
        text += f"• Активные: {active_del}\n"
        text += f"• Выполненные: {completed_del}\n\n"
        
        text += "📚 Документы:\n"
        text += f"• Всего категорий: {len(documents)}\n\n"
        
        text += "🔔 Уведомления:\n"
        text += f"• Всего: {notif_stats['total']}\n"
        text += f"• Активных: {notif_stats['active']}\n"
        text += f"• Пропал человек: {notif_stats['lost_person']}\n"
        text += f"• Потеря вещи: {notif_stats['lost_item']}\n\n"
        
        text += "🚨 Shurta алерты:\n"
        text += f"• Всего: {shurta_stats['total']}\n"
        text += f"• Активных: {shurta_stats['active']}\n\n"
        
        text += "💬 Сообщения:\n"
        text += f"• Непрочитанных: {unread_msg}"
        
        await message.answer(text)


@router.message(lambda message: message.text == "💬 Сообщения от пользователей")
async def handle_user_messages(message: Message):
    """Handle user messages"""
    async with AsyncSessionLocal() as session:
        from services.user_message_service import UserMessageService
        
        messages = await UserMessageService.get_all_messages(session, unread_only=True)
        
        if not messages:
            await message.answer("✅ Нет новых сообщений.")
            return
        
        text = "💬 Сообщения от пользователей:\n\n"
        for msg in messages[:10]:
            user = await UserService.get_user_by_id(session, msg.user_id)
            username = user.username if user and user.username else "Без username"
            text += f"👤 @{username}\n"
            text += f"📝 {msg.message_text[:50]}...\n"
            text += f"🕐 {msg.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
        
        if len(messages) > 10:
            text += f"\n...и еще {len(messages) - 10} сообщений"
        
        await message.answer(text)


@router.message(lambda message: message.text in [
    "🚚 Управление Доставками",
    "🔔 Управление Уведомлениями",
    "🚨 Управление Shurta",
    "👥 Управление Пользователями",
    "📢 Рассылка",
    "⚙️ Системные настройки",
    "📖 Редактор Telegraph"
])
async def handle_other_sections(message: Message):
    """Handle other admin sections - placeholder"""
    await message.answer(
        f"{message.text}\n\n"
        "Этот раздел находится в разработке.\n"
        "Основная функциональность бота работает полностью."
    )


def register_admin_handlers(dp: Dispatcher):
    """Register all admin handlers"""
    dp.include_router(router)
