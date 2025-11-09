import csv
import json
import sqlite3
import tempfile
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import Alert, User, Delivery, AlertType
from utils.logger import logger


class ExportService:
    """Service for exporting data to various formats"""
    
    @staticmethod
    async def export_alerts_csv(
        session: AsyncSession,
        alert_type: Optional[AlertType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export alerts to CSV file, return file path"""
        try:
            # Query alerts
            query = select(Alert)
            
            if alert_type:
                query = query.where(Alert.alert_type == alert_type)
            if start_date:
                query = query.where(Alert.created_at >= start_date)
            if end_date:
                query = query.where(Alert.created_at <= end_date)
            
            query = query.order_by(Alert.created_at.desc())
            
            result = await session.execute(query)
            alerts = result.scalars().all()
            
            # Create temporary CSV file
            temp_dir = tempfile.gettempdir()
            filename = f"alerts_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Тип', 'Заголовок', 'Описание', 'Создатель ID', 'Создан',
                    'Одобрен', 'Модератор ID', 'Отмодерирован', 'Активен', 'Телефон',
                    'Адрес', 'Количество рассылок', 'Дата рассылки'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for alert in alerts:
                    writer.writerow({
                        'ID': alert.id,
                        'Тип': alert.alert_type.value,
                        'Заголовок': alert.title or '',
                        'Описание': alert.description[:100] + '...' if len(alert.description) > 100 else alert.description,
                        'Создатель ID': alert.creator_id,
                        'Создан': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'Одобрен': 'Да' if alert.is_approved else 'Нет',
                        'Модератор ID': alert.moderator_id or '',
                        'Отмодерирован': alert.moderated_at.strftime('%Y-%m-%d %H:%M:%S') if alert.moderated_at else '',
                        'Активен': 'Да' if alert.is_active else 'Нет',
                        'Телефон': alert.phone or '',
                        'Адрес': alert.address_text or '',
                        'Количество рассылок': alert.broadcast_count,
                        'Дата рассылки': alert.broadcast_at.strftime('%Y-%m-%d %H:%M:%S') if alert.broadcast_at else ''
                    })
            
            logger.info(f"✅ [exporter] Экспортировано {len(alerts)} алертов в CSV: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ [exporter] Ошибка экспорта алертов в CSV: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def export_users_csv(
        session: AsyncSession,
        language: Optional[str] = None,
        citizenship: Optional[str] = None,
        is_courier: Optional[bool] = None
    ) -> str:
        """Export users to CSV file, return file path"""
        try:
            # Query users
            query = select(User)
            
            if language:
                query = query.where(User.language == language)
            if citizenship:
                query = query.where(User.citizenship == citizenship)
            if is_courier is not None:
                query = query.where(User.is_courier == is_courier)
            
            query = query.order_by(User.created_at.desc())
            
            result = await session.execute(query)
            users = result.scalars().all()
            
            # Create temporary CSV file
            temp_dir = tempfile.gettempdir()
            filename = f"users_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Telegram ID', 'Username', 'Имя', 'Телефон', 'Язык',
                    'Гражданство', 'Админ', 'Курьер', 'Заблокирован', 'Зарегистрирован',
                    'Последняя активность'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for user in users:
                    writer.writerow({
                        'ID': user.id,
                        'Telegram ID': user.telegram_id,
                        'Username': user.username or '',
                        'Имя': user.first_name or '',
                        'Телефон': user.phone or '',
                        'Язык': user.language,
                        'Гражданство': user.citizenship or '',
                        'Админ': 'Да' if user.is_admin else 'Нет',
                        'Курьер': 'Да' if user.is_courier else 'Нет',
                        'Заблокирован': 'Да' if user.is_banned else 'Нет',
                        'Зарегистрирован': user.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'Последняя активность': user.last_active.strftime('%Y-%m-%d %H:%M:%S') if user.last_active else ''
                    })
            
            logger.info(f"✅ [exporter] Экспортировано {len(users)} пользователей в CSV: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ [exporter] Ошибка экспорта пользователей в CSV: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def export_deliveries_csv(
        session: AsyncSession,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export deliveries to CSV file, return file path"""
        try:
            # Query deliveries
            query = select(Delivery)
            
            if status:
                query = query.where(Delivery.status == status)
            if start_date:
                query = query.where(Delivery.created_at >= start_date)
            if end_date:
                query = query.where(Delivery.created_at <= end_date)
            
            query = query.order_by(Delivery.created_at.desc())
            
            result = await session.execute(query)
            deliveries = result.scalars().all()
            
            # Create temporary CSV file
            temp_dir = tempfile.gettempdir()
            filename = f"deliveries_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'ID', 'Описание', 'Создатель ID', 'Курьер ID', 'Статус',
                    'Телефон', 'Адрес', 'Создан', 'Назначен', 'Завершен'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for delivery in deliveries:
                    writer.writerow({
                        'ID': delivery.id,
                        'Описание': delivery.description[:100] + '...' if len(delivery.description) > 100 else delivery.description,
                        'Создатель ID': delivery.creator_id,
                        'Курьер ID': delivery.courier_id or '',
                        'Статус': delivery.status,
                        'Телефон': delivery.phone,
                        'Адрес': delivery.address_text or '',
                        'Создан': delivery.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        'Назначен': delivery.assigned_at.strftime('%Y-%m-%d %H:%M:%S') if delivery.assigned_at else '',
                        'Завершен': delivery.completed_at.strftime('%Y-%m-%d %H:%M:%S') if delivery.completed_at else ''
                    })
            
            logger.info(f"✅ [exporter] Экспортировано {len(deliveries)} доставок в CSV: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ [exporter] Ошибка экспорта доставок в CSV: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def export_alerts_json(
        session: AsyncSession,
        alert_type: Optional[AlertType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """Export alerts to JSON file, return file path"""
        try:
            # Query alerts
            query = select(Alert)
            
            if alert_type:
                query = query.where(Alert.alert_type == alert_type)
            if start_date:
                query = query.where(Alert.created_at >= start_date)
            if end_date:
                query = query.where(Alert.created_at <= end_date)
            
            query = query.order_by(Alert.created_at.desc())
            
            result = await session.execute(query)
            alerts = result.scalars().all()
            
            # Create temporary JSON file
            temp_dir = tempfile.gettempdir()
            filename = f"alerts_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = os.path.join(temp_dir, filename)
            
            # Convert to dict
            alerts_data = []
            for alert in alerts:
                alerts_data.append({
                    'id': alert.id,
                    'alert_type': alert.alert_type.value,
                    'title': alert.title,
                    'description': alert.description,
                    'creator_id': alert.creator_id,
                    'created_at': alert.created_at.isoformat(),
                    'is_approved': alert.is_approved,
                    'is_moderated': alert.is_moderated,
                    'moderator_id': alert.moderator_id,
                    'moderated_at': alert.moderated_at.isoformat() if alert.moderated_at else None,
                    'is_active': alert.is_active,
                    'phone': alert.phone,
                    'address_text': alert.address_text,
                    'location_type': alert.location_type,
                    'latitude': alert.latitude,
                    'longitude': alert.longitude,
                    'broadcast_count': alert.broadcast_count,
                    'broadcast_at': alert.broadcast_at.isoformat() if alert.broadcast_at else None,
                    'target_languages': alert.target_languages,
                    'target_citizenships': alert.target_citizenships
                })
            
            with open(filepath, 'w', encoding='utf-8') as jsonfile:
                json.dump(alerts_data, jsonfile, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ [exporter] Экспортировано {len(alerts)} алертов в JSON: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ [exporter] Ошибка экспорта алертов в JSON: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    async def export_database_sqlite(db_url: str) -> str:
        """Export entire database to SQLite dump, return file path"""
        try:
            # Extract database path from URL
            if "sqlite:///" in db_url:
                db_path = db_url.replace("sqlite:///", "")
            else:
                logger.error("❌ [exporter] Экспорт SQLite поддерживается только для SQLite баз данных")
                raise ValueError("SQLite export only supported for SQLite databases")
            
            # Create temporary dump file
            temp_dir = tempfile.gettempdir()
            filename = f"database_dump_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.sql"
            filepath = os.path.join(temp_dir, filename)
            
            # Connect and dump
            conn = sqlite3.connect(db_path)
            with open(filepath, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write(f'{line}\n')
            conn.close()
            
            logger.info(f"✅ [exporter] База данных экспортирована в SQLite dump: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ [exporter] Ошибка экспорта базы данных: {str(e)}", exc_info=True)
            raise
    
    @staticmethod
    def cleanup_export_file(filepath: str) -> bool:
        """Delete export file after sending"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                logger.info(f"✅ [exporter] Удален временный файл: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ [exporter] Ошибка удаления файла {filepath}: {str(e)}", exc_info=True)
            return False
