from functools import lru_cache
from pathlib import Path
from typing import Optional

from config import settings

PROJECT_ROOT = Path(__file__).resolve().parent.parent
UPLOAD_URL_PREFIX = "webapp/uploads"


@lru_cache(maxsize=1)
def get_upload_directory() -> Path:
    """Return absolute directory path for stored uploads, ensuring it exists."""
    raw_path = Path(settings.webapp_upload_dir)
    if raw_path.is_absolute():
        upload_dir = raw_path
    else:
        upload_dir = (PROJECT_ROOT / raw_path).resolve()

    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def build_storage_path(filename: str) -> str:
    """Return storage path to persist in DB relative to public mount."""
    sanitized = filename.lstrip("/\\")
    return f"{UPLOAD_URL_PREFIX}/{sanitized}"


def resolve_physical_path(storage_path: Optional[str]) -> Optional[Path]:
    """Map stored relative path back to an absolute filesystem path."""
    if not storage_path:
        return None

    normalized = storage_path.lstrip("/\\")
    prefix = f"{UPLOAD_URL_PREFIX}/"

    if normalized.startswith(prefix):
        relative = normalized[len(prefix):]
        return get_upload_directory() / relative

    return None


def get_upload_url_prefix() -> str:
    """Return the base URL prefix for uploaded files."""
    return UPLOAD_URL_PREFIX
