"""Centralized project settings.

Copy .env.example to .env and fill in values for your test environment.
ENV supports: test / staging / prod.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env", override=False)

ENV = os.getenv("ENV", "test").strip().lower()
VALID_ENVS = ("test", "staging", "prod")
if ENV not in VALID_ENVS:
    raise ValueError(f"Invalid ENV={ENV!r}; expected one of {VALID_ENVS}")

_PREFIX = ENV.upper()
BASE_URL = os.getenv(f"{_PREFIX}_BASE_URL", "").strip().rstrip("/")
AUTH_TOKEN = os.getenv(f"{_PREFIX}_AUTH_TOKEN", "").strip()

# Keep import/pytest collection possible before a developer creates .env.
# ApiClient validates BASE_URL when a request client is instantiated.
DEFAULT_HEADERS = {
    "content-type": "application/json",
    "Language": os.getenv("LANGUAGE", "zh"),
    "Lang": os.getenv("LANG", "zh"),
    "device-type": os.getenv("DEVICE_TYPE", "ios"),
    "device-brand": os.getenv("DEVICE_BRAND", "Apple"),
    "device-manufacturer": os.getenv("DEVICE_MANUFACTURER", "Apple"),
    "device-model": os.getenv("DEVICE_MODEL", "iPad Pro 12-Inch 3"),
    "device-system-name": os.getenv("DEVICE_SYSTEM_NAME", "iPadOS"),
    "device-os-version": os.getenv("DEVICE_OS_VERSION", "18.5"),
    "app-version": os.getenv("APP_VERSION", "1.0.0"),
    "app-build-number": os.getenv("APP_BUILD_NUMBER", "1"),
    "app-package-name": os.getenv("APP_PACKAGE_NAME", "com.example.autotest"),
}

# Device identifiers are optional and should be configured locally where required.
DEVICE_ID = os.getenv("DEVICE_ID", "").strip()
FCM_DEVICE_TOKEN = os.getenv("FCM_DEVICE_TOKEN", "").strip()
if DEVICE_ID:
    DEFAULT_HEADERS["device-id"] = DEVICE_ID
if FCM_DEVICE_TOKEN:
    DEFAULT_HEADERS["fcm-device-token"] = FCM_DEVICE_TOKEN
if AUTH_TOKEN:
    DEFAULT_HEADERS["Authorization"] = AUTH_TOKEN

LOGIN_FINGERPRINT = os.getenv("LOGIN_FINGERPRINT", "").strip()
