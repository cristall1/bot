from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    language = Column(String(2), default="RU")  # RU or UZ
    citizenship = Column(String(2), nullable=True)  # UZ, RU, KZ, KG
    is_admin = Column(Boolean, default=False)
    is_courier = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    deliveries_created = relationship("Delivery", foreign_keys="Delivery.creator_id", back_populates="creator")
    deliveries_assigned = relationship("Delivery", foreign_keys="Delivery.courier_id", back_populates="courier")
    notifications_created = relationship("Notification", back_populates="creator")
    shurta_alerts = relationship("ShurtaAlert", back_populates="creator")
    user_messages = relationship("UserMessage", back_populates="user")
    courier_info = relationship("Courier", back_populates="user", uselist=False)


class Document(Base):
    """Documents for Hujjat Yordami section"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    citizenship_scope = Column(String(2), nullable=False)  # UZ, RU, KZ, KG
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    content_ru = Column(Text, nullable=True)
    content_uz = Column(Text, nullable=True)
    content_type = Column(String(20), default="TEXT")  # TEXT, PHOTO, PDF, AUDIO, LINK, GEO
    photo_file_id = Column(String(500), nullable=True)  # Telegram file_id
    pdf_file_id = Column(String(500), nullable=True)   # Telegram file_id
    audio_file_id = Column(String(500), nullable=True)  # Telegram file_id
    telegraph_url = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)  # Soft delete

    # Relationships
    buttons = relationship("DocumentButton", back_populates="document", cascade="all, delete-orphan")


class DocumentButton(Base):
    """Inline buttons for documents"""
    __tablename__ = "document_buttons"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    text_ru = Column(String(255), nullable=False)
    text_uz = Column(String(255), nullable=False)
    button_type = Column(String(20), default="LINK")  # LINK, CALLBACK, PHOTO, PDF, AUDIO, GEO
    button_value = Column(String(500), nullable=False)  # URL, callback_data, file_id, coordinates
    button_interface = Column(JSON, nullable=True)  # Additional interface data
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="buttons")


class Delivery(Base):
    """Delivery orders for Dostavka Xizmati"""
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    courier_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=False)
    location_type = Column(String(20), nullable=False)  # ADDRESS, GEO, MAPS
    address_text = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_name = Column(String(255), nullable=True)  # Readable location name
    maps_url = Column(String(500), nullable=True)  # Google Maps URL
    phone = Column(String(50), nullable=False)
    status = Column(String(20), default="WAITING")  # WAITING, ASSIGNED, COMPLETED, REJECTED, CANCELLED
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)  # Auto-expiration

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], back_populates="deliveries_created")
    courier = relationship("User", foreign_keys=[courier_id], back_populates="deliveries_assigned")


class Notification(Base):
    """Notifications for Xabarnoma (lost people/items)"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(20), nullable=False)  # PROPAJA_ODAM, PROPAJA_NARSA
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)  # Name or What
    description = Column(Text, nullable=False)
    photo_file_id = Column(String(500), nullable=True)
    location_type = Column(String(20), nullable=False)  # ADDRESS, GEO, MAPS
    address_text = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_name = Column(String(255), nullable=True)  # Readable location name
    maps_url = Column(String(500), nullable=True)  # Google Maps URL
    phone = Column(String(50), nullable=False)
    is_approved = Column(Boolean, default=False)  # Admin approval required
    is_moderated = Column(Boolean, default=False)  # Has been reviewed by admin
    moderator_id = Column(Integer, nullable=True)  # Admin who moderated
    moderated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-expiration after 48 hours

    # Relationships
    creator = relationship("User", back_populates="notifications_created")


class ShurtaAlert(Base):
    """Police alerts for Shurta section"""
    __tablename__ = "shurta_alerts"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text, nullable=False)
    location_type = Column(String(20), nullable=False)  # ADDRESS, GEO, MAPS
    address_text = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_name = Column(String(255), nullable=True)  # Readable location name
    maps_url = Column(String(500), nullable=True)  # Google Maps URL
    photo_file_id = Column(String(500), nullable=True)
    is_approved = Column(Boolean, default=False)  # Admin approval required
    is_moderated = Column(Boolean, default=False)  # Has been reviewed by admin
    moderator_id = Column(Integer, nullable=True)  # Admin who moderated
    moderated_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Auto-expiration after 48 hours

    # Relationships
    creator = relationship("User", back_populates="shurta_alerts")


class UserMessage(Base):
    """Messages from users to admin"""
    __tablename__ = "user_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    is_moderated = Column(Boolean, default=False)  # For moderation if needed
    moderator_id = Column(Integer, nullable=True)
    moderation_status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED
    admin_reply = Column(Text, nullable=True)
    admin_id = Column(Integer, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="user_messages")


class Broadcast(Base):
    """Broadcasts from admin"""
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, nullable=False)
    name_ru = Column(String(255), nullable=False)  # Campaign name
    name_uz = Column(String(255), nullable=False)  # Campaign name
    message_ru = Column(Text, nullable=False)
    message_uz = Column(Text, nullable=True)
    photo_file_id = Column(String(500), nullable=True)
    recipient_filter = Column(String(50), default="ALL")  # ALL, RU, UZ, COURIERS, CITIZENSHIP_UZ, etc
    sent_at = Column(DateTime, nullable=True)
    recipient_count = Column(Integer, default=0)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelegraphArticle(Base):
    """Telegraph articles for admin management"""
    __tablename__ = "telegraph_articles"

    id = Column(Integer, primary_key=True, index=True)
    title_ru = Column(String(255), nullable=False)
    title_uz = Column(String(255), nullable=False)
    content_html = Column(Text, nullable=False)
    telegraph_url = Column(String(500), nullable=True)
    author_name = Column(String(100), default="Admin")
    tags = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Courier(Base):
    """Courier information"""
    __tablename__ = "couriers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    completed_deliveries = Column(Integer, default=0)
    rating = Column(Float, default=5.0)
    status = Column(String(20), default="ACTIVE")  # ACTIVE, SUSPENDED
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="courier_info")


class SystemSetting(Base):
    """System settings for toggling features"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_name_ru = Column(String(255), nullable=False)
    setting_name_uz = Column(String(255), nullable=False)
    value = Column(Boolean, default=True)
    last_modified_by = Column(Integer, nullable=True)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AdminLog(Base):
    """Admin action logs"""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
