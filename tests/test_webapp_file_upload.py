"""
Tests for Web App file upload endpoints ensuring files are stored and cleaned up properly.
"""

from pathlib import Path

import pytest
from httpx import AsyncClient

from config import settings
from services.webapp_content_service import WebAppContentService
from webapp.server import create_app


@pytest.mark.asyncio
async def test_upload_and_delete_file(
    clean_webapp_tables,
    admin_user,
    admin_init_data,
    temp_upload_dir,
    monkeypatch,
    db_session
):
    """Upload a file via API and ensure physical cleanup happens on delete."""
    monkeypatch.setattr(settings, "webapp_upload_dir", str(temp_upload_dir))

    app = create_app()
    headers = {"X-Telegram-Init-Data": admin_init_data}

    async with AsyncClient(app=app, base_url="http://test") as client:
        file_bytes = b"example-document"
        response = await client.post(
            "/webapp/upload",
            headers=headers,
            files={
                "file": ("document.pdf", file_bytes, "application/pdf")
            },
            data={"tag": "integration"}
        )
        assert response.status_code == 200
        data = response.json()
        file_id = data["id"]
        file_url = data["file_url"]
        stored_filename = Path(file_url).name
        physical_path = Path(settings.webapp_upload_dir) / stored_filename
        assert physical_path.exists(), "Физический файл должен существовать после загрузки"

        # Delete via API
        response = await client.delete(f"/webapp/file/{file_id}", headers=headers)
        assert response.status_code == 200
        assert not physical_path.exists(), "Физический файл должен удаляться"

        # Database record should be removed
        deleted_record = await WebAppContentService.get_file(db_session, file_id)
        assert deleted_record is None, "Запись о файле должна быть удалена из БД"


@pytest.mark.asyncio
async def test_upload_rejects_large_file(
    clean_webapp_tables,
    admin_user,
    admin_init_data,
    temp_upload_dir,
    monkeypatch
):
    """Large files beyond limit should be rejected with 400."""
    monkeypatch.setattr(settings, "webapp_upload_dir", str(temp_upload_dir))
    monkeypatch.setattr(settings, "webapp_max_upload_size", 10)

    app = create_app()
    headers = {"X-Telegram-Init-Data": admin_init_data}

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Create payload larger than limit (11 bytes)
        response = await client.post(
            "/webapp/upload",
            headers=headers,
            files={
                "file": ("large.bin", b"01234567890", "application/octet-stream")
            }
        )
        assert response.status_code == 400
        assert "слишком большой" in response.json()["detail"]
