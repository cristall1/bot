"""
Integration tests for Web App Admin API
Tests CRUD operations for categories and items (admin-only)
"""

import asyncio
import hashlib
import hmac
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from sqlalchemy import delete, select

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from database import init_db, AsyncSessionLocal
from models import WebAppCategoryItem, WebAppCategoryItemType
from services.user_service import UserService
from services.webapp_content_service import WebAppContentService
from utils.logger import logger


def generate_init_data(bot_token: str, user_data: dict) -> str:
    """Generate signed initData string for testing"""
    auth_date = int(datetime.now().timestamp())
    encoded_user = json.dumps(user_data, separators=(",", ":"))

    data_payload = {
        "auth_date": str(auth_date),
        "query_id": "TEST_QUERY_ID",
        "user": encoded_user,
    }

    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data_payload.items()))

    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    data_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    signed_payload = {
        **data_payload,
        "hash": data_hash,
    }

    return urlencode(signed_payload)


async def cleanup_test_data(session):
    """Clean up test data from previous runs"""
    from models import WebAppCategory, WebAppFile
    
    await session.execute(delete(WebAppCategoryItem))
    await session.execute(delete(WebAppCategory))
    await session.execute(delete(WebAppFile))
    await session.commit()


async def setup_test_users(session):
    """Set up test users"""
    regular_user_data = {
        "id": 12345,
        "first_name": "Test User",
        "username": "testuser",
        "language_code": "ru",
    }
    regular_user = await UserService.create_or_update_user(
        session=session,
        telegram_id=regular_user_data["id"],
        username=regular_user_data["username"],
        first_name=regular_user_data["first_name"],
        language="RU"
    )
    
    admin_user_data = {
        "id": 67890,
        "first_name": "Admin User",
        "username": "adminuser",
        "language_code": "ru",
    }
    admin_user = await UserService.create_or_update_user(
        session=session,
        telegram_id=admin_user_data["id"],
        username=admin_user_data["username"],
        first_name=admin_user_data["first_name"],
        language="RU"
    )
    admin_user.is_admin = True
    await session.commit()
    
    return {
        "regular_user": regular_user_data,
        "admin_user": admin_user_data,
    }


