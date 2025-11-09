# Tests

This directory contains automated tests for the application, with a focus on Web App functionality.

## Test Files

### `conftest.py`
Pytest configuration and shared fixtures:
- Event loop setup for async tests
- Database session fixtures with automatic cleanup
- User fixtures (regular and admin users)
- Telegram initData generation utilities
- Temporary upload directory fixture
- Helper assertion functions

### `test_webapp_schema.py`
Legacy schema tests - basic validation of Web App models and service methods.

**Coverage:**
- Category creation and retrieval
- Item creation (TEXT, IMAGE, BUTTON types)
- File record management
- Navigation between categories
- Item reordering
- Eager loading (no N+1 queries)

**Running:**
```bash
python tests/test_webapp_schema.py
# or
pytest tests/test_webapp_schema.py -v
```

### `test_webapp_auth.py`
Tests Web App authentication and authorization flows.

**Coverage:**
- Telegram initData signature validation
- Admin vs. regular user permissions
- Authentication header parsing
- 401/403 error handling

**Running:**
```bash
pytest tests/test_webapp_auth.py -v
```

### `test_webapp_categories.py`
Integration tests for category and item API endpoints (user perspective).

**Coverage:**
- GET `/webapp/categories` - list all categories
- GET `/webapp/category/{id}` - category details with items
- Active/inactive filtering
- Order preservation
- File URL resolution

**Running:**
```bash
pytest tests/test_webapp_categories.py -v
```

### `test_webapp_admin.py`
Integration tests for admin CRUD operations.

**Coverage:**
- POST `/webapp/category` - create category
- PUT `/webapp/category/{id}` - update category
- DELETE `/webapp/category/{id}` - soft/hard delete
- POST `/webapp/categories/reorder` - reorder categories
- POST `/webapp/category/{id}/items` - add items
- PUT `/webapp/category/{id}/items/{item_id}` - update item
- DELETE `/webapp/category/{id}/items/{item_id}` - delete item
- POST `/webapp/category/{id}/items/reorder` - reorder items

**Running:**
```bash
pytest tests/test_webapp_admin.py -v
```

### `test_webapp_uploads.py`
File upload handling tests (existing implementation).

**Coverage:**
- File upload validation (MIME type, extension)
- Image dimension extraction
- Storage path handling
- File size limits

**Running:**
```bash
pytest tests/test_webapp_uploads.py -v
```

### `test_webapp_service.py` ⭐ NEW
Service-layer tests for `WebAppContentService` using direct database sessions.

**Coverage:**
- Category CRUD operations
- Item ordering and reordering
- File record creation and URL resolution
- Active/inactive filtering
- Item type validation and normalization

**Running:**
```bash
pytest tests/test_webapp_service.py -v
```

### `test_webapp_integration.py` ⭐ NEW
End-to-end integration tests simulating real user + admin workflows.

**Coverage:**
- Complete scenario: admin creates content → user views it
- File upload with temporary directories
- Active/inactive toggling and visibility
- Item reordering with user verification
- Physical file cleanup

**Running:**
```bash
pytest tests/test_webapp_integration.py -v
```

### `test_webapp_file_upload.py` ⭐ NEW
File upload endpoint tests with cleanup verification.

**Coverage:**
- File upload via `/webapp/upload`
- Physical file storage in temporary directories
- File deletion cleanup (DB + disk)
- File size limit enforcement

**Running:**
```bash
pytest tests/test_webapp_file_upload.py -v
```

## Running All Tests

```bash
# All tests
pytest

# All Web App tests
pytest tests/test_webapp_*.py -v

# With coverage
pytest --cov=webapp --cov=services.webapp_content_service tests/test_webapp_*.py

# Specific test
pytest tests/test_webapp_integration.py::test_admin_creates_content_and_user_reads -v

# With detailed output
pytest -vvs
```

## Fixtures Usage

Common fixtures available from `conftest.py`:

- `db_session` - Clean async database session
- `clean_webapp_tables` - Cleanup Web App tables before/after test
- `temp_upload_dir` - Temporary directory for file uploads
- `regular_user`, `admin_user` - Test user instances
- `regular_init_data`, `admin_init_data` - Signed Telegram initData
- `regular_user_data`, `admin_user_data` - User data dicts
- `sample_category` - Pre-created category
- `sample_category_with_items` - Category with sample items

## Expected Behavior

- All tests should pass with Russian success messages in logs
- No lazy-loading warnings
- Database tables created automatically
- Temporary upload directories cleaned up after tests
- Authentication properly validated via Telegram initData signatures

## Manual QA

For manual regression testing, follow the checklist in:
- `WEBAPP_USER_UI_QA_CHECKLIST.md` - User interface testing
- Front-end integration testing

## CI/CD

Tests are designed to run in CI environments. To integrate:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --junitxml=junit.xml --cov=webapp --cov=services.webapp_content_service
```
