from typing import Any, Optional

from cryptography.fernet import Fernet

from key_manager import create_key_if_missing, load_key


def generate_key() -> bytes:
    return Fernet.generate_key()


def _get_fernet(key: Optional[bytes] = None) -> Fernet:
    return Fernet(key or load_key() or create_key_if_missing())


def encrypt_value(value: Any, key: Optional[bytes] = None) -> str:
    if value is None:
        return ""
    cipher = _get_fernet(key)
    return cipher.encrypt(str(value).encode("utf-8")).decode("utf-8")


def decrypt_value(token: Any, key: Optional[bytes] = None) -> str:
    if token is None:
        return ""
    cipher = _get_fernet(key)
    return cipher.decrypt(str(token).encode("utf-8")).decode("utf-8")
