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
    language = Column(String(2), default="RU")
    citizenship = Column(String(2), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_courier = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    notifications_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    service_requests = relationship("ServiceRequest", back_populates="user", cascade="all, delete-orphan")
    courier_info = relationship("CourierManagement", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    admin_messages = relationship("AdminMessage", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    description_ru = Column(Text, nullable=True)
    description_uz = Column(Text, nullable=True)
    parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    level = Column(Integer, default=1)
    order_index = Column(Integer, default=0)
    icon = Column(String(10), default="📁")
    category_type = Column(String(20), default="GENERAL")
    citizenship_scope = Column(String(2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by_admin_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    parent = relationship("Category", remote_side=[id], backref="children")
    content = relationship("CategoryContent", back_populates="category", cascade="all, delete-orphan")
    buttons = relationship("InlineButton", back_populates="category", cascade="all, delete-orphan")


class CategoryContent(Base):
    __tablename__ = "category_content"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    content_ru = Column(Text, nullable=True)
    content_uz = Column(Text, nullable=True)
    content_type = Column(String(20), default="TEXT")
    image_url = Column(String(500), nullable=True)
    pdf_url = Column(String(500), nullable=True)
    link_url = Column(String(500), nullable=True)
    telegraph_url_ru = Column(String(500), nullable=True)
    telegraph_url_uz = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="content")


class InlineButton(Base):
    __tablename__ = "inline_buttons"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    button_text_ru = Column(String(255), nullable=False)
    button_text_uz = Column(String(255), nullable=False)
    button_url = Column(String(500), nullable=False)
    button_type = Column(String(20), default="LINK")
    order_index = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by_admin_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="buttons")


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True)
    service_type = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title_ru = Column(String(255), nullable=True)
    title_uz = Column(String(255), nullable=True)
    description_ru = Column(Text, nullable=True)
    description_uz = Column(Text, nullable=True)
    service_category_id = Column(Integer, nullable=True)
    image_url = Column(String(500), nullable=True)
    phone_contact = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    is_approved = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=48))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="service_requests")


class CourierManagement(Base):
    __tablename__ = "courier_management"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    is_courier = Column(Boolean, default=True)
    courier_status = Column(String(20), default="ACTIVE")
    cairo_zone = Column(String(100), nullable=True)
    completed_deliveries = Column(Integer, default=0)
    rating = Column(Float, default=5.0)
    joined_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="courier_info")


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    language = Column(String(2), default="RU")
    notifications_enabled = Column(Boolean, default=True)
    service_type_courier_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="preferences")


class AdminMessage(Base):
    __tablename__ = "admin_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message_text = Column(Text, nullable=False)
    user_telegram_id = Column(Integer, nullable=False)
    is_read = Column(Boolean, default=False)
    admin_reply = Column(Text, nullable=True)
    admin_id = Column(Integer, nullable=True)
    replied_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="admin_messages")


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, nullable=False)
    message_ru = Column(Text, nullable=False)
    message_uz = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)
    broadcast_type = Column(String(50), default="ALL")
    sent_at = Column(DateTime, default=datetime.utcnow)
    total_recipients = Column(Integer, default=0)


class AdminLog(Base):
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemSetting(Base):
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_name_ru = Column(String(255), nullable=False)
    setting_name_uz = Column(String(255), nullable=False)
    value = Column(Boolean, default=True)
    last_modified_by = Column(Integer, nullable=True)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
