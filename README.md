# Al-Azhar & Dirassa Dual Telegram Bot System

**Comprehensive dual bot system for Al-Azhar and Dirassa students from Uzbekistan, Russia, Kazakhstan, and Kyrgyzstan.**

🇷🇺 [Русская версия](#русская-версия) | 🇬🇧 [English version](#english-version)

---

## English Version

### 📋 Overview

This is a complete Telegram bot system consisting of two bots:
- **User Bot**: For students to access information, request services, and become couriers
- **Admin Bot**: For administrators to manage content, approve services, and broadcast messages

### ✨ Key Features

#### User Bot Features:
- 🌐 **Bilingual Interface**: Full Russian and Uzbek language support
- 🌍 **Multi-Citizenship Support**: Uzbekistan, Russia, Kazakhstan, Kyrgyzstan
- 🌐 **Web App Integration**: Access the full Web App directly from the bot menu with a dedicated button
- 📚 **Hierarchical Categories**: 4-level category system (Dirassa/Al-Azhar → Citizenship → Stage → Content)
- 🏢 **Service Requests**: Request or offer services (tutoring, accommodation, courier, etc.)
- 🚚 **Cairo Courier System**: Become a courier and earn by delivering packages
- 🔍 **Search**: Search across all content
- 📞 **Admin Contact**: Direct messaging to administration
- ⚙️ **Settings**: Language, citizenship, notifications management
- 🔗 **Inline Buttons**: Direct links to resources within categories

#### Admin Bot Features:
- 📚 **Category Management**: Create, edit, delete, toggle categories with 4-level hierarchy
- 🔗 **Inline Button Management**: Add custom buttons with URLs to any category
- 🏢 **Service Management**: Approve/reject service requests
- 👥 **User Management**: Ban/unban, make admin, view statistics
- 🚚 **Courier Management**: Verify, suspend, manage Cairo couriers
- 📢 **Broadcast System**: Send messages to all users or filtered groups
- 📊 **Statistics Dashboard**: Comprehensive analytics
- ⚙️ **System Settings**: Toggle features on/off
- 🔍 **Content Parser**: Extract information from result.json
- 📋 **Admin Logs**: All actions logged with details

### 🛠️ Tech Stack

- **Python**: 3.11+
- **aiogram**: 3.4.1 (Telegram Bot API)
- **SQLAlchemy**: 2.0.27 (ORM)
- **aiosqlite**: 0.19.0 (Async SQLite)
- **Pydantic**: 2.6.1 (Settings management)
- **FastAPI**: 0.109.0 (ASGI web framework for Telegram Web App)
- **Uvicorn**: 0.27.0 (ASGI server)
- **Jinja2**: 3.1.3 (Templating engine for web views)
- **Telegraph**: 2.2.0 (Long content articles)

### 📁 Project Structure

```
bot/
├── config.py                          # Configuration settings
├── database.py                        # Database initialization
├── models.py                          # SQLAlchemy models (11 tables)
├── locales.py                         # Bilingual translations
├── main.py                            # Entry point
│
├── bots/
│   ├── user_bot.py                   # User bot instance
│   ├── admin_bot.py                  # Admin bot instance
│   └── handlers/
│       ├── user_handlers.py          # User bot handlers
│       └── admin_handlers.py         # Admin bot handlers
│
├── services/                          # Business logic layer
│   ├── category_service.py
│   ├── service_management.py
│   ├── courier_service.py
│   ├── broadcast_service.py
│   ├── user_service.py
│   ├── admin_log_service.py
│   ├── telegraph_service.py
│   ├── admin_menu_service.py
│   └── inline_button_service.py
│
├── utils/                             # Utility functions
│   ├── logger.py
│   ├── validators.py
│   ├── parsers.py
│   ├── helpers.py
│   └── keyboard_builder.py
│
├── webapp/                            # FastAPI web application
│   ├── server.py                     # FastAPI app factory
│   ├── routes/                       # HTTP endpoints
│   │   └── __init__.py              # Health check endpoint
│   ├── static/                       # Static assets (CSS, JS, images)
│   └── templates/                    # Jinja2 HTML templates
│
├── data/                              # Seed data
│   ├── result.json                   # Telegram chat export
│   ├── categories_seed.json
│   ├── services_seed.json
│   └── dirassa_content.json
│
├── requirements.txt
├── .env.example
└── README.md
```

### 🗄️ Database Schema

**11 Tables:**
1. `users` - User accounts with language/citizenship
2. `categories` - Hierarchical content categories (4 levels)
3. `category_content` - Content within categories
4. `inline_buttons` - Custom buttons with URLs
5. `service_requests` - User service requests
6. `courier_management` - Cairo courier system
7. `user_preferences` - User settings
8. `admin_messages` - User-admin communication
9. `broadcasts` - Mass messaging history
10. `admin_logs` - Admin action audit trail
11. `system_settings` - Feature toggles

### 🚀 Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd bot
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt  # includes FastAPI, Uvicorn, python-multipart, Jinja2
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your bot tokens and admin IDs
```

4. **Run the system**:
```bash
python main.py
```

### ⚙️ Configuration

Edit `.env` file:

```env
USER_BOT_TOKEN=your_user_bot_token_here
ADMIN_BOT_TOKEN=your_admin_bot_token_here
DATABASE_URL=sqlite+aiosqlite:///./bot_database.db
ADMIN_IDS=123456789,987654321
LOG_LEVEL=INFO
LOG_FILE=bot.log

# WebApp Settings (for Telegram Web App)
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8000
WEBAPP_PUBLIC_URL=http://localhost:8000
WEBAPP_URL=https://your-domain.com/webapp  # Public HTTPS URL for WebApp button
WEBAPP_CORS_ORIGINS=    # comma-separated allowed origins (optional)
```

**Getting Bot Tokens:**
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create two bots: `/newbot`
3. Copy tokens to `.env`

**Admin IDs:**
- Your Telegram user ID (get from [@userinfobot](https://t.me/userinfobot))
- Comma-separated for multiple admins

### 📚 Usage

#### User Bot

1. **Start**: `/start`
2. **Choose Language**: Russian or Uzbek
3. **Select Citizenship**: UZ, RU, KZ, or KG
4. **Main Menu**:
   - 🌍 WebApp - Open the full Web App interface
   - 📄 Documents - Browse documents by citizenship
   - 🚚 Delivery - Request or offer delivery services
   - 🔔 Notifications - Report lost people or items
   - 🚨 Police - Report safety alerts
   - 👨‍💼 Contact Admin - Send message
   - ⚙️ Settings - Change preferences
5. **WebApp Command**: Use `/webapp` to get direct access to the WebApp button

#### Admin Bot

1. **Start**: `/start` (admin IDs only)
2. **Main Menu**:
   - 📚 Manage Categories
   - 🔗 Manage Buttons
   - 🏢 Manage Services
   - 👥 Manage Users
   - 🚚 Manage Couriers
   - 📢 Broadcast
   - 📊 Statistics
   - ⚙️ Settings
   - 🔍 Parse Content

### 🔧 Development

**Adding Categories:**
1. Admin Bot → Manage Categories → Add
2. Enter name (RU/UZ), description, select type
3. Set parent category for hierarchy

**Adding Inline Buttons:**
1. Admin Bot → Manage Buttons → Add
2. Select category
3. Enter button text (RU/UZ) and URL
4. Buttons appear in user bot

**Approving Services:**
1. Admin Bot → Manage Services → Pending
2. Review requests
3. Approve or Reject

**Broadcasting:**
1. Admin Bot → Broadcast → Create
2. Enter message (RU/UZ)
3. Select filter (all/language/citizenship/couriers)
4. Confirm and send

### 🌐 Web App Features

#### Overview

The Telegram Web App provides a rich content browsing experience with:
- **Dynamic Categories**: Hierarchical content organization with customizable items
- **No-Code Admin Editor**: Visual content management built into the web interface
- **File Upload Support**: Images, documents, and videos with automatic optimization
- **Responsive Design**: Mobile-first UI that works on all devices

#### For Users

Access the Web App through:
1. Main menu button: **🌍 WebApp / Путник**
2. Command: `/webapp`
3. Direct link: Your `WEBAPP_URL` (configured in `.env`)

The Web App displays:
- **Categories**: Browse organized content with cover images
- **Multiple Content Types**: Text, images, videos, documents, navigation buttons
- **Rich Formatting**: Support for markdown-style text formatting
- **Dark/Light Mode**: Automatic theme switching based on Telegram settings

#### For Admins

Admins see an **Admin Editor** with additional controls:

1. **Toggle Edit Mode**: Switch between edit and preview modes
2. **Category Management**:
   - Create/edit/delete categories
   - Set cover images and descriptions
   - Reorder categories using drag controls
   - Toggle visibility (active/inactive)

3. **Item Management**:
   - Add TEXT, IMAGE, VIDEO, DOCUMENT, LINK, or BUTTON items
   - Inline editing with save/cancel actions
   - Reorder items within categories
   - Upload files directly from the editor

4. **File Uploads**:
   - Drag-and-drop or click to upload
   - Image dimensions extracted automatically
   - File validation (MIME type, size limits)
   - Thumbnail generation for images

#### Environment Variables

```env
# WebApp Core Settings
WEBAPP_HOST=0.0.0.0                              # Host to bind the web server
WEBAPP_PORT=8000                                 # Port for FastAPI server
WEBAPP_PUBLIC_URL=http://localhost:8000          # Base URL for static assets and file URLs
WEBAPP_URL=https://your-domain.com/webapp        # Public HTTPS URL for WebApp button in bot

# Optional WebApp Settings
WEBAPP_CORS_ORIGINS=https://example.com          # Comma-separated CORS origins (if needed)
WEBAPP_DEBUG_SKIP_AUTH=false                     # Skip auth for local testing (NEVER in production)
WEBAPP_DEBUG_USER_ID=12345                       # User ID for debug mode
WEBAPP_UPLOAD_DIR=webapp/uploads                 # Directory for uploaded files
WEBAPP_MAX_UPLOAD_SIZE=10485760                  # Max file size in bytes (default: 10MB)
```

**Important**: `WEBAPP_URL` must be HTTPS for Telegram Web Apps to work in production. Use services like ngrok for local development or deploy to a server with HTTPS.

#### Running the Web App

The Web App starts automatically when you run `python main.py`. It runs alongside the bots on the configured port.

To run only the Web App (for development):

```bash
# Install dependencies
pip install -r requirements.txt

# Run with uvicorn directly
uvicorn webapp.server:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

#### Testing

Run the automated test suite:

```bash
# All tests
pytest

# Only Web App tests
pytest tests/test_webapp_*.py -v

# With coverage
pytest --cov=webapp --cov=services.webapp_content_service tests/test_webapp_*.py

# Optional static analysis (run if ruff/flake8 configured)
ruff check .
# or
flake8
```

Test categories:
- `test_webapp_auth.py` - Authentication and security
- `test_webapp_categories.py` - Category listing and retrieval
- `test_webapp_admin.py` - Admin CRUD operations
- `test_webapp_uploads.py` - File upload and storage
- `test_webapp_schema.py` - Service layer and database models
- `tests/test_webapp_integration.py` - End-to-end user + admin flows

See `tests/conftest.py` for available fixtures and test utilities. For manual regression testing, follow `WEBAPP_USER_UI_QA_CHECKLIST.md`.

#### Security Considerations

1. **HTTPS Required**: Telegram Web Apps only work over HTTPS in production
2. **InitData Validation**: Every request validates Telegram's signed init data
3. **Admin Verification**: Admin endpoints check `user.is_admin` flag
4. **File Upload Validation**: MIME types and sizes are validated
5. **Debug Mode**: Never enable `WEBAPP_DEBUG_SKIP_AUTH` in production

#### Deployment Checklist

1. Set `WEBAPP_URL` to your public HTTPS domain
2. Ensure `WEBAPP_PUBLIC_URL` matches where static files are served
3. Configure reverse proxy (Nginx, Apache) for HTTPS termination
4. Mount static files at `/webapp/static` and uploads at `/webapp/uploads`
5. Set appropriate `WEBAPP_MAX_UPLOAD_SIZE` limits
6. Add your domain to BotFather's web app settings
7. Test with real Telegram clients (iOS, Android, Desktop)

See `docs/webapp.md` for detailed architecture documentation.

### 📊 Statistics

Admin dashboard shows:
- Total users, new today, by language/citizenship
- Total categories, buttons, content items
- Service requests (approved/pending/rejected)
- Courier statistics (active, deliveries, ratings)
- Message analytics

### 🔍 Content Parsing

The system can parse `result.json` (Telegram chat export) to extract:
- **Dirassa**: Course levels, books, curriculum, pricing
- **Al-Azhar**: Faculties, requirements, visa info, scholarships
- **Contacts**: Phone numbers, emails
- **Links**: All URLs from messages

### 🌟 Courier System

**Cairo-Focused Delivery:**
- Users can become couriers with one click
- Track deliveries and ratings
- Zone-based delivery (Nasr City, Heliopolis, Maadi, etc.)
- Statistics dashboard for couriers

### 📝 Logging

All admin actions are logged:
- Action type (CREATE, UPDATE, DELETE, APPROVE, etc.)
- Entity type (CATEGORY, BUTTON, SERVICE, etc.)
- Timestamp and admin ID
- Detailed changes in JSON format

### 🔐 Security

- Admin-only access for admin bot
- User ban system
- Feature toggles for services
- Input validation (URLs, phones, etc.)

### 🐛 Troubleshooting

**Bot not responding:**
- Check bot tokens in `.env`
- Ensure bots are not stopped in BotFather
- Check logs: `tail -f bot.log`

**Database errors:**
- Delete `bot_database.db` and restart
- Check SQLite installation

**Import errors:**
- Reinstall dependencies: `pip install -r requirements.txt --upgrade`

### 📄 License

This project is licensed under the MIT License.

---

## Русская версия

### 📋 Обзор

Комплексная система из двух Telegram-ботов:
- **Пользовательский бот**: Для студентов - доступ к информации, заказ услуг, работа курьером
- **Админский бот**: Для администраторов - управление контентом, модерация, рассылки

### ✨ Основные возможности

#### Возможности пользовательского бота:
- 🌐 **Билингвальный интерфейс**: Полная поддержка русского и узбекского языков
- 🌍 **Поддержка 4 стран**: Узбекистан, Россия, Казахстан, Киргизия
- 🌐 **Интеграция с веб-приложением**: Кнопка в основном меню открывает Web App прямо в Telegram
- 📚 **Иерархические категории**: 4-уровневая система (Dirassa/Al-Azhar → Гражданство → Этап → Контент)
- 🏢 **Заказ услуг**: Запрос или предложение услуг (репетиторство, жильё, курьер и др.)
- 🚚 **Система курьеров Каира**: Станьте курьером и зарабатывайте на доставке
- 🔍 **Поиск**: Поиск по всему контенту
- 📞 **Связь с админом**: Прямая отправка сообщений администрации
- ⚙️ **Настройки**: Управление языком, гражданством, уведомлениями
- 🔗 **Inline-кнопки**: Прямые ссылки на ресурсы в категориях

#### Возможности админского бота:
- 📚 **Управление категориями**: Создание, редактирование, удаление, переключение категорий
- 🔗 **Управление кнопками**: Добавление кастомных кнопок с URL в любую категорию
- 🏢 **Управление услугами**: Одобрение/отклонение заявок на услуги
- 👥 **Управление пользователями**: Бан/разбан, назначение админов, статистика
- 🚚 **Управление курьерами**: Верификация, приостановка, управление курьерами Каира
- 📢 **Система рассылок**: Отправка сообщений всем или фильтрованным группам
- 📊 **Статистика**: Комплексная аналитика
- ⚙️ **Системные настройки**: Включение/отключение функций
- 🔍 **Парсер контента**: Извлечение информации из result.json
- 📋 **Логи действий**: Все действия логируются с деталями

### 🛠️ Технологический стек

- **Python**: 3.11+
- **aiogram**: 3.4.1 (Telegram Bot API)
- **SQLAlchemy**: 2.0.27 (ORM)
- **aiosqlite**: 0.19.0 (Асинхронный SQLite)
- **Pydantic**: 2.6.1 (Управление настройками)
- **FastAPI**: 0.109.0 (веб-фреймворк для Telegram Web App)
- **Uvicorn**: 0.27.0 (ASGI-сервер)
- **Jinja2**: 3.1.3 (шаблонизатор для веб-интерфейсов)
- **Telegraph**: 2.2.0 (Длинные статьи)

### 🚀 Установка

1. **Клонировать репозиторий**:
```bash
git clone <repository-url>
cd bot
```

2. **Установить зависимости**:
```bash
pip install -r requirements.txt  # включает FastAPI, Uvicorn, python-multipart, Jinja2
```

3. **Настроить окружение**:
```bash
cp .env.example .env
# Отредактировать .env с вашими токенами и ID админов
```

4. **Запустить систему**:
```bash
python main.py
```

### ⚙️ Конфигурация

Отредактируйте файл `.env`:

```env
USER_BOT_TOKEN=токен_пользовательского_бота
ADMIN_BOT_TOKEN=токен_админского_бота
DATABASE_URL=sqlite+aiosqlite:///./bot_database.db
ADMIN_IDS=123456789,987654321
LOG_LEVEL=INFO
LOG_FILE=bot.log

# Настройки веб-приложения (для Telegram Web App)
WEBAPP_HOST=0.0.0.0
WEBAPP_PORT=8000
WEBAPP_PUBLIC_URL=http://localhost:8000
WEBAPP_URL=https://ваш-домен.com/webapp  # Публичный HTTPS URL для кнопки Web App
WEBAPP_CORS_ORIGINS=    # разрешенные источники через запятую (необязательно)
```

**Получение токенов ботов:**
1. Напишите [@BotFather](https://t.me/botfather) в Telegram
2. Создайте два бота: `/newbot`
3. Скопируйте токены в `.env`

**ID администраторов:**
- Ваш Telegram ID (получите у [@userinfobot](https://t.me/userinfobot))
- Через запятую для нескольких админов

### 📚 Использование

#### Пользовательский бот

1. **Старт**: `/start`
2. **Выбор языка**: Русский или Узбекский
3. **Выбор гражданства**: UZ, RU, KZ или KG
4. **Главное меню**:
   - 🌍 Путник - Открыть веб-приложение
   - 📄 Документы - Информация по гражданству
   - 🚚 Доставка - Услуги доставки
   - 🔔 Потеря - Сообщить о потерях
   - 🚨 Полиция - Алерты о безопасности
   - 👨‍💼 Написать админу - Отправить сообщение
   - ⚙️ Настройки - Изменить предпочтения
5. **Команда WebApp**: Используйте `/webapp` для прямого доступа к веб-приложению

#### Админский бот

1. **Старт**: `/start` (только для ID админов)
2. **Главное меню**:
   - 📚 Управление категориями
   - 🔗 Управление кнопками
   - 🏢 Управление услугами
   - 👥 Управление пользователями
   - 🚚 Управление курьерами
   - 📢 Рассылка
   - 📊 Статистика
   - ⚙️ Настройки
   - 🔍 Анализ контента

### 🌐 Web App — Веб-приложение

#### Обзор

Веб-приложение Telegram предоставляет богатый интерфейс для просмотра контента:
- **Динамические категории**: Иерархическая структура с гибкими элементами
- **Встроенный админ-редактор**: Визуальное управление контентом прямо в Web App
- **Загрузка файлов**: Поддержка изображений, документов и видео с валидацией
- **Адаптивный дизайн**: Оптимизировано для мобильных и десктопных клиентов Telegram

#### Для пользователей

Доступ к Web App осуществляется через:
1. Кнопку меню: **🌍 Путник / WebApp**
2. Команду: `/webapp`
3. Прямую ссылку: значение `WEBAPP_URL` из `.env`

Пользовательский интерфейс предоставляет:
- **Категории**: Просмотр рубрик с описаниями и обложками
- **Типы контента**: Тексты, изображения, видео, документы, кнопки навигации
- **Форматирование**: Поддержка базового markdown
- **Темы**: Автоматическое переключение между светлой и темной темой Telegram

#### Для администраторов

Админы видят дополнительные элементы управления:

- Переключатель режимов «Редактирование / Просмотр»
- Управление категориями (создание, редактирование, удаление, сортировка, обложки)
- Управление элементами (TEXT, IMAGE, VIDEO, DOCUMENT, LINK, BUTTON)
- Перетаскивание/сортировка элементов
- Встроенная загрузка файлов с извлечением размеров изображений
- Тосты с результатами операций и подтверждения перед удалением

#### Переменные окружения

```env
# Основные настройки Web App
WEBAPP_HOST=0.0.0.0                              # Хост для FastAPI
WEBAPP_PORT=8000                                 # Порт сервера
WEBAPP_PUBLIC_URL=http://localhost:8000          # База для статических файлов и ссылок
WEBAPP_URL=https://ваш-домен.com/webapp          # Публичная HTTPS ссылка для кнопки в боте

# Дополнительные настройки
WEBAPP_CORS_ORIGINS=https://example.com          # Разрешённые origin'ы (опционально)
WEBAPP_DEBUG_SKIP_AUTH=false                     # Пропуск авторизации (только для локалки)
WEBAPP_DEBUG_USER_ID=12345                       # Пользователь по умолчанию в debug-режиме
WEBAPP_UPLOAD_DIR=webapp/uploads                 # Каталог для загруженных файлов
WEBAPP_MAX_UPLOAD_SIZE=10485760                  # Максимальный размер файла (10 МБ)
```

> ⚠️ `WEBAPP_URL` в продакшене обязательно должен указывать на HTTPS — Telegram Web App не работает по HTTP.

#### Запуск Web App

Веб-приложение запускается автоматически вместе с ботами командой `python main.py`.

Для разработки можно поднять только Web App:

```bash
pip install -r requirements.txt
uvicorn webapp.server:create_app --factory --host 0.0.0.0 --port 8000 --reload
```

#### Тестирование

```bash
# Полный прогон
pytest

# Только тесты Web App
pytest tests/test_webapp_*.py -v

# Покрытие
pytest --cov=webapp --cov=services.webapp_content_service tests/test_webapp_*.py

# Дополнительно (если настроены линтеры)
ruff check .
# или
flake8
```

Категории тестов:
- `test_webapp_auth.py` — аутентификация и права доступа
- `test_webapp_categories.py` — пользовательские эндпоинты категорий
- `test_webapp_admin.py` — админские CRUD операции
- `test_webapp_service.py` — сервисный слой (новый)
- `test_webapp_integration.py` — сквозные сценарии (новый)
- `test_webapp_file_upload.py` — загрузка и очистка файлов (новый)
- Другие тесты Web App остаются для совместимости

Заfixtures и утилиты отвечают `tests/conftest.py`. Для ручного тестирования следуйте чек-листу `WEBAPP_USER_UI_QA_CHECKLIST.md`.

#### Безопасность и логирование

1. **HTTPS обязателен** для публичного доступа
2. **initData проверяется** для каждого запроса (подписанные данные Telegram)
3. **Права администратора** проверяются на стороне API (`user.is_admin`)
4. **Валидация файлов**: MIME-типы и размер
5. **Debug-режим** (`WEBAPP_DEBUG_SKIP_AUTH`) нельзя включать в продакшене
6. Логи пишутся на русском языке через `utils.logger` с emoji-иконками статуса

#### Развёртывание

1. Настройте `WEBAPP_URL` на публичный HTTPS-домен
2. `WEBAPP_PUBLIC_URL` должен совпадать с адресом, откуда доступны статические файлы
3. Настройте прокси (Nginx, Caddy и т.д.) для HTTPS и статики `/webapp/static`, `/webapp/uploads`
4. Проверьте лимит загрузок (`WEBAPP_MAX_UPLOAD_SIZE`) и дисковое пространство
5. Добавьте домен в настройках BotFather (Web App URL)
6. Протестируйте с реальными клиентами Telegram (iOS, Android, Desktop)

Подробнее об архитектуре см. `docs/webapp.md`.

### 🔧 Разработка

**Добавление категорий:**
1. Админ бот → Управление категориями → Добавить
2. Ввести название (RU/UZ), описание, выбрать тип
3. Установить родительскую категорию для иерархии

**Добавление inline-кнопок:**
1. Админ бот → Управление кнопками → Добавить
2. Выбрать категорию
3. Ввести текст кнопки (RU/UZ) и URL
4. Кнопки появляются в пользовательском боте

**Одобрение услуг:**
1. Админ бот → Управление услугами → На модерации
2. Просмотр заявок
3. Одобрить или Отклонить

**Рассылка:**
1. Админ бот → Рассылка → Создать
2. Ввести сообщение (RU/UZ)
3. Выбрать фильтр (все/язык/гражданство/курьеры)
4. Подтвердить и отправить

### 📊 Статистика

Админская панель показывает:
- Всего пользователей, новых сегодня, по языкам/гражданству
- Всего категорий, кнопок, элементов контента
- Заявки на услуги (одобрено/на модерации/отклонено)
- Статистику курьеров (активные, доставки, рейтинги)
- Аналитику сообщений

### 🌟 Система курьеров

**Доставка в Каире:**
- Пользователи могут стать курьерами одним кликом
- Отслеживание доставок и рейтингов
- Доставка по зонам (Наср Сити, Гелиополис, Маади и др.)
- Статистика для курьеров

### 📝 Логирование

Все действия админов логируются:
- Тип действия (CREATE, UPDATE, DELETE, APPROVE и др.)
- Тип сущности (CATEGORY, BUTTON, SERVICE и др.)
- Временная метка и ID админа
- Детальные изменения в формате JSON

### 🔐 Безопасность

- Доступ к админ-боту только для админов
- Система блокировки пользователей
- Переключатели функций для сервисов
- Валидация ввода (URL, телефоны и др.)

### 🐛 Устранение неполадок

**Бот не отвечает:**
- Проверьте токены ботов в `.env`
- Убедитесь, что боты не остановлены в BotFather
- Проверьте логи: `tail -f bot.log`

**Ошибки базы данных:**
- Удалите `bot_database.db` и перезапустите
- Проверьте установку SQLite

**Ошибки импорта:**
- Переустановите зависимости: `pip install -r requirements.txt --upgrade`

### 👥 Контакты

По вопросам и предложениям: создайте issue в репозитории.

### 📄 Лицензия

Этот проект лицензирован под MIT License.

---

**Developed with ❤️ for Al-Azhar and Dirassa students**
