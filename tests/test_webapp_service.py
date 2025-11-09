"""
Service-layer tests for WebAppContentService
Tests CRUD operations and ordering logic using async database sessions
"""

import pytest

from models import WebAppCategoryItemType
from services.webapp_content_service import WebAppContentService
from utils.logger import logger


@pytest.mark.asyncio
async def test_category_crud_operations(db_session, clean_webapp_tables):
    """Test basic category CRUD operations"""
    logger.info("=== Тест: CRUD операции для категорий ===")

    # Create category
    category = await WebAppContentService.create_category(
        session=db_session,
        slug="test-crud-category",
        title="CRUD Test Category",
        description="Testing create/read/update/delete",
        order_index=10
    )
    assert category.id is not None
    assert category.slug == "test-crud-category"
    assert category.order_index == 10
    logger.info(f"✅ Категория создана: {category.id}")

    # Read by ID
    retrieved = await WebAppContentService.get_category(db_session, category.id)
    assert retrieved is not None
    assert retrieved.id == category.id
    logger.info("✅ Категория прочитана по ID")

    # Read by slug
    by_slug = await WebAppContentService.get_category_by_slug(db_session, "test-crud-category")
    assert by_slug is not None
    assert by_slug.id == category.id
    logger.info("✅ Категория прочитана по slug")

    # Update
    updated = await WebAppContentService.update_category(
        session=db_session,
        category_id=category.id,
        title="Updated Title",
        order_index=20
    )
    assert updated.title == "Updated Title"
    assert updated.order_index == 20
    logger.info("✅ Категория обновлена")

    # Delete
    success = await WebAppContentService.delete_category(db_session, category.id)
    assert success is True
    logger.info("✅ Категория удалена")

    # Verify deletion
    deleted_cat = await WebAppContentService.get_category(
        db_session, category.id, include_inactive=True
    )
    assert deleted_cat is None
    logger.info("✅ Категория не найдена после удаления")

    logger.info("=== ✅ Тест CRUD категорий завершён ===")


@pytest.mark.asyncio
async def test_item_ordering_and_reordering(db_session, clean_webapp_tables):
    """Test item ordering and reordering within a category"""
    logger.info("=== Тест: упорядочивание элементов ===")

    # Create category
    category = await WebAppContentService.create_category(
        session=db_session,
        slug="ordering-test",
        title="Ordering Test",
        order_index=1
    )

    # Add items in specific order
    item_a = await WebAppContentService.add_item(
        session=db_session,
        category_id=category.id,
        item_type=WebAppCategoryItemType.TEXT,
        text_content="Item A",
        order_index=0
    )
    item_b = await WebAppContentService.add_item(
        session=db_session,
        category_id=category.id,
        item_type=WebAppCategoryItemType.TEXT,
        text_content="Item B",
        order_index=1
    )
    item_c = await WebAppContentService.add_item(
        session=db_session,
        category_id=category.id,
        item_type=WebAppCategoryItemType.TEXT,
        text_content="Item C",
        order_index=2
    )
    logger.info(f"✅ Добавлено 3 элемента: {item_a.id}, {item_b.id}, {item_c.id}")

    # Verify initial order
    category_with_items = await WebAppContentService.get_category(db_session, category.id)
    items = sorted(category_with_items.items, key=lambda x: x.order_index)
    assert [i.id for i in items] == [item_a.id, item_b.id, item_c.id]
    logger.info("✅ Изначальный порядок верен")

    # Reorder items (C, A, B)
    new_order = [
        {"id": item_c.id, "order_index": 0},
        {"id": item_a.id, "order_index": 1},
        {"id": item_b.id, "order_index": 2}
    ]
    await WebAppContentService.reorder_items(db_session, new_order)
    logger.info("✅ Элементы переупорядочены")

    # Verify new order
    reloaded_category = await WebAppContentService.get_category(db_session, category.id)
    items = sorted(reloaded_category.items, key=lambda x: x.order_index)
    assert [i.id for i in items] == [item_c.id, item_a.id, item_b.id]
    logger.info("✅ Новый порядок применён")

    logger.info("=== ✅ Тест упорядочивания элементов завершён ===")


