from aiogram.types import InlineKeyboardMarkup
from utils.keyboard_builder import KeyboardBuilder
from locales import t


class AdminMenuService:
    """Service for admin menu navigation"""
    
    @staticmethod
    def get_main_menu(language: str = "RU") -> InlineKeyboardMarkup:
        """Get main admin menu"""
        buttons = [
            {"text": t("admin_categories", language), "callback_data": "admin_categories"},
            {"text": t("admin_buttons", language), "callback_data": "admin_buttons"},
            {"text": t("admin_services", language), "callback_data": "admin_services"},
            {"text": t("admin_users", language), "callback_data": "admin_users"},
            {"text": t("admin_couriers", language), "callback_data": "admin_couriers"},
            {"text": t("admin_broadcast", language), "callback_data": "admin_broadcast"},
            {"text": t("admin_stats", language), "callback_data": "admin_stats"},
            {"text": t("admin_settings", language), "callback_data": "admin_settings"},
            {"text": t("admin_parse", language), "callback_data": "admin_parse"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)
    
    @staticmethod
    def get_category_menu(language: str = "RU") -> InlineKeyboardMarkup:
        """Get category management menu"""
        buttons = [
            {"text": t("add_category", language), "callback_data": "cat_add"},
            {"text": t("edit_category", language), "callback_data": "cat_edit"},
            {"text": t("view_category_tree", language), "callback_data": "cat_tree"},
            {"text": t("btn_back", language), "callback_data": "admin_menu"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)
    
    @staticmethod
    def get_button_menu(language: str = "RU") -> InlineKeyboardMarkup:
        """Get button management menu"""
        buttons = [
            {"text": t("add_button", language), "callback_data": "btn_add"},
            {"text": t("list_buttons", language), "callback_data": "btn_list"},
            {"text": t("btn_back", language), "callback_data": "admin_menu"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)
    
    @staticmethod
    def get_service_menu(language: str = "RU") -> InlineKeyboardMarkup:
        """Get service management menu"""
        buttons = [
            {"text": t("pending_services", language), "callback_data": "svc_pending"},
            {"text": t("approved_services", language), "callback_data": "svc_approved"},
            {"text": t("btn_back", language), "callback_data": "admin_menu"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)
    
    @staticmethod
    def get_user_menu(language: str = "RU") -> InlineKeyboardMarkup:
        """Get user management menu"""
        buttons = [
            {"text": t("users_list", language), "callback_data": "usr_list"},
            {"text": t("search_user", language), "callback_data": "usr_search"},
            {"text": t("btn_back", language), "callback_data": "admin_menu"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)
    
    @staticmethod
    def get_courier_menu(language: str = "RU") -> InlineKeyboardMarkup:
        """Get courier management menu"""
        buttons = [
            {"text": t("couriers_list", language), "callback_data": "courier_list"},
            {"text": t("btn_back", language), "callback_data": "admin_menu"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=1)
    
    @staticmethod
    def get_broadcast_menu(language: str = "RU") -> InlineKeyboardMarkup:
        """Get broadcast menu"""
        buttons = [
            {"text": t("create_broadcast", language), "callback_data": "bc_create"},
            {"text": t("btn_back", language), "callback_data": "admin_menu"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=1)
