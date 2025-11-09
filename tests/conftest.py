"""
Pytest fixtures and utilities for Web App tests
Shared test configuration and helper functions
"""

import asyncio
import hashlib
import hmac
import json
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, AsyncGenerator
from urllib.parse import urlencode

import pytest
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import init_db, AsyncSessionLocal
from models import (
    WebAppCategory, 
    WebAppCategoryItem, 
    WebAppFile,
    User
)
from services.user_service import UserService
from utils.logger import logger


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean database session for each test"""
    await init_db()
    
    async with AsyncSessionLocal() as session:
        yield session
        
        # Cleanup after test
        await session.rollback()


@pytest.fixture
async def clean_webapp_tables(db_session: AsyncSession):
    """Clean Web App tables before and after test"""
    # Cleanup before test
    await db_session.execute(delete(WebAppCategoryItem))
    await db_session.execute(delete(WebAppCategory))
    await db_session.execute(delete(WebAppFile))
    await db_session.commit()
    
    yield
    
    # Cleanup after test
    await db_session.execute(delete(WebAppCategoryItem))
    await db_session.execute(delete(WebAppCategory))
    await db_session.execute(delete(WebAppFile))
    await db_session.commit()


@pytest.fixture
def temp_upload_dir():
    """Create temporary directory for file upload tests"""
    temp_dir = Path(tempfile.mkdtemp(prefix="webapp_test_uploads_"))
    logger.info(f"Создан временный каталог для загрузок: {temp_dir}")
    
    yield temp_dir
    
    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
        logger.info(f"Удалён временный каталог: {temp_dir}")


@pytest.fixture
def regular_user_data() -> Dict:
    """Regular test user data"""
    return {
        "id": 12345,
        "first_name": "Test User",
        "username": "testuser",
        "language_code": "ru",
    }


@pytest.fixture
def admin_user_data() -> Dict:
    """Admin test user data"""
    return {
        "id": 67890,
        "first_name": "Admin User",
        "username": "adminuser",
        "language_code": "ru",
    }


@pytest.fixture
async def regular_user(db_session: AsyncSession, regular_user_data: Dict) -> User:
    """Create regular test user"""
    user = await UserService.create_or_update_user(
        session=db_session,
        telegram_id=regular_user_data["id"],
        username=regular_user_data["username"],
        first_name=regular_user_data["first_name"],
        language="RU"
    )
    return user


@pytest.fixture
async def admin_user(db_session: AsyncSession, admin_user_data: Dict) -> User:
    """Create admin test user"""
    user = await UserService.create_or_update_user(
        session=db_session,
        telegram_id=admin_user_data["id"],
        username=admin_user_data["username"],
        first_name=admin_user_data["first_name"],
        language="RU"
    )
    # Make user admin
    user.is_admin = True
    await db_session.commit()
    await db_session.refresh(user)
    return user


def generate_init_data(bot_token: str, user_data: Dict) -> str:
    """
    Generate signed initData string for Telegram Web App authentication testing
    
    Args:
        bot_token: Bot token to sign the data
        user_data: User data dictionary with id, first_name, etc.
    
    Returns:
        URL-encoded initData string with valid hash
    """
    auth_date = int(datetime.now().timestamp())
    encoded_user = json.dumps(user_data, separators=(",", ":"))

    data_payload = {
        "auth_date": str(auth_date),
        "query_id": "TEST_QUERY_ID",
        "user": encoded_user,
    }

    # Create check string (sorted key=value pairs)
    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(data_payload.items())
    )

    # Generate secret key
    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    # Generate hash
    data_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # Add hash to payload
    signed_payload = {
        **data_payload,
        "hash": data_hash,
    }

    return urlencode(signed_payload)


@pytest.fixture
def regular_init_data(regular_user_data: Dict) -> str:
    """Generate initData for regular user"""
    return generate_init_data(settings.user_bot_token, regular_user_data)


@pytest.fixture
def admin_init_data(admin_user_data: Dict) -> str:
    """Generate initData for admin user"""
    return generate_init_data(settings.user_bot_token, admin_user_data)


@pytest.fixture
async def sample_category(db_session: AsyncSession, admin_user: User) -> WebAppCategory:
    """Create a sample category for testing"""
    from services.webapp_content_service import WebAppContentService
    
    category = await WebAppContentService.create_category(
        session=db_session,
        slug="test-category",
        title="Тестовая категория",
        description="Категория для тестирования",
        order_index=1
    )
    return category


@pytest.fixture
async def sample_category_with_items(
    db_session: AsyncSession, 
    sample_category: WebAppCategory
) -> WebAppCategory:
    """Create a category with sample items"""
    from services.webapp_content_service import WebAppContentService
    from models import WebAppCategoryItemType
    
    # Add text item
    await WebAppContentService.add_item(
        session=db_session,
        category_id=sample_category.id,
        item_type=WebAppCategoryItemType.TEXT,
        text_content="Тестовый текст",
        order_index=1
    )
    
    # Add image item with file
    file_record = await WebAppContentService.create_file(
        session=db_session,
        file_type="IMAGE",
        telegram_file_id="test_file_id_123",
        mime_type="image/jpeg",
        file_size=1024
    )
    
    await WebAppContentService.add_item(
        session=db_session,
        category_id=sample_category.id,
        item_type=WebAppCategoryItemType.IMAGE,
        text_content="Тестовое изображение",
        file_id=file_record.id,
        order_index=2
    )
    
    # Refresh category to get items
    await db_session.refresh(sample_category)
    return sample_category


# Helper assertions for common test scenarios
def assert_category_valid(category: WebAppCategory):
    """Assert that a category has valid required fields"""
    assert category.id is not None
    assert category.slug is not None and len(category.slug) > 0
    assert category.title is not None and len(category.title) > 0
    assert category.order_index >= 0


def assert_item_valid(item: WebAppCategoryItem):
    """Assert that a category item has valid required fields"""
    assert item.id is not None
    assert item.category_id is not None
    assert item.type is not None
    assert item.order_index >= 0


def assert_file_valid(file: WebAppFile):
    """Assert that a file record has valid required fields"""
    assert file.id is not None
    assert file.file_type is not None
    assert file.telegram_file_id or file.storage_path  # At least one should exist
