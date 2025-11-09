from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from models import Alert, AlertType, User, UserAlertPreference, SystemSetting
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from utils.logger import logger


class AlertService:
    """Service for managing unified alert system"""
    
    @staticmethod
    async def ensure_user_alert_preferences(
        session: AsyncSession,
        user_id: int
    ) -> List[UserAlertPreference]:
        """Ensure the user has preferences for all alert types."""
        try:
            result = await session.execute(
                select(UserAlertPreference).where(UserAlertPreference.user_id == user_id)
            )
            existing_prefs = result.scalars().all()
            existing_types = {pref.alert_type for pref in existing_prefs}
            created_prefs: List[UserAlertPreference] = []
            
            for alert_type in AlertType:
                if alert_type in existing_types:
                    continue
                is_enabled = alert_type == AlertType.SHURTA
                pref = UserAlertPreference(
                    user_id=user_id,
                    alert_type=alert_type,
                    is_enabled=is_enabled
                )
                session.add(pref)
                created_prefs.append(pref)
            
            if created_prefs:
                await session.commit()
                for pref in created_prefs:
                    await session.refresh(pref)
                logger.info(
                    "✅ [alert_service] Созданы настройки уведомлений для пользователя %s: %s",
                    user_id,
                    [pref.alert_type.value for pref in created_prefs]
                )
                return existing_prefs + created_prefs
            
            return existing_prefs
        except Exception as e:
            logger.error(
                "❌ [alert_service] Ошибка создания настроек уведомлений пользователя %s: %s",
                user_id,
                str(e),
                exc_info=True
            )
            await session.rollback()
            raise
    
    @staticmethod
    async def create_alert(
        session: AsyncSession,
        alert_type: AlertType,
        creator_id: int,
        description: str,
        title: Optional[str] = None,
        photo_file_id: Optional[str] = None,
        location_type: Optional[str] = None,
        address_text: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        geo_name: Optional[str] = None,
        maps_url: Optional[str] = None,
        phone: Optional[str] = None,
        contact_info: Optional[Dict] = None,
        additional_files: Optional[List[str]] = None,
        target_languages: Optional[List[str]] = None,
        target_citizenships: Optional[List[str]] = None,
        target_couriers_only: bool = False,
        expires_hours: Optional[int] = None
    ) -> Alert:
        """Create a new alert"""
        try:
            expires_at = None
            if expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            alert = Alert(
                alert_type=alert_type,
                creator_id=creator_id,
                title=title,
                description=description,
                photo_file_id=photo_file_id,
                additional_files=additional_files,
                location_type=location_type,
                address_text=address_text,
                latitude=latitude,
                longitude=longitude,
                geo_name=geo_name,
                maps_url=maps_url,
                phone=phone,
                contact_info=contact_info,
                target_languages=target_languages,
                target_citizenships=target_citizenships,
                target_couriers_only=target_couriers_only,
                expires_at=expires_at
            )
            
            session.add(alert)
            await session.commit()
            await session.refresh(alert)
            
            logger.info(f"✅ [alert_service] Создан алерт #{alert.id} типа {alert_type.value} от пользователя {creator_id}")
            return alert
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка создания алерта: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_alert(session: AsyncSession, alert_id: int) -> Optional[Alert]:
        """Get alert by ID with relationships"""
        try:
            result = await session.execute(
                select(Alert)
                .options(selectinload(Alert.creator), selectinload(Alert.moderator))
                .where(Alert.id == alert_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка получения алерта: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_pending_alerts(
        session: AsyncSession,
        alert_type: Optional[AlertType] = None,
        language: Optional[str] = None,
        citizenship: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Alert]:
        """Get pending (unmoderated) alerts with filters"""
        try:
            query = select(Alert).options(
                selectinload(Alert.creator),
                selectinload(Alert.moderator)
            ).where(
                and_(
                    Alert.is_moderated == False,
                    Alert.is_active == True
                )
            )
            
            if alert_type:
                query = query.where(Alert.alert_type == alert_type)
            
            if language:
                query = query.where(
                    or_(
                        Alert.target_languages == None,
                        Alert.target_languages.contains([language])
                    )
                )
            
            if citizenship:
                query = query.where(
                    or_(
                        Alert.target_citizenships == None,
                        Alert.target_citizenships.contains([citizenship])
                    )
                )
            
            query = query.order_by(Alert.created_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка получения неотмодерированных алертов: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_pending_count_by_type(session: AsyncSession) -> Dict[str, int]:
        """Get count of pending alerts grouped by type"""
        try:
            result = await session.execute(
                select(Alert.alert_type, func.count(Alert.id))
                .where(and_(Alert.is_moderated == False, Alert.is_active == True))
                .group_by(Alert.alert_type)
            )
            
            counts = {row[0].value: row[1] for row in result.all()}
            
            # Ensure all alert types are in result (with 0 if none)
            for alert_type in AlertType:
                if alert_type.value not in counts:
                    counts[alert_type.value] = 0
            
            return counts
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка подсчета алертов: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def approve_alert(
        session: AsyncSession,
        alert_id: int,
        moderator_id: int
    ) -> Optional[Alert]:
        """Approve an alert for broadcasting"""
        try:
            alert = await AlertService.get_alert(session, alert_id)
            if not alert:
                return None
            
            alert.is_approved = True
            alert.is_moderated = True
            alert.moderator_id = moderator_id
            alert.moderated_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(alert)
            
            logger.info(f"✅ [alert_service] Алерт #{alert_id} одобрен модератором {moderator_id}")
            return alert
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка одобрения алерта: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def reject_alert(
        session: AsyncSession,
        alert_id: int,
        moderator_id: int,
        reason: Optional[str] = None
    ) -> Optional[Alert]:
        """Reject an alert"""
        try:
            alert = await AlertService.get_alert(session, alert_id)
            if not alert:
                return None
            
            alert.is_approved = False
            alert.is_moderated = True
            alert.moderator_id = moderator_id
            alert.moderated_at = datetime.utcnow()
            alert.rejection_reason = reason
            alert.is_active = False
            
            await session.commit()
            await session.refresh(alert)
            
            logger.info(f"✅ [alert_service] Алерт #{alert_id} отклонен модератором {moderator_id}")
            return alert
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка отклонения алерта: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_broadcast_targets(
        session: AsyncSession,
        alert: Alert
    ) -> List[User]:
        """Get list of users who should receive this alert broadcast"""
        try:
            query = select(User).where(
                and_(
                    User.is_banned == False,
                    User.notifications_enabled == True
                )
            )
            
            # Filter by language
            if alert.target_languages:
                query = query.where(User.language.in_(alert.target_languages))
            
            # Filter by citizenship
            if alert.target_citizenships:
                query = query.where(User.citizenship.in_(alert.target_citizenships))
            
            # Filter by courier status
            if alert.target_couriers_only:
                query = query.where(User.is_courier == True)
            
            result = await session.execute(query)
            users = list(result.scalars().all())
            
            # Filter by user preferences
            filtered_users = []
            for user in users:
                # Check if user has disabled this alert type
                pref_result = await session.execute(
                    select(UserAlertPreference).where(
                        and_(
                            UserAlertPreference.user_id == user.id,
                            UserAlertPreference.alert_type == alert.alert_type
                        )
                    )
                )
                pref = pref_result.scalar_one_or_none()
                
                # If no preference set, default to enabled
                if pref is None or pref.is_enabled:
                    filtered_users.append(user)
            
            logger.info(f"✅ [alert_service] Найдено {len(filtered_users)} получателей для алерта #{alert.id}")
            return filtered_users
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка получения целевой аудитории: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def mark_broadcast_sent(
        session: AsyncSession,
        alert_id: int,
        recipient_count: int
    ) -> Optional[Alert]:
        """Mark alert as broadcast and record statistics"""
        try:
            alert = await AlertService.get_alert(session, alert_id)
            if not alert:
                return None
            
            alert.broadcast_sent = True
            alert.broadcast_count = recipient_count
            alert.broadcast_at = datetime.utcnow()
            
            await session.commit()
            await session.refresh(alert)
            
            logger.info(f"✅ [alert_service] Отмечена рассылка алерта #{alert_id} ({recipient_count} получателей)")
            return alert
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка записи статистики рассылки: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def get_approved_alerts(
        session: AsyncSession,
        alert_type: Optional[AlertType] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Alert]:
        """Get approved alerts"""
        try:
            query = select(Alert).options(
                selectinload(Alert.creator),
                selectinload(Alert.moderator)
            ).where(
                and_(
                    Alert.is_approved == True,
                    Alert.is_active == True
                )
            )
            
            if alert_type:
                query = query.where(Alert.alert_type == alert_type)
            
            query = query.order_by(Alert.created_at.desc()).limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка получения одобренных алертов: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def get_user_preferences(
        session: AsyncSession,
        user_id: int
    ) -> Dict[AlertType, bool]:
        """Get user's alert preferences"""
        try:
            result = await session.execute(
                select(UserAlertPreference).where(UserAlertPreference.user_id == user_id)
            )
            prefs = result.scalars().all()
            
            # Build dict with all alert types
            pref_dict = {}
            for alert_type in AlertType:
                pref = next((p for p in prefs if p.alert_type == alert_type), None)
                pref_dict[alert_type] = pref.is_enabled if pref else True  # Default enabled
            
            return pref_dict
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка получения предпочтений: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def update_user_preference(
        session: AsyncSession,
        user_id: int,
        alert_type: AlertType,
        is_enabled: bool
    ) -> UserAlertPreference:
        """Update or create user alert preference"""
        try:
            result = await session.execute(
                select(UserAlertPreference).where(
                    and_(
                        UserAlertPreference.user_id == user_id,
                        UserAlertPreference.alert_type == alert_type
                    )
                )
            )
            pref = result.scalar_one_or_none()
            
            if pref:
                pref.is_enabled = is_enabled
                pref.updated_at = datetime.utcnow()
            else:
                pref = UserAlertPreference(
                    user_id=user_id,
                    alert_type=alert_type,
                    is_enabled=is_enabled
                )
                session.add(pref)
            
            await session.commit()
            await session.refresh(pref)
            
            logger.info(f"✅ [alert_service] Обновлены предпочтения пользователя {user_id} для типа {alert_type.value}: {is_enabled}")
            return pref
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка обновления предпочтений: {str(e)}", exc_info=True)
            await session.rollback()
            raise
    
    @staticmethod
    async def check_alert_type_enabled(
        session: AsyncSession,
        alert_type: AlertType
    ) -> bool:
        """Check if alert type is enabled in system settings"""
        try:
            setting_key = f"alert_{alert_type.value.lower()}"
            result = await session.execute(
                select(SystemSetting).where(SystemSetting.setting_key == setting_key)
            )
            setting = result.scalar_one_or_none()
            
            # Default to True if setting doesn't exist
            return setting.value if setting else True
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка проверки настроек: {str(e)}", exc_info=True)
            return True  # Fail open
    
    @staticmethod
    async def get_alert_statistics(session: AsyncSession) -> Dict[str, Any]:
        """Get comprehensive alert statistics"""
        try:
            stats = {}
            
            # Total counts by type
            for alert_type in AlertType:
                result = await session.execute(
                    select(func.count(Alert.id)).where(
                        and_(
                            Alert.alert_type == alert_type,
                            Alert.is_active == True
                        )
                    )
                )
                stats[f"total_{alert_type.value.lower()}"] = result.scalar() or 0
            
            # Pending counts
            pending_counts = await AlertService.get_pending_count_by_type(session)
            stats["pending_by_type"] = pending_counts
            stats["total_pending"] = sum(pending_counts.values())
            
            # Approved count (total)
            result = await session.execute(
                select(func.count(Alert.id)).where(
                    and_(
                        Alert.is_approved == True,
                        Alert.is_active == True
                    )
                )
            )
            stats["total_approved"] = result.scalar() or 0
            
            # Broadcasts sent
            result = await session.execute(
                select(func.count(Alert.id)).where(Alert.broadcast_sent == True)
            )
            stats["total_broadcasts"] = result.scalar() or 0
            
            # Total reach
            result = await session.execute(
                select(func.sum(Alert.broadcast_count))
            )
            stats["total_reach"] = result.scalar() or 0
            
            # Expired alerts
            result = await session.execute(
                select(func.count(Alert.id)).where(
                    and_(
                        Alert.expires_at != None,
                        Alert.expires_at < datetime.utcnow(),
                        Alert.is_active == True
                    )
                )
            )
            stats["expired"] = result.scalar() or 0
            
            logger.info(f"✅ [alert_service] Статистика алертов собрана")
            return stats
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка сбора статистики: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def expire_old_alerts(session: AsyncSession) -> int:
        """Deactivate expired alerts, return count"""
        try:
            result = await session.execute(
                select(Alert).where(
                    and_(
                        Alert.expires_at != None,
                        Alert.expires_at < datetime.utcnow(),
                        Alert.is_active == True
                    )
                )
            )
            alerts = result.scalars().all()
            
            count = 0
            for alert in alerts:
                alert.is_active = False
                count += 1
            
            await session.commit()
            
            if count > 0:
                logger.info(f"✅ [alert_service] Деактивировано {count} истекших алертов")
            
            return count
            
        except Exception as e:
            logger.error(f"❌ [alert_service] Ошибка деактивации алертов: {str(e)}", exc_info=True)
            await session.rollback()
            raise
