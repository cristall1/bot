from aiogram.fsm.state import State, StatesGroup


class UserStates(StatesGroup):
    """States for user bot"""
    # Language selection
    selecting_language = State()
    
    # Delivery creation states
    delivery_description = State()
    delivery_location_choice = State()
    delivery_location_text = State()
    delivery_location_maps = State()
    delivery_phone = State()
    
    # Notification (lost person) states
    notification_person_name = State()
    notification_person_desc = State()
    notification_person_photo = State()
    notification_person_location_choice = State()
    notification_person_location_text = State()
    notification_person_location_maps = State()
    notification_person_phone = State()
    
    # Notification (lost item) states
    notification_item_what = State()
    notification_item_desc = State()
    notification_item_photo = State()
    notification_item_location_choice = State()
    notification_item_location_text = State()
    notification_item_location_maps = State()
    notification_item_phone = State()
    
    # Shurta (police) states
    shurta_description = State()
    shurta_location_choice = State()
    shurta_location_text = State()
    shurta_location_maps = State()
    shurta_photo = State()
    
    # Admin contact
    admin_contact_message = State()
    
    # Viewing active orders
    viewing_active_orders = State()


class AdminStates(StatesGroup):
    """States for admin bot"""
    # Document management
    doc_select_citizenship = State()
    doc_name_ru = State()
    doc_name_uz = State()
    doc_content_ru = State()
    doc_content_uz = State()
    doc_photo = State()
    doc_telegraph = State()
    doc_order_index = State()
    
    # Document editing
    doc_edit_select = State()
    doc_edit_field = State()
    doc_edit_value = State()
    
    # Document button management
    doc_button_text_ru = State()
    doc_button_text_uz = State()
    doc_button_url = State()
    doc_button_order = State()
    
    # Delivery management
    delivery_view = State()
    
    # Courier management
    courier_select = State()
    courier_action = State()
    
    # User management
    user_search = State()
    user_select = State()
    user_action = State()
    
    # Message management
    message_select = State()
    message_reply = State()
    
    # Broadcast
    broadcast_message_ru = State()
    broadcast_message_uz = State()
    broadcast_photo = State()
    broadcast_filter = State()
    broadcast_confirm = State()
    
    # Telegraph editor
    telegraph_title_ru = State()
    telegraph_title_uz = State()
    telegraph_content = State()
    telegraph_author = State()
    telegraph_tags = State()
    telegraph_edit_select = State()
    
    # Notification management
    notification_view = State()
    notification_action = State()
    
    # Shurta management
    shurta_view = State()
    shurta_action = State()
