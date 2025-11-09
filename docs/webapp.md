# Web App Architecture and Developer Guide

## Overview

The Al-Azhar & Dirassa Web App extends the dual Telegram bot ecosystem with a rich client web interface powered by FastAPI for the backend and a vanilla JavaScript admin interface for content management.

This document summarizes the backend architecture, key modules, and best practices for extending the Web App while following project conventions (including Russian logging messages and async service designs).

---

## Backend Architecture

### Entry Point & Application Factory

- `webapp/server.py` exposes `create_app()` which builds the FastAPI instance.
- Custom `RequestLoggingMiddleware` logs each request/response pair in Russian with success (`✅`) or error (`❌`) formatting through `utils.logger`.
- Static assets (`/webapp/static`) and uploaded files (`/webapp/uploads`) are mounted as separate Starlette static files apps during startup.

### Authentication Flow

- Authentication is performed via Telegram Web App `initData` signatures.
- `webapp/auth.py` contains:
  - `verify_telegram_init_data()` for signature validation using the user bot token.
  - Dependencies `get_current_user` (regular authenticated user) and `require_admin_user` (admin-only).
- Test fixtures in `tests/conftest.py` generate signed init data to simulate Telegram web app launches.
- During development you can enable `WEBAPP_DEBUG_SKIP_AUTH=True` and set `WEBAPP_DEBUG_USER_ID` for bypassing signature validation; production deployments **must keep this disabled**.

### Routing Modules

- `webapp/routes/__init__.py` registers shared routes (health, `/webapp/me`).
- `webapp/routes/categories.py` provides read-only category and item endpoints authenticated as general users.
  - Responses are serialized using helper Pydantic models (`WebAppCategoryOut`, `WebAppCategoryItemOut`).
  - File URLs are normalized to `settings.webapp_public_url` and respect Telegram-hosted file IDs.
- `webapp/routes/admin.py` contains CRUD endpoints restricted to admins for managing categories, items, ordering, and file records.

### Service Layer

- `services/webapp_content_service.py` orchestrates operations on `WebAppCategory`, `WebAppCategoryItem`, and `WebAppFile` models.
- All service methods expect an `AsyncSession` and rely on eager loading via `selectinload` to avoid lazy-loading in async contexts.
- Item types are validated against the `WebAppCategoryItemType` enum; `WebAppContentService.ALLOWED_ITEM_TYPES` centralizes permitted values.

### Database & Models

- SQLAlchemy models are defined in `models.py` and use the shared `database.py` async engine.
- The service layer ensures transactions are committed or rolled back with clear logging.
- Relationships:
  - `WebAppCategory` → `items` (one-to-many) ordered by `order_index`.
  - `WebAppCategory` → `cover_file` (optional `WebAppFile`).
  - `WebAppCategoryItem` → `file` (optional `WebAppFile`).

### File Storage

- `webapp/storage.py` resolves paths relative to `settings.webapp_upload_dir` (defaults to `webapp/uploads`).
- Files can be stored via Telegram (`telegram_file_id`) or locally (`storage_path`).
- `WebAppContentService.delete_file()` removes both DB record and physical files using async-compatible `Path.unlink` inside `asyncio.to_thread()`.
- Tests use the `temp_upload_dir` fixture to isolate and clean up temporary directories.

---

## Front-End Structure

- Located under `webapp/static/` with modular ES6 JavaScript:
  - `static/js/admin.js` drives the admin editor UI.
  - `static/js/api.js` wraps fetch calls to backend endpoints.
- Templates under `webapp/templates/` are rendered client-side; the admin toolbar toggles edit/preview modes.
- Styling lives in `static/css/admin.css` and respects dark mode with class toggles.

---

## Testing Strategy

### Fixtures (`tests/conftest.py`)

- Provides event loop, async database sessions, and cleanup utilities.
- Fixtures create regular and admin users, signed `initData`, and temporary upload directories.
- Helper assertions verify category/item/file integrity.

### Integration Tests

- `tests/test_webapp_integration.py` covers end-to-end admin + user flows using `httpx.AsyncClient` against `create_app()`.
- Verifies:
  - Admin creates categories and items.
  - User fetches categories/items respecting active flags.
  - Ordering and filtering behave as expected.

### Service Tests

- `tests/test_webapp_service.py` exercises `WebAppContentService` CRUD operations and ordering logic directly with `AsyncSession` fixtures.

### File Upload Tests

- `tests/test_webapp_file_upload.py` validates file record creation, local storage handling, and cleanup inside temporary directories.
- Ensures `delete_file` removes both DB records and physical files.

Run all tests with:

```bash
pytest -m webapp --asyncio-mode=auto
```

Use raw `pytest` to execute the entire suite; see README for more detailed commands.

---

## Extending the Web App

### Best Practices

1. **Follow Service Layer Patterns**: Use `WebAppContentService` for operations to maintain logging, validation, and transaction safety.
2. **Respect Item Ordering**: Always set `order_index`. Use `reorder_items` for bulk updates.
3. **Prepare Translations**: Admin UI messages and logs should remain in Russian; reuse existing utils for consistency.
4. **Avoid Lazy Loading**: Utilize `selectinload` or `joinedload` when adding new queries.
5. **File Handling**:
   - Use `webapp.storage.save_upload()` (if available) or similar helper for new file flow implementations.
   - Always remove physical files when deleting records; reuse `delete_file()`.
6. **Authorization**:
   - Public endpoints should depend on `get_current_user`.
   - Admin-only endpoints must call `require_admin_user`.
   - Do not rely on `WEBAPP_DEBUG_SKIP_AUTH` outside local development.

### Deployment Considerations

- Ensure HTTPS termination for serving the Web App to satisfy Telegram requirements (`WEBAPP_URL` must be HTTPS and publicly accessible).
- Set `WEBAPP_PUBLIC_URL` to the externally reachable base URL used for building static asset links.
- Configure `WEBAPP_CORS_ORIGINS` when hosting the API and static assets on different domains/subdomains.
- Mount static files via a reverse proxy (e.g., Nginx) or use FastAPI's built-in static mounting as provided.

### Admin Experience

- Admin toolbar loads only when `/webapp/me` reports `is_admin=True`.
- Editor mode reveals inline controls (edit, reorder, delete) tied to admin endpoints.
- Confirmation dialogs and toast notifications must wrap destructive actions.
- Manual QA checklist (`WEBAPP_USER_UI_QA_CHECKLIST.md`) outlines regression steps.

---

## Security Notes

- Always serve the Web App backend over HTTPS; Telegram clients refuse non-HTTPS web apps.
- Validate Telegram `initData` tokens for every request; compromised tokens should expire quickly (front-end refresh recommended).
- Keep admin endpoints protected; avoid exposing private logs or debug information.
- Log access attempts and security events using `utils.logger` with consistent Russian messaging.

---

## Additional Resources

- `README.md` – Deployment and setup instructions.
- `WEBAPP_SCHEMA_IMPLEMENTATION.md` – Detailed schema/documentation of categories/items.
- `WEBAPP_USER_UI_QA_CHECKLIST.md` – Manual QA procedures for user/admin flows.
- `ADMIN_PANEL_IMPLEMENTATION.md` – Admin editor implementation details.

Contributions should update associated docs/tests when backend behavior changes to keep QA coverage aligned.
