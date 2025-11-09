# Web App Schema Implementation

## Overview

This document describes the implementation of the Web App content management system, including database models, services, and tests.

## Database Schema

### Models Added

#### 1. `WebAppFile`
Stores metadata for files uploaded for Web App content.

**Table**: `webapp_files`

**Fields**:
- `id`: Integer, Primary Key
- `telegram_file_id`: String(500), Optional - Telegram file_id if uploaded via bot
- `storage_path`: String(500), Optional - Local storage path
- `file_type`: String(50), Required - Type of file (IMAGE, DOCUMENT, VIDEO, AUDIO)
- `mime_type`: String(100), Optional - MIME type
- `file_size`: Integer, Optional - Size in bytes
- `uploaded_by`: Integer, Optional FK to `users.id`
- `created_at`: DateTime, Auto-set to UTC now

**Relationships**:
- `uploader`: User who uploaded the file
- `category_items`: Items that reference this file
- `categories_as_cover`: Categories using this file as cover

#### 2. `WebAppCategory`
Hierarchical categories for organizing Web App content.

**Table**: `webapp_categories`

**Fields**:
- `id`: Integer, Primary Key
- `slug`: String(100), Unique, Indexed - URL-friendly identifier
- `title`: String(255), Required - Display title
- `description`: Text, Optional - Category description
- `order_index`: Integer, Indexed, Default 0 - For ordering
- `is_active`: Boolean, Indexed, Default True - Visibility flag
- `cover_file_id`: Integer, Optional FK to `webapp_files.id`
- `created_at`: DateTime, Auto-set
- `updated_at`: DateTime, Auto-updated

**Relationships**:
- `items`: List of content items (eager-loaded, ordered by order_index)
- `cover_file`: Optional cover image/file
- `targeted_items`: Items that navigate to this category

**Indexes**:
- `slug` (unique)
- `order_index`
- `is_active`

#### 3. `WebAppCategoryItem`
Individual content items within categories.

**Table**: `webapp_category_items`

**Fields**:
- `id`: Integer, Primary Key
- `category_id`: Integer, Indexed, Required FK to `webapp_categories.id`
- `type`: String(20), Required - Type of item (TEXT, IMAGE, DOCUMENT, LINK, VIDEO, BUTTON)
- `text_content`: Text, Optional - Textual content or caption
- `rich_metadata`: JSON, Optional - Rich metadata for complex items
- `file_id`: Integer, Optional FK to `webapp_files.id`
- `button_text`: String(255), Optional - For BUTTON type
- `target_category_id`: Integer, Optional FK to `webapp_categories.id` - Navigation target
- `order_index`: Integer, Indexed, Default 0 - Display order
- `is_active`: Boolean, Indexed, Default True - Visibility flag
- `created_at`: DateTime, Auto-set
- `updated_at`: DateTime, Auto-updated

**Relationships**:
- `category`: Parent category
- `file`: Referenced file (if any)
- `target_category`: Target category for navigation (if BUTTON type)

**Indexes**:
- `category_id`
- `order_index`
- `is_active`

#### 4. `WebAppCategoryItemType` (Enum)
Python enum defining allowed item types:
- TEXT
- IMAGE
- DOCUMENT
- LINK
- VIDEO
- BUTTON

## Service Layer

### `WebAppContentService`

Located in: `services/webapp_content_service.py`

#### Category Operations

**`list_categories(session, include_inactive=False)`**
- Returns all categories with preloaded items
- Ordered by `order_index`
- Optionally includes inactive categories
- Uses eager loading to avoid N+1 queries

**`get_category(session, category_id, include_inactive=False)`**
- Fetches single category by ID
- Preloads items and cover file
- Supports filtering by active status

**`get_category_by_slug(session, slug, include_inactive=False)`**
- Fetches category by slug
- Same eager loading as `get_category`

**`create_category(...)`**
- Creates new category
- Logs success/errors in Russian
- Returns created category with ID

**`update_category(session, category_id, **kwargs)`**
- Updates category fields
- Only updates provided fields
- Logs operation

**`delete_category(session, category_id)`**
- Hard deletes category
- Cascade deletes associated items
- Returns boolean success

#### Item Operations

**`add_item(session, category_id, item_type, ...)`**
- Adds content item to category
- Validates item type against enum
- Supports all item types with appropriate fields
- Logs operation in Russian

**`update_item(session, item_id, ...)`**
- Updates item fields
- Type-safe item type validation
- Returns updated item

