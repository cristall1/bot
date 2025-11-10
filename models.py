import enum

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, JSON, Enum as SQLEnum
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
    alerts_created = relationship("Alert", foreign_keys="Alert.creator_id", back_populates="creator")
    alerts_moderated = relationship("Alert", foreign_keys="Alert.moderator_id", back_populates="moderator")
    alert_preferences = relationship("UserAlertPreference", back_populates="user", cascade="all, delete-orphan")
    user_messages = relationship("UserMessage", back_populates="user")
    courier_info = relationship("Courier", back_populates="user", uselist=False)
    activities = relationship("UserActivity", back_populates="user")
    button_clicks = relationship("ButtonClick", back_populates="user")


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


class AlertType(enum.Enum):
    """11 alert types for the Al-Azhar community"""
    SHURTA = "SHURTA"  # Police alert
    MISSING_PERSON = "MISSING_PERSON"  # Lost person
    LOST_ITEM = "LOST_ITEM"  # Lost item
    SCAM_WARNING = "SCAM_WARNING"  # Fraud / scam warning
    MEDICAL_EMERGENCY = "MEDICAL_EMERGENCY"  # Medical emergency support
    ACCOMMODATION_NEEDED = "ACCOMMODATION_NEEDED"  # Housing request
    RIDE_SHARING = "RIDE_SHARING"  # Ride sharing / carpool
    JOB_POSTING = "JOB_POSTING"  # Job offer
    LOST_DOCUMENT = "LOST_DOCUMENT"  # Lost official document
    EVENT_ANNOUNCEMENT = "EVENT_ANNOUNCEMENT"  # Event announcements
    COURIER_NEEDED = "COURIER_NEEDED"  # Courier request


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


