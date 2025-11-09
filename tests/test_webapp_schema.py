"""
Тесты для Web App схемы и сервисов
Tests for Web App schema and services
"""

import asyncio
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database import init_db, AsyncSessionLocal
from models import WebAppCategoryItemType
from services.webapp_content_service import WebAppContentService
from utils.logger import logger


async def run_webapp_schema_scenario():
    """Asynchronous test scenario for Web App schema and service"""
    logger.info("=== Начало тестирования Web App схемы ===")

    # Ensure database tables are created
    await init_db()
    logger.info("✅ База данных инициализирована")

    async with AsyncSessionLocal() as session:
        # Create a unique slug to avoid collisions
        slug_base = "test-category"
        slug = slug_base
        counter = 1
        while True:
            existing = await WebAppContentService.get_category_by_slug(
                session=session,
                slug=slug,
                include_inactive=True
            )
            if not existing:
                break
            counter += 1
            slug = f"{slug_base}-{counter}"

        # 1. Create a category
        category = await WebAppContentService.create_category(
            session=session,
            slug=slug,
            title="Тестовая категория",
            description="Это тестовая категория для проверки функциональности",
            order_index=1
        )
        assert category.id is not None
        assert category.slug == slug

        # 2. List categories and ensure the new category is present
        categories = await WebAppContentService.list_categories(session)
        assert any(cat.id == category.id for cat in categories)

        # 3. Add a text item to the category
        text_item = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Это тестовый текстовый элемент",
            order_index=1
        )
        assert text_item.id is not None
        assert text_item.type == WebAppCategoryItemType.TEXT.value

        # 4. Fetch the category with items and ensure eager loading works
        loaded_category = await WebAppContentService.get_category(session=session, category_id=category.id)
        assert loaded_category is not None
        assert len(loaded_category.items) >= 1
        assert loaded_category.items[0].order_index == 1

        # 5. Create a file record
        file_record = await WebAppContentService.create_file(
            session=session,
            file_type="IMAGE",
            telegram_file_id="test_file_id_12345",
            mime_type="image/jpeg",
            file_size=1024000
        )
        assert file_record.id is not None

        # 6. Add an image item referencing the file
        image_item = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.IMAGE,
            text_content="Описание изображения",
            file_id=file_record.id,
            order_index=2
        )
        assert image_item.file_id == file_record.id

        # 7. Create target category for navigation
        nav_category = await WebAppContentService.create_category(
            session=session,
            slug=f"navigation-target-{category.id}",
            title="Целевая категория",
            description="Категория для проверки навигации",
            order_index=2
        )
        assert nav_category.id is not None

        # 8. Add button item linking to target category
        button_item = await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.BUTTON,
            button_text="Перейти к категории",
            target_category_id=nav_category.id,
            order_index=3
        )
        assert button_item.target_category_id == nav_category.id

        # 9. Update category title
        updated_category = await WebAppContentService.update_category(
            session=session,
            category_id=category.id,
            title="Обновлённая тестовая категория"
        )
        assert updated_category.title == "Обновлённая тестовая категория"

        # 10. Reorder items
        item_order = [
            {"id": button_item.id, "order_index": 1},
            {"id": image_item.id, "order_index": 2},
            {"id": text_item.id, "order_index": 3}
        ]
        reorder_result = await WebAppContentService.reorder_items(session=session, item_order=item_order)
        assert reorder_result is True

        # 11. Verify item order is updated and eager-loaded
        ordered_category = await WebAppContentService.get_category(session=session, category_id=category.id)
        assert [item.order_index for item in ordered_category.items] == [1, 2, 3]
        assert ordered_category.items[0].id == button_item.id

        # 12. Ensure resolver works for file URLs
        resolved_url = await WebAppContentService.resolve_file_url(file_record)
        assert resolved_url == "test_file_id_12345"

        # 13. Fetch category by slug and ensure retrieval works
        slug_lookup = await WebAppContentService.get_category_by_slug(session=session, slug=category.slug)
        assert slug_lookup is not None
        assert slug_lookup.id == category.id

    logger.info("=== ✅ Все тесты Web App схемы пройдены успешно! ===")


def test_webapp_schema():
    """Entry point for pytest"""
    asyncio.run(run_webapp_schema_scenario())
