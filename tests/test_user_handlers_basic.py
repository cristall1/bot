"""
Basic smoke tests for new user handlers
"""

import pytest
from models import AlertType
from locales import t

def test_alert_types_exist():
    """Test that all 11 alert types exist"""
    expected_types = [
        AlertType.SHURTA,
        AlertType.MISSING_PERSON,
        AlertType.LOST_ITEM,
        AlertType.SCAM_WARNING,
        AlertType.MEDICAL_EMERGENCY,
        AlertType.ACCOMMODATION_NEEDED,
        AlertType.RIDE_SHARING,
        AlertType.JOB_POSTING,
        AlertType.LOST_DOCUMENT,
        AlertType.EVENT_ANNOUNCEMENT,
        AlertType.COURIER_NEEDED
    ]
    
    # Check we have exactly 11
    all_alert_types = list(AlertType)
    assert len(all_alert_types) == 11, f"Expected 11 alert types, got {len(all_alert_types)}"
    
    # Check all expected types exist
    for alert_type in expected_types:
        assert alert_type in AlertType


def test_alert_type_translations_ru():
    """Test that all alert types have RU translations"""
    for alert_type in AlertType:
        key = f"alert_type_{alert_type.value.lower()}"
        translation = t(key, "RU")
        # Should not return the key itself (means translation missing)
        assert translation != key, f"Missing RU translation for {key}"
        # Should have content
        assert len(translation) > 0, f"Empty RU translation for {key}"


def test_alert_type_translations_uz():
    """Test that all alert types have UZ translations"""
    for alert_type in AlertType:
        key = f"alert_type_{alert_type.value.lower()}"
        translation = t(key, "UZ")
        # Should not return the key itself (means translation missing)
        assert translation != key, f"Missing UZ translation for {key}"
        # Should have content
        assert len(translation) > 0, f"Empty UZ translation for {key}"


def test_alert_menu_translations():
    """Test alert menu translations"""
    keys = [
        "alert_menu_title",
        "alert_select_type",
        "alert_title_prompt",
        "alert_description_prompt",
        "alert_phone_prompt",
        "alert_location_prompt",
        "alert_photo_prompt",
        "alert_skip_photo",
        "alert_created"
    ]
    
    for key in keys:
        ru = t(key, "RU")
        uz = t(key, "UZ")
        
        assert ru != key, f"Missing RU translation for {key}"
        assert uz != key, f"Missing UZ translation for {key}"
        assert len(ru) > 0, f"Empty RU translation for {key}"
        assert len(uz) > 0, f"Empty UZ translation for {key}"


def test_settings_translations():
    """Test settings menu translations"""
    keys = [
        "settings_alert_preferences",
        "settings_alert_prefs_title",
        "alert_pref_enabled",
        "alert_pref_disabled"
    ]
    
    for key in keys:
        ru = t(key, "RU")
        uz = t(key, "UZ")
        
        assert ru != key, f"Missing RU translation for {key}"
        assert uz != key, f"Missing UZ translation for {key}"


def test_category_translations():
    """Test category navigation translations"""
    keys = [
        "category_back",
        "category_main_menu",
        "category_no_content",
        "category_select"
    ]
    
    for key in keys:
        ru = t(key, "RU")
        uz = t(key, "UZ")
        
        assert ru != key, f"Missing RU translation for {key}"
        assert uz != key, f"Missing UZ translation for {key}"
