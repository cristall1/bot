import logging
import sys
from config import settings


class RussianFormatter(logging.Formatter):
    """Кастомный форматтер с русскими статусами и иконками"""
    
    STATUS_ICONS = {
        'INFO': '✅',
        'ERROR': '❌',
        'WARNING': '⚠️',
        'DEBUG': '🔍'
    }
    
    STATUS_NAMES = {
        'INFO': 'Успех',
        'ERROR': 'Ошибка',
        'WARNING': 'Предупреждение',
        'DEBUG': 'Отладка'
    }
    
    def format(self, record):
        # Извлекаем имя функции
        func_name = record.funcName if hasattr(record, 'funcName') else 'unknown'
        
        # Получаем иконку и статус
        icon = self.STATUS_ICONS.get(record.levelname, '●')
        status = self.STATUS_NAMES.get(record.levelname, record.levelname)
        
        # Формат: [ФУНКЦИЯ] [СТАТУС] [СООБЩЕНИЕ]
        base_line = f"[{func_name}] {icon} {status} | {record.getMessage()}"
        
        # Добавляем traceback если есть исключение
        if record.exc_info:
            base_line += "\n" + self.formatException(record.exc_info)
        
        return base_line


def setup_logger():
    logger = logging.getLogger("bot")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    formatter = RussianFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
