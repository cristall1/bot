# Tests

This directory contains tests for the application.

## Web App Schema Tests

### `test_webapp_schema.py`

Tests the Web App content management system, including:

- **Models**: `WebAppCategory`, `WebAppCategoryItem`, `WebAppFile`
- **Service**: `WebAppContentService`

#### What it tests:
1. Category creation and retrieval
2. Item creation (TEXT, IMAGE, BUTTON types)
3. File record management
4. Navigation between categories
5. Item reordering
6. Eager loading (no N+1 queries)
7. Service methods (CRUD operations)

#### Running the tests:

```bash
# Run the test directly
python tests/test_webapp_schema.py

# Or with pytest (if installed)
pytest tests/test_webapp_schema.py -v
```

#### Expected behavior:
- All tests should pass with Russian success messages in logs
- No lazy-loading warnings
- Database tables created automatically
- Example category seeded on first run of main.py
