"""
Integration tests for Web App Categories API
Tests read endpoints for categories and category details
"""

import asyncio
import hashlib
import hmac
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from sqlalchemy import delete

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from database import init_db, AsyncSessionLocal
from models import WebAppCategory, WebAppCategoryItem, WebAppCategoryItemType, WebAppFile
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
    await session.execute(delete(WebAppCategoryItem))
    await session.execute(delete(WebAppCategory))
    await session.execute(delete(WebAppFile))
    await session.commit()


async def setup_test_data(session):
    """Set up test categories and items"""
    
    # Clean up first
    await cleanup_test_data(session)
    
    # Create test users
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
    
    # Create test categories
    category1 = await WebAppContentService.create_category(
        session=session,
        slug="test-category-1",
        title="Test Category 1",
        description="First test category",
        order_index=1,
        is_active=True
    )
    
    category2 = await WebAppContentService.create_category(
        session=session,
        slug="test-category-2",
        title="Test Category 2",
        description="Second test category",
        order_index=2,
        is_active=True
    )
    
    inactive_category = await WebAppContentService.create_category(
        session=session,
        slug="test-inactive-category",
        title="Inactive Category",
        description="This category is inactive",
        order_index=3,
        is_active=False
    )
    
    # Add items to category 1
    text_item = await WebAppContentService.add_item(
        session=session,
        category_id=category1.id,
        item_type=WebAppCategoryItemType.TEXT,
        text_content="This is a test text item",
        order_index=1,
        is_active=True
    )
    
    # Create a file and add image item
    file_record = await WebAppContentService.create_file(
        session=session,
        file_type="IMAGE",
        telegram_file_id="test_file_12345",
        mime_type="image/jpeg",
        file_size=102400
    )
    
    image_item = await WebAppContentService.add_item(
        session=session,
        category_id=category1.id,
        item_type=WebAppCategoryItemType.IMAGE,
        text_content="Test image caption",
        file_id=file_record.id,
        order_index=2,
        is_active=True
    )
    
    # Add button item linking to category2
    button_item = await WebAppContentService.add_item(
        session=session,
        category_id=category1.id,
        item_type=WebAppCategoryItemType.BUTTON,
        button_text="Go to Category 2",
        target_category_id=category2.id,
        order_index=3,
        is_active=True
    )
    
    # Add inactive item to category 1
    inactive_item = await WebAppContentService.add_item(
        session=session,
        category_id=category1.id,
        item_type=WebAppCategoryItemType.TEXT,
        text_content="This item is inactive",
        order_index=4,
        is_active=False
    )
    
    return {
        "regular_user": regular_user_data,
        "admin_user": admin_user_data,
        "category1": category1,
        "category2": category2,
        "inactive_category": inactive_category,
        "items": {
            "text": text_item,
            "image": image_item,
            "button": button_item,
            "inactive": inactive_item
        }
    }


