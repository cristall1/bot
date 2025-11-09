"""Tests for Telegram WebApp authentication helper"""

import hashlib
import hmac
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
import sys

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from webapp.auth import validate_telegram_webapp_data, TelegramAuthError


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


def test_validate_telegram_webapp_data_success():
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

    validated = validate_telegram_webapp_data(init_data, bot_token)

    assert validated["user"]["id"] == user_data["id"]
    assert validated["user"]["username"] == user_data["username"]
    assert validated["auth_date"] == str(auth_date)


def test_validate_telegram_webapp_data_invalid_hash():
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

    # Corrupt the hash (replace with zeros)
    init_parts = []
    for part in init_data.split("&"):
        if part.startswith("hash="):
            init_parts.append("hash=" + "0" * 64)
        else:
            init_parts.append(part)
    tampered_init_data = "&".join(init_parts)

    try:
        validate_telegram_webapp_data(tampered_init_data, bot_token)
        assert False, "Expected TelegramAuthError for invalid hash"
    except TelegramAuthError as exc:
        assert "Неверная подпись" in str(exc)


def test_validate_telegram_webapp_data_expired_auth_date():
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
        assert False, "Expected TelegramAuthError for expired auth data"
    except TelegramAuthError as exc:
        assert "устарел" in str(exc)
