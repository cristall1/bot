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
    delivery_location = State()  # Deprecated, kept for compatibility
    delivery_location_choice = State()  # Choose: text, geo, maps
    delivery_location_type = State()  # Choose: address, geo, maps
    delivery_location_text = State()  # For text address
    delivery_location_geo = State()   # For geolocation
    delivery_location_maps = State()  # For Google Maps link
    delivery_phone = State()
    viewing_active_deliveries = State()
    courier_status = State()
    
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
    
    # Propaja Narsa (Потеря вещи)
    propaja_narsa_what = State()
    propaja_narsa_description = State()
    propaja_narsa_location_type = State()  # Choose: address, geo, maps
    propaja_narsa_location_text = State()
    propaja_narsa_location_geo = State()
    propaja_narsa_location_maps = State()
    propaja_narsa_phone = State()
    propaja_narsa_photo = State()
    
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
    shurta_description = State()
    shurta_location_choice = State()  # Choose: text, geo, maps
    shurta_location_input = State()  # For text address input
    shurta_location_type = State()  # Choose: address, geo, maps
    shurta_location_text = State()
    shurta_location_geo = State()
    shurta_location_maps = State()
    shurta_photo = State()
    
    # Admin message
    admin_message = State()
    admin_contact_message = State()
    
    # Settings
    settings_menu = State()


class AdminStates(StatesGroup):
    """States for admin bot"""
    # Main menu
    admin_menu = State()
    
    # Documents management (Hujjat yordami)
    hujjat_menu = State()
    hujjat_citizenship_selection = State()
    hujjat_list = State()
    editing_hujjat = State()
    editing_hujjat_name = State()
    editing_hujjat_content = State()
    editing_hujjat_photo = State()
    
    # Document buttons management
    managing_buttons = State()
    adding_button = State()
    button_text_ru = State()
    button_text_uz = State()
    button_type_selection = State()  # link, photo, pdf, geo
    button_url = State()
    button_photo = State()
    button_file = State()
    button_geo = State()
    
    # Delivery management (Dostavka xizmati)
    delivery_management = State()
    viewing_active_deliveries = State()
    viewing_completed_deliveries = State()
    viewing_rejected_deliveries = State()
    
    # Courier management
    courier_management = State()
    courier_list = State()
    
    # Propaja management
    propaja_management = State()
    propaja_odam_list = State()
    propaja_narsa_list = State()
    viewing_propaja_item = State()
    
    # Shurta management
    shurta_management = State()
    shurta_list = State()
    viewing_shurta_item = State()
    
    # User management
    user_management = State()
    searching_user = State()
    user_details = State()
    
    # Messages management
    messages_management = State()
    viewing_message = State()
    replying_message = State()
    
    # Broadcast
    broadcast_creation = State()
    broadcast_text_ru = State()
    broadcast_text_uz = State()
    broadcast_photo = State()
    broadcast_recipient_filter = State()
    
    # Settings
    settings_menu = State()
    
    # Telegraph editor
    telegraph_menu = State()
    creating_telegraph = State()
    telegraph_title = State()
    telegraph_content = State()
