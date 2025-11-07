from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
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
from services.courier_service import CourierService
from services.admin_log_service import AdminLogService
from states import AdminStates
from utils.logger import logger
from sqlalchemy import select, func
from models import UserMessage, Delivery, Notification, ShurtaAlert, User

router = Router()


def get_admin_main_menu():
    """Get admin main menu with inline buttons"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Hujjat yordami", callback_data="admin_documents")],
        [InlineKeyboardButton(text="🚚 Dostavka xizmati", callback_data="admin_delivery")],
        [InlineKeyboardButton(text="🔔 Propaja", callback_data="admin_propaja")],
        [InlineKeyboardButton(text="🚨 Shurta", callback_data="admin_shurta")],
        [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
        [InlineKeyboardButton(text="💬 Xabarlar", callback_data="admin_messages")],
        [InlineKeyboardButton(text="📢 Rассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="⚙️ Sozlamalar", callback_data="admin_settings")],
        [InlineKeyboardButton(text="🔙 Chiqish", callback_data="admin_exit")]
    ])
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
            
            # Create/update admin user
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
            reply_markup=get_admin_main_menu()
        )


# ============= DOCUMENT MANAGEMENT =============

@router.callback_query(F.data == "admin_documents")
async def handle_documents_menu(callback: CallbackQuery):
    """Show document management menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇺🇿 Oʻzbekiston", callback_data="admin_doc_cit_UZ")],
        [InlineKeyboardButton(text="🇷🇺 Rossiya", callback_data="admin_doc_cit_RU")],
        [InlineKeyboardButton(text="🇰🇿 Qazaqstan", callback_data="admin_doc_cit_KZ")],
        [InlineKeyboardButton(text="🇰🇬 Qirgiziston", callback_data="admin_doc_cit_KG")],
        [InlineKeyboardButton(text="← Orqaga", callback_data="admin_back_main")]
    ])
    
    await callback.message.edit_text(
        "Hujjat yordami bo'limini tanlang:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_doc_cit_"))
