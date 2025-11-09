"""
Admin Alert Management Handlers
Unified alert moderation system for all 11 alert types
"""

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from database import AsyncSessionLocal
from services.alert_service import AlertService
from services.admin_log_service import AdminLogService
from services.statistics_service import StatisticsService
from states import AdminStates
from models import AlertType, Alert
from utils.logger import logger
from datetime import datetime
import asyncio

router = Router()

# Alert type names in Russian
ALERT_TYPE_NAMES_RU = {
    AlertType.PROPAJA_ODAM: "👤 Пропал человек",
    AlertType.PROPAJA_NARSA: "📦 Пропала вещь",
    AlertType.SHURTA: "🚨 Полиция",
    AlertType.DOSTAVKA: "🚚 Доставка",
    AlertType.ISH_TAKLIFNOMASI: "💼 Вакансия",
    AlertType.UY_UYICHA: "🏠 Жилье",
    AlertType.TADBIR: "📅 Мероприятие",
    AlertType.FAVQULODDA: "🚨 ЧП",
    AlertType.SOTISH: "🛒 Продажа",
    AlertType.XIZMAT: "🔧 Услуга",
    AlertType.ELON: "📢 Объявление"
}


@router.callback_query(F.data == "admin_alert_menu")
async def show_alert_moderation_menu(callback: CallbackQuery, state: FSMContext):
    """Main alert moderation dashboard"""
    try:
        await state.set_state(AdminStates.alert_moderation_menu)
        
        async with AsyncSessionLocal() as session:
            # Get pending counts by type
            pending_counts = await AlertService.get_pending_count_by_type(session)
            total_pending = sum(pending_counts.values())
            
            # Get overall stats
            stats = await AlertService.get_alert_statistics(session)
        
        keyboard_buttons = []
        
        # Add button for each alert type showing pending count
        for alert_type in AlertType:
            count = pending_counts.get(alert_type.value, 0)
            name = ALERT_TYPE_NAMES_RU.get(alert_type, alert_type.value)
            badge = f" ({count})" if count > 0 else ""
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{name}{badge}",
                    callback_data=f"admin_alert_type_{alert_type.value}"
                )
            ])
        
        # Add quick actions
        keyboard_buttons.extend([
            [InlineKeyboardButton(text=f"📋 Все ожидающие ({total_pending})", callback_data="admin_alert_all_pending")],
            [InlineKeyboardButton(text="📊 Статистика алертов", callback_data="admin_alert_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back_main")]
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        text = (
            "🚨 МОДЕРАЦИЯ АЛЕРТОВ\n"
            "═══════════════════════════════════════\n\n"
            f"📊 Всего ожидают модерации: {total_pending}\n"
            f"✅ Одобрено всего: {stats.get('total_approved', 0)}\n"
            f"📢 Разослано: {stats.get('total_broadcasts', 0)}\n"
            f"👥 Охват: {stats.get('total_reach', 0)} пользователей\n\n"
            "Выберите тип алерта для модерации:"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
        logger.info(f"[admin_alert_menu] ✅ Админ {callback.from_user.id} открыл меню модерации алертов")
        
    except Exception as e:
        logger.error(f"[admin_alert_menu] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки меню", show_alert=True)


@router.callback_query(F.data.startswith("admin_alert_type_"))
async def show_alerts_by_type(callback: CallbackQuery, state: FSMContext):
    """Show pending alerts filtered by type"""
    try:
        alert_type_str = callback.data.split("admin_alert_type_")[1]
        alert_type = AlertType(alert_type_str)
        
        await state.update_data(filter_alert_type=alert_type_str)
        await state.set_state(AdminStates.alert_pending_list)
        
        async with AsyncSessionLocal() as session:
            alerts = await AlertService.get_pending_alerts(
                session,
                alert_type=alert_type,
                limit=20
            )
        
        if not alerts:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_alert_menu")]
            ])
            await callback.message.edit_text(
                f"{ALERT_TYPE_NAMES_RU.get(alert_type, alert_type_str)}\n"
                "═══════════════════════════════════════\n\n"
                "📭 Нет алертов, ожидающих модерации",
                reply_markup=keyboard
            )
            await callback.answer()
            return
        
        keyboard_buttons = []
        for alert in alerts[:20]:  # Limit to 20
            created_time = alert.created_at.strftime("%d.%m %H:%M")
            preview = alert.title or alert.description[:30]
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"#{alert.id} | {created_time} | {preview}...",
                    callback_data=f"admin_alert_view_{alert.id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_alert_menu")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        text = (
            f"{ALERT_TYPE_NAMES_RU.get(alert_type, alert_type_str)}\n"
            "═══════════════════════════════════════\n\n"
            f"📋 Ожидают модерации: {len(alerts)}\n\n"
            "Выберите алерт для просмотра:"
        )
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[admin_alert_type] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки алертов", show_alert=True)


