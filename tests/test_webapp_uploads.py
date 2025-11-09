"""
Integration tests for Web App file upload functionality
Tests upload, retrieval, and deletion of files (admin-only)
"""

import asyncio
import hashlib
import hmac
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from PIL import Image
from sqlalchemy import delete

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import settings
from database import init_db, AsyncSessionLocal
from models import WebAppCategoryItem, WebAppFile
from services.user_service import UserService
from services.webapp_content_service import WebAppContentService
from utils.logger import logger
from webapp.storage import get_upload_directory


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
    from models import WebAppCategory
    
    await session.execute(delete(WebAppCategoryItem))
    await session.execute(delete(WebAppCategory))
    await session.execute(delete(WebAppFile))
    await session.commit()
    
    upload_dir = get_upload_directory()
    for file in upload_dir.glob("*"):
        if file.is_file():
            try:
                file.unlink()
            except Exception as e:
                logger.warning(f"Could not delete test file {file}: {e}")


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


def create_test_image(width: int = 100, height: int = 100) -> io.BytesIO:
    """Create a test image in memory"""
    img = Image.new('RGB', (width, height), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


def create_test_pdf() -> io.BytesIO:
    """Create a minimal test PDF"""
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
>>
>>
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 24 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000317 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
410
%%EOF
"""
    return io.BytesIO(pdf_content)


async def test_upload_image_as_admin():
    """Test uploading image as admin"""
    logger.info("=== Test: Upload image as admin ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        test_image = create_test_image(200, 150)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/webapp/upload",
                headers={"X-Telegram-Init-Data": init_data},
                files={"file": ("test_image.png", test_image, "image/png")},
                data={"description": "Test image", "tag": "test"}
            )
        
        assert response.status_code == 200
        file_data = response.json()
        
        assert "id" in file_data
        assert file_data["file_type"] == "IMAGE"
        assert file_data["mime_type"] == "image/png"
        assert file_data["original_name"] == "test_image.png"
        assert file_data["description"] == "Test image"
        assert file_data["tag"] == "test"
        assert file_data["width"] == 200
        assert file_data["height"] == 150
        assert "file_url" in file_data
        assert file_data["file_url"].startswith(settings.webapp_public_url)
        
        file_record = await WebAppContentService.get_file(session, file_data["id"])
        assert file_record is not None
        assert file_record.file_type == "IMAGE"
        assert file_record.storage_path is not None
        
        logger.info("✅ Test passed: Upload image as admin")


async def test_upload_pdf_as_admin():
    """Test uploading PDF as admin"""
    logger.info("=== Test: Upload PDF as admin ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        test_pdf = create_test_pdf()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/webapp/upload",
                headers={"X-Telegram-Init-Data": init_data},
                files={"file": ("test_document.pdf", test_pdf, "application/pdf")},
                data={"description": "Test PDF document"}
            )
        
        assert response.status_code == 200
        file_data = response.json()
        
        assert file_data["file_type"] == "DOCUMENT"
        assert file_data["mime_type"] == "application/pdf"
        assert file_data["original_name"] == "test_document.pdf"
        assert file_data["description"] == "Test PDF document"
        assert file_data["width"] is None
        assert file_data["height"] is None
        
        logger.info("✅ Test passed: Upload PDF as admin")


async def test_upload_403_non_admin():
    """Test non-admin cannot upload files"""
    logger.info("=== Test: Non-admin cannot upload files (403) ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["regular_user"])
        
        test_image = create_test_image()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/webapp/upload",
                headers={"X-Telegram-Init-Data": init_data},
                files={"file": ("test_image.png", test_image, "image/png")}
            )
        
        assert response.status_code == 403
        
        logger.info("✅ Test passed: Non-admin gets 403 for upload")


async def test_upload_invalid_file_type():
    """Test uploading invalid file type returns 400"""
    logger.info("=== Test: Upload invalid file type (400) ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        invalid_file = io.BytesIO(b"Invalid content")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/webapp/upload",
                headers={"X-Telegram-Init-Data": init_data},
                files={"file": ("test.exe", invalid_file, "application/x-msdownload")}
            )
        
        assert response.status_code == 400
        assert "Неподдерживаемый" in response.json()["detail"]
        
        logger.info("✅ Test passed: Invalid file type returns 400")


async def test_delete_file():
    """Test deleting uploaded file"""
    logger.info("=== Test: Delete uploaded file ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        test_image = create_test_image()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            upload_response = await client.post(
                "/webapp/upload",
                headers={"X-Telegram-Init-Data": init_data},
                files={"file": ("test_image.png", test_image, "image/png")}
            )
            
            assert upload_response.status_code == 200
            file_data = upload_response.json()
            file_id = file_data["id"]
            
            file_record = await WebAppContentService.get_file(session, file_id)
            assert file_record is not None
            
            delete_response = await client.delete(
                f"/webapp/file/{file_id}",
                headers={"X-Telegram-Init-Data": init_data}
            )
            
            assert delete_response.status_code == 200
            result = delete_response.json()
            assert result["success"] is True
            
            file_record = await WebAppContentService.get_file(session, file_id)
            assert file_record is None
        
        logger.info("✅ Test passed: Delete uploaded file")


async def test_file_physically_stored():
    """Test that uploaded file is physically stored on disk"""
    logger.info("=== Test: File physically stored on disk ===")
    
    await init_db()
    
    async with AsyncSessionLocal() as session:
        await cleanup_test_data(session)
        users = await setup_test_users(session)
        
        from httpx import AsyncClient
        from webapp.server import create_app
        
        app = create_app()
        init_data = generate_init_data(settings.user_bot_token, users["admin_user"])
        
        test_image = create_test_image()
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/webapp/upload",
                headers={"X-Telegram-Init-Data": init_data},
                files={"file": ("test_image.png", test_image, "image/png")}
            )
        
        assert response.status_code == 200
        file_data = response.json()
        
        file_record = await WebAppContentService.get_file(session, file_data["id"])
        assert file_record is not None
        
        from webapp.storage import resolve_physical_path
        physical_path = resolve_physical_path(file_record.storage_path)
        assert physical_path is not None
        assert physical_path.exists()
        assert physical_path.is_file()
        
        logger.info("✅ Test passed: File physically stored on disk")


async def main():
    """Run all tests"""
    tests = [
        test_upload_image_as_admin,
        test_upload_pdf_as_admin,
        test_upload_403_non_admin,
        test_upload_invalid_file_type,
        test_delete_file,
        test_file_physically_stored,
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            logger.error(f"Test {test.__name__} failed: {str(e)}", exc_info=True)
            raise
    
    logger.info("✅ All upload tests passed!")


if __name__ == "__main__":
    asyncio.run(main())
