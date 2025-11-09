"""
Telegram Web App authentication module
Implements initData validation and user authentication
"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from urllib.parse import parse_qs, unquote

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import AsyncSessionLocal
from models import User
from services.user_service import UserService
from utils.logger import logger

__all__ = [
    "TelegramAuthError",
    "validate_telegram_webapp_data",
    "get_current_user",
    "require_admin_user",
]


class TelegramAuthError(Exception):
    """Base exception for Telegram auth errors"""
    pass


def validate_telegram_webapp_data(init_data: str, bot_token: str) -> dict:
    """
    Validate Telegram Web App initData using HMAC-SHA256.
    
    Args:
        init_data: The initData string from Telegram Web App
        bot_token: Bot token to use for validation
        
    Returns:
        dict: Parsed and validated data
        
    Raises:
        TelegramAuthError: If validation fails
    """
    try:
        # Parse the query string
        parsed_data = parse_qs(init_data, keep_blank_values=True)
        
        # Extract hash
        hash_value = parsed_data.get('hash', [None])[0]
        if not hash_value:
            raise TelegramAuthError("Отсутствует параметр hash в initData")
        
        # Remove hash from data and prepare data-check-string
        data_check_pairs = []
        for key in sorted(parsed_data.keys()):
            if key == 'hash':
                continue
            value = parsed_data[key][0]
            data_check_pairs.append(f"{key}={value}")
        
        data_check_string = "\n".join(data_check_pairs)
        
        # Calculate secret key: HMAC-SHA256(bot_token, "WebAppData")
        secret_key = hmac.new(
            key="WebAppData".encode(),
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()
        
        # Calculate hash of data-check-string using secret key
        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Compare hashes
        if not hmac.compare_digest(calculated_hash, hash_value):
            raise TelegramAuthError("Неверная подпись HMAC - данные не прошли проверку")
        
        # Check auth_date to prevent replay attacks (24 hours expiration)
        auth_date = parsed_data.get('auth_date', [None])[0]
        if auth_date:
            try:
                auth_timestamp = int(auth_date)
                auth_datetime = datetime.fromtimestamp(auth_timestamp)
                now = datetime.now()
                
                # Check if data is not too old (24 hours)
                if (now - auth_datetime) > timedelta(hours=24):
                    raise TelegramAuthError("initData устарел (более 24 часов)")
                
                # Check if data is not from the future (with 5 min tolerance)
                if auth_datetime > (now + timedelta(minutes=5)):
                    raise TelegramAuthError("initData из будущего - проверьте время на сервере")
            except ValueError:
                raise TelegramAuthError("Неверный формат auth_date")
        
        # Parse user data
        user_json = parsed_data.get('user', [None])[0]
        if not user_json:
            raise TelegramAuthError("Отсутствуют данные пользователя в initData")
        
        try:
            user_data = json.loads(unquote(user_json))
        except json.JSONDecodeError:
            raise TelegramAuthError("Неверный формат JSON в данных пользователя")
        
        # Return validated data
        return {
            'user': user_data,
            'auth_date': auth_date,
            'query_id': parsed_data.get('query_id', [None])[0],
        }
        
    except TelegramAuthError:
        raise
    except Exception as e:
        logger.error(f"Ошибка валидации Telegram Web App данных: {e}")
        raise TelegramAuthError(f"Ошибка валидации: {str(e)}")


async def get_db_session() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    
    Validates Telegram Web App initData and creates/updates user in database.
    
    Args:
        request: FastAPI request object
        session: Database session
        
    Returns:
        User: Authenticated user object
        
    Raises:
        HTTPException: 401 if authentication fails
    """
    # Check for debug bypass
    if hasattr(settings, 'webapp_debug_skip_auth') and settings.webapp_debug_skip_auth:
        logger.warning("⚠️ ВНИМАНИЕ: Используется отладочный режим без проверки аутентификации!")
        
        # Get debug user ID from settings or use default
        debug_telegram_id = getattr(settings, 'webapp_debug_user_id', 5912983856)
        
        user = await UserService.get_user(session, debug_telegram_id)
        if not user:
            # Create debug user
            user = await UserService.create_or_update_user(
                session=session,
                telegram_id=debug_telegram_id,
                username="debug_user",
                first_name="Debug User",
                language="RU"
            )
            logger.info(f"Создан отладочный пользователь: {debug_telegram_id}")
        
        return user
    
    # Try to get initData from header first, then from query params
    init_data = request.headers.get('X-Telegram-Init-Data')
    
    if not init_data:
        # Try to get from query params
        init_data = request.query_params.get('initData')
    
    if not init_data:
        logger.error("❌ Отсутствует initData в запросе")
        raise HTTPException(
            status_code=401,
            detail="Требуется аутентификация Telegram Web App"
        )
    
    try:
        # Validate initData
        validated_data = validate_telegram_webapp_data(init_data, settings.user_bot_token)
        user_data = validated_data['user']
        
        # Extract user information
        telegram_id = user_data.get('id')
        if not telegram_id:
            raise TelegramAuthError("Отсутствует ID пользователя")
        
        username = user_data.get('username')
        first_name = user_data.get('first_name', '')
        language_code = user_data.get('language_code', 'ru')
        
        # Map language code to our format (RU/UZ)
        language_code_lower = language_code.lower() if isinstance(language_code, str) else 'ru'
        if language_code_lower.startswith('uz'):
            language = 'UZ'
        else:
            language = 'RU'
        
        # Create or update user in database
        user = await UserService.create_or_update_user(
            session=session,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language=language
        )
        
        logger.info(f"✅ Успешная аутентификация пользователя: {telegram_id} (@{username})")
        return user
        
    except TelegramAuthError as e:
        logger.error(f"❌ Ошибка аутентификации Telegram: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Ошибка аутентификации: {str(e)}"
        )
    except Exception as e:
        logger.error(f"❌ Неожиданная ошибка при аутентификации: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Ошибка аутентификации"
        )


async def require_admin_user(
    user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to require admin privileges.
    
    Args:
        user: Current authenticated user
        
    Returns:
        User: Admin user object
        
    Raises:
        HTTPException: 403 if user is not an admin
    """
    if not user.is_admin:
        logger.warning(f"⚠️ Попытка доступа к админским функциям от пользователя {user.telegram_id} (@{user.username})")
        raise HTTPException(
            status_code=403,
            detail="Требуются права администратора"
        )
    
    logger.info(f"✅ Администратор {user.telegram_id} (@{user.username}) получил доступ")
    return user