class Alert(Base):
    """Unified alert system for all 11 alert types"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    alert_type = Column(SQLEnum(AlertType), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Content fields
    title = Column(String(255), nullable=True)  # Name for person, what for item, job title, etc
    description = Column(Text, nullable=False)
    photo_file_id = Column(String(500), nullable=True)
    additional_files = Column(JSON, nullable=True)  # Additional file IDs if needed
    
    # Location fields
    location_type = Column(String(20), nullable=True)  # ADDRESS, GEO, MAPS
    address_text = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_name = Column(String(255), nullable=True)
    maps_url = Column(String(500), nullable=True)
    
    # Contact
    phone = Column(String(50), nullable=True)
    contact_info = Column(JSON, nullable=True)  # Additional contact methods
    
    # Moderation fields
    is_approved = Column(Boolean, default=False)
    is_moderated = Column(Boolean, default=False)
    moderator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderated_at = Column(DateTime, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Targeting filters (for broadcasts after approval)
    target_languages = Column(JSON, nullable=True)  # ["RU", "UZ"] or null for all
    target_citizenships = Column(JSON, nullable=True)  # ["UZ", "RU", "KZ", "KG"] or null
    target_couriers_only = Column(Boolean, default=False)
    
    # Statistics
    broadcast_sent = Column(Boolean, default=False)
    broadcast_count = Column(Integer, default=0)  # Number of users reached
    broadcast_at = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)  # Auto-expiration (48h for some types)
    
    # Relationships
    creator = relationship("User", foreign_keys=[creator_id], back_populates="alerts_created")
    moderator = relationship("User", foreign_keys=[moderator_id], back_populates="alerts_moderated")


class UserAlertPreference(Base):
    """User preferences for receiving specific alert types"""
    __tablename__ = "user_alert_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    alert_type = Column(SQLEnum(AlertType), nullable=False)
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="alert_preferences")


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


class UserActivity(Base):
    """Отслеживание активности пользователей для статистики"""
    __tablename__ = "user_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # BUTTON_CLICK, MESSAGE_SENT, etc
    activity_data = Column(JSON, nullable=True)  # Дополнительные метаданные
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="activities")


class ButtonClick(Base):
    """Отслеживание кликов по кнопкам для статистики"""
    __tablename__ = "button_clicks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    button_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="button_clicks")


class MainMenu(Base):
    """Главное меню (TALIM, DOSTAVKA)"""
    __tablename__ = "main_menu"

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    icon = Column(String(50), nullable=True)
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    categories = relationship("Category", back_populates="main_menu", cascade="all, delete-orphan")
    filters = relationship("MenuFilter", back_populates="main_menu", cascade="all, delete-orphan")


class MenuFilter(Base):
    """Фильтры меню (Гражданство, Вид документа)"""
    __tablename__ = "menu_filters"

    id = Column(Integer, primary_key=True, index=True)
    main_menu_id = Column(Integer, ForeignKey("main_menu.id"), nullable=False, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    filter_type = Column(String(20), default="buttons")
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    main_menu = relationship("MainMenu", back_populates="filters")
    options = relationship("MenuFilterOption", back_populates="filter", cascade="all, delete-orphan")


class MenuFilterOption(Base):
    """Опции фильтра (Узбекистан, Россия, Казахстан)"""
    __tablename__ = "menu_filter_options"

    id = Column(Integer, primary_key=True, index=True)
    filter_id = Column(Integer, ForeignKey("menu_filters.id"), nullable=False, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    icon = Column(String(50), nullable=True)
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    filter = relationship("MenuFilter", back_populates="options")
    categories = relationship("Category", back_populates="filter_option")


class Category(Base):
    """Категории с иерархией"""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    main_menu_id = Column(Integer, ForeignKey("main_menu.id"), nullable=False, index=True)
    parent_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True, index=True)
    filter_option_id = Column(Integer, ForeignKey("menu_filter_options.id"), nullable=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    icon = Column(String(50), nullable=True)
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    main_menu = relationship("MainMenu", back_populates="categories")
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    filter_option = relationship("MenuFilterOption", back_populates="categories")
    content = relationship("CategoryContent", back_populates="category", cascade="all, delete-orphan")
    buttons = relationship("CategoryButton", back_populates="category", cascade="all, delete-orphan")


class CategoryContent(Base):
    """Контент категории"""
    __tablename__ = "category_content"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    content_type = Column(String(20), nullable=False)  # text|photo|pdf|audio|location
    text_ru = Column(Text, nullable=True)
    text_uz = Column(Text, nullable=True)
    file_id = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_title_ru = Column(String(255), nullable=True)
    location_title_uz = Column(String(255), nullable=True)
    order_index = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="content")


class CategoryButton(Base):
    """Кнопки категории"""
    __tablename__ = "category_buttons"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    text_ru = Column(String(255), nullable=False)
    text_uz = Column(String(255), nullable=False)
    button_type = Column(String(20), default="url")  # url|next_category
    action_data = Column(JSON, nullable=True)
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="buttons")


class ModerationQueue(Base):
    """Очередь модерации (Moderation queue)"""
    __tablename__ = "moderation_queue"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False)  # NOTIFICATION, SHURTA_ALERT, DELIVERY, USER_MESSAGE
    entity_id = Column(Integer, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="PENDING")  # PENDING, APPROVED, REJECTED
    moderator_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    moderator_comment = Column(Text, nullable=True)
    admin_message_id = Column(Integer, nullable=True)  # Message ID in admin chat
    created_at = Column(DateTime, default=datetime.utcnow)
    moderated_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    moderator = relationship("User", foreign_keys=[moderator_id])


class WebAppCategoryItemType(enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    DOCUMENT = "DOCUMENT"
    LINK = "LINK"
    VIDEO = "VIDEO"
    BUTTON = "BUTTON"


class WebAppFile(Base):
    """Files uploaded for Web App content"""
    __tablename__ = "webapp_files"

    id = Column(Integer, primary_key=True, index=True)
    telegram_file_id = Column(String(500), nullable=True)  # Telegram file_id if uploaded via bot
    storage_path = Column(String(500), nullable=True)  # Local storage path
    file_type = Column(String(50), nullable=False)  # IMAGE, DOCUMENT, VIDEO, AUDIO
    mime_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    original_name = Column(String(500), nullable=True)  # Original filename
    description = Column(Text, nullable=True)  # Optional description
    tag = Column(String(255), nullable=True)  # Optional tag label
    width = Column(Integer, nullable=True)  # Image width (for images only)
    height = Column(Integer, nullable=True)  # Image height (for images only)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    uploader = relationship("User", lazy="selectin")
    category_items = relationship(
        "WebAppCategoryItem",
        foreign_keys="WebAppCategoryItem.file_id",
        back_populates="file",
        lazy="selectin"
    )
    categories_as_cover = relationship(
        "WebAppCategory",
        back_populates="cover_file",
        lazy="selectin"
    )


class WebAppCategory(Base):
    """Categories for Web App content"""
    __tablename__ = "webapp_categories"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    cover_file_id = Column(Integer, ForeignKey("webapp_files.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = relationship(
        "WebAppCategoryItem",
        back_populates="category",
        foreign_keys="WebAppCategoryItem.category_id",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="WebAppCategoryItem.order_index"
    )
    cover_file = relationship(
        "WebAppFile",
        foreign_keys=[cover_file_id],
        back_populates="categories_as_cover",
        lazy="selectin"
    )
    targeted_items = relationship(
        "WebAppCategoryItem",
        foreign_keys="WebAppCategoryItem.target_category_id",
        lazy="selectin"
    )


class WebAppCategoryItem(Base):
    """Content items for Web App categories"""
    __tablename__ = "webapp_category_items"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("webapp_categories.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # TEXT, IMAGE, DOCUMENT, LINK, VIDEO, BUTTON
    text_content = Column(Text, nullable=True)  # Text content or caption
    rich_metadata = Column(JSON, nullable=True)  # Rich metadata for complex items
    file_id = Column(Integer, ForeignKey("webapp_files.id"), nullable=True)
    button_text = Column(String(255), nullable=True)  # For BUTTON type
    target_category_id = Column(Integer, ForeignKey("webapp_categories.id"), nullable=True)  # Navigation target
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = relationship(
        "WebAppCategory",
        foreign_keys=[category_id],
        back_populates="items",
        lazy="selectin"
    )
    file = relationship(
        "WebAppFile",
        foreign_keys=[file_id],
        back_populates="category_items",
        lazy="selectin"
    )
    target_category = relationship(
        "WebAppCategory",
        foreign_keys=[target_category_id],
        lazy="selectin"
    )


class MainMenuButton(Base):
    """Main menu buttons for User Bot (Inline Keyboard Buttons)"""
    __tablename__ = "main_menu_buttons"

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    icon = Column(String(50), nullable=True)  # Emoji icon
    callback_data = Column(String(255), nullable=False)  # Callback data for button
    order_index = Column(Integer, default=0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MenuItem(Base):
    """Menu items for User Bot main menu"""
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    name_ru = Column(String(255), nullable=False)
    name_uz = Column(String(255), nullable=False)
    description_ru = Column(Text, nullable=True)
    description_uz = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # Emoji icon
    is_active = Column(Boolean, default=True, index=True)
    order_index = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    content = relationship("MenuContent", back_populates="menu_item", cascade="all, delete-orphan", order_by="MenuContent.order_index")
    buttons = relationship("MenuButton", back_populates="menu_item", cascade="all, delete-orphan", order_by="MenuButton.order_index")


class MenuContent(Base):
    """Content items attached to menu items"""
    __tablename__ = "menu_content"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False, index=True)
    content_type = Column(String(20), nullable=False)  # TEXT, PHOTO, PDF, AUDIO, LOCATION
    text_ru = Column(Text, nullable=True)
    text_uz = Column(Text, nullable=True)
    file_id = Column(String(500), nullable=True)  # Telegram file_id for photo, pdf, audio
    caption_ru = Column(Text, nullable=True)  # Caption for photo/file
    caption_uz = Column(Text, nullable=True)  # Caption for photo/file
    location_type = Column(String(20), nullable=True)  # ADDRESS, GEO, MAPS
    address_text = Column(String(500), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    geo_name = Column(String(255), nullable=True)
    maps_url = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    menu_item = relationship("MenuItem", back_populates="content")


class MenuButton(Base):
    """Buttons attached to menu items"""
    __tablename__ = "menu_buttons"

    id = Column(Integer, primary_key=True, index=True)
    menu_item_id = Column(Integer, ForeignKey("menu_items.id"), nullable=False, index=True)
    button_type = Column(String(20), default="INLINE")  # INLINE or KEYBOARD
    text_ru = Column(String(255), nullable=False)
    text_uz = Column(String(255), nullable=False)
    action_type = Column(String(20), nullable=False)  # OPEN_URL, SEND_TEXT, SEND_PHOTO, SEND_PDF, SEND_AUDIO, SEND_LOCATION
    action_data = Column(JSON, nullable=True)  # Flexible data: {"url": "...", "file_id": "...", "text_ru": "...", "text_uz": "...", etc}
    order_index = Column(Integer, default=0, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    menu_item = relationship("MenuItem", back_populates="buttons")
