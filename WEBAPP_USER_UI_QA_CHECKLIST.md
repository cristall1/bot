# WebApp User UI - QA Checklist

## Manual Testing Checklist for Stage 1 Implementation

### Initial Load & Setup
- [ ] WebApp loads successfully from Telegram
- [ ] Telegram Web App SDK is loaded and initialized
- [ ] Theme colors are applied correctly (light/dark mode)
- [ ] Categories list is fetched and displayed
- [ ] Loading spinner appears during initial load
- [ ] Error message displays if categories fail to load

### Navigation
- [ ] Sidebar displays all active categories (desktop view)
- [ ] Floating category bar displays on mobile (< 768px width)
- [ ] Category buttons are clickable and trigger category load
- [ ] Active category is highlighted in navigation
- [ ] Breadcrumbs display current navigation path
- [ ] Home breadcrumb returns to category overview
- [ ] Clicking intermediate breadcrumb navigates correctly
- [ ] Navigation is smooth without page refresh

### Category Display
- [ ] Category title displays correctly
- [ ] Category description shows when available
- [ ] Item count displays with correct pluralization
- [ ] Cover image displays when present
- [ ] Cover image is hidden when not present
- [ ] Empty state shows for categories with no items

### Content Rendering - TEXT Items
- [ ] Plain text renders with proper line breaks
- [ ] **Bold** text renders correctly
- [ ] *Italic* text renders correctly
- [ ] [Links](url) render as clickable links
- [ ] Links open in new tab
- [ ] Multi-paragraph text displays properly

### Content Rendering - IMAGE Items
- [ ] Images load and display correctly
- [ ] Image dimensions are preserved (aspect ratio)
- [ ] Image captions display when present
- [ ] Clicking image opens modal viewer
- [ ] Modal displays full-size image
- [ ] Modal close button works
- [ ] Clicking modal background closes modal
- [ ] ESC key closes modal
- [ ] Lazy loading works for images

### Content Rendering - DOCUMENT Items
- [ ] Document icon displays based on MIME type
- [ ] Document name displays correctly
- [ ] File size displays in readable format (B/KB/MB)
- [ ] Clicking document triggers download/open
- [ ] Download works correctly

### Content Rendering - VIDEO Items
- [ ] Video player displays with controls
- [ ] Video loads and plays correctly
- [ ] Video placeholder displays when no file available
- [ ] Video respects mobile/desktop dimensions

### Content Rendering - LINK Items
- [ ] External link button displays
- [ ] Link text shows correctly
- [ ] Clicking link opens in browser
- [ ] Telegram WebApp.openLink() is used when available
- [ ] Arrow icon displays

### Content Rendering - BUTTON Items (Navigation)
- [ ] Navigation buttons display correctly
- [ ] Button text shows from button_text or text_content
- [ ] Clicking button navigates to target category
- [ ] Disabled state shows for buttons without target
- [ ] Navigation updates breadcrumbs correctly

### Responsive Design - Desktop (> 768px)
- [ ] Two-column layout (sidebar + content)
- [ ] Sidebar is visible and sticky
- [ ] Content area uses available space
- [ ] Category cards display in grid
- [ ] All content types render correctly
- [ ] No horizontal scrolling
- [ ] No layout breakage

### Responsive Design - Mobile (≤ 768px)
- [ ] Single column layout
- [ ] Sidebar is hidden
- [ ] Floating category bar is visible
- [ ] Floating bar scrolls horizontally
- [ ] All content stacks vertically
- [ ] Touch targets are adequate (min 44x44px)
- [ ] No horizontal overflow
- [ ] Readable text sizes

### Theme Support
- [ ] Light theme colors applied correctly
- [ ] Dark theme colors applied correctly
- [ ] Theme switches dynamically when Telegram theme changes
- [ ] All UI elements respect theme colors
- [ ] Contrast is sufficient in both modes
- [ ] Links are visually distinct

### Loading & Error States
- [ ] Loading spinner displays during category fetch
- [ ] Loading text updates appropriately
- [ ] Error message displays on network failure
- [ ] Error message displays on 404/500 errors
- [ ] Retry button appears in error state
- [ ] Retry button refetches data successfully
- [ ] Empty state displays when no content

