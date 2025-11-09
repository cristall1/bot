LOCALES = {
    "RU": {
        # Welcome & Language Selection
        "welcome": "Добро пожаловать! 👋",
        "choose_language": "Выберите язык:",
        "language_selected": "✅ Язык установлен: Русский",
        
        # Main Menu (7 buttons)
        "main_menu": "🏠 Главное меню",
        "menu_documents": "🗂️ Категории",
        "menu_delivery": "🚚 Доставка",
        "menu_notifications": "🔔 Потеря",
        "menu_shurta": "🚨 Полиция",
        "menu_admin_contact": "👨‍💼 Написать админу",
        "menu_settings": "⚙️ Настройки",
        "menu_webapp": "🌍 Путник",
        
        # Documents (Hujjat Yordami)
        "documents_title": "📄 Помощь с документами",
        "select_citizenship": "Выберите гражданство:",
        "citizenship_uz": "🇺🇿 Узбекистан",
        "citizenship_ru": "🇷🇺 Россия",
        "citizenship_kz": "🇰🇿 Казахстан",
        "citizenship_kg": "🇰🇬 Кыргызстан",
        "no_documents": "Документы для этой страны еще не добавлены.",
        "document_content": "📋 {title}",
        "back": "← Назад",
        "to_main_menu": "🏠 Главное меню",
        
        # Delivery (Dostavka)
        "delivery_title": "🚚 Служба доставки",
        "delivery_menu_create": "📦 Создать новый заказ",
        "delivery_menu_active": "🚚 Активные заказы",
        "delivery_menu_my_stats": "📊 Моя статистика",
        "delivery_create_desc": "💬 Что нужно доставить?",
        "delivery_location_choice": "📍 Как указать местоположение?",
        "delivery_location_text": "✏️ Текстовый адрес",
        "delivery_location_geo": "📍 Отправить геолокацию",
        "delivery_location_maps": "🗺 Google Maps ссылка",
        "delivery_create_phone": "📞 Контактный телефон:",
        "delivery_created": "✅ Заказ создан! Курьеры получили уведомление.",
        "delivery_accepted": "✅ Курьер принял ваш заказ!",
        "delivery_open_chat": "💬 Открыть чат с курьером",
        "delivery_take": "✅ Взять заказ",
        "delivery_reject": "❌ Отклонить",
        "delivery_taken": "✅ Заказ принят! Клиент получит уведомление.",
        "delivery_rejected": "❌ Заказ отклонен.",
        "delivery_already_taken": "Этот заказ уже взят другим курьером.",
        "delivery_no_active": "Нет активных заказов.",
        "delivery_become_courier": "🚚 Стать курьером",
        "delivery_courier_registered": "✅ Теперь вы курьер!",
        "delivery_stats_title": "📊 Статистика курьера",
        "delivery_stats_completed": "✅ Выполнено доставок: {count}",
        "delivery_stats_rating": "⭐ Рейтинг: {rating}/5.0",
        "delivery_stats_not_courier": "Вы еще не курьер.",
        "delivery_alert_new": "🚚 Новый заказ доставки!\n\n📦 {description}\n📍 {location}\n📞 {phone}",
        
        # Notifications (Propaja - Lost people/items)
        "notifications_title": "🔔 Потеря",
        "notifications_menu_lost_person": "👤 Пропал человек",
        "notifications_menu_lost_item": "📦 Потеря вещи",
        "notifications_lost_person_name": "👤 Имя пропавшего:",
        "notifications_lost_person_desc": "📝 Описание:",
        "notifications_lost_person_photo": "📷 Фото (необязательно):",
        "notifications_lost_person_location": "📍 Местоположение:",
        "notifications_lost_person_phone": "📞 Контактный телефон:",
        "notifications_lost_item_what": "📦 Что потеряно?",
        "notifications_lost_item_desc": "📝 Описание:",
        "notifications_lost_item_photo": "📷 Фото (необязательно):",
        "notifications_lost_item_location": "📍 Где потеряно?",
        "notifications_lost_item_phone": "📞 Контакт:",
        "notifications_location_choice": "📍 Как указать местоположение?",
        "notifications_location_text": "✏️ Текстовый адрес",
        "notifications_location_geo": "📍 Отправить геолокацию",
        "notifications_location_maps": "🗺 Google Maps ссылка",
        "notifications_created": "✅ Уведомление создано! Все пользователи получат его.",
        "notifications_skip_photo": "⏭ Пропустить",
        "notifications_alert_person": "🚨 ПРОПАЛ ЧЕЛОВЕК\n\n👤 {name}\n📝 {description}\n📍 {location}\n📞 {phone}",
        "notifications_alert_item": "🔔 ПОТЕРЯ ВЕЩИ\n\n📦 {what}\n📝 {description}\n📍 {location}\n📞 {phone}",
        
        # Shurta (Police)
        "shurta_title": "🚨 Полиция - Алерт",
        "shurta_description": "💬 Что произошло?",
        "shurta_location_choice": "📍 Как указать местоположение?",
        "shurta_location_maps": "🗺 Google Maps ссылка",
        "shurta_location_geo": "📍 Отправить геолокацию",
        "shurta_location_text": "✏️ Текстовый адрес",
        "shurta_location_input": "📍 Введите адрес (район/улица):",
        "shurta_location_geo_input": "📍 Отправьте вашу геолокацию:",
        "shurta_location_maps_input": "🗺️ Введите Google Maps ссылку:",
        "shurta_photo": "📷 Фото (необязательно):",
        "shurta_created": "✅ Алерт создан! Все пользователи уведомлены.",
        "shurta_alert": "🚨 ПОЛИЦИЯ - АЛЕРТ\n\n📝 {description}\n📍 {location}",
        
        # Admin Contact
        "admin_contact_title": "👨‍💼 Написать админу",
        "admin_contact_prompt": "💬 Напишите ваше сообщение:",
        "admin_contact_sent": "✅ Сообщение отправлено администратору!",
        
        # Settings
        "settings_title": "⚙️ Настройки",
        "settings_language": "🌐 Язык",
        "settings_notifications": "🔔 Уведомления",
        "settings_notifications_on": "✅ Включены",
        "settings_notifications_off": "❌ Выключены",
        "settings_change_language": "Сменить язык",
        "settings_toggle_notifications": "Переключить уведомления",
        "settings_notifications_enabled": "✅ Уведомления включены",
        "settings_notifications_disabled": "❌ Уведомления выключены",
        "settings_alert_preferences": "🔔 Типы уведомлений",
        "settings_alert_prefs_title": "🔔 Выберите типы уведомлений, которые хотите получать:",
        "alert_pref_enabled": "✅",
        "alert_pref_disabled": "❌",
        
        # 11 Alert Types
        "alert_type_shurta": "🚨 Полиция",
        "alert_type_missing_person": "👤 Пропал человек",
        "alert_type_lost_item": "📦 Потеря вещи",
        "alert_type_scam_warning": "⚠️ Мошенничество",
        "alert_type_medical_emergency": "🏥 Медпомощь",
        "alert_type_accommodation_needed": "🏠 Нужно жилье",
        "alert_type_ride_sharing": "🚗 Попутчики",
        "alert_type_job_posting": "💼 Вакансия",
        "alert_type_lost_document": "📄 Потеря документа",
        "alert_type_event_announcement": "🎉 Мероприятие",
        "alert_type_courier_needed": "📦 Нужен курьер",
        
        # Alert Creation
        "alert_menu_title": "📝 Создать объявление",
        "alert_select_type": "Выберите тип объявления:",
        "alert_title_prompt": "📝 Заголовок (имя, название, что?):",
        "alert_description_prompt": "📄 Описание:",
        "alert_phone_prompt": "📞 Телефон для связи:",
        "alert_location_prompt": "📍 Как указать местоположение?",
        "alert_photo_prompt": "📷 Фото (необязательно):",
        "alert_skip_photo": "⏭ Пропустить",
        "alert_created": "✅ Объявление создано! Отправлено на модерацию.",
        "alert_approved_notification": "✅ Ваше объявление одобрено и опубликовано!",
        "alert_rejected_notification": "❌ Ваше объявление отклонено. Причина: {reason}",
        
        # Categories & Navigation
        "category_back": "⬅️ Назад",
        "category_main_menu": "🏠 Главное меню",
        "category_no_content": "Контент пока не добавлен.",
        "category_select": "Выберите раздел:",
        
        # WebApp
        "webapp_title": "🌍 Путник",
        "webapp_description": "Откройте веб-приложение для удобного доступа к информации, категориям и контенту. Нажмите кнопку ниже для запуска:",
        
        # Common
        "error": "❌ Произошла ошибка. Попробуйте позже.",
        "cancel": "❌ Отмена",
        "cancelled": "❌ Отменено.",
        "invalid_input": "❌ Неверный ввод. Попробуйте снова.",
        "banned": "❌ Ваш аккаунт заблокирован.",
        "send": "✅ Отправить",
    },
    
    "UZ": {
        # Welcome & Language Selection
        "welcome": "Xush kelibsiz! 👋",
        "choose_language": "Tilni tanlang:",
        "language_selected": "✅ Til o'rnatildi: Oʻzbekcha",
        
        # Main Menu (7 buttons)
        "main_menu": "🏠 Asosiy menyu",
        "menu_documents": "🗂️ Kategoriyalar",
        "menu_delivery": "🚚 Dostavka xizmati",
        "menu_notifications": "🔔 Propaja",
        "menu_shurta": "🚨 Shurta",
        "menu_admin_contact": "👨‍💼 Admin bilan bog'lanish",
        "menu_settings": "⚙️ Sozlamalar",
        "menu_webapp": "🌍 Sayohat",
        
        # Documents (Hujjat Yordami)
        "documents_title": "📄 Hujjat yordami",
        "select_citizenship": "Fuqoroligingizni tanlang:",
        "citizenship_uz": "🇺🇿 Oʻzbekiston",
        "citizenship_ru": "🇷🇺 Rossiya",
        "citizenship_kz": "🇰🇿 Qozog'iston",
        "citizenship_kg": "🇰🇬 Qirg'iziston",
        "no_documents": "Bu mamlakat uchun hujjatlar hali qo'shilmagan.",
        "document_content": "📋 {title}",
        "back": "← Orqaga",
        "to_main_menu": "🏠 Asosiy menyu",
        
        # Delivery (Dostavka)
        "delivery_title": "🚚 Dostavka xizmati",
        "delivery_menu_create": "📦 Yangi zakaz yaratish",
        "delivery_menu_active": "🚚 Faol zakazlar",
        "delivery_menu_my_stats": "📊 Mening statistikam",
        "delivery_create_desc": "💬 Nima yetkazish kerak?",
        "delivery_location_choice": "📍 Joylashuvni qanday ko'rsatish?",
        "delivery_location_text": "✏️ Matnli manzil",
        "delivery_location_geo": "📍 Geolokatsiyani yuborish",
        "delivery_location_maps": "🗺 Google Maps havolasi",
        "delivery_create_phone": "📞 Kontakt telefon:",
        "delivery_created": "✅ Zakaz yaratildi! Kuryerlar xabardor qilindi.",
        "delivery_accepted": "✅ Kuryer zakazingizni qabul qildi!",
        "delivery_open_chat": "💬 Kuryer bilan chatni ochish",
        "delivery_take": "✅ Olish",
        "delivery_reject": "❌ Rad etish",
        "delivery_taken": "✅ Zakaz qabul qilindi! Mijoz xabardor qilindi.",
        "delivery_rejected": "❌ Zakaz rad etildi.",
        "delivery_already_taken": "Bu zakazni boshqa kuryer olgan.",
        "delivery_no_active": "Faol zakazlar yo'q.",
        "delivery_become_courier": "🚚 Kuryer bo'lish",
        "delivery_courier_registered": "✅ Endi siz kuryersiz!",
        "delivery_stats_title": "📊 Kuryer statistikasi",
        "delivery_stats_completed": "✅ Bajarilgan: {count}",
        "delivery_stats_rating": "⭐ Reyting: {rating}/5.0",
        "delivery_stats_not_courier": "Siz hali kuryer emassiz.",
        "delivery_alert_new": "🚚 Yangi zakaz!\n\n📦 {description}\n📍 {location}\n📞 {phone}",
        
        # Notifications (Propaja - Lost people/items)
        "notifications_title": "🔔 Propaja",
        "notifications_menu_lost_person": "👤 Propaja odam",
        "notifications_menu_lost_item": "📦 Propaja narsa",
        "notifications_lost_person_name": "👤 Yo'qolgan odamning ismi:",
        "notifications_lost_person_desc": "📝 Tavsif:",
        "notifications_lost_person_photo": "📷 Foto (ixtiyoriy):",
        "notifications_lost_person_location": "📍 Joylashuv:",
        "notifications_lost_person_phone": "📞 Kontakt telefon:",
        "notifications_lost_item_what": "📦 Nima yo'qoldi?",
        "notifications_lost_item_desc": "📝 Tavsif:",
        "notifications_lost_item_photo": "📷 Foto (ixtiyoriy):",
        "notifications_lost_item_location": "📍 Qayerda yo'qoldi?",
        "notifications_lost_item_phone": "📞 Kontakt:",
        "notifications_location_choice": "📍 Joylashuvni qanday ko'rsatish?",
        "notifications_location_text": "✏️ Matnli manzil",
        "notifications_location_geo": "📍 Geolokatsiyani yuborish",
        "notifications_location_maps": "🗺 Google Maps havolasi",
        "notifications_created": "✅ Xabarnoma yaratildi! Barcha foydalanuvchilar uni oladi.",
        "notifications_skip_photo": "⏭ O'tkazib yuborish",
        "notifications_alert_person": "🚨 ODAM YO'QOLDI\n\n👤 {name}\n📝 {description}\n📍 {location}\n📞 {phone}",
        "notifications_alert_item": "🔔 NARSA YO'QOLDI\n\n📦 {what}\n📝 {description}\n📍 {location}\n📞 {phone}",
        
        # Shurta (Police)
        "shurta_title": "🚨 Shurta - Ogohlantirish",
        "shurta_description": "💬 Nima sodir bo'ldi?",
        "shurta_location_choice": "📍 Joylashuvni qanday ko'rsatish?",
        "shurta_location_maps": "🗺 Google Maps havolasi",
        "shurta_location_geo": "📍 Geolokatsiyani yuborish",
        "shurta_location_text": "✏️ Matnli manzil",
        "shurta_location_input": "📍 Manzilni kiriting (tuman/ko'cha):",
        "shurta_location_geo_input": "📍 Geolokatsiyangizni yuboring:",
        "shurta_location_maps_input": "🗺️ Google Maps havolasini kiriting:",
        "shurta_photo": "📷 Foto (ixtiyoriy):",
        "shurta_created": "✅ Ogohlantirish yaratildi! Barcha foydalanuvchilar xabardor qilindi.",
        "shurta_alert": "🚨 SHURTA - OGOHLANTIRISH\n\n📝 {description}\n📍 {location}",
        
        # Admin Contact
        "admin_contact_title": "👨‍💼 Admin bilan bog'lanish",
        "admin_contact_prompt": "💬 Xabaringizni yozing:",
        "admin_contact_sent": "✅ Xabar administratorga yuborildi!",
        
        # Settings
        "settings_title": "⚙️ Sozlamalar",
        "settings_language": "🌐 Til",
        "settings_notifications": "🔔 Xabarnomalar",
        "settings_notifications_on": "✅ Yoqilgan",
        "settings_notifications_off": "❌ O'chirilgan",
        "settings_change_language": "Tilni o'zgartirish",
        "settings_toggle_notifications": "Xabarnomalarni almashtirish",
        "settings_notifications_enabled": "✅ Xabarnomalar yoqildi",
        "settings_notifications_disabled": "❌ Xabarnomalar o'chirildi",
        "settings_alert_preferences": "🔔 Xabarnoma turlari",
        "settings_alert_prefs_title": "🔔 Qaysi turdagi xabarnomalarni olishni xohlaysiz:",
        "alert_pref_enabled": "✅",
        "alert_pref_disabled": "❌",
        
        # 11 Alert Types
        "alert_type_shurta": "🚨 Politsiya",
        "alert_type_missing_person": "👤 Odam yo'qoldi",
        "alert_type_lost_item": "📦 Narsa yo'qoldi",
        "alert_type_scam_warning": "⚠️ Firibgarlik",
        "alert_type_medical_emergency": "🏥 Tibbiy yordam",
        "alert_type_accommodation_needed": "🏠 Uy-joy kerak",
        "alert_type_ride_sharing": "🚗 Yo'lovchi qidirish",
        "alert_type_job_posting": "💼 Ish taklifnomasi",
        "alert_type_lost_document": "📄 Hujjat yo'qoldi",
        "alert_type_event_announcement": "🎉 Tadbir e'loni",
        "alert_type_courier_needed": "📦 Kuryer kerak",
        
        # Alert Creation
        "alert_menu_title": "📝 E'lon yaratish",
        "alert_select_type": "E'lon turini tanlang:",
        "alert_title_prompt": "📝 Sarlavha (ism, nom, nima?):",
        "alert_description_prompt": "📄 Tavsif:",
        "alert_phone_prompt": "📞 Aloqa telefoni:",
        "alert_location_prompt": "📍 Joylashuvni qanday ko'rsatamiz?",
        "alert_photo_prompt": "📷 Foto (ixtiyoriy):",
        "alert_skip_photo": "⏭ O'tkazib yuborish",
        "alert_created": "✅ E'lon yaratildi! Moderatsiyaga yuborildi.",
        "alert_approved_notification": "✅ E'loningiz tasdiqlandi va e'lon qilindi!",
        "alert_rejected_notification": "❌ E'loningiz rad etildi. Sabab: {reason}",
        
        # Categories & Navigation
        "category_back": "⬅️ Orqaga",
        "category_main_menu": "🏠 Asosiy menyu",
        "category_no_content": "Kontent hali qo'shilmagan.",
        "category_select": "Bo'limni tanlang:",
        
        # WebApp
        "webapp_title": "🌍 Sayohat",
        "webapp_description": "Veb-ilovani ochib, barcha bo'limlar va yangiliklarga qulay kirish oling. Quyidagi tugmani bosing:",
        
        # Common
        "error": "❌ Xatolik yuz berdi. Keyinroq urinib ko'ring.",
        "cancel": "❌ Bekor qilish",
        "cancelled": "❌ Bekor qilindi.",
        "invalid_input": "❌ Noto'g'ri kiritish. Qayta urinib ko'ring.",
        "banned": "❌ Sizning akkauntingiz bloklangan.",
        "send": "✅ Yuborish",
    }
}


def t(key: str, lang: str = "RU", **kwargs) -> str:
    """
    Get translated string by key and language.
    
    Args:
        key: Translation key (e.g., "welcome", "main_menu")
        lang: Language code (RU or UZ)
        **kwargs: Format parameters for string formatting
    
    Returns:
        Translated and formatted string
    """
    lang = lang.upper() if lang else "RU"
    if lang not in LOCALES:
        lang = "RU"
    
    text = LOCALES[lang].get(key, key)
    
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    
    return text
