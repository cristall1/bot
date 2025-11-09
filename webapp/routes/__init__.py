from fastapi import APIRouter, Depends, Request, HTTPException
from starlette.responses import HTMLResponse

from config import settings
from models import User
from webapp.auth import get_current_user, require_admin_user

router = APIRouter(prefix="/webapp", tags=["webapp"])


@router.get("/", response_class=HTMLResponse)
async def index(request: Request, mode: str = "user") -> HTMLResponse:
    """Главная страница Telegram Web App."""
    if not hasattr(request.app.state, 'templates'):
        raise HTTPException(status_code=500, detail="Шаблоны не настроены")
    
    templates = request.app.state.templates
    normalized_mode = mode if mode in {"user", "admin"} else "user"

    api_base = settings.webapp_public_url.rstrip('/')
    config = {
        'apiBaseUrl': api_base,
        'version': settings.webapp_version,
        'mode': normalized_mode
    }
    
    return templates.TemplateResponse('index.html', {
        'request': request,
        'version': settings.webapp_version,
        'mode': normalized_mode,
        'config': config
    })


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
