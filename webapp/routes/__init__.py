from fastapi import APIRouter, Depends

from models import User
from webapp.auth import get_current_user, require_admin_user

router = APIRouter(prefix="/webapp", tags=["webapp"])


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    """Простая проверка доступности веб-приложения."""
    return {"status": "ok"}


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)) -> dict:
    """Получить информацию о текущем пользователе."""
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "language": user.language,
        "is_admin": user.is_admin,
        "is_courier": user.is_courier
    }


@router.get("/admin/test")
async def admin_test(user: User = Depends(require_admin_user)) -> dict:
    """Тестовый endpoint для администраторов."""
    return {
        "message": "Доступ разрешен",
        "admin_id": user.telegram_id,
        "admin_username": user.username
    }