async def test_list_categories_authenticated():
    """Test listing categories as authenticated user"""
    logger.info("=== Test: List categories as authenticated user ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        test_data = await setup_test_data(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, test_data["regular_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/webapp/categories",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        categories = response.json()
        
        # Should only return active categories
        assert len(categories) == 2
        assert all(cat["slug"] in ["test-category-1", "test-category-2"] for cat in categories)
        
        # Check ordering
        assert categories[0]["order_index"] <= categories[1]["order_index"]
        
        # Check fields
        cat1 = next(cat for cat in categories if cat["slug"] == "test-category-1")
        assert "id" in cat1
        assert "title" in cat1
        assert "description" in cat1
        assert "order_index" in cat1
        assert "items_count" in cat1
        assert cat1["items_count"] == 3  # Only active items count
        
        logger.info("✅ Test passed: List categories as authenticated user")


async def test_get_category_detail_authenticated():
    """Test getting category details as authenticated user"""
    logger.info("=== Test: Get category details as authenticated user ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        test_data = await setup_test_data(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, test_data["regular_user"])
        
        category_id = test_data["category1"].id
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/webapp/category/{category_id}",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        category = response.json()
        
        # Check basic fields
        assert category["id"] == category_id
        assert category["slug"] == "test-category-1"
        assert category["title"] == "Test Category 1"
        
        # Check items - should only include active items
        assert len(category["items"]) == 3
        assert all(item["is_active"] for item in category["items"])
        
        # Check ordering
        order_indices = [item["order_index"] for item in category["items"]]
        assert order_indices == sorted(order_indices)
        
        # Verify item types
        item_types = {item["type"] for item in category["items"]}
        assert "TEXT" in item_types
        assert "IMAGE" in item_types
        assert "BUTTON" in item_types
        
        # Verify file URL in image item
        image_item = next(item for item in category["items"] if item["type"] == "IMAGE")
        assert image_item["file"] is not None
        assert "file_url" in image_item["file"]
        assert image_item["file"]["file_url"] == "test_file_12345"
        
        # Verify button target
        button_item = next(item for item in category["items"] if item["type"] == "BUTTON")
        assert button_item["target_category_id"] == test_data["category2"].id
        assert button_item["button_text"] == "Go to Category 2"
        
        logger.info("✅ Test passed: Get category details as authenticated user")


async def test_get_category_not_found():
    """Test getting non-existent category returns 404"""
    logger.info("=== Test: Get non-existent category returns 404 ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        test_data = await setup_test_data(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, test_data["regular_user"])
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/webapp/category/99999",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 404
        
        logger.info("✅ Test passed: Get non-existent category returns 404")


async def test_list_categories_admin_with_inactive():
    """Test admin can list inactive categories"""
    logger.info("=== Test: Admin can list inactive categories ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        test_data = await setup_test_data(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, test_data["admin_user"])
        
        # Without include_inactive flag
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/webapp/categories",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) == 2  # Only active
        
        # With include_inactive flag
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/webapp/categories?include_inactive=true",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) == 3  # All categories including inactive
        
        slugs = {cat["slug"] for cat in categories}
        assert "test-inactive-category" in slugs
        
        logger.info("✅ Test passed: Admin can list inactive categories")


async def test_get_category_admin_with_inactive_items():
    """Test admin can get category with inactive items"""
    logger.info("=== Test: Admin can get category with inactive items ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        test_data = await setup_test_data(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, test_data["admin_user"])
        
        category_id = test_data["category1"].id
        
        # With include_inactive flag
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/webapp/category/{category_id}?include_inactive=true",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        category = response.json()
        
        # Should include inactive items
        assert len(category["items"]) == 4
        
        # Check that inactive item is present
        inactive_item = next((item for item in category["items"] if not item["is_active"]), None)
        assert inactive_item is not None
        assert inactive_item["text_content"] == "This item is inactive"
        
        logger.info("✅ Test passed: Admin can get category with inactive items")


async def test_regular_user_cannot_see_inactive():
    """Test regular user cannot see inactive categories/items even with flag"""
    logger.info("=== Test: Regular user cannot see inactive with flag ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        test_data = await setup_test_data(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, test_data["regular_user"])
        
        # Try to list with include_inactive flag
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                "/webapp/categories?include_inactive=true",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        categories = response.json()
        assert len(categories) == 2  # Still only active categories
        
        # Try to get category with inactive items
        category_id = test_data["category1"].id
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                f"/webapp/category/{category_id}?include_inactive=true",
                headers={"X-Telegram-Init-Data": init_data}
            )
        
        assert response.status_code == 200
        category = response.json()
        assert len(category["items"]) == 3  # Still only active items
        
        logger.info("✅ Test passed: Regular user cannot see inactive with flag")


async def test_unauthenticated_access_denied():
    """Test unauthenticated requests are denied"""
    logger.info("=== Test: Unauthenticated access denied ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        test_data = await setup_test_data(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        
        # Try to list categories without auth
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/webapp/categories")
        
        # Should require authentication
        assert response.status_code == 401
        
        logger.info("✅ Test passed: Unauthenticated access denied")


async def run_all_tests():
    """Run all integration tests"""
    logger.info("=== Starting Web App Categories API Tests ===")
    
    try:
        await test_list_categories_authenticated()
        await test_get_category_detail_authenticated()
        await test_get_category_not_found()
        await test_list_categories_admin_with_inactive()
        await test_get_category_admin_with_inactive_items()
        await test_regular_user_cannot_see_inactive()
        await test_unauthenticated_access_denied()
        
        logger.info("=== ✅ All Web App Categories API tests passed! ===")
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}", exc_info=True)
        raise


def test_webapp_categories():
    """Entry point for pytest"""
    asyncio.run(run_all_tests())


if __name__ == "__main__":
    asyncio.run(run_all_tests())
