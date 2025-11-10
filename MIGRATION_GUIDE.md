# Migration Guide - Руководство по миграции

## 🚀 Быстрый старт

### 1. Проверьте зависимости

```bash
pip install -r requirements.txt
```

### 2. Инициализируйте динамическое меню

```bash
python3 init_dynamic_menu.py
```

Это создаст:
- ✅ Меню "TALIM" с фильтром "Гражданство"
- ✅ Опции фильтра: Узбекистан 🇺🇿, Россия 🇷🇺, Казахстан 🇰🇿
- ✅ Меню "DOSTAVKA"

### 3. Запустите боты

```bash
python3 main.py
```

## 📊 Что изменилось

### Модели БД

#### Новые таблицы:

- `main_menu` - Главное меню (TALIM, DOSTAVKA)
- `menu_filters` - Фильтры меню
- `menu_filter_options` - Опции фильтров
- `category_content` - Контент категорий (отдельная таблица)

#### Изменения в существующих таблицах:

**Category:**
- ❌ Удалено: `key`, `content_type`, `text_content_ru`, `text_content_uz`, `photo_file_id`, `audio_file_id`, `pdf_file_id`, `link_url`, `location_type`, `location_address`, `latitude`, `longitude`, `geo_name`, `maps_url`, `button_type`
- ✅ Добавлено: `main_menu_id`, `parent_category_id`, `filter_option_id`
- ✅ Переименовано: `parent_id` → `parent_category_id`

**CategoryButton:**
- ❌ Удалено: `button_value`
- ✅ Добавлено: `action_data` (JSON)
- ✅ Изменено: `button_type` теперь `url` или `next_category`

### Сервисы

#### Новые:

- `services/dynamic_menu_service.py` - DynamicMenuService, MenuFilterService, MenuFilterOptionService, CategoryContentService

#### Обновленные:

- `services/category_service.py`:
  - ❌ Удалено: `get_category_by_key()`
  - ✅ Добавлено: `get_categories_by_menu()`
  - ✅ Обновлено: `create_category()` теперь требует `main_menu_id`

### Хендлеры

#### Новые:

- `bots/handlers/user_navigation_handlers.py` - ONE MESSAGE навигация для пользователей
- `bots/handlers/admin_dynamic_menu_handlers.py` - ONE MESSAGE управление меню

#### Обновленные:

- `bots/user_bot.py` - добавлен `user_navigation_handlers.router`
- `bots/admin_bot.py` - добавлен `admin_dynamic_menu_handlers.router`

## ⚠️ Breaking Changes

### CategoryService

**До:**
```python
category = await CategoryService.create_category(
    session,
    key="talim",
    name_ru="TALIM",
    name_uz="Ta'lim"
)
```

**После:**
```python
category = await CategoryService.create_category(
    session,
    main_menu_id=1,  # ID главного меню
    name_ru="Учебники",
    name_uz="Darsliklar"
)
```

### CategoryButton

**До:**
```python
button = CategoryButton(
    button_type="LINK",
    button_value="https://example.com"
)
```

**После:**
```python
button = CategoryButton(
    button_type="url",
    action_data={"url": "https://example.com"}
)
```

### User Navigation

**До:**
```python
# Множество сообщений при навигации
await message.answer("Выберите категорию...")
await message.answer("Выберите подкатегорию...")
await message.answer("Контент...")
```

**После:**
```python
# ОДНО сообщение, обновляется при навигации
text, markup = await build_category_view(category_id, lang)
await callback.message.edit_text(text, reply_markup=markup)
```

## 🔄 Миграция данных

### Если у вас есть старые категории с `key`:

```python
# Пример миграции
async def migrate_old_categories():
    async with AsyncSessionLocal() as session:
        # 1. Создайте главное меню
        talim = await DynamicMenuService.create_menu(
            session, "TALIM", "Ta'lim", "📚"
        )
        
        # 2. Мигрируйте старые категории
        old_categories = await session.execute(
            select(OldCategory).where(OldCategory.key == "talim")
        )
        
        for old_cat in old_categories:
            # Создайте новую категорию
            new_cat = await CategoryService.create_category(
                session,
                main_menu_id=talim.id,
                name_ru=old_cat.name_ru,
                name_uz=old_cat.name_uz
            )
            
            # Мигрируйте контент
            if old_cat.text_content_ru:
                await CategoryContentService.create_content(
                    session,
                    category_id=new_cat.id,
                    content_type="text",
                    text_ru=old_cat.text_content_ru,
                    text_uz=old_cat.text_content_uz
                )
```

## ✅ Проверка работоспособности

### 1. Проверьте БД

```python
async with AsyncSessionLocal() as session:
    menus = await DynamicMenuService.get_all_menus(session)
    print(f"Меню: {len(menus)}")
    
    for menu in menus:
        print(f"- {menu.name_ru}")
        print(f"  Фильтры: {len(menu.filters)}")
        print(f"  Категории: {len(menu.categories)}")
```

### 2. Проверьте User Bot

1. Запустите бота
2. Нажмите кнопку "📚 TALIM"
3. Должно появиться ОДНО сообщение с фильтрами и категориями
4. Выберите фильтр → сообщение обновится
5. Выберите категорию → сообщение обновится

### 3. Проверьте Admin Bot

1. Запустите админ бота
2. Перейдите в "Управление → Dynamic Menu"
3. Должен отобразиться список меню
4. Нажмите "✏️ Edit" на TALIM
5. Попробуйте добавить фильтр

## 🐛 Возможные проблемы

### Ошибка: "No such column: categories.key"

**Причина**: Старая БД без миграции

**Решение**:
```bash
# Пересоздайте БД (только для разработки!)
rm bot_database.db
python3 init_dynamic_menu.py
```

### Ошибка: "MainMenu table not found"

**Причина**: Таблицы не созданы

**Решение**:
```python
# В Python консоли
from database import engine, Base
import models
Base.metadata.create_all(bind=engine)
```

### Ошибка: "category.key not found"

**Причина**: Старый код использует `get_category_by_key()`

**Решение**: Замените на `get_categories_by_menu()`

## 📝 Рекомендации

1. ✅ **Тестируйте на копии БД** перед миграцией production
2. ✅ **Создайте backup** перед миграцией
3. ✅ **Обновите все зависимости** старого кода
4. ✅ **Проверьте работу** всех функций после миграции
5. ✅ **Обновите документацию** для вашей команды

## 🎉 Готово!

После миграции ваш бот будет использовать новую динамическую систему меню!

## 📞 Поддержка

- 📖 Документация: `DYNAMIC_MENU_README.md`
- 🐛 Issues: Создайте issue в репозитории
- 💬 Вопросы: Напишите в чат команды
