"""
Сервис статистики - Комплексная статистика пользователей и системы
"""

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from models import (
    User, ButtonClick, UserActivity, Delivery,
    Notification, ShurtaAlert, UserMessage
)
from utils.logger import logger


class StatisticsService:
    """Сервис для сбора комплексной статистики"""
    
    @staticmethod
    async def get_user_statistics(session: AsyncSession) -> Dict[str, Any]:
        """
        Получить комплексную статистику пользователей
        Returns: Словарь со всей статистикой
        """
        try:
            logger.info("Начало сбора статистики пользователей")
            
            # Всего пользователей
            total_users_result = await session.execute(
                select(func.count(User.id))
            )
            total_users = total_users_result.scalar()
            
            # Активные сегодня (последние 24 часа)
            yesterday = datetime.utcnow() - timedelta(days=1)
            active_today_result = await session.execute(
                select(func.count(User.id)).where(User.last_active >= yesterday)
            )
            active_today = active_today_result.scalar()
            
            # Активные за неделю (последние 7 дней)
            week_ago = datetime.utcnow() - timedelta(days=7)
            active_week_result = await session.execute(
                select(func.count(User.id)).where(User.last_active >= week_ago)
            )
            active_week = active_week_result.scalar()
            
            # Новые пользователи за неделю
            new_week_result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= week_ago)
            )
            new_week = new_week_result.scalar()
            
            # По языкам
            language_result = await session.execute(
                select(User.language, func.count(User.id))
                .group_by(User.language)
            )
            language_stats = {row[0]: row[1] for row in language_result}
            
            # По гражданству
            citizenship_result = await session.execute(
                select(User.citizenship, func.count(User.id))
                .where(User.citizenship.isnot(None))
                .group_by(User.citizenship)
            )
            citizenship_stats = {row[0]: row[1] for row in citizenship_result}
            
            # Количество курьеров
            couriers_result = await session.execute(
                select(func.count(User.id)).where(User.is_courier == True)
            )
            couriers_count = couriers_result.scalar()
            
            logger.info(f"Статистика собрана: всего {total_users} пользователей")
            
            return {
                "total_users": total_users,
                "active_today": active_today,
                "active_week": active_week,
                "new_week": new_week,
                "language_stats": language_stats,
                "citizenship_stats": citizenship_stats,
                "couriers_count": couriers_count
            }
        except Exception as e:
            logger.error(f"Ошибка при сборе статистики пользователей: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_button_statistics(session: AsyncSession, days: int = 30) -> Dict[str, int]:
        """Получить топ кликов по кнопкам за последние N дней"""
        try:
            logger.info(f"Сбор статистики кнопок за {days} дней")
            
            date_from = datetime.utcnow() - timedelta(days=days)
            
            result = await session.execute(
                select(ButtonClick.button_name, func.count(ButtonClick.id))
                .where(ButtonClick.created_at >= date_from)
                .group_by(ButtonClick.button_name)
                .order_by(func.count(ButtonClick.id).desc())
                .limit(5)
            )
            
            button_stats = {row[0]: row[1] for row in result}
            logger.info(f"Статистика кнопок собрана: {len(button_stats)} записей")
            
            return button_stats
        except Exception as e:
            logger.error(f"Ошибка при сборе статистики кнопок: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_peak_hours(session: AsyncSession, days: int = 30) -> Dict[str, int]:
        """Получить пиковые часы активности"""
        try:
            logger.info(f"Сбор статистики пиковых часов за {days} дней")
            
            date_from = datetime.utcnow() - timedelta(days=days)
            
            # Получаем все активности с их часами
            result = await session.execute(
                select(ButtonClick.created_at)
                .where(ButtonClick.created_at >= date_from)
            )
            
            # Подсчитываем по часам
            hour_counts = {}
            for row in result:
                hour = row[0].hour
                hour_range = f"{hour:02d}:00-{(hour+1):02d}:00"
                hour_counts[hour_range] = hour_counts.get(hour_range, 0) + 1
            
            # Сортируем и возвращаем топ 4
            sorted_hours = dict(sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:4])
            
            logger.info(f"Пиковые часы определены: {list(sorted_hours.keys())}")
            
            return sorted_hours
        except Exception as e:
            logger.error(f"Ошибка при определении пиковых часов: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def track_button_click(
        session: AsyncSession,
        user_id: int,
        button_name: str,
        category: Optional[str] = None
    ):
        """Записать клик по кнопке для статистики"""
        try:
            click = ButtonClick(
                user_id=user_id,
                button_name=button_name,
                category=category
            )
            session.add(click)
            await session.commit()
            logger.info(f"Клик записан: {button_name} от пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при записи клика: {str(e)}", exc_info=True)
    
    @staticmethod
    async def track_activity(
        session: AsyncSession,
        user_id: int,
        activity_type: str,
        activity_data: Optional[Dict] = None
    ):
        """Записать активность пользователя"""
        try:
            activity = UserActivity(
                user_id=user_id,
                activity_type=activity_type,
                activity_data=activity_data
            )
            session.add(activity)
            await session.commit()
            logger.info(f"Активность записана: {activity_type} от пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при записи активности: {str(e)}", exc_info=True)
    
    @staticmethod
    async def get_moderation_queue_count(session: AsyncSession) -> Dict[str, int]:
        """Получить количество элементов в очереди модерации"""
        try:
            logger.info("Подсчет очереди модерации")
            
            # Уведомления на модерации
            notif_result = await session.execute(
                select(func.count(Notification.id))
                .where(Notification.is_moderated == False)
            )
            notif_count = notif_result.scalar()
            
            # Shurta на модерации
            shurta_result = await session.execute(
                select(func.count(ShurtaAlert.id))
                .where(ShurtaAlert.is_moderated == False)
            )
            shurta_count = shurta_result.scalar()
            
            # Непрочитанные сообщения
            msg_result = await session.execute(
                select(func.count(UserMessage.id))
                .where(UserMessage.is_read == False)
            )
            msg_count = msg_result.scalar()
            
            stats = {
                "notifications_pending": notif_count,
                "shurta_pending": shurta_count,
                "messages_unread": msg_count,
                "total_pending": notif_count + shurta_count + msg_count
            }
            
            logger.info(f"Очередь модерации: {stats['total_pending']} элементов")
            
            return stats
        except Exception as e:
            logger.error(f"Ошибка при подсчете очереди: {str(e)}", exc_info=True)
            raise
