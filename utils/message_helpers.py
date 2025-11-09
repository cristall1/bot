"""
Message Helper Utilities
Auto-delete messages, button layouts, and keyboard management
"""
import asyncio
from typing import Optional, List, Union
from aiogram import Bot
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Message,
    ReplyKeyboardMarkup
)
from utils.logger import logger


async def send_menu_auto_delete(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    delete_after: int = 30
) -> Message:
    """
    Send a menu message that auto-deletes after specified seconds
    
    Args:
        bot: Bot instance
        chat_id: Chat ID
        text: Message text
        reply_markup: Optional keyboard markup
        delete_after: Seconds before deletion (default: 30)
    
    Returns:
        Sent message object
    """
    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup
    )
    
    # Schedule deletion
    asyncio.create_task(
        delete_message_later(bot, chat_id, msg.message_id, delete_after)
    )
    
    return msg


async def delete_message_later(
    bot: Bot,
    chat_id: int,
    message_id: int,
    delay: int
):
    """
    Delete message after delay
    
    Args:
        bot: Bot instance
        chat_id: Chat ID
        message_id: Message ID to delete
        delay: Delay in seconds
    """
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"✅ Сообщение {message_id} удалено автоматически")
    except Exception as e:
        # Message may have been already deleted or is too old
        logger.debug(f"⚠️ Не удалось удалить сообщение {message_id}: {str(e)}")


async def delete_message_immediately(
    bot: Bot,
    chat_id: int,
    message_id: int
):
    """
    Delete message immediately (no delay)
    
    Args:
        bot: Bot instance
        chat_id: Chat ID
        message_id: Message ID to delete
    """
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        logger.info(f"✅ Сообщение {message_id} удалено немедленно")
    except Exception as e:
        # Message may have been already deleted or is too old
        logger.debug(f"⚠️ Не удалось удалить сообщение {message_id}: {str(e)}")


def build_keyboard_2_columns(
    buttons: List[InlineKeyboardButton],
    back_button: Optional[InlineKeyboardButton] = None,
    single_row_buttons: Optional[List[InlineKeyboardButton]] = None
) -> InlineKeyboardMarkup:
    """
    Build inline keyboard with 2 buttons per row for compact layout
    
    Args:
        buttons: List of inline keyboard buttons
        back_button: Optional back button (will be on its own row)
        single_row_buttons: Optional list of buttons that should be on single rows
    
    Returns:
        InlineKeyboardMarkup with 2-column layout
    """
    keyboard_rows = []
    
    # Add main buttons in 2-column layout
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            keyboard_rows.append([buttons[i], buttons[i + 1]])
        else:
            keyboard_rows.append([buttons[i]])
    
    # Add single row buttons if provided
    if single_row_buttons:
        for btn in single_row_buttons:
            keyboard_rows.append([btn])
    
    # Add back button if provided
    if back_button:
        keyboard_rows.append([back_button])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard_rows)


def build_keyboard_rows(
    button_rows: List[List[InlineKeyboardButton]]
) -> InlineKeyboardMarkup:
    """
    Build inline keyboard from predefined rows
    
    Args:
        button_rows: List of button rows
    
    Returns:
        InlineKeyboardMarkup
    """
    return InlineKeyboardMarkup(inline_keyboard=button_rows)
