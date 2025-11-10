from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """States for user bot"""
    # Main menu
    main_menu = State()
    
    # Language & Citizenship selection
    waiting_language = State()
    waiting_citizenship = State()
    selecting_language = State()
    
    # Documents (Hujjat yordami)
    viewing_documents = State()
    viewing_citizenship_docs = State()
    viewing_document_content = State()
    
    # Delivery (Dostavka xizmati)
    delivery_menu = State()
    creating_delivery = State()
    delivery_description = State()
    delivery_location_type = State()  # Choose: address, geo, maps
    delivery_location_text = State()  # For text address
    delivery_location_geo = State()   # For geolocation
    delivery_location_maps = State()  # For Google Maps link
    delivery_phone = State()
    delivery_review = State()
    viewing_active_deliveries = State()
    taking_delivery = State()
    courier_status = State()
    
    # Legacy states for compatibility
    delivery_location = State()  # Deprecated, kept for compatibility
    delivery_location_choice = State()  # Deprecated, kept for compatibility
    
    # Propaja (Потеря)
    propaja_menu = State()
    propaja_type_selection = State()  # Choose: odam or narsa
    
    # Propaja Odam (Пропал человек)
    propaja_odam_name = State()
    propaja_odam_description = State()
    propaja_odam_location_type = State()  # Choose: address, geo, maps
    propaja_odam_location_text = State()
    propaja_odam_location_geo = State()
    propaja_odam_location_maps = State()
    propaja_odam_phone = State()
    propaja_odam_photo = State()
    propaja_odam_review = State()
    
    # Propaja Narsa (Потеря вещи)
    propaja_narsa_what = State()
    propaja_narsa_description = State()
    propaja_narsa_location_type = State()  # Choose: address, geo, maps
    propaja_narsa_location_text = State()
    propaja_narsa_location_geo = State()
    propaja_narsa_location_maps = State()
    propaja_narsa_phone = State()
    propaja_narsa_photo = State()
    propaja_narsa_review = State()
    
    # Notifications (Legacy naming - used in handlers)
    notification_person_name = State()
    notification_person_desc = State()
    notification_person_photo = State()
    notification_person_location = State()  # Deprecated, kept for compatibility
    notification_person_location_choice = State()  # Choose: text, geo, maps
    notification_person_location_text = State()
    notification_person_location_geo = State()
    notification_person_location_maps = State()
    notification_person_phone = State()
    
    notification_item_what = State()
    notification_item_desc = State()
    notification_item_photo = State()
    notification_item_location = State()  # Deprecated, kept for compatibility
    notification_item_location_choice = State()  # Choose: text, geo, maps
    notification_item_location_text = State()
    notification_item_location_geo = State()
    notification_item_location_maps = State()
    notification_item_phone = State()
    
    # Shurta (Полиция)
    shurta_menu = State()
    shurta_description = State()
    shurta_location_type = State()  # Choose: address, geo, maps
    shurta_location_text = State()
    shurta_location_geo = State()
    shurta_location_maps = State()
    shurta_photo = State()
    shurta_review = State()
    
    # Admin message
    admin_message = State()
    admin_contact_message = State()
    
    # Settings
    settings_menu = State()
    settings_language = State()
    settings_notifications = State()
    settings_alert_preferences = State()
    
    # Unified Alert Creation (11 types)
    alert_type_selection = State()
    alert_title = State()
    alert_description = State()
    alert_phone = State()
    alert_location_choice = State()
    alert_location_text = State()
    alert_location_geo = State()
    alert_location_maps = State()
    alert_photo = State()
    alert_review = State()
    
    # Category Navigation
    browsing_categories = State()