### Caching & Performance
- [ ] Categories are cached for 5 minutes
- [ ] Category details are cached for 5 minutes
- [ ] Cached data is used on subsequent requests
- [ ] Cache invalidates after TTL
- [ ] Page loads quickly on cached data
- [ ] No unnecessary API calls

### Accessibility
- [ ] Semantic HTML is used (header, nav, main, section)
- [ ] ARIA labels are present where needed
- [ ] ARIA live regions announce state changes
- [ ] Keyboard navigation works throughout
- [ ] Focus states are visible
- [ ] Screen reader can navigate content
- [ ] alt attributes on images
- [ ] Color is not the only indicator

### Browser Compatibility
- [ ] Works in Telegram iOS WebView
- [ ] Works in Telegram Android WebView
- [ ] Works in Telegram Desktop
- [ ] Works in Chrome (for testing)
- [ ] Works in Safari (for testing)
- [ ] No console errors in any browser

### Authentication
- [ ] initData is sent in X-Telegram-Init-Data header
- [ ] API requests are authenticated correctly
- [ ] 401 errors handled gracefully
- [ ] Debug mode works when enabled (WEBAPP_DEBUG_SKIP_AUTH)
- [ ] Production auth works with real Telegram data

### Admin Mode Toggle
- [ ] mode=user hides admin features (currently all features)
- [ ] mode=admin parameter works (for future use)
- [ ] Mode badge displays current mode
- [ ] No admin controls visible in user mode

### Edge Cases
- [ ] Empty category list displays empty state
- [ ] Category with no items displays empty state
- [ ] Very long category names don't break layout
- [ ] Very long text content wraps correctly
- [ ] Large images don't overflow container
- [ ] Many categories display correctly
- [ ] Rapid navigation doesn't cause issues
- [ ] Network interruption handled gracefully
- [ ] Invalid category ID shows error

### Performance Metrics (Lighthouse Mobile)
- [ ] Performance score ≥ 75
- [ ] Accessibility score ≥ 75
- [ ] Best Practices score ≥ 75
- [ ] SEO score ≥ 75
- [ ] First Contentful Paint < 2s
- [ ] Time to Interactive < 3.5s
- [ ] Total Blocking Time < 300ms

### Final Verification
- [ ] No JavaScript errors in console
- [ ] No network request failures
- [ ] All images load successfully
- [ ] All API endpoints respond correctly
- [ ] Page is responsive at all viewport sizes
- [ ] Telegram WebApp integrations work
- [ ] Theme changes work smoothly
- [ ] Navigation history works correctly
- [ ] All content types render as expected
- [ ] User experience is smooth and intuitive

## Test Scenarios

### Scenario 1: First-Time User
1. User opens WebApp from Telegram
2. Categories load and display
3. User clicks first category
4. Category content displays
5. User scrolls through items
6. User clicks image to view in modal
7. User closes modal
8. User navigates to another category
9. User uses breadcrumbs to go back

### Scenario 2: Navigation Button Flow
1. User opens WebApp
2. User selects category with navigation button item
3. User clicks navigation button
4. Target category loads
5. Breadcrumbs show navigation trail
6. User clicks home breadcrumb
7. Category overview displays

### Scenario 3: Mobile User
1. User opens WebApp on mobile device
2. Floating category bar displays
3. User swipes through categories
4. User selects category
5. Content displays in single column
6. User views images, videos, documents
7. All interactions work with touch

### Scenario 4: Error Recovery
1. User opens WebApp offline
2. Error message displays
3. User goes online
4. User clicks retry button
5. Categories load successfully
6. Normal operation resumes

### Scenario 5: Theme Switching
1. User opens WebApp in light mode
2. UI uses light theme colors
3. User switches Telegram to dark mode
4. UI updates to dark theme colors
5. All elements remain readable

## Notes
- Document any issues found with screenshots
- Record browser/device combinations tested
- Note performance metrics from Lighthouse
- Save network logs for API request verification
- Test with real content variety (long text, large images, etc.)
