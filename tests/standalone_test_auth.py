"""Standalone tests for Telegram WebApp authentication helper (no pytest needed)"""

import hashlib
import hmac
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _generate_init_data(bot_token: str, user_data: dict, auth_date: int, query_id: str) -> str:
    """Helper to generate signed initData string."""
    encoded_user = json.dumps(user_data, separators=(",", ":"))

    data_payload = {
        "auth_date": str(auth_date),
        "query_id": query_id,
        "user": encoded_user,
    }

    # Prepare data-check-string sorted by keys
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(data_payload.items()))

    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()

    data_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()

    signed_payload = {
        **data_payload,
        "hash": data_hash,
    }

    return urlencode(signed_payload)


# We'll import only after setting up the path
from webapp.auth import validate_telegram_webapp_data, TelegramAuthError


def test_validate_success():
    """Test successful validation"""
    print("Test 1: Valid initData validation")
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    user_data = {
        "id": 999,
        "first_name": "Ivan",
        "username": "ivan_the_test",
        "language_code": "ru",
    }
    auth_date = int(datetime.now().timestamp())

    init_data = _generate_init_data(
        bot_token=bot_token,
        user_data=user_data,
        auth_date=auth_date,
        query_id="AAH1pYdmAAAAANalh2bZ1IEl",
    )

    try:
        validated = validate_telegram_webapp_data(init_data, bot_token)
        assert validated["user"]["id"] == user_data["id"], "User ID mismatch"
        assert validated["user"]["username"] == user_data["username"], "Username mismatch"
        assert validated["auth_date"] == str(auth_date), "Auth date mismatch"
        print("✅ PASSED: Valid initData validated successfully")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    return True


def test_invalid_hash():
    """Test invalid hash rejection"""
    print("\nTest 2: Invalid hash rejection")
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    user_data = {
        "id": 555,
        "first_name": "Maria",
        "username": "maria_test",
        "language_code": "en",
    }
    auth_date = int(datetime.now().timestamp())

    init_data = _generate_init_data(
        bot_token=bot_token,
        user_data=user_data,
        auth_date=auth_date,
        query_id="AAH1pYdmAAAAANalh2bZ1IXx",
    )

    # Corrupt the hash
    init_parts = []
    for part in init_data.split("&"):
        if part.startswith("hash="):
            init_parts.append("hash=" + "0" * 64)
        else:
            init_parts.append(part)
    tampered_init_data = "&".join(init_parts)

    try:
        validate_telegram_webapp_data(tampered_init_data, bot_token)
        print("❌ FAILED: Should have rejected invalid hash")
        return False
    except TelegramAuthError as exc:
        if "Неверная подпись" in str(exc):
            print(f"✅ PASSED: Invalid hash rejected with message: {exc}")
            return True
        else:
            print(f"❌ FAILED: Wrong error message: {exc}")
            return False


def test_expired_auth_date():
    """Test expired auth date rejection"""
    print("\nTest 3: Expired auth date rejection")
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
    user_data = {
        "id": 777,
        "first_name": "Sergey",
        "username": "sergey_old",
        "language_code": "ru",
    }
    old_date = int((datetime.now() - timedelta(days=2)).timestamp())

    init_data = _generate_init_data(
        bot_token=bot_token,
        user_data=user_data,
        auth_date=old_date,
        query_id="AAH1pYdmAAAAANalh2bZ1IYZ",
    )

    try:
        validate_telegram_webapp_data(init_data, bot_token)
        print("❌ FAILED: Should have rejected expired auth date")
        return False
    except TelegramAuthError as exc:
        if "устарел" in str(exc):
            print(f"✅ PASSED: Expired auth date rejected with message: {exc}")
            return True
        else:
            print(f"❌ FAILED: Wrong error message: {exc}")
            return False


def test_missing_hash():
    """Test missing hash rejection"""
    print("\nTest 4: Missing hash rejection")
    init_data = "auth_date=123456&user=%7B%22id%22%3A123%7D"  # No hash parameter
    bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"

    try:
        validate_telegram_webapp_data(init_data, bot_token)
        print("❌ FAILED: Should have rejected missing hash")
        return False
    except TelegramAuthError as exc:
        if "hash" in str(exc).lower():
            print(f"✅ PASSED: Missing hash rejected with message: {exc}")
            return True
        else:
            print(f"❌ FAILED: Wrong error message: {exc}")
            return False


def test_real_telegram_sample():
    """Test with a real-world like sample"""
    print("\nTest 5: Real-world like sample")
    # This simulates a more realistic scenario
    bot_token = "7406237492:AAGiCnoZ2Caobsv9JQMpDjJZI5YOtianG18"
    user_data = {
        "id": 5912983856,
        "first_name": "Test User",
        "last_name": "Lastname",
        "username": "testuser",
        "language_code": "ru",
        "allows_write_to_pm": True
    }
    auth_date = int(datetime.now().timestamp())
    query_id = "AAHdF6IQAAAAAd0XohDhrOrc"

    init_data = _generate_init_data(
        bot_token=bot_token,
        user_data=user_data,
        auth_date=auth_date,
        query_id=query_id,
    )

    print(f"Generated initData: {init_data[:100]}...")

    try:
        validated = validate_telegram_webapp_data(init_data, bot_token)
        assert validated["user"]["id"] == user_data["id"]
        assert validated["user"]["first_name"] == user_data["first_name"]
        print("✅ PASSED: Real-world sample validated successfully")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Running Telegram WebApp Authentication Tests")
    print("=" * 60)
    
    results = []
    results.append(test_validate_success())
    results.append(test_invalid_hash())
    results.append(test_expired_auth_date())
    results.append(test_missing_hash())
    results.append(test_real_telegram_sample())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        sys.exit(1)
