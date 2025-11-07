from datetime import datetime, timedelta
from typing import Optional


def format_datetime(dt: datetime, language: str = "RU") -> str:
    """Format datetime for display"""
    if language == "UZ":
        return dt.strftime("%d.%m.%Y %H:%M")
    return dt.strftime("%d.%m.%Y %H:%M")


def time_ago(dt: datetime, language: str = "RU") -> str:
    """Get time ago string"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff < timedelta(minutes=1):
        return "только что" if language == "RU" else "hozirgina"
    elif diff < timedelta(hours=1):
        minutes = int(diff.total_seconds() / 60)
        if language == "RU":
            return f"{minutes} мин. назад"
        return f"{minutes} daqiqa oldin"
    elif diff < timedelta(days=1):
        hours = int(diff.total_seconds() / 3600)
        if language == "RU":
            return f"{hours} ч. назад"
        return f"{hours} soat oldin"
    elif diff < timedelta(days=7):
        days = diff.days
        if language == "RU":
            return f"{days} дн. назад"
        return f"{days} kun oldin"
    else:
        return format_datetime(dt, language)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def get_citizenship_flag(citizenship: str) -> str:
    """Get flag emoji for citizenship"""
    flags = {
        "UZ": "🇺🇿",
        "RU": "🇷🇺",
        "KZ": "🇰🇿",
        "KG": "🇰🇬"
    }
    return flags.get(citizenship, "🌍")


def get_citizenship_name(citizenship: str, language: str = "RU") -> str:
    """Get citizenship name"""
    names = {
        "RU": {
            "UZ": "Узбекистан",
            "RU": "Россия",
            "KZ": "Казахстан",
            "KG": "Киргизия"
        },
        "UZ": {
            "UZ": "O'zbekiston",
            "RU": "Rossiya",
            "KZ": "Qozog'iston",
            "KG": "Qirg'iziston"
        }
    }
    return names.get(language, names["RU"]).get(citizenship, citizenship)


def paginate_list(items: list, page: int = 1, per_page: int = 10):
    """Paginate list"""
    total = len(items)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    return {
        "items": items[start:end],
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }


def escape_markdown(text: str) -> str:
    """Escape markdown special characters"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