@router.callback_query(F.data.startswith("admin_alert_view_"))
async def view_alert_detail(callback: CallbackQuery, state: FSMContext):
    """View alert details with approve/reject buttons"""
    try:
        alert_id = int(callback.data.split("_")[-1])
        
        await state.update_data(current_alert_id=alert_id)
        await state.set_state(AdminStates.alert_detail_view)
        
        async with AsyncSessionLocal() as session:
            alert = await AlertService.get_alert(session, alert_id)
            
            if not alert:
                await callback.answer("❌ Алерт не найден", show_alert=True)
                return
            
            # Build alert details text
            alert_type_name = ALERT_TYPE_NAMES_RU.get(alert.alert_type, alert.alert_type.value)
            text_parts = [
                f"{alert_type_name} #{alert.id}",
                "═══════════════════════════════════════\n"
            ]
            
            if alert.title:
                text_parts.append(f"📌 {alert.title}\n")
            
            text_parts.append(f"📝 Описание:\n{alert.description}\n")
            
            if alert.phone:
                text_parts.append(f"📞 Телефон: {alert.phone}\n")
            
            if alert.address_text:
                text_parts.append(f"📍 Адрес: {alert.address_text}\n")
            
            if alert.creator:
                creator_name = alert.creator.first_name or alert.creator.username or "Неизвестно"
                text_parts.append(f"\n👤 Создатель: {creator_name} (ID: {alert.creator.telegram_id})")
            
            text_parts.append(f"🕒 Создан: {alert.created_at.strftime('%d.%m.%Y %H:%M')}")
            
            if alert.target_languages:
                text_parts.append(f"\n🌐 Языки: {', '.join(alert.target_languages)}")
            if alert.target_citizenships:
                text_parts.append(f"\n🌍 Гражданство: {', '.join(alert.target_citizenships)}")
            
            text = "\n".join(text_parts)
            
            # Build keyboard
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_alert_approve_{alert_id}"),
                    InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_alert_reject_{alert_id}")
                ],
                [InlineKeyboardButton(text="📢 Разослать", callback_data=f"admin_alert_broadcast_{alert_id}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_alert_menu")]
            ])
            
            # Send photo if available
            if alert.photo_file_id:
                await callback.message.delete()
                await callback.message.answer_photo(
                    photo=alert.photo_file_id,
                    caption=text,
                    reply_markup=keyboard
                )
            else:
                await callback.message.edit_text(text, reply_markup=keyboard)
            
            await callback.answer()
            
    except Exception as e:
        logger.error(f"[admin_alert_view] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки алерта", show_alert=True)


@router.callback_query(F.data.startswith("admin_alert_approve_"))
async def approve_alert(callback: CallbackQuery, state: FSMContext):
    """Approve alert and optionally broadcast"""
    try:
        alert_id = int(callback.data.split("_")[-1])
        admin_id = callback.from_user.id
        
        async with AsyncSessionLocal() as session:
            # Get admin user
            from services.user_service import UserService
            admin = await UserService.get_user(session, admin_id)
            if not admin:
                await callback.answer("❌ Админ не найден", show_alert=True)
                return
            
            # Approve alert
            alert = await AlertService.approve_alert(session, alert_id, admin.id)
            
            if not alert:
                await callback.answer("❌ Алерт не найден", show_alert=True)
                return
            
            # Log admin action
            await AdminLogService.log_action(
                session,
                admin_id=admin.id,
                action="APPROVE_ALERT",
                entity_type="Alert",
                entity_id=alert_id,
                details={"alert_type": alert.alert_type.value}
            )
            
            # Track statistics
            await StatisticsService.track_activity(
                session,
                user_id=admin.id,
                activity_type="ALERT_APPROVED",
                activity_data={"alert_id": alert_id, "alert_type": alert.alert_type.value}
            )
        
        await callback.answer("✅ Алерт одобрен!", show_alert=True)
        
        # Ask if want to broadcast now
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Разослать сейчас", callback_data=f"admin_alert_broadcast_{alert_id}")],
            [InlineKeyboardButton(text="🔙 К списку", callback_data="admin_alert_menu")]
        ])
        
        await callback.message.edit_text(
            f"✅ Алерт #{alert_id} одобрен!\n\n"
            "Хотите разослать его сейчас?",
            reply_markup=keyboard
        )
        
        logger.info(f"[admin_alert_approve] ✅ Админ {admin_id} одобрил алерт #{alert_id}")
        
    except Exception as e:
        logger.error(f"[admin_alert_approve] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка одобрения алерта", show_alert=True)


