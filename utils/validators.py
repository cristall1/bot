import re
import phonenumbers
from typing import Optional


def validate_url(url: str) -> bool:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return url_pattern.match(url) is not None


def validate_phone(phone: str, region: str = None) -> bool:
    """Validate phone number"""
    try:
        parsed = phonenumbers.parse(phone, region)
        return phonenumbers.is_valid_number(parsed)
    except:
        return False


def format_phone(phone: str, region: str = None) -> Optional[str]:
    """Format phone number to international format"""
    try:
        parsed = phonenumbers.parse(phone, region)
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
    except:
        return None


def validate_telegram_id(telegram_id: int) -> bool:
    """Validate Telegram ID"""
    return isinstance(telegram_id, int) and telegram_id > 0


def sanitize_text(text: str, max_length: int = 4096) -> str:
    """Sanitize text for Telegram messages"""
    if not text:
        return ""
    text = text.strip()
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def validate_citizenship(citizenship: str) -> bool:
    """Validate citizenship code"""
    return citizenship in ["UZ", "RU", "KZ", "KG"]


def validate_language(language: str) -> bool:
    """Validate language code"""
    return language in ["RU", "UZ"]