async def test_create_category_as_admin():
    """Test creating category as admin"""
    logger.info("=== Test: Create category as admin ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/webapp/category",
                json={
                    "slug": "test-category",
                    "title": "Test Category",
                    "description": "Test description",
                    "is_active": True
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        category = response.json()
        
        assert category["slug"] == "test-category"
        assert category["title"] == "Test Category"
        assert category["description"] == "Test description"
        assert category["is_active"] is True
        assert "id" in category
        assert category["order_index"] == 0  # Auto-assigned
        
        logger.info("✅ Test passed: Create category as admin")


async def test_create_category_403_non_admin():
    """Test non-admin cannot create category"""
    logger.info("=== Test: Non-admin cannot create category (403) ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["regular_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/webapp/category",
                json={
                    "slug": "test-category",
                    "title": "Test Category",
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 403
        
        logger.info("✅ Test passed: Non-admin gets 403 for create category")


async def test_update_category():
    """Test updating category"""
    logger.info("=== Test: Update category ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category first
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Original Title",
            description="Original description",
            order_index=1,
            is_active=True
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                f"/webapp/category/{category.id}",
                json={
                    "title": "Updated Title",
                    "description": "Updated description",
                    "is_active": False
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        updated_category = response.json()
        
        assert updated_category["id"] == category.id
        assert updated_category["title"] == "Updated Title"
        assert updated_category["description"] == "Updated description"
        assert updated_category["is_active"] is False
        assert updated_category["slug"] == "test-category"  # Unchanged
        
        logger.info("✅ Test passed: Update category")


async def test_update_category_with_items_order():
    """Test updating category with items_order reorders items"""
    logger.info("=== Test: Update category with items_order ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create category and items
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        item_a = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Item A",
            order_index=0
        )
        item_b = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Item B",
            order_index=1
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                f"/webapp/category/{category.id}",
                json={
                    "items_order": [item_b.id, item_a.id]
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        category_response = response.json()
        items = category_response["items"]
        assert len(items) == 2
        assert items[0]["id"] == item_b.id
        assert items[0]["order_index"] == 0
        assert items[1]["id"] == item_a.id
        assert items[1]["order_index"] == 1
        
        # Verify in database
        updated_category = await WebAppContentService.get_category(
            session=session,
            category_id=category.id,
            include_inactive=True
        )
        db_items = sorted(updated_category.items, key=lambda x: x.order_index)
        assert db_items[0].id == item_b.id
        assert db_items[0].order_index == 0
        assert db_items[1].id == item_a.id
        assert db_items[1].order_index == 1
        
        logger.info("✅ Test passed: Update category with items_order")


async def test_delete_category_soft():
    """Test soft deleting category"""
    logger.info("=== Test: Soft delete category ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category",
            is_active=True
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        # Soft delete (default)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(
                f"/webapp/category/{category.id}",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["deleted"] is False  # Soft delete
        
        # Verify category still exists but is inactive
        cat = await WebAppContentService.get_category(session, category.id, include_inactive=True)
        assert cat is not None
        assert cat.is_active is False
        
        logger.info("✅ Test passed: Soft delete category")


async def test_delete_category_hard():
    """Test hard deleting category"""
    logger.info("=== Test: Hard delete category ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category",
            is_active=True
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        # Hard delete
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(
                f"/webapp/category/{category.id}?hard_delete=true",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["deleted"] is True  # Hard delete
        
        # Verify category no longer exists
        cat = await WebAppContentService.get_category(session, category.id, include_inactive=True)
        assert cat is None
        
        logger.info("✅ Test passed: Hard delete category")


async def test_create_item():
    """Test creating item in category"""
    logger.info("=== Test: Create item in category ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/webapp/category/{category.id}/items",
                json={
                    "type": "TEXT",
                    "text_content": "Test text item",
                    "is_active": True
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        item = response.json()
        
        assert item["type"] == "TEXT"
        assert item["text_content"] == "Test text item"
        assert item["is_active"] is True
        assert "id" in item
        assert item["order_index"] == 0  # Auto-assigned
        
        logger.info("✅ Test passed: Create item in category")


async def test_create_item_403_non_admin():
    """Test non-admin cannot create item"""
    logger.info("=== Test: Non-admin cannot create item (403) ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["regular_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/webapp/category/{category.id}/items",
                json={
                    "type": "TEXT",
                    "text_content": "Test text item"
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 403
        
        logger.info("✅ Test passed: Non-admin cannot create item")


async def test_create_button_item_validation():
    """Test button item requires button_text and target_category_id"""
    logger.info("=== Test: Button item validation ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create categories
        category1 = await WebAppContentService.create_category(
            session=session,
            slug="category-1",
            title="Category 1"
        )
        
        category2 = await WebAppContentService.create_category(
            session=session,
            slug="category-2",
            title="Category 2"
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        # Try to create button without button_text - should fail
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/webapp/category/{category1.id}/items",
                json={
                    "type": "BUTTON",
                    "target_category_id": category2.id,
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 422  # Validation error
        
        # Try to create button without target_category_id - should fail
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/webapp/category/{category1.id}/items",
                json={
                    "type": "BUTTON",
                    "button_text": "Click me",
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 422  # Validation error
        
        # Create button with all required fields - should succeed
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/webapp/category/{category1.id}/items",
                json={
                    "type": "BUTTON",
                    "button_text": "Click me",
                    "target_category_id": category2.id,
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        item = response.json()
        assert item["type"] == "BUTTON"
        assert item["button_text"] == "Click me"
        assert item["target_category_id"] == category2.id
        
        logger.info("✅ Test passed: Button item validation")


async def test_update_item():
    """Test updating item"""
    logger.info("=== Test: Update item ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category and item
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        
        item = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Original text",
            is_active=True
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.put(
                f"/webapp/category/{category.id}/items/{item.id}",
                json={
                    "text_content": "Updated text",
                    "is_active": False
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        updated_item = response.json()
        
        assert updated_item["id"] == item.id
        assert updated_item["text_content"] == "Updated text"
        assert updated_item["is_active"] is False
        assert updated_item["type"] == "TEXT"  # Unchanged
        
        logger.info("✅ Test passed: Update item")


async def test_update_item_to_button_requires_fields():
    """Test updating item to button requires specific fields"""
    logger.info("=== Test: Update item to button validation ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create categories and a text item
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        target_category = await WebAppContentService.create_category(
            session=session,
            slug="target-category",
            title="Target Category"
        )
        
        item = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Original text",
            is_active=True
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Try to update to BUTTON without button_text
            response = await client.put(
                f"/webapp/category/{category.id}/items/{item.id}",
                json={
                    "type": "BUTTON",
                    "target_category_id": target_category.id
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 400
        error = response.json()
        assert "кнопки" in error["detail"]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Update with all required fields
            response = await client.put(
                f"/webapp/category/{category.id}/items/{item.id}",
                json={
                    "type": "BUTTON",
                    "button_text": "Перейти",
                    "target_category_id": target_category.id
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["type"] == "BUTTON"
        assert updated_item["button_text"] == "Перейти"
        assert updated_item["target_category_id"] == target_category.id
        
        logger.info("✅ Test passed: Update item to button validation")


async def test_delete_item_soft():
    """Test soft deleting item"""
    logger.info("=== Test: Soft delete item ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category and item
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        
        item = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Test text",
            is_active=True
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        # Soft delete (default)
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.delete(
                f"/webapp/category/{category.id}/items/{item.id}",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        assert result["deleted"] is False  # Soft delete
        
        # Verify item still exists but is inactive
        result = await session.execute(
            select(WebAppCategoryItem).where(WebAppCategoryItem.id == item.id)
        )
        updated_item = result.scalar_one_or_none()
        assert updated_item is not None
        assert updated_item.is_active is False
        
        logger.info("✅ Test passed: Soft delete item")


async def test_reorder_items():
    """Test reordering items"""
    logger.info("=== Test: Reorder items ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category and items
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        
        item1 = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Item 1",
            order_index=0
        )
        
        item2 = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Item 2",
            order_index=1
        )
        
        item3 = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Item 3",
            order_index=2
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        # Reorder: item3, item1, item2
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/webapp/category/{category.id}/items/reorder",
                json={
                    "item_ids": [item3.id, item1.id, item2.id]
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 3
        
        # Verify new order in response
        assert items[0]["id"] == item3.id
        assert items[0]["order_index"] == 0
        assert items[1]["id"] == item1.id
        assert items[1]["order_index"] == 1
        assert items[2]["id"] == item2.id
        assert items[2]["order_index"] == 2
        
        # Verify new order in database
        updated_category = await WebAppContentService.get_category(
            session, category.id, include_inactive=True
        )
        db_items = sorted(updated_category.items, key=lambda x: x.order_index)
        
        assert db_items[0].id == item3.id
        assert db_items[0].order_index == 0
        assert db_items[1].id == item1.id
        assert db_items[1].order_index == 1
        assert db_items[2].id == item2.id
        assert db_items[2].order_index == 2
        
        logger.info("✅ Test passed: Reorder items")


async def test_invalid_file_id():
    """Test validation of file_id"""
    logger.info("=== Test: Invalid file_id validation ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        # Create a category
        category = await WebAppContentService.create_category(
            session=session,
            slug="test-category",
            title="Test Category"
        )
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        # Try to create item with non-existent file_id
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                f"/webapp/category/{category.id}/items",
                json={
                    "type": "IMAGE",
                    "text_content": "Test image",
                    "file_id": 99999  # Non-existent
                },
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 400
        error = response.json()
        assert "не существует" in error["detail"]
        
        logger.info("✅ Test passed: Invalid file_id validation")


async def run_all_tests():
    """Run all integration tests"""
    logger.info("=== Starting Web App Admin API Tests ===")
    
    try:
        await test_create_category_as_admin()
        await test_create_category_403_non_admin()
        await test_update_category()
        await test_update_category_with_items_order()
        await test_delete_category_soft()
        await test_delete_category_hard()
        await test_create_item()
        await test_create_item_403_non_admin()
        await test_create_button_item_validation()
        await test_update_item()
        await test_update_item_to_button_requires_fields()
        await test_delete_item_soft()
        await test_reorder_items()
        await test_invalid_file_id()
        
        logger.info("=== ✅ All Web App Admin API tests passed! ===")
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
        raise


def test_webapp_admin():
    """Entry point for pytest"""
    asyncio.run(run_all_tests())


if __name__ == "__main__":
    asyncio.run(run_all_tests())
