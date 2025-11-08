# Admin Panel Implementation Guide

## Overview
This document describes the implementation of the new admin panel for category management, moderation, and user control as per the specification.

## Changes Made

### 1. Database Models (models.py)

#### New Models Added:

**Category Model** (lines 283-308)
- Hierarchical category system with parent-child relationships
- Supports on/off toggle (`is_active` field)
- Multi-language support (RU/UZ)
- Media support (photo, audio, PDF, links)
- Button type configuration (inline, keyboard, none)

**CategoryButton Model** (lines 311-326)
- Buttons for categories
- Support for different button types (LINK, CALLBACK, GEO)
- Multi-language support

**ModerationQueue Model** (lines 329-346)
- Central moderation queue for all entities
- Tracks status (PENDING, APPROVED, REJECTED)
- Records moderator actions
- Stores admin message IDs for inline keyboard updates

### 2. Services

#### CategoryService (services/category_service.py) - COMPLETELY REWRITTEN
- Full CRUD operations for categories
- Toggle functionality for on/off switches
- Hierarchical category tree management
- Button management (add, update, delete)
- Default category initialization
- Tree serialization for frontend

#### ModerationQueueService (services/moderation_queue_service.py) - NEW
- Add items to moderation queue
- Get pending items by type
- Approve/reject functionality
- Statistics for queue monitoring

### 3. Admin Handlers

#### admin_category_handlers.py - NEW FILE
Complete implementation of category management interface:

**Main Features:**
- Category dashboard with on/off toggles
- Edit category name, text, media
- Photo/audio/PDF upload
- Nested subcategory management
- Inline keyboard with exact layout as specified:
  ```
  [on/off] [📚 Talim]  [✏️]
  [on/off] [🚚 Dostavka] [✏️]
  ...
  [➕ Добавить категорию]
  [🔙 Назад]
  ```

**Handlers Implemented:**
- `show_category_management` - Main dashboard
- `toggle_category` - On/off toggle (instant DB persist)
- `view_category` - View/edit specific category
- `edit_category` - Edit name/text/media
- `process_category_name_input` - Handle name changes
- `process_category_text_input` - Handle text changes
- `process_photo_upload` - Handle photo uploads
- `start_add_category` - Begin adding new category

### 4. FSM States (states.py)

Added new admin states for category management:
- `category_management`
- `category_list`
- `category_editing`
- `category_name_input`
- `category_text_input`
- `category_button_type_selection`
- `category_media_management`
- `category_photo_upload`
- `category_audio_upload`
- `category_pdf_upload`
- `category_link_input`
- `category_subcategory_management`

### 5. Integration

#### admin_bot.py
- Registered category handlers alongside existing admin handlers

#### admin_handlers.py
- Added "📁 Управление категориями" button to main menu
- Imported CategoryService and category dashboard renderer

## Initialization

### init_categories.py - NEW FILE
Script to initialize default categories in the database:
- Talim (📚)
- Dostavka (🚚)
- Yoqolgan (🔔)
- Shurta (🚨)
- Sozlamalar (⚙️)
- Admin (💬)
- Settings (⚙️)

Run with:
```bash
python init_categories.py
```

## Architecture Decisions

### 1. On/Off Toggle Implementation
- Instant persistence: Changes saved immediately to DB
- Real-time UI update: Keyboard refreshes after toggle
- Cascading effect: When category is off, it disappears from user menu

### 2. Moderation Flow
- Centralized ModerationQueue table for all entity types
- Admin receives inline keyboard with [✅ Принять] [❌ Отклонить]
- User notification after approval/rejection
- Auto-delete user confirmation message after 10 seconds (already implemented in user_handlers.py)

### 3. Media Management
- File IDs stored in category table
- Support for photo, audio, PDF, and links
- Upload/change/delete operations for each media type

### 4. Nested Categories
- Self-referential parent_id foreign key
- Recursive tree building with `_serialize_category`
- Supports unlimited nesting levels

### 5. Logging Strategy
- All logs in Russian for admin debugging
- English comments in code for developers
- Success (✅) and error (❌) icons in logs
- Detailed error logging with exc_info=True

## What's Not Yet Implemented

### High Priority
1. **Media Upload Handlers**
   - Audio upload handler
   - PDF upload handler
   - Link input handler
   
2. **Add New Category Flow**
   - Complete step-by-step wizard (name → text → buttons/media)
   - Choice between inline/keyboard/simple buttons
   
3. **Subcategory Management**
   - List subcategories
   - Add/edit/delete subcategories
   - Nested editing interface

4. **Delivery Management Interface**
   ```
   [on/off] [Faol zakazy (12)]    [👁️ Посмотреть]
   [on/off] [Bajarilgan (45)]     [👁️ Посмотреть]
   ...
   ```

5. **Moderation Alerts Integration**
   - Update user_handlers.py to use ModerationQueueService
   - Send notifications to admin with inline keyboards
   - Handle approve/reject callbacks

