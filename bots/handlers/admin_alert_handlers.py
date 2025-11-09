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
from utils.message_helpers import delete_message_later
from bot_registry import get_admin_bot, get_user_bot
from datetime import datetime
import asyncio

router = Router()

# Alert type names in Russian (COURIER_NEEDED hidden from UI per ticket)
ALERT_TYPE_NAMES_RU = {
    AlertType.SHURTA: "🚨 Полиция",
    AlertType.MISSING_PERSON: "👤 Пропал человек",
    AlertType.LOST_ITEM: "📦 Потеря вещи",
    AlertType.SCAM_WARNING: "⚠️ Мошенничество",
    AlertType.MEDICAL_EMERGENCY: "🏥 Медпомощь",
    AlertType.ACCOMMODATION_NEEDED: "🏠 Нужно жилье",
    AlertType.RIDE_SHARING: "🚗 Попутчики",
    AlertType.JOB_POSTING: "💼 Вакансия",
    AlertType.LOST_DOCUMENT: "📄 Потеря документа",
    AlertType.EVENT_ANNOUNCEMENT: "🎉 Мероприятие",
    # AlertType.COURIER_NEEDED removed from UI - delivery managed through Delivery section
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
            if alert_type == AlertType.COURIER_NEEDED:
                # Courier requests managed via Delivery flow - skip from moderation menu
                continue
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
    """Approve alert and automatically broadcast to users"""
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
        
        await callback.answer("✅ Алерт одобрен! Начинаем рассылку...", show_alert=True)
        
        # DELETE MODERATION MESSAGE IMMEDIATELY (not after 10 seconds)
        admin_bot = get_admin_bot()
        if admin_bot:
            from utils.message_helpers import delete_message_immediately
            asyncio.create_task(
                delete_message_immediately(admin_bot, callback.message.chat.id, callback.message.message_id)
            )
        
        # AUTOMATICALLY TRIGGER BROADCAST (FIX #5 - broadcast must work!)
        # Start broadcast in background immediately after approval
        asyncio.create_task(_broadcast_alert_task(alert_id, callback.message.chat.id))
        
        logger.info(f"[admin_alert_approve] ✅ Админ {admin_id} одобрил алерт #{alert_id} - начата рассылка")
        
    except Exception as e:
        logger.error(f"[admin_alert_approve] ❌ Ошибка: {str(e)}", exc_info=True)
        await callback.answer("❌ Ошибка одобрения алерта", show_alert=True)


async def _broadcast_alert_task(alert_id: int, admin_chat_id: int):
    """Background task to broadcast alert to users"""
    try:
        user_bot = get_user_bot()
        admin_bot = get_admin_bot()
        
        if not user_bot:
            logger.error(f"[_broadcast_alert_task] ❌ User Bot не доступен!")
            return
        
        async with AsyncSessionLocal() as session:
            alert = await AlertService.get_alert(session, alert_id)
            
            if not alert or not alert.is_approved:
                logger.error(f"[_broadcast_alert_task] ❌ Алерт #{alert_id} не найден или не одобрен")
                return
            
            # Get target users
            target_users = await AlertService.get_broadcast_targets(session, alert)
            
            if not target_users:
                logger.warning(f"[_broadcast_alert_task] ⚠️ Нет получателей для алерта #{alert_id}")
                if admin_bot:
                    await admin_bot.send_message(
                        chat_id=admin_chat_id,
                        text=f"⚠️ Алерт #{alert_id}: Нет получателей для рассылки"
                    )
                return
            
            logger.info(f"[_broadcast_alert_task] 📢 Начинаем рассылку алерта #{alert_id} для {len(target_users)} пользователей")
            
            # Send to all target users
            sent_count = 0
            failed_count = 0
            
            for user in target_users:
                try:
                    # Build alert message based on user language
                    message_text = _format_alert_message(alert, user.language)
                    
                    # Send photo if available
                    if alert.photo_file_id:
                        await user_bot.send_photo(
                            chat_id=user.telegram_id,
                            photo=alert.photo_file_id,
                            caption=message_text,
                            parse_mode="HTML"
                        )
                    else:
                        await user_bot.send_message(
                            chat_id=user.telegram_id,
                            text=message_text,
                            parse_mode="HTML"
                        )
                    
                    # Send location if available
                    if alert.latitude and alert.longitude:
                        await user_bot.send_location(
                            chat_id=user.telegram_id,
                            latitude=alert.latitude,
                            longitude=alert.longitude
                        )
                    
                    sent_count += 1
                    logger.debug(f"[_broadcast_alert_task] ✅ Отправлено пользователю {user.telegram_id}")
                    
                except Exception as e:
                    failed_count += 1
                    logger.error(f"[_broadcast_alert_task] ❌ Ошибка отправки пользователю {user.telegram_id}: {str(e)}")
            
            # Mark as broadcast
            await AlertService.mark_broadcast_sent(session, alert_id, sent_count)
            
            # Notify admin about results
            if admin_bot:
                result_text = (
                    f"✅ РАССЫЛКА ЗАВЕРШЕНА!\n\n"
                    f"Алерт #{alert_id}\n"
                    f"📊 Статистика:\n"
                    f"✅ Отправлено: {sent_count}\n"
                    f"❌ Ошибок: {failed_count}"
                )
                await admin_bot.send_message(
                    chat_id=admin_chat_id,
                    text=result_text
                )
            
            logger.info(f"[_broadcast_alert_task] ✅ Рассылка алерта #{alert_id} завершена: отправлено={sent_count}, ошибок={failed_count}")
            
    except Exception as e:
        logger.error(f"[_broadcast_alert_task] ❌ Критическая ошибка рассылки: {str(e)}", exc_info=True)


def _format_alert_message(alert: Alert, language: str) -> str:
    """Format alert message for broadcast"""
    # Alert type emojis
    type_emojis = {
        AlertType.SHURTA: "🚨",
        AlertType.MISSING_PERSON: "👤",
        AlertType.LOST_ITEM: "📦",
        AlertType.SCAM_WARNING: "⚠️",
        AlertType.MEDICAL_EMERGENCY: "🏥",
        AlertType.ACCOMMODATION_NEEDED: "🏠",
        AlertType.RIDE_SHARING: "🚗",
        AlertType.JOB_POSTING: "💼",
        AlertType.LOST_DOCUMENT: "📄",
        AlertType.EVENT_ANNOUNCEMENT: "🎉",
    }
    
    emoji = type_emojis.get(alert.alert_type, "📝")
    
    # Alert type names
    type_names_ru = {
        AlertType.SHURTA: "ПОЛИЦИЯ",
        AlertType.MISSING_PERSON: "ПРОПАЛ ЧЕЛОВЕК",
        AlertType.LOST_ITEM: "ПОТЕРЯ ВЕЩИ",
        AlertType.SCAM_WARNING: "МОШЕННИЧЕСТВО",
        AlertType.MEDICAL_EMERGENCY: "МЕДПОМОЩЬ",
        AlertType.ACCOMMODATION_NEEDED: "НУЖНО ЖИЛЬЕ",
        AlertType.RIDE_SHARING: "ПОПУТЧИКИ",
        AlertType.JOB_POSTING: "ВАКАНСИЯ",
        AlertType.LOST_DOCUMENT: "ПОТЕРЯ ДОКУМЕНТА",
        AlertType.EVENT_ANNOUNCEMENT: "МЕРОПРИЯТИЕ",
    }
    
    type_names_uz = {
        AlertType.SHURTA: "POLITSIYA",
        AlertType.MISSING_PERSON: "ODAM YO'QOLDI",
        AlertType.LOST_ITEM: "NARSA YO'QOLDI",
        AlertType.SCAM_WARNING: "FIRIBGARLIK",
        AlertType.MEDICAL_EMERGENCY: "TIBBIY YORDAM",
        AlertType.ACCOMMODATION_NEEDED: "UY-JOY KERAK",
        AlertType.RIDE_SHARING: "YO'LOVCHI QIDIRISH",
        AlertType.JOB_POSTING: "ISH TAKLIFI",
        AlertType.LOST_DOCUMENT: "HUJJAT YO'QOLDI",
        AlertType.EVENT_ANNOUNCEMENT: "TADBIR E'LONI",
    }
    
    if language == "UZ":
        type_name = type_names_uz.get(alert.alert_type, alert.alert_type.value)
        text = f"{emoji} <b>{type_name}</b>\n\n"
        
        if alert.title:
            text += f"<b>{alert.title}</b>\n\n"
        
        text += f"{alert.description}\n"
        
        if alert.phone:
            text += f"\n📞 <b>Aloqa:</b> {alert.phone}"
        
        if alert.address_text:
            text += f"\n📍 <b>Manzil:</b> {alert.address_text}"
        
        text += f"\n\n🕒 {alert.created_at.strftime('%d.%m.%Y %H:%M')}"
    else:  # RU
        type_name = type_names_ru.get(alert.alert_type, alert.alert_type.value)
        text = f"{emoji} <b>{type_name}</b>\n\n"
        
        if alert.title:
            text += f"<b>{alert.title}</b>\n\n"
        
        text += f"{alert.description}\n"
        
        if alert.phone:
            text += f"\n📞 <b>Контакт:</b> {alert.phone}"
        
        if alert.address_text:
            text += f"\n📍 <b>Место:</b> {alert.address_text}"
        
        text += f"\n\n🕒 {alert.created_at.strftime('%d.%m.%Y %H:%M')}"
    
    return text


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
    """Manually trigger broadcast for already approved alert"""
    try:
        alert_id = int(callback.data.split("_")[-1])
        
        await callback.message.edit_text(
            "📢 Рассылка алерта запущена...\n\n"
            "Пожалуйста, подождите отчёт о результатах"
        )
        
        # Launch broadcast task (same as automatic flow)
        asyncio.create_task(_broadcast_alert_task(alert_id, callback.message.chat.id))
        
        await callback.answer("📢 Рассылка запускается", show_alert=True)
        
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
