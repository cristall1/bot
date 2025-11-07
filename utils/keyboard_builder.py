from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional, Dict


class KeyboardBuilder:
    @staticmethod
    def inline_keyboard(buttons: List[Dict], row_width: int = 2) -> InlineKeyboardMarkup:
        """Build inline keyboard from button list"""
        keyboard = []
        row = []
        
        for button in buttons:
            btn = InlineKeyboardButton(
                text=button.get("text", ""),
                callback_data=button.get("callback_data"),
                url=button.get("url")
            )
            row.append(btn)
            
            if len(row) >= row_width:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def reply_keyboard(buttons: List[str], row_width: int = 2, resize: bool = True) -> ReplyKeyboardMarkup:
        """Build reply keyboard from button list"""
        keyboard = []
        row = []
        
        for button_text in buttons:
            btn = KeyboardButton(text=button_text)
            row.append(btn)
            
            if len(row) >= row_width:
                keyboard.append(row)
                row = []
        
        if row:
            keyboard.append(row)
        
        return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=resize)

    @staticmethod
    def main_menu_keyboard(language: str = "RU") -> ReplyKeyboardMarkup:
        """Build main menu keyboard"""
        from locales import t
        
        buttons = [
            t("menu_categories", language),
            t("menu_services", language),
            t("menu_search", language),
            t("menu_contact", language),
            t("menu_courier", language),
            t("menu_settings", language),
            t("menu_help", language)
        ]
        
        return KeyboardBuilder.reply_keyboard(buttons, row_width=2)

    @staticmethod
    def admin_menu_keyboard(language: str = "RU") -> ReplyKeyboardMarkup:
        """Build admin menu keyboard"""
        from locales import t
        
        buttons = [
            t("admin_categories", language),
            t("admin_buttons", language),
            t("admin_services", language),
            t("admin_users", language),
            t("admin_couriers", language),
            t("admin_broadcast", language),
            t("admin_stats", language),
            t("admin_settings", language),
            t("admin_parse", language)
        ]
        
        return KeyboardBuilder.reply_keyboard(buttons, row_width=2)

    @staticmethod
    def language_keyboard() -> InlineKeyboardMarkup:
        """Build language selection keyboard"""
        buttons = [
            {"text": "🇷🇺 Русский", "callback_data": "lang_RU"},
            {"text": "🇺🇿 O'zbekcha", "callback_data": "lang_UZ"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)

    @staticmethod
    def citizenship_keyboard(language: str = "RU") -> InlineKeyboardMarkup:
        """Build citizenship selection keyboard"""
        from locales import t
        
        buttons = [
            {"text": t("citizenship_uz", language), "callback_data": "citizenship_UZ"},
            {"text": t("citizenship_ru", language), "callback_data": "citizenship_RU"},
            {"text": t("citizenship_kz", language), "callback_data": "citizenship_KZ"},
            {"text": t("citizenship_kg", language), "callback_data": "citizenship_KG"}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)

    @staticmethod
    def back_button(language: str = "RU", callback_data: str = "back") -> InlineKeyboardMarkup:
        """Build back button"""
        from locales import t
        
        buttons = [{"text": t("btn_back", language), "callback_data": callback_data}]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=1)

    @staticmethod
    def confirm_keyboard(language: str = "RU", confirm_data: str = "confirm", cancel_data: str = "cancel") -> InlineKeyboardMarkup:
        """Build confirm/cancel keyboard"""
        from locales import t
        
        buttons = [
            {"text": t("btn_confirm", language), "callback_data": confirm_data},
            {"text": t("btn_cancel", language), "callback_data": cancel_data}
        ]
        return KeyboardBuilder.inline_keyboard(buttons, row_width=2)

    @staticmethod
    def pagination_keyboard(page: int, total_pages: int, prefix: str = "page", language: str = "RU") -> InlineKeyboardMarkup:
        """Build pagination keyboard"""
        buttons = []
        
        if page > 1:
            buttons.append({"text": "⬅️", "callback_data": f"{prefix}_{page - 1}"})
        
        buttons.append({"text": f"{page}/{total_pages}", "callback_data": "current_page"})
        
        if page < total_pages:
            buttons.append({"text": "➡️", "callback_data": f"{prefix}_{page + 1}"})
        
        return KeyboardBuilder.inline_keyboard(buttons, row_width=3)
