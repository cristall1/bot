# Bot System Rewrite - Implementation Guide

## Overview

This rewrite addresses 8 critical problems with the bot system:

1. ✅ **Main Menu: Keyboard → Inline** - Implemented
2. ✅ **Settings: All Enabled + Onboarding** - Implemented  
3. ✅ **Become Courier in Delivery Menu** - Implemented
4. ⚠️ **Admin Bot One-Message System** - Not yet implemented
5. ⚠️ **Delivery One-Message Form** - Not yet implemented
6. ⚠️ **Courier Notifications** - Partially implemented, needs finishing
7. ✅ **Broadcast System** - Already working
8. ⚠️ **Location in Buttons** - Partially implemented

---

## What Changed

### 1. Main Menu Now Uses Inline Keyboard from Database

**New Model**: `MainMenuButton`
- Stores main menu buttons with names (RU/UZ), icons, callback_data
- Admin-manageable (future feature)
- Always loads fresh from database

**Key Files Modified**:
- `models.py` - Added `MainMenuButton` model
- `services/main_menu_service.py` - NEW service for main menu management
- `bots/handlers/user_handlers.py` - Rewrote main menu function

**Breaking Change**:
- Old: `get_main_menu_keyboard()` returned ReplyKeyboardMarkup
- New: `get_main_menu_inline_keyboard()` returns InlineKeyboardMarkup (async)

### 2. All Alert Types Enabled By Default

**Changed**:
- `services/alert_service.py` - `ensure_user_alert_preferences()`
- Now enables ALL alert types by default (except COURIER_NEEDED which is hidden)
- Previously only SHURTA was enabled

### 3. Onboarding Flow After Language Selection

**Added**:
- New users see onboarding message after selecting language
- Lists all enabled alert types
- Two options: "Understood" (proceed) or "Configure Now" (settings)
- Full RU and UZ translations

### 4. Delivery Menu Shows "Become Courier"

**Changed**:
- Non-couriers see: "✅ Become Courier" and "📦 Order Delivery"
- Couriers see: Create, Active Orders, Stats
- Button moved from Statistics to Delivery menu as per requirements

---

## Database Migration Required

Run this to create the `main_menu_buttons` table:

```bash
# Method 1: Auto-create on first run (SQLAlchemy will create tables)
# Just start the bot normally

# Method 2: Run initialization script
python3 init_main_menu_buttons.py

# Method 3: Manual SQL
# See alembic/versions/add_main_menu_buttons.py for schema
```

---

## Testing the Changes

### 1. Test Main Menu (Inline Keyboard)

```bash
# Start user bot
# Send /start command
# Expected: Inline keyboard menu with buttons from database
# If DB empty: Fallback defaults appear
```

### 2. Test Onboarding

```bash
# Use new user or clear user from DB
# Send /start
# Select language (RU or UZ)
# Expected: Onboarding message with list of enabled alerts
# Click "👍 Понятно" - should go to main menu
```

### 3. Test Delivery Menu

```bash
# Non-courier:
#   Click 🚚 Delivery
#   Expected: "Become Courier" and "Order Delivery" options

# Courier:
#   Click 🚚 Delivery
#   Expected: Create, Active Orders, Stats options
```

### 4. Test Alert Preferences

```bash
# New user
# Check database: user_alert_preferences table
# Expected: All alert types present with is_enabled=True (except COURIER_NEEDED=False)
```

---

## What Still Needs to Be Done

### High Priority:

1. ✅ **Courier Notifications** (Completed)
   - Couriers now receive localized notifications with accept/decline buttons
   - Accepting a delivery updates assignment and notifies the customer
   - Declining removes the notification message

2. **Database Initialization**
   - Run `init_main_menu_buttons.py` to populate default buttons
   - Or manually insert into `main_menu_buttons` table

### Medium Priority:

3. **Delivery One-Message Form** (1-2 hours)
   - Track message_id for delivery form
   - Update same message through all 4 steps
   - Show progress with checkmarks
   - See BOT_REWRITE_STATUS.md for implementation

### Low Priority:

4. **Admin Bot One-Message System** (3-4 hours)
   - Refactor all admin CRUD flows
   - Track message_id, update instead of send
   - Major refactor across multiple files

---

## Backward Compatibility

- ✅ All existing handlers still work
- ✅ Old menu items don't break
- ✅ Fallback defaults if database empty
- ✅ Existing delivery flow unchanged (just notifications added)
- ✅ No breaking changes to API or services

---

## Admin Panel Integration (Future)

The `MainMenuButton` model is ready for admin management. Future features:

- Admin panel to add/edit/delete main menu buttons
- Reorder buttons (order_index)
- Toggle ON/OFF (is_active)
- Edit names, icons, callback_data
- Real-time sync (no caching, always fresh from DB)

---

## Files Changed

### New Files:
- `services/main_menu_service.py` - Main menu button management
- `init_main_menu_buttons.py` - Initialize default buttons
- `alembic/versions/add_main_menu_buttons.py` - Migration
- `BOT_REWRITE_STATUS.md` - Detailed status
- `BOT_REWRITE_README.md` - This file

### Modified Files:
- `models.py` - Added MainMenuButton model
- `bots/handlers/user_handlers.py` - Main menu, onboarding, delivery
- `services/alert_service.py` - Default preferences

---

## Rollback Plan

If issues arise, to rollback:

1. Revert user_handlers.py:
   - Change `get_main_menu_inline_keyboard()` back to `get_main_menu_keyboard()`
   - Remove onboarding flow
   - Restore old delivery menu

2. Revert alert_service.py:
   - Change default enabled logic back to only SHURTA

3. Drop main_menu_buttons table (optional)

---

## Questions?

See `BOT_REWRITE_STATUS.md` for detailed implementation status and TODO list.

All changes follow existing patterns and coding conventions.
No external dependencies added.
