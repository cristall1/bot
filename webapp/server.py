from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable, Awaitable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from config import settings
from utils.logger import logger
from webapp.routes import router as webapp_router
from webapp.routes.categories import router as categories_router
from webapp.routes.admin import router as admin_router

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        logger.info(f"HTTP запрос: {request.method} {request.url.path}")
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                f"Ошибка обработки HTTP запроса {request.method} {request.url.path}: {exc}"
            )
            raise
        logger.info(
            f"HTTP ответ: {response.status_code} {request.url.path}"
        )
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Запуск веб-приложения...")
    try:
        yield
    finally:
        logger.info("Остановка веб-приложения...")


def create_app() -> FastAPI:
    app = FastAPI(title="Al-Azhar & Dirassa WebApp", lifespan=lifespan)

    app.add_middleware(RequestLoggingMiddleware)

    if settings.webapp_cors_origins_list:
        logger.info("Включаем CORS для веб-приложения")
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.webapp_cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(webapp_router)
    app.include_router(categories_router)
    app.include_router(admin_router)

    if STATIC_DIR.exists():
        app.mount("/webapp/static", StaticFiles(directory=str(STATIC_DIR)), name="webapp_static")
        logger.info("Статические файлы веб-приложения подключены")

    if TEMPLATES_DIR.exists():
        app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
        logger.info("Шаблоны веб-приложения настроены")

    return app