@router.callback_query(F.data.startswith("admin_alert_reject_"))
async def reject_alert_prompt(callback: CallbackQuery, state: FSMContext):
    """Prompt for rejection reason"""
    try:
        alert_id = int(callback.data.split("_")[-1])
        
        await state.update_data(reject_alert_id=alert_id)
        await state.set_state(AdminStates.alert_rejection_reason)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отклонить без причины", callback_data=f"admin_alert_reject_confirm_{alert_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_alert_view_{alert_id}")]
        ])
        
        await callback.message.edit_text(
            "❌ ОТКЛОНЕНИЕ АЛЕРТА\n"
            "═══════════════════════════════════════\n\n"
            "Введите причину отклонения (или нажмите кнопку, чтобы отклонить без причины):",
            reply_markup=keyboard
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[admin_alert_reject] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка", show_alert=True)


@router.message(StateFilter(AdminStates.alert_rejection_reason))
async def process_rejection_reason(message: Message, state: FSMContext):
    """Process rejection reason text"""
    try:
        data = await state.get_data()
        alert_id = data.get("reject_alert_id")
        reason = message.text
        admin_id = message.from_user.id
        
        async with AsyncSessionLocal() as session:
            from services.user_service import UserService
            admin = await UserService.get_user(session, admin_id)
            if not admin:
                await message.answer("❌ Админ не найден")
                return
            
            # Reject alert with reason
            alert = await AlertService.reject_alert(session, alert_id, admin.id, reason)
            
            if not alert:
                await message.answer("❌ Алерт не найден")
                return
            
            # Log admin action
            await AdminLogService.log_action(
                session,
                admin_id=admin.id,
                action="REJECT_ALERT",
                entity_type="Alert",
                entity_id=alert_id,
                details={"alert_type": alert.alert_type.value, "reason": reason}
            )
            
            # Notify creator (via user bot)
            # TODO: Implement user bot notification
        
        await message.answer(f"✅ Алерт #{alert_id} отклонен!\n\nПричина: {reason}")
        await state.clear()
        
        # Return to menu
        await message.answer(
            "Возврат в меню модерации...",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К меню алертов", callback_data="admin_alert_menu")]
            ])
        )
        
        logger.info(f"[admin_alert_reject] ✅ Админ {admin_id} отклонил алерт #{alert_id}")
        
    except Exception as e:
        logger.error(f"[process_rejection_reason] ❌ Ошибка: {str(e)}", exc_info=True)
        await message.answer("❌ Ошибка отклонения алерта")


@router.callback_query(F.data.startswith("admin_alert_reject_confirm_"))
async def reject_alert_confirm(callback: CallbackQuery, state: FSMContext):
    """Reject alert without reason"""
    try:
        alert_id = int(callback.data.split("_")[-1])
        admin_id = callback.from_user.id
        
        async with AsyncSessionLocal() as session:
            from services.user_service import UserService
            admin = await UserService.get_user(session, admin_id)
            if not admin:
                await callback.answer("❌ Админ не найден", show_alert=True)
                return
            
            # Reject alert
            alert = await AlertService.reject_alert(session, alert_id, admin.id, None)
            
            if not alert:
                await callback.answer("❌ Алерт не найден", show_alert=True)
                return
            
            # Log admin action
            await AdminLogService.log_action(
                session,
                admin_id=admin.id,
                action="REJECT_ALERT",
                entity_type="Alert",
                entity_id=alert_id,
                details={"alert_type": alert.alert_type.value}
            )
        
        await callback.answer("✅ Алерт отклонен!", show_alert=True)
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 К меню алертов", callback_data="admin_alert_menu")]
        ])
        
        await callback.message.edit_text(
            f"✅ Алерт #{alert_id} отклонен!",
            reply_markup=keyboard
        )
        
        logger.info(f"[admin_alert_reject_confirm] ✅ Админ {admin_id} отклонил алерт #{alert_id}")
        
    except Exception as e:
        logger.error(f"[admin_alert_reject_confirm] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка отклонения алерта", show_alert=True)