@pytest.mark.asyncio
async def test_file_record_creation_and_resolution(db_session, clean_webapp_tables):
    """Test creating file records and resolving URLs"""
    logger.info("=== Тест: создание файлов и разрешение URL ===")

    # Create file with telegram_file_id
    telegram_file = await WebAppContentService.create_file(
        session=db_session,
        file_type="IMAGE",
        telegram_file_id="AgACAgIAAxkBAAIF3",
        mime_type="image/jpeg",
        file_size=4096
    )
    assert telegram_file.id is not None
    assert telegram_file.telegram_file_id == "AgACAgIAAxkBAAIF3"
    logger.info(f"✅ Файл с telegram_file_id создан: {telegram_file.id}")

    # Resolve URL (should return telegram_file_id)
    resolved = await WebAppContentService.resolve_file_url(telegram_file)
    assert resolved == "AgACAgIAAxkBAAIF3"
    logger.info("✅ URL разрешён на telegram_file_id")

    # Create file with storage_path
    local_file = await WebAppContentService.create_file(
        session=db_session,
        file_type="DOCUMENT",
        storage_path="webapp/uploads/document.pdf",
        mime_type="application/pdf",
        file_size=8192
    )
    assert local_file.id is not None
    assert local_file.storage_path == "webapp/uploads/document.pdf"
    logger.info(f"✅ Файл с storage_path создан: {local_file.id}")

    # Resolve URL (should return storage_path)
    resolved = await WebAppContentService.resolve_file_url(local_file)
    assert resolved == "webapp/uploads/document.pdf"
    logger.info("✅ URL разрешён на storage_path")

    logger.info("=== ✅ Тест файлов завершён ===")


@pytest.mark.asyncio
async def test_active_inactive_filtering(db_session, clean_webapp_tables):
    """Test filtering of active/inactive categories and items"""
    logger.info("=== Тест: фильтрация активных/неактивных элементов ===")

    # Create two categories: one active, one inactive
    active_cat = await WebAppContentService.create_category(
        session=db_session,
        slug="active-category",
        title="Active Category",
        is_active=True
    )
    inactive_cat = await WebAppContentService.create_category(
        session=db_session,
        slug="inactive-category",
        title="Inactive Category",
        is_active=False
    )
    logger.info(f"✅ Созданы активная ({active_cat.id}) и неактивная ({inactive_cat.id}) категории")

    # List categories without include_inactive (should only see active)
    categories = await WebAppContentService.list_categories(
        session=db_session,
        include_inactive=False
    )
    assert len([c for c in categories if c.id == active_cat.id]) == 1
    assert len([c for c in categories if c.id == inactive_cat.id]) == 0
    logger.info("✅ Неактивная категория скрыта при include_inactive=False")

    # List categories with include_inactive (should see both)
    all_categories = await WebAppContentService.list_categories(
        session=db_session,
        include_inactive=True
    )
    assert len([c for c in all_categories if c.id == active_cat.id]) == 1
    assert len([c for c in all_categories if c.id == inactive_cat.id]) == 1
    logger.info("✅ Неактивная категория видна при include_inactive=True")

    # Get inactive category with include_inactive=False (should return None)
    not_found = await WebAppContentService.get_category(
        session=db_session,
        category_id=inactive_cat.id,
        include_inactive=False
    )
    assert not_found is None
    logger.info("✅ Неактивная категория не возвращается без include_inactive=True")

    # Get inactive category with include_inactive=True (should return it)
    found = await WebAppContentService.get_category(
        session=db_session,
        category_id=inactive_cat.id,
        include_inactive=True
    )
    assert found is not None
    assert found.id == inactive_cat.id
    logger.info("✅ Неактивная категория возвращается с include_inactive=True")

    logger.info("=== ✅ Тест фильтрации завершён ===")


@pytest.mark.asyncio
async def test_item_type_validation(db_session, clean_webapp_tables):
    """Test item type validation and normalization"""
    logger.info("=== Тест: валидация типов элементов ===")

    category = await WebAppContentService.create_category(
        session=db_session,
        slug="type-test",
        title="Type Test"
    )

    # Test with enum
    item1 = await WebAppContentService.add_item(
        session=db_session,
        category_id=category.id,
        item_type=WebAppCategoryItemType.TEXT,
        text_content="Using enum"
    )
    assert item1.type == "TEXT"
    logger.info("✅ Enum тип принят")

    # Test with uppercase string
    item2 = await WebAppContentService.add_item(
        session=db_session,
        category_id=category.id,
        item_type="IMAGE",
        text_content="Using string"
    )
    assert item2.type == "IMAGE"
    logger.info("✅ Строковый тип принят")

    # Test with lowercase string (should be normalized)
    item3 = await WebAppContentService.add_item(
        session=db_session,
        category_id=category.id,
        item_type="video",
        text_content="Lowercase string"
    )
    assert item3.type == "VIDEO"
    logger.info("✅ Строчный тип нормализован")

    # Test invalid type (should raise)
    try:
        await WebAppContentService.add_item(
            session=db_session,
            category_id=category.id,
            item_type="INVALID_TYPE",
            text_content="Invalid"
        )
        assert False, "Должно быть исключение для недопустимого типа"
    except ValueError as e:
        assert "Недопустимый тип элемента" in str(e)
        logger.info("✅ Недопустимый тип отклонён")

    logger.info("=== ✅ Тест валидации типов завершён ===")
