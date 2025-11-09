from fastapi import APIRouter

router = APIRouter(prefix="/webapp", tags=["webapp"])


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    """Простая проверка доступности веб-приложения."""
    return {"status": "ok"}