**`delete_item(session, item_id)`**
- Hard deletes item
- Returns boolean success

**`reorder_items(session, item_order)`**
- Bulk reorders items
- Accepts list of `{id, order_index}` dicts
- Atomic operation

#### File Operations

**`create_file(...)`**
- Creates file metadata record
- Stores either `telegram_file_id` or `storage_path`
- Tracks uploader and file properties

**`get_file(session, file_id)`**
- Retrieves file metadata

**`resolve_file_url(file)`**
- Static utility to get usable URL from file record
- Prefers `telegram_file_id` over `storage_path`

### Logging Convention

All service methods log in Russian with status icons:
- ✅ Success operations
- ❌ Errors with full traceback
- ⚠️ Warnings

Example:
```
[create_category] ✅ Успех | Категория Web App создана: 1 - Добро пожаловать
```

## Eager Loading Strategy

All relationships use `lazy="selectin"` to prevent N+1 query problems:
- Relationships load efficiently in batch
- No lazy-loading warnings
- Optimal for API serialization

The `items` relationship is additionally ordered:
```python
order_by="WebAppCategoryItem.order_index"
```

## Data Seeding

### Location: `main.py` - `seed_initial_data()`

When the database is empty, the system seeds an example category:

**Category**: "welcome"
- **Title**: "Добро пожаловать"
- **Description**: "Вводная категория с информацией о боте"
- **Item**: Single TEXT item with welcome message

This ensures:
1. UI has data to render during development
2. Example structure for developers
3. No disruption to existing seed flow

## Tests

### Location: `tests/test_webapp_schema.py`

Comprehensive integration test covering:

1. **Database initialization** - Tables created via `init_db()`
2. **Category CRUD** - Create, read, update, delete
3. **Item CRUD** - All item types (TEXT, IMAGE, BUTTON)
4. **File management** - Create and reference files
5. **Navigation** - Button items linking to categories
6. **Ordering** - Reorder items and verify
7. **Eager loading** - No lazy-loading warnings
8. **Service layer** - All public methods tested

### Running Tests

```bash
# Direct execution
python tests/test_webapp_schema.py

# With pytest (if installed)
pytest tests/test_webapp_schema.py -v
```

### Expected Output

All tests log Russian success messages and verify:
- Tables are created
- CRUD operations work
- Relationships load correctly
- No database warnings

## Integration Points

### With Existing Code

1. **Models**: Added to `models.py` alongside existing models
2. **Main**: Imported in `main.py` for table registration
3. **Seeding**: Integrated into existing `seed_initial_data()`
4. **Logging**: Uses existing `utils.logger` with Russian messages
5. **Database**: Automatically picked up by `init_db()`

### No Conflicts

- New table names don't conflict with existing tables
- Relationships follow existing patterns
- Conventions match (timestamps, indexes, naming)
- Soft deletion uses `is_active` flag consistently

## Future Enhancements

Potential additions (not in current scope):

1. **Soft delete**: Add `deleted_at` column for recovery
2. **Versioning**: Track content changes
3. **Localization**: Multi-language support in items
4. **Analytics**: Track item views/interactions
5. **Media processing**: Thumbnail generation, compression
6. **Access control**: Permission-based visibility

## API Example Usage

```python
from database import AsyncSessionLocal
from services.webapp_content_service import WebAppContentService
from models import WebAppCategoryItemType

async def example():
    async with AsyncSessionLocal() as session:
        # Create category
        category = await WebAppContentService.create_category(
            session=session,
            slug="announcements",
            title="Объявления",
            description="Важные объявления"
        )
        
        # Add text item
        await WebAppContentService.add_item(
            session=session,
            category_id=category.id,
            item_type=WebAppCategoryItemType.TEXT,
            text_content="Важное объявление!"
        )
        
        # List all categories with items
        categories = await WebAppContentService.list_categories(session)
        for cat in categories:
            print(f"{cat.title}: {len(cat.items)} items")
```

## Summary

This implementation provides:
- ✅ Three new database models with proper relationships
- ✅ Comprehensive service layer with CRUD operations
- ✅ Eager loading to prevent N+1 queries
- ✅ Russian logging following project conventions
- ✅ Integration with existing seed flow
- ✅ Full test coverage
- ✅ Type safety with enum for item types
- ✅ Documentation for future developers

All acceptance criteria met:
- Fresh database creates three new tables
- Service methods return ordered data without lazy-loading warnings
- Russian success messages in logs
- Existing models and seeds unaffected
