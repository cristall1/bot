"""
Integration tests combining admin and user flows for the Web App API.
"""

from pathlib import Path

import pytest
from httpx import AsyncClient

from config import settings
from webapp.server import create_app


@pytest.mark.asyncio
async def test_admin_creates_content_and_user_reads(
    clean_webapp_tables,
    admin_user,
    regular_user,
    admin_init_data,
    regular_init_data,
    temp_upload_dir,
    monkeypatch
):
    """Full scenario: admin prepares content, user consumes it."""
    # Ensure uploads are isolated per test
    monkeypatch.setattr(settings, "webapp_upload_dir", str(temp_upload_dir))

    app = create_app()

    admin_headers = {"X-Telegram-Init-Data": admin_init_data}
    user_headers = {"X-Telegram-Init-Data": regular_init_data}

    async with AsyncClient(app=app, base_url="http://test") as client:
        # Admin creates a category
        category_payload = {
            "slug": "integration-category",
            "title": "Интеграционный сценарий",
            "description": "Категория для энд-ту-энд теста",
            "order_index": 5
        }
        response = await client.post(
            "/webapp/category",
            json=category_payload,
            headers=admin_headers
        )
        assert response.status_code == 200
        category = response.json()
        category_id = category["id"]

        # Admin uploads an image file (stored locally in temporary directory)
        file_bytes = b"fake-image-data"
        response = await client.post(
            "/webapp/upload",
            headers=admin_headers,
            files={
                "file": ("integration.png", file_bytes, "image/png")
            },
            data={
                "description": "Интеграционный файл"
            }
        )
        assert response.status_code == 200
        upload_result = response.json()
        file_id = upload_result["id"]
        assert upload_result["original_name"] == "integration.png"
        stored_filename = Path(upload_result["file_url"]).name
        assert stored_filename.endswith(".png")
        stored_path = Path(settings.webapp_upload_dir) / stored_filename
        assert stored_path.exists()

        # Admin adds TEXT item
        response = await client.post(
            f"/webapp/category/{category_id}/items",
            headers=admin_headers,
            json={
                "type": "TEXT",
                "text_content": "Первый компонент",
                "order_index": 0
            }
        )
        assert response.status_code == 200
        text_item = response.json()

        # Admin adds IMAGE item referencing uploaded file
        response = await client.post(
            f"/webapp/category/{category_id}/items",
            headers=admin_headers,
            json={
                "type": "IMAGE",
                "text_content": "Второй компонент",
                "file_id": file_id,
                "order_index": 1
            }
        )
        assert response.status_code == 200
        image_item = response.json()

        # User lists categories (category should be visible)
        response = await client.get("/webapp/categories", headers=user_headers)
        assert response.status_code == 200
        categories = response.json()
        assert any(c["id"] == category_id for c in categories)

        # User requests category details and sees ordered items
        response = await client.get(f"/webapp/category/{category_id}", headers=user_headers)
        assert response.status_code == 200
        details = response.json()
        assert [item["id"] for item in details["items"]] == [text_item["id"], image_item["id"]]

        # Admin reorders items (swap positions)
        response = await client.post(
            f"/webapp/category/{category_id}/items/reorder",
            headers=admin_headers,
            json={"item_ids": [image_item["id"], text_item["id"]]}
        )
        assert response.status_code == 200
        reordered_items = response.json()
        assert [item["id"] for item in reordered_items] == [image_item["id"], text_item["id"]]

        # User sees new order immediately
        response = await client.get(f"/webapp/category/{category_id}", headers=user_headers)
        assert response.status_code == 200
        details = response.json()
        assert [item["id"] for item in details["items"]] == [image_item["id"], text_item["id"]]

        # Admin deactivates category
        response = await client.put(
            f"/webapp/category/{category_id}",
            headers=admin_headers,
            json={"is_active": False}
        )
        assert response.status_code == 200
        assert response.json()["is_active"] is False

        # Regular user no longer sees category
        response = await client.get("/webapp/categories", headers=user_headers)
        assert response.status_code == 200
        categories = response.json()
        assert all(c["id"] != category_id for c in categories)

        # Admin can still fetch inactive category with include_inactive flag
        response = await client.get(
            "/webapp/categories?include_inactive=true",
            headers=admin_headers
        )
        data = response.json()
        hidden_category = next((c for c in data if c["id"] == category_id), None)
        assert hidden_category is not None
        assert hidden_category["is_active"] is False

    # Uploaded file still on disk for further deletion test (handled in dedicated upload tests)
