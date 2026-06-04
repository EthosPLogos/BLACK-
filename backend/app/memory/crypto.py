"""
Transparent Fernet encryption for memory-at-rest.

When MEMORY_ENCRYPTION_KEY is set, load_memory/save_memory use this module
to encrypt/decrypt the JSON blob before touching disk. The key never appears
in the memory file itself.

Key generation (run once, store in backend/.env):
  python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""
from cryptography.fernet import Fernet, InvalidToken

from app.config import MEMORY_ENCRYPTION_KEY

_fernet: Fernet | None = None


def is_enabled() -> bool:
    return bool(MEMORY_ENCRYPTION_KEY)


def _get() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(MEMORY_ENCRYPTION_KEY.encode())
    return _fernet


def encrypt(plaintext: str) -> str:
    return _get().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _get().decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception) as exc:
        raise RuntimeError(
            "Memory decryption failed — MEMORY_ENCRYPTION_KEY may have changed or "
            f"the file is corrupt. Original error: {exc}"
        )
