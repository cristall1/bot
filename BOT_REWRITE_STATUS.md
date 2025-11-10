# Bot System Rewrite Status

## ✅ COMPLETED

### 1. Main Menu: Keyboard → Inline ✅
- [x] Created `MainMenuButton` model in `models.py`
- [x] Created `MainMenuService` in `services/main_menu_service.py`
- [x] Created init script `init_main_menu_buttons.py`
- [x] Rewrote `get_main_menu_inline_keyboard()` to load from database
- [x] Updated `/start` command to use inline keyboard
- [x] Added fallback defaults if database is empty
- [x] Added main menu callback handlers: `menu_delivery`, `menu_alert`, `menu_message_admin`, `menu_settings`
- [x] Added `back_main` handler to return to main menu
- [x] WebApp button still included (if HTTPS)

**Result**: Main menu now uses inline keyboard buttons loaded from database. Admin can manage these in the future via admin panel.

### 2. Settings - All Enabled By Default + Onboarding ✅
- [x] Updated `AlertService.ensure_user_alert_preferences()` to enable ALL alert types by default (except COURIER_NEEDED)
- [x] Added onboarding flow after language selection
- [x] Onboarding shows all enabled alert types
- [x] Two buttons: "👍 Понятно" (understood) and "⚙️ Настроить сейчас" (configure settings)
- [x] Onboarding text in both RU and UZ languages

**Result**: New users see onboarding explaining that all alert types are enabled by default, can proceed to main menu or configure settings.

### 3. "Become Courier" in Delivery Menu ✅
- [x] Delivery menu checks if user is courier
- [x] Non-couriers see: "✅ Стать курьером" and "📦 Заказать доставку"
- [x] Couriers see: Create, Active Orders, Stats
- [x] "Become Courier" button directly in Delivery menu (not in Statistics)

**Result**: Become courier button is now in the right place as per requirements.

---

## ⚠️ PARTIALLY IMPLEMENTED / TODO

### 4. Admin Bot Message Spam - ONE MESSAGE SYSTEM ⚠️
**Status**: Not implemented yet. Complex refactor required.

**What's needed**:
- Admin handlers need to track `message_id` for each form
- Use `edit_message_text()` instead of `send_message()` 
- Store state: `{admin_id: {message_id: int, step: int, data: dict}}`
- Update same message through all form steps

**Files to modify**:
- `bots/handlers/admin_handlers.py` - all CRUD flows
- `bots/handlers/admin_category_handlers.py` - category editing
- `bots/handlers/admin_menu_handlers.py` - menu management

### 5. Delivery Form - ONE MESSAGE SYSTEM ⚠️
**Status**: Not implemented yet. Complex refactor required.

**What's needed**:
- Create delivery form state manager
- Track message_id for delivery form
- Update ONE message through all 4 steps:
  1. What to deliver?
  2. From where? (location)
  3. To where? (location)
  4. Contact phone?
- Show progress in same message with checkmarks
- Final confirmation with [✅ Create Order] [❌ Cancel] buttons

**Files to modify**:
- `bots/handlers/user_handlers.py` - delivery flow (lines 1230-1555)
- Create new `delivery_form_state` dict similar to admin_temp_data

### 6. Courier Notifications ✅
**Status**: Completed. Couriers now receive inline notifications with accept/decline actions.

**Implementation**:
- Added `notify_couriers_about_delivery()` helper in `bots/handlers/user_handlers.py`
- After delivery creation, the system triggers notifications (async task)
- Couriers receive localized message (RU/UZ), optional location, and inline buttons
- Added handlers for `accept_delivery_{id}` and `decline_delivery_{id}` callbacks
- Accepting a delivery assigns courier, updates message, and notifies customer

**Tests**:
- `python3 -m py_compile bots/handlers/user_handlers.py`
- Manual flow testing recommended (create delivery, check courier receives message)


### 7. Broadcast System ⚠️
**Status**: Already implemented and working according to memory. Should verify.

**Verification needed**:
- Check `admin_alert_handlers.py` for broadcast logic
- Verify `AlertService.get_broadcast_targets()` filters properly
- Test end-to-end broadcast flow

### 8. Location in Buttons ⚠️
**Status**: Partially implemented for categories, needs implementation for MenuButtons.

**What's needed**:
- Menu buttons can have action_type = "SEND_LOCATION"
- action_data = {"latitude": float, "longitude": float, "title": str}
- User bot handler for menu button clicks needs to send location

**Files to modify**:
- User bot needs handler for clicking MenuButton with SEND_LOCATION action
- Similar to category geolocation handler (lines 473-500 in user_handlers.py)

---

## 📋 DATABASE MIGRATION

### Required:
Run migration to create `main_menu_buttons` table:
```bash
# Option 1: Use alembic
alembic upgrade head

# Option 2: Use database auto-create (SQLAlchemy)
# Tables will be created automatically on first run

# Option 3: Manual initialization
python3 init_main_menu_buttons.py
```

---

## 🎯 PRIORITY FOR COMPLETION

### High Priority (Core Functionality):
1. ✅ **Courier Notifications** - COMPLETED
2. **Database Migration** - Must run init script or tables won't exist
3. **Verify Broadcast System** - Ensure it's working as expected

### Medium Priority (UX Improvements):
4. **Delivery Form - One Message** - Greatly improves user experience, reduces spam
5. **Location in Menu Buttons** - Adds functionality for location sharing

### Low Priority (Admin UX):
6. **Admin Bot - One Message** - Improves admin experience but not user-facing

---

## 🧪 TESTING CHECKLIST

### User Bot:
- [ ] /start shows inline keyboard menu
- [ ] Language selection shows onboarding
- [ ] All alert types enabled by default
- [ ] Main menu buttons work (Delivery, Alert, Message Admin, Settings)
- [ ] Delivery menu shows "Become Courier" for non-couriers
- [ ] Delivery creation works (existing multi-message flow)
- [ ] Couriers receive notifications when order created
- [ ] WebApp button appears if HTTPS URL configured

### Admin Bot:
- [ ] Can manage main menu buttons (future feature)
- [ ] Alert moderation works
- [ ] Broadcast sends to all users with correct preferences

---

## 🔧 RECOMMENDED NEXT STEPS

1. **Run database migration** to create main_menu_buttons table
2. **Run init script** to populate default menu buttons
3. **Test user bot** /start flow and main menu
4. **Implement courier notifications** (15-20 minutes)
5. **Test delivery creation** end-to-end with courier notifications
6. **Consider implementing one-message delivery form** (1-2 hours)
7. **Consider implementing one-message admin forms** (3-4 hours)

---

## 📝 NOTES

- Old ReplyKeyboardMarkup code commented out or removed
- Inline keyboard always loads fresh from database (no caching)
- Fallback defaults ensure menu works even if database empty
- All changes backward compatible - existing handlers still work
- Future: Add admin panel to manage MainMenuButtons via Admin Bot
