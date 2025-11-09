# Telegram WebApp Authentication

## Overview

This module implements secure authentication for Telegram Web App API calls using the official Telegram WebApp `initData` validation mechanism.

## How It Works

### 1. Authentication Flow

1. **Client sends request** with `initData` parameter either as:
   - HTTP header: `X-Telegram-Init-Data`
   - Query parameter: `?initData=...`

2. **Server validates** the `initData` using HMAC-SHA256:
   - Parses the query string
   - Extracts all parameters except `hash`
   - Creates data-check-string (sorted key=value pairs)
   - Calculates HMAC-SHA256 signature using secret key
   - Compares with provided hash

3. **User is created/updated** in database:
   - Extracts user info (id, username, first_name, language_code)
   - Creates or updates User record via `UserService`
   - Returns authenticated User object

### 2. Security Features

- **HMAC-SHA256 signature validation**: Ensures data comes from Telegram
- **Timestamp validation**: Rejects data older than 24 hours
- **Replay attack prevention**: Checks auth_date timestamp
- **No password/token storage**: Uses Telegram's built-in security

### 3. Secret Key Generation

According to [Telegram Web Apps documentation](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app):

```python
secret_key = HMAC-SHA256(bot_token, "WebAppData")
hash = HMAC-SHA256(data_check_string, secret_key)
```

## Usage

### Basic Authentication

```python
from fastapi import APIRouter, Depends
from webapp.auth import get_current_user
from models import User

router = APIRouter()

@router.get("/api/me")
async def get_me(user: User = Depends(get_current_user)):
    return {"user_id": user.telegram_id, "username": user.username}
```

### Admin-Only Endpoints

```python
from webapp.auth import require_admin_user

@router.post("/api/admin/action")
async def admin_action(user: User = Depends(require_admin_user)):
    # Only admins can access this
    return {"message": "Admin action performed"}
```

### Manual Validation

```python
from webapp.auth import validate_telegram_webapp_data, TelegramAuthError

try:
    validated = validate_telegram_webapp_data(init_data, bot_token)
    user_data = validated['user']
    print(f"User ID: {user_data['id']}")
except TelegramAuthError as e:
    print(f"Validation failed: {e}")
```

## Development Mode

For local development without Telegram Web App, you can enable debug mode:

### In `.env` file:

```env
WEBAPP_DEBUG_SKIP_AUTH=true
WEBAPP_DEBUG_USER_ID=5912983856
```

**⚠️ IMPORTANT**: Never enable this in production! It bypasses all security checks.

### How Debug Mode Works

When `WEBAPP_DEBUG_SKIP_AUTH=true`:
- Authentication checks are bypassed
- A debug user is automatically created/used
- Warning is logged for every request
- User ID is taken from `WEBAPP_DEBUG_USER_ID` setting

## API Response Codes

- **200**: Success (user authenticated)
- **401**: Unauthorized (invalid/missing initData)
- **403**: Forbidden (user not admin for admin-only endpoints)

## Error Messages

All error messages are in Russian to match the application's locale:

- `"Требуется аутентификация Telegram Web App"` - Missing initData
- `"Отсутствует параметр hash в initData"` - Missing hash
- `"Неверная подпись HMAC - данные не прошли проверку"` - Invalid signature
- `"initData устарел (более 24 часов)"` - Expired data
- `"Требуются права администратора"` - Not an admin

## Testing

### Unit Tests

Located in `tests/test_webapp_auth.py`:

```bash
python -m pytest tests/test_webapp_auth.py -v
```

Or run standalone tests:

```bash
python tests/standalone_test_auth.py
```

### Manual Testing

1. **Enable debug mode** in `.env`:
   ```env
   WEBAPP_DEBUG_SKIP_AUTH=true
   ```

2. **Test endpoints**:
   ```bash
   curl http://localhost:8000/webapp/me
   curl http://localhost:8000/webapp/admin/test
   ```

3. **Disable debug mode** and test with real initData:
   ```bash
   curl -H "X-Telegram-Init-Data: query_id=..." http://localhost:8000/webapp/me
   ```

## Implementation Details

### Dependencies

The auth system integrates with:
- **FastAPI**: For dependency injection
- **SQLAlchemy**: For database sessions
- **UserService**: For user management
- **Logger**: For Russian-language logging

### Database Integration

Uses FastAPI's dependency injection:

```python
async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

### User Creation/Update

Respects existing user fields:
- Language is updated from initData
- Username and first_name are updated
- Citizenship and other fields are preserved
- last_active timestamp is updated

## Security Best Practices

1. **Never expose bot token** in client-side code
2. **Always use HTTPS** in production
3. **Disable debug mode** in production
4. **Set short CORS origins** list
5. **Monitor auth failures** in logs
6. **Rotate bot token** if compromised

## Logging

All authentication events are logged with Russian messages and icons:

- ✅ `Успешная аутентификация пользователя: {id}`
- ❌ `Ошибка аутентификации Telegram: {error}`
- ⚠️ `Попытка доступа к админским функциям от пользователя {id}`
- ⚠️ `ВНИМАНИЕ: Используется отладочный режим без проверки аутентификации!`

## References

- [Telegram Web Apps Documentation](https://core.telegram.org/bots/webapps)
- [Validating Data Received via Mini App](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
