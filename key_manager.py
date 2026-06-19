import os
from typing import Optional

from cryptography.fernet import Fernet

from config import settings

KEYFILE_PATH = os.path.join(settings.DATA_DIR, ".keyfile")


def _ensure_data_dir() -> None:
    os.makedirs(settings.DATA_DIR, exist_ok=True)


def generate_key() -> bytes:
    return Fernet.generate_key()


def create_key_if_missing() -> bytes:
    _ensure_data_dir()
    env_key = os.getenv("ENMASK_MASTER_KEY")
    if env_key:
        return env_key.encode("utf-8")
    if os.path.exists(KEYFILE_PATH):
        with open(KEYFILE_PATH, "rb") as handler:
            return handler.read().strip()

    key = generate_key()
    with open(KEYFILE_PATH, "wb") as handler:
        handler.write(key)
    try:
        os.chmod(KEYFILE_PATH, 0o600)
    except (AttributeError, PermissionError, OSError):
        pass
    return key


def load_key() -> bytes:
    _ensure_data_dir()
    env_key = os.getenv("ENMASK_MASTER_KEY")
    if env_key:
        key = env_key.encode("utf-8")
        if validate_key(key):
            return key
    if not os.path.exists(KEYFILE_PATH):
        return create_key_if_missing()
    with open(KEYFILE_PATH, "rb") as handler:
        key = handler.read().strip()
    if not validate_key(key):
        raise ValueError("La llave almacenada no es válida para Fernet.")
    return key


def validate_key(key: Optional[bytes]) -> bool:
    if not key:
        return False
    try:
        Fernet(key)
        return True
    except Exception:
        return False


def rotate_key() -> bytes:
    _ensure_data_dir()
    key = generate_key()
    with open(KEYFILE_PATH, "wb") as handler:
        handler.write(key)
    try:
        os.chmod(KEYFILE_PATH, 0o600)
    except (AttributeError, PermissionError, OSError):
        pass
    return key
