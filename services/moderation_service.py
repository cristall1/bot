"""
Сервис модерации - Управление потоками модерации для Propaja и Shurta
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Optional
from datetime import datetime, timedelta
from models import Notification, ShurtaAlert, User
from utils.logger import logger


class ModerationService:
    """Сервис для рабочих процессов модерации"""
    
    @staticmethod
    async def get_pending_notifications(session: AsyncSession) -> List[Notification]:
        """
        Получить все уведомления, ожидающие модерации
        Returns: Список объектов Notification
        """
        try:
            logger.info("Получение уведомлений на модерации")
            
            result = await session.execute(
                select(Notification)
                .options(joinedload(Notification.creator))
                .where(Notification.is_moderated == False)
                .order_by(Notification.created_at.desc())
            )
            notifications = result.scalars().all()
            
            logger.info(f"Найдено {len(notifications)} уведомлений на модерации")
            return notifications
        except Exception as e:
            logger.error(f"Ошибка при получении уведомлений: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_pending_shurta(session: AsyncSession) -> List[ShurtaAlert]:
        """
        Получить все объявления Shurta, ожидающие модерации
        Returns: Список объектов ShurtaAlert
        """
        try:
            logger.info("Получение Shurta на модерации")
            
            result = await session.execute(
                select(ShurtaAlert)
                .options(joinedload(ShurtaAlert.creator))
                .where(ShurtaAlert.is_moderated == False)
                .order_by(ShurtaAlert.created_at.desc())
            )
            alerts = result.scalars().all()
            
            logger.info(f"Найдено {len(alerts)} Shurta на модерации")
            return alerts
        except Exception as e:
            logger.error(f"Ошибка при получении Shurta: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def approve_notification(
        session: AsyncSession,
        notification_id: int,
        moderator_id: int
    ) -> Optional[Notification]:
        """
        Одобрить уведомление для рассылки
        """
        try:
            logger.info(f"Одобрение уведомления {notification_id}")
            
            result = await session.execute(
                select(Notification)
                .options(joinedload(Notification.creator))
                .where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()
            
            if not notification:
                logger.error(f"Уведомление {notification_id} не найдено")
                return None
            
            notification.is_approved = True
            notification.is_moderated = True
            notification.moderator_id = moderator_id
            notification.moderated_at = datetime.utcnow()
            
            # Установить срок истечения (48 часов с текущего момента)
            notification.expires_at = datetime.utcnow() + timedelta(hours=48)
            
            await session.commit()
            await session.refresh(notification)
            
            logger.info(f"Уведомление {notification_id} одобрено модератором {moderator_id}")
            return notification
        except Exception as e:
            logger.error(f"Ошибка при одобрении уведомления: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def reject_notification(
        session: AsyncSession,
        notification_id: int,
        moderator_id: int
    ) -> Optional[Notification]:
        """
        Отклонить уведомление
        """
        try:
            logger.info(f"Отклонение уведомления {notification_id}")
            
            result = await session.execute(
                select(Notification)
                .options(joinedload(Notification.creator))
                .where(Notification.id == notification_id)
            )
            notification = result.scalar_one_or_none()
            
            if not notification:
                logger.error(f"Уведомление {notification_id} не найдено")
                return None
            
            notification.is_approved = False
            notification.is_moderated = True
            notification.moderator_id = moderator_id
            notification.moderated_at = datetime.utcnow()
            notification.is_active = False
            
            await session.commit()
            await session.refresh(notification)
            
            logger.info(f"Уведомление {notification_id} отклонено модератором {moderator_id}")
            return notification
        except Exception as e:
            logger.error(f"Ошибка при отклонении уведомления: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def approve_shurta(
        session: AsyncSession,
        shurta_id: int,
        moderator_id: int
    ) -> Optional[ShurtaAlert]:
        """
        Одобрить объявление Shurta для рассылки
        """
        try:
            logger.info(f"Одобрение Shurta {shurta_id}")
            
            result = await session.execute(
                select(ShurtaAlert)
                .options(joinedload(ShurtaAlert.creator))
                .where(ShurtaAlert.id == shurta_id)
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                logger.error(f"Shurta {shurta_id} не найдено")
                return None
            
            alert.is_approved = True
            alert.is_moderated = True
            alert.moderator_id = moderator_id
            alert.moderated_at = datetime.utcnow()
            
            # Установить срок истечения (48 часов с текущего момента)
            alert.expires_at = datetime.utcnow() + timedelta(hours=48)
            
            await session.commit()
            await session.refresh(alert)
            
            logger.info(f"Shurta {shurta_id} одобрен модератором {moderator_id}")
            return alert
        except Exception as e:
            logger.error(f"Ошибка при одобрении Shurta: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def reject_shurta(
        session: AsyncSession,
        shurta_id: int,
        moderator_id: int
    ) -> Optional[ShurtaAlert]:
        """
        Отклонить объявление Shurta
        """
        try:
            logger.info(f"Отклонение Shurta {shurta_id}")
            
            result = await session.execute(
                select(ShurtaAlert)
                .options(joinedload(ShurtaAlert.creator))
                .where(ShurtaAlert.id == shurta_id)
            )
            alert = result.scalar_one_or_none()
            
            if not alert:
                logger.error(f"Shurta {shurta_id} не найдено")
                return None
            
            alert.is_approved = False
            alert.is_moderated = True
            alert.moderator_id = moderator_id
            alert.moderated_at = datetime.utcnow()
            alert.is_active = False
            
            await session.commit()
            await session.refresh(alert)
            
            logger.info(f"Shurta {shurta_id} отклонен модератором {moderator_id}")
            return alert
        except Exception as e:
            logger.error(f"Ошибка при отклонении Shurta: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_users_for_notification(
        session: AsyncSession,
        notification_type: str
    ) -> List[User]:
        """
        Получить список пользователей для отправки уведомления
        На основе настроек уведомлений
        """
        try:
            logger.info(f"Получение пользователей для рассылки типа {notification_type}")
            
            query = select(User).where(
                User.notifications_enabled == True,
                User.is_banned == False
            )
            
            result = await session.execute(query)
            users = result.scalars().all()
            
            logger.info(f"Найдено {len(users)} пользователей для рассылки")
            return users
        except Exception as e:
            logger.error(f"Ошибка при получении пользователей: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def format_notification_for_user(
        notification: Notification,
        user_language: str
    ) -> str:
        """
        Форматировать сообщение уведомления для пользователя на основе его языка
        """
        try:
            if notification.type == "PROPAJA_ODAM":
                header = "🔔 ПРОПАЛ ЧЕЛОВЕК" if user_language == "RU" else "🔔 ODAM YO'QOLGAN"
            else:
                header = "🔔 ПРОПАЛА ВЕЩЬ" if user_language == "RU" else "🔔 NARSA YO'QOLGAN"
            
            message = f"{header}\n\n"
            message += f"{'Имя' if user_language == 'RU' else 'Ism'}: {notification.title}\n"
            message += f"{'Описание' if user_language == 'RU' else 'Tavsif'}: {notification.description}\n"
            
            if notification.address_text:
                message += f"{'Место' if user_language == 'RU' else 'Joy'}: {notification.address_text}\n"
            
            message += f"{'Телефон' if user_language == 'RU' else 'Telefon'}: {notification.phone}\n"
            
            return message
        except Exception as e:
            logger.error(f"Ошибка при форматировании уведомления: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def format_shurta_for_user(
        alert: ShurtaAlert,
        user_language: str
    ) -> str:
        """
        Форматировать сообщение Shurta для пользователя на основе его языка
        """
        try:
            header = "🚨 ВНИМАНИЕ! ПОЛИЦИЯ ИЩЕТ!" if user_language == "RU" else "🚨 DIQQAT! POLITSIYA QIDIRMOQDA!"
            
            message = f"{header}\n\n"
            message += f"{'Описание' if user_language == 'RU' else 'Tavsif'}: {alert.description}\n"
            
            if alert.address_text:
                message += f"{'Место' if user_language == 'RU' else 'Joy'}: {alert.address_text}\n"
            
            if user_language == "RU":
                message += "\nЕсли видели - свяжитесь с полицией!"
            else:
                message += "\nAgar ko'rgan bo'lsangiz - politsiya bilan bog'laning!"
            
            return message
        except Exception as e:
            logger.error(f"Ошибка при форматировании Shurta: {str(e)}", exc_info=True)
            raise
