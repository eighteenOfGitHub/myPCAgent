from cryptography.fernet import Fernet, InvalidToken
from config.env_config import env_config

_fernet = Fernet(env_config.FERNET_KEY.encode("utf-8"))

def encrypt_text(plain_text: str | None) -> str:
    if not plain_text:
        return ""
    return _fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")

def decrypt_text(token: str | None) -> str:
    if not token:
        return ""
    try:
        return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        # Fallback for legacy/plaintext input
        return token
