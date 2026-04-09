import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from app.config import settings

_SALT = b"social_api_token_salt_v1"


def _derive_key(secret: str) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(secret.encode()))


_fernet = Fernet(_derive_key(settings.SECRET_KEY))


class TokenManager:
    @staticmethod
    def encrypt(token: str) -> str:
        return _fernet.encrypt(token.encode()).decode()

    @staticmethod
    def decrypt(encrypted: str) -> str:
        return _fernet.decrypt(encrypted.encode()).decode()


token_manager = TokenManager()