class AdminStates(StatesGroup):
    """States for admin bot"""
    # Main menu
    admin_menu = State()
    
    # Category management (New admin panel structure)
    category_management = State()
    category_list = State()
    category_editing = State()
    category_name_input = State()
    category_text_input = State()
    category_button_type_selection = State()  # inline, keyboard, or simple
    category_media_management = State()
    category_photo_upload = State()
    category_audio_upload = State()
    category_pdf_upload = State()
    category_link_input = State()
    category_subcategory_management = State()
    
    # Documents management (Hujjat yordami)
    hujjat_menu = State()
    hujjat_citizenship_selection = State()
    hujjat_list = State()
    hujjat_item = State()
    editing_hujjat = State()
    editing_hujjat_name_ru = State()
    editing_hujjat_name_uz = State()
    editing_hujjat_content_ru = State()
    editing_hujjat_content_uz = State()
    editing_hujjat_photo = State()
    editing_hujjat_audio = State()
    editing_hujjat_pdf = State()
    deleting_hujjat = State()
    
    # Document buttons management
    button_management = State()
    button_list = State()
    editing_button = State()
    button_name_ru = State()
    button_name_uz = State()
    button_type_selection = State()  # link, photo, pdf, audio, geo
    button_url = State()
    button_photo = State()
    button_audio = State()
    button_pdf = State()
    button_geo = State()
    adding_button = State()
    deleting_button = State()
    
    # Legacy states for compatibility
    managing_buttons = State()
    button_text_ru = State()
    button_text_uz = State()
    button_file = State()
    
    # Delivery management (Dostavka xizmati)
    delivery_management = State()
    delivery_active_list = State()
    delivery_completed_list = State()
    delivery_rejected_list = State()
    courier_management = State()
    courier_list = State()
    
    # Legacy states for compatibility
    viewing_active_deliveries = State()
    viewing_completed_deliveries = State()
    viewing_rejected_deliveries = State()
    
    # Propaja management
    propaja_management = State()
    propaja_odam_list = State()
    propaja_narsa_list = State()
    propaja_item_view = State()
    moderating_propaja = State()
    
    # Shurta management
    shurta_management = State()
    shurta_list = State()
    shurta_item_view = State()
    moderating_shurta = State()
    
    # User management
    user_management = State()
    searching_user = State()
    user_search_input = State()
    user_details = State()
    
    # Messages management
    messages_management = State()
    message_view = State()
    message_reply_input = State()
    
    # Broadcast
    broadcast_menu = State()
    broadcast_text_ru = State()
    broadcast_text_uz = State()
    broadcast_photo = State()
    broadcast_recipient_filter = State()
    broadcast_preview = State()
    
    # Telegraph editor
    telegraph_menu = State()
    telegraph_list = State()
    creating_telegraph = State()
    telegraph_title = State()
    telegraph_content = State()
    
    # Settings
    settings_menu = State()
    toggle_settings = State()
    
    # Alert moderation (unified 11 types)
    alert_moderation_menu = State()
    alert_type_filter = State()
    alert_pending_list = State()
    alert_detail_view = State()
    alert_rejection_reason = State()
    alert_broadcast_confirm = State()
    
    # Export
    export_menu = State()
    export_type_selection = State()
    export_format_selection = State()
    export_filter_selection = State()
    
    # Statistics
    statistics_menu = State()
    statistics_detail = State()
    
    # Legacy states for compatibility
    viewing_propaja_item = State()
    viewing_shurta_item = State()
    viewing_message = State()
    replying_message = State()
    broadcast_creation = State()
    
    # Main Menu Management (One-Message System)
    menu_management = State()
    menu_item_editing = State()
    menu_item_name_ru = State()
    menu_item_name_uz = State()
    menu_item_icon = State()
    menu_item_description_ru = State()
    menu_item_description_uz = State()
    menu_add_text_ru = State()
    menu_add_text_uz = State()
    menu_add_photo = State()
    menu_add_photo_caption_ru = State()
    menu_add_photo_caption_uz = State()
    menu_add_pdf = State()
    menu_add_pdf_caption_ru = State()
    menu_add_pdf_caption_uz = State()
    menu_add_audio = State()
    menu_add_audio_caption_ru = State()
    menu_add_audio_caption_uz = State()
    menu_add_location_type = State()
    menu_add_location_text = State()
    menu_add_location_geo = State()
    menu_add_location_maps = State()
    menu_add_button_type = State()
    menu_add_button_text_ru = State()
    menu_add_button_text_uz = State()
    menu_add_button_action = State()
    menu_add_button_action_data = State()
    menu_create_name_ru = State()
    menu_create_name_uz = State()
    menu_create_icon = State()