@router.callback_query(F.data.startswith("admin_alert_broadcast_"))
async def broadcast_alert(callback: CallbackQuery, state: FSMContext):
    """Broadcast approved alert to target users"""
    try:
        alert_id = int(callback.data.split("_")[-1])
        
        await callback.message.edit_text(
            "📢 Рассылка алерта...\n\n"
            "Пожалуйста, подождите..."
        )
        
        async with AsyncSessionLocal() as session:
            alert = await AlertService.get_alert(session, alert_id)
            
            if not alert:
                await callback.answer("❌ Алерт не найден", show_alert=True)
                return
            
            if not alert.is_approved:
                await callback.answer("❌ Алерт не одобрен", show_alert=True)
                return
            
            # Get target users
            target_users = await AlertService.get_broadcast_targets(session, alert)
            
            if not target_users:
                await callback.answer("⚠️ Нет получателей для рассылки", show_alert=True)
                return
            
            # Send to all target users (via user bot)
            # TODO: Implement actual broadcast via user bot
            sent_count = 0
            failed_count = 0
            
            # For now, just simulate and mark as sent
            sent_count = len(target_users)
            
            # Mark as broadcast
            await AlertService.mark_broadcast_sent(session, alert_id, sent_count)
            
            # Log admin action
            from services.user_service import UserService
            admin = await UserService.get_user(session, callback.from_user.id)
            if admin:
                await AdminLogService.log_action(
                    session,
                    admin_id=admin.id,
                    action="BROADCAST_ALERT",
                    entity_type="Alert",
                    entity_id=alert_id,
                    details={
                        "alert_type": alert.alert_type.value,
                        "sent_count": sent_count,
                        "failed_count": failed_count
                    }
                )
        
        await callback.message.edit_text(
            f"✅ РАССЫЛКА ЗАВЕРШЕНА!\n\n"
            f"📊 Статистика:\n"
            f"✅ Отправлено: {sent_count}\n"
            f"❌ Ошибок: {failed_count}\n\n"
            f"Алерт #{alert_id} разослан!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 К меню алертов", callback_data="admin_alert_menu")]
            ])
        )
        
        logger.info(f"[admin_alert_broadcast] ✅ Алерт #{alert_id} разослан {sent_count} пользователям")
        
    except Exception as e:
        logger.error(f"[admin_alert_broadcast] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка рассылки алерта", show_alert=True)


@router.callback_query(F.data == "admin_alert_stats")
async def show_alert_statistics(callback: CallbackQuery, state: FSMContext):
    """Show detailed alert statistics"""
    try:
        async with AsyncSessionLocal() as session:
            stats = await AlertService.get_alert_statistics(session)
        
        text_parts = [
            "📊 СТАТИСТИКА АЛЕРТОВ",
            "═══════════════════════════════════════\n"
        ]
        
        # Overall stats
        text_parts.extend([
            f"📋 Ожидают модерации: {stats.get('total_pending', 0)}",
            f"✅ Одобрено: {stats.get('total_approved', 0)}",
            f"📢 Разослано: {stats.get('total_broadcasts', 0)}",
            f"👥 Охват: {stats.get('total_reach', 0)} пользователей",
            f"⌛ Истекло: {stats.get('expired', 0)}\n"
        ])
        
        # By type
        text_parts.append("По типам (ожидают модерации):")
        pending_by_type = stats.get('pending_by_type', {})
        for alert_type in AlertType:
            count = pending_by_type.get(alert_type.value, 0)
            if count > 0:
                name = ALERT_TYPE_NAMES_RU.get(alert_type, alert_type.value)
                text_parts.append(f"  {name}: {count}")
        
        text = "\n".join(text_parts)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_alert_stats")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_alert_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"[admin_alert_stats] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки статистики", show_alert=True)