async def show_documents_for_citizenship(callback: CallbackQuery):
    """Show documents for selected citizenship"""
    citizenship = callback.data.split("_")[-1]
    
    async with AsyncSessionLocal() as session:
        documents = await DocumentService.get_documents_by_citizenship(session, citizenship)
        
        buttons = []
        for doc in documents:
            buttons.append([InlineKeyboardButton(
                text=f"✏️ {doc.name_ru}",
                callback_data=f"admin_doc_edit_{doc.id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="➕ Yangi hujjat qo'shish", callback_data=f"admin_doc_add_{citizenship}")])
        buttons.append([InlineKeyboardButton(text="← Orqaga", callback_data="admin_documents")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        citizenship_name = {"UZ": "🇺🇿 Oʻzbekiston", "RU": "🇷🇺 Rossiya", "KZ": "🇰🇿 Qazaqstan", "KG": "🇰🇬 Qirgiziston"}.get(citizenship)
        
        await callback.message.edit_text(
            f"{citizenship_name} uchun hujjatlar:",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_doc_edit_"))
async def edit_document(callback: CallbackQuery):
    """Show document edit menu"""
    doc_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        if not document:
            await callback.answer("Hujjat topilmadi")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Nomini o'zgartirish", callback_data=f"admin_doc_name_{doc_id}")],
            [InlineKeyboardButton(text="📄 Matnini o'zgartirish", callback_data=f"admin_doc_content_{doc_id}")],
            [InlineKeyboardButton(text="🖼️ Rasmni o'zgartirish", callback_data=f"admin_doc_photo_{doc_id}")],
            [InlineKeyboardButton(text="🔗 Havolani o'zgartirish", callback_data=f"admin_doc_telegraph_{doc_id}")],
            [InlineKeyboardButton(text="⚙️ Tugmalarni boshqarish", callback_data=f"admin_doc_buttons_{doc_id}")],
            [InlineKeyboardButton(text="🗑️ Hujjatni o'chirib tashlash", callback_data=f"admin_doc_delete_{doc_id}")],
            [InlineKeyboardButton(text="← Orqaga", callback_data=f"admin_doc_cit_{document.citizenship_scope}")]
        ])
        
        await callback.message.edit_text(
            f"HUJJAT: {document.name_ru}\n═══════════════════════════",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_doc_buttons_"))
async def manage_document_buttons(callback: CallbackQuery):
    """Manage document buttons"""
    doc_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        document = await DocumentService.get_document(session, doc_id)
        buttons_list = await DocumentService.get_document_buttons(session, doc_id)
        
        keyboard_buttons = []
        for btn in buttons_list:
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"✏️ Tugma: \"{btn.text_ru}\"",
                callback_data=f"admin_btn_edit_{btn.id}"
            )])
        
        keyboard_buttons.append([InlineKeyboardButton(text="➕ Yangi tugma qo'shish", callback_data=f"admin_btn_add_{doc_id}")])
        keyboard_buttons.append([InlineKeyboardButton(text="← Orqaga", callback_data=f"admin_doc_edit_{doc_id}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            f"{document.name_ru} - Tugmalar:\n═══════════════════════════",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ============= DELIVERY MANAGEMENT =============

@router.callback_query(F.data == "admin_delivery")
async def handle_delivery_menu(callback: CallbackQuery):
    """Show delivery management menu"""
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select, func
        from models import Delivery
        
        # Count deliveries by status
        waiting = await session.execute(select(func.count(Delivery.id)).where(Delivery.status == "WAITING"))
        waiting_count = waiting.scalar() or 0
        
        completed = await session.execute(select(func.count(Delivery.id)).where(Delivery.status == "COMPLETED"))
        completed_count = completed.scalar() or 0
        
        rejected = await session.execute(select(func.count(Delivery.id)).where(Delivery.status.in_(["REJECTED", "CANCELLED"])))
        rejected_count = rejected.scalar() or 0
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"📬 Faol zakazy ({waiting_count})", callback_data="admin_del_active")],
            [InlineKeyboardButton(text=f"✅ Bajarilgan ({completed_count})", callback_data="admin_del_completed")],
            [InlineKeyboardButton(text=f"❌ Rad etilgan ({rejected_count})", callback_data="admin_del_rejected")],
            [InlineKeyboardButton(text="👨‍💼 Kuryer boshqaruvi", callback_data="admin_couriers")],
            [InlineKeyboardButton(text="← Orqaga", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(
            "Dostavka bo'limi\n═════════════════",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ============= STATISTICS =============

@router.callback_query(F.data == "admin_stats")
async def handle_statistics(callback: CallbackQuery):
    """Handle statistics"""
    async with AsyncSessionLocal() as session:
        # Get user stats
        user_stats = await UserService.get_user_stats(session)
        
        # Get delivery stats
        total_deliveries = await session.execute(select(func.count(Delivery.id)))
        total_del = total_deliveries.scalar() or 0
        
        active_deliveries = await session.execute(
            select(func.count(Delivery.id)).where(Delivery.status == "WAITING")
        )
        active_del = active_deliveries.scalar() or 0
        
        # Get notification stats
        total_notifications = await session.execute(select(func.count(Notification.id)))
        total_notif = total_notifications.scalar() or 0
        
        # Get shurta stats
        total_shurta = await session.execute(select(func.count(ShurtaAlert.id)))
        total_shurt = total_shurta.scalar() or 0
        
        # Get courier stats
        couriers = await session.execute(select(func.count(User.id)).where(User.is_courier == True))
        courier_count = couriers.scalar() or 0
        
        message_text = f"""
STATISTIKA PANELI
═════════════════

👥 Foydalanuvchilar: {user_stats.get('total', 0)}
🚚 Faol zakasy: {active_del}
📦 Propaja: {total_notif}
🚨 Shurta: {total_shurt}
👨‍💼 Kuryer: {courier_count}
"""
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👁️ Batafsil ko'rish", callback_data="admin_stats_detail")],
            [InlineKeyboardButton(text="← Orqaga", callback_data="admin_back_main")]
        ])
        
        await callback.message.edit_text(message_text, reply_markup=keyboard)
    
    await callback.answer()


# ============= MESSAGES FROM USERS =============

@router.callback_query(F.data == "admin_messages")
async def handle_user_messages(callback: CallbackQuery):
    """Show user messages"""
    async with AsyncSessionLocal() as session:
        unread_count = await session.execute(
            select(func.count(UserMessage.id)).where(UserMessage.is_read == False)
        )
        unread = unread_count.scalar() or 0
        
        messages = await session.execute(
            select(UserMessage).order_by(UserMessage.created_at.desc()).limit(10)
        )
        user_messages = messages.scalars().all()
        
        if not user_messages:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="← Orqaga", callback_data="admin_back_main")]
            ])
            await callback.message.edit_text("Xabarlar yo'q.", reply_markup=keyboard)
            await callback.answer()
            return
        
        buttons = []
        for msg in user_messages:
            preview = msg.message_text[:30] + "..." if len(msg.message_text) > 30 else msg.message_text
            status = "🔴" if not msg.is_read else "✅"
            buttons.append([InlineKeyboardButton(
                text=f"{status} @{msg.user.username if msg.user else 'Unknown'} - {preview}",
                callback_data=f"admin_msg_view_{msg.id}"
            )])
        
        buttons.append([InlineKeyboardButton(text="← Orqaga", callback_data="admin_back_main")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await callback.message.edit_text(
            f"Foydalanuvchilardan xabarlar\n═════════════════════════════\n\nO'qilmagan: {unread}",
            reply_markup=keyboard
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("admin_msg_view_"))
async def view_user_message(callback: CallbackQuery):
    """View specific user message"""
    msg_id = int(callback.data.split("_")[-1])
    
    async with AsyncSessionLocal() as session:
        message = await UserMessageService.get_message(session, msg_id)
        if not message:
            await callback.answer("Xabar topilmadi")
            return
        
        # Mark as read
        await UserMessageService.mark_as_read(session, msg_id)
        
        user_info = f"@{message.user.username}" if message.user.username else f"ID: {message.user_id}"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Javob", callback_data=f"admin_msg_reply_{msg_id}")],
            [InlineKeyboardButton(text="🗑️ O'chirib tashlash", callback_data=f"admin_msg_delete_{msg_id}")],
            [InlineKeyboardButton(text="← Orqaga", callback_data="admin_messages")]
        ])
        
        await callback.message.edit_text(
            f"Xabar: {user_info}\n═════════════════\n\n{message.message_text}",
            reply_markup=keyboard
        )
    
    await callback.answer()


# ============= BROADCAST =============

@router.callback_query(F.data == "admin_broadcast")
async def handle_broadcast(callback: CallbackQuery, state: FSMContext):
    """Handle broadcast menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Yangi xabarnoma", callback_data="admin_bc_new")],
        [InlineKeyboardButton(text="📋 O'tgan xabarnomalar", callback_data="admin_bc_history")],
        [InlineKeyboardButton(text="← Orqaga", callback_data="admin_back_main")]
    ])
    
    await callback.message.edit_text(
        "Xabarnoma jo'natish\n═══════════════════",
        reply_markup=keyboard
    )
    await callback.answer()


# ============= BACK TO MAIN =============

@router.callback_query(F.data == "admin_back_main")
async def back_to_admin_main(callback: CallbackQuery):
    """Go back to admin main menu"""
    await callback.message.edit_text(
        "🔐 Админ-панель\n\nДобро пожаловать в систему управления.",
        reply_markup=get_admin_main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_exit")
async def exit_admin(callback: CallbackQuery):
    """Exit admin panel"""
    await callback.message.delete()
    await callback.answer()


def register_admin_handlers(dp):
    """Register admin handlers with dispatcher"""
    dp.include_router(router)
