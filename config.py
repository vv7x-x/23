"""
config.py

Secure configuration helper.

Best practice: never hard-code credentials in source. Use environment variables
on PythonAnywhere (Web -> Environment variables) or use OAuth tokens.
"""
import os
from typing import Tuple


def get_instagram_credentials() -> Tuple[str, str]:
    """Return (username, password) from environment variables.

    Raises RuntimeError if not set. Callers should handle the error and
    avoid printing secrets to logs.
    """
    user = os.environ.get("INSTA_USER")
    pwd = os.environ.get("INSTA_PASS")
    if not user or not pwd:
        raise RuntimeError("Instagram credentials not set. Set INSTA_USER and INSTA_PASS environment variables.")
    return user, pwd


def get_default_context() -> str:
    return os.environ.get("N0X_DEFAULT_CONTEXT", "أنا ماسح إنستا ومبخش كتير")


def is_production() -> bool:
    return os.environ.get("N0X_ENV", "dev").lower() == "prod"