### Medium Priority
6. **Broadcast System Enhancements**
   - Auto-translation feature
   - Preview before sending
   - Progress indicator
   - History management with delete option
   - Timer/scheduler

7. **User Search (Inline Mode)**
   - Implement inline query handler
   - Paginated user list
   - Detailed user profile view
   - Ban/unban buttons

8. **Statistics Dashboard**
   - Total users, active today/week
   - Top buttons with usage counts
   - Peak hours analysis
   - Language/citizenship breakdown

9. **User Messages to Admin**
   - Message queue interface
   - Reply functionality
   - Auto-response if admin doesn't reply
   - Mark as answered/pending

### Low Priority
10. **Geolocation Handling**
    - Remove geo/maps from delivery (manual address only)
    - Keep geo for police/lost persons
    - Show Telegram location (not coordinates)

11. **Courier Features**
    - Button to open chat with customer after accepting order
    - Deep link to customer's Telegram

## Testing Checklist

### Category Management
- [ ] Admin can see main category dashboard
- [ ] Toggle on/off persists to DB immediately
- [ ] Toggle updates UI without refresh
- [ ] Clicking category name shows details
- [ ] Editing category name works
- [ ] Editing category text works
- [ ] Uploading photo works
- [ ] Add new category wizard works

### Moderation (When Implemented)
- [ ] Lost person submission creates queue item
- [ ] Lost item submission creates queue item
- [ ] Shurta submission creates queue item
- [ ] Admin receives notification with buttons
- [ ] Approval broadcasts to users
- [ ] Rejection notifies user
- [ ] User message deleted after 10 seconds

### Database
- [ ] Migration runs successfully
- [ ] Default categories created
- [ ] Toggle changes persist across restarts
- [ ] Relationships load correctly (eager loading)

## Migration Notes

**Required migrations:**
1. Add `categories` table
2. Add `category_buttons` table
3. Add `moderation_queue` table

**Run migrations:**
```bash
# If using Alembic:
alembic revision --autogenerate -m "Add categories and moderation queue"
alembic upgrade head

# Manual initialization:
python init_categories.py
```

## Error Handling

All handlers follow consistent error handling pattern:
```python
try:
    logger.info(f"[handler_name] Операция началась...")
    # ... operation code ...
    logger.info(f"[handler_name] ✅ Операция завершена успешно")
except Exception as e:
    logger.error(f"[handler_name] ❌ Ошибка: {str(e)}", exc_info=True)
    await callback/message.answer("❌ Ошибка", show_alert=True)
```

## API Reference

### CategoryService Methods

- `create_category(session, key, name_ru, name_uz, **kwargs)` → Category
- `get_category(session, category_id)` → Optional[Category]
- `get_category_by_key(session, key)` → Optional[Category]
- `get_all_categories(session, active_only=True)` → List[Category]
- `get_root_categories(session, active_only=True)` → List[Category]
- `get_subcategories(session, parent_id, active_only=True)` → List[Category]
- `update_category(session, category_id, **kwargs)` → Optional[Category]
- `delete_category(session, category_id)` → bool
- `toggle_category(session, category_id)` → Optional[Category]
- `add_button(session, category_id, text_ru, text_uz, button_type, button_value, order_index=0)` → CategoryButton
- `update_button(session, button_id, **kwargs)` → Optional[CategoryButton]
- `delete_button(session, button_id)` → bool
- `ensure_default_categories(session)` → List[Category]
- `get_category_tree(session, active_only=True)` → List[Dict[str, Any]]

### ModerationQueueService Methods

- `add_to_queue(session, entity_type, entity_id, user_id, admin_message_id=None)` → ModerationQueue
- `get_pending_items(session, entity_type=None)` → List[ModerationQueue]
- `approve_item(session, queue_id, moderator_id, comment=None)` → Optional[ModerationQueue]
- `reject_item(session, queue_id, moderator_id, comment=None)` → Optional[ModerationQueue]
- `get_queue_item_by_entity(session, entity_type, entity_id)` → Optional[ModerationQueue]
- `get_statistics(session)` → dict

## Next Steps

1. **Immediate:**
   - Test category management interface
   - Complete media upload handlers (audio, PDF, link)
   - Implement complete add category wizard

2. **Short-term:**
   - Integrate moderation queue with user handlers
   - Create moderation dashboard for admin
   - Implement delivery management interface

3. **Medium-term:**
   - Build broadcast system with translations
   - Create statistics dashboard
   - Implement user search inline mode

4. **Long-term:**
   - Add subcategory management UI
   - Implement user message queue
   - Build geolocation improvements

## Contact & Support

For questions or issues:
- Check logs in console (all in Russian)
- Search for error icons (❌) in logs
- Review handler name in brackets (e.g., `[admin_cat_toggle]`)
- Check FSM state transitions
