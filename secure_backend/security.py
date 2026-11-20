# This uses argon2id hashing for passwords, and Fernet (AES-128-CBC and HMAC-SHA256) for field encryption for names, health data, etc
# emails use HMAC-SHA256, and JWT session tokens are used for authentication
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from cryptography.fernet import Fernet, InvalidToken

import config

# Argon2id with defaults, includes salting
_hasher = PasswordHasher()

# we calculate a dummy hash so that a failed login takes the same time whether or not the account exists.
# this prevents attackers using timining to see if a given email is known or not
_DUMMY_HASH = _hasher.hash("dummy-password-for-timing")

_fernet = Fernet(config.FIELD_ENCRYPTION_KEY.encode())

JWT_ALGORITHM = "HS256"


# passwords
def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


# reject passwords that appear in lists of commonly used or breached passwords
COMMON_PASSWORDS = {
    "password", "password1", "password123", "pass", "pass1", "pass123", "12345678", "123456789", "1234567890",
    "qwerty123", "qwertyuiop", "iloveyou", "11111111", "00000000", "abc12345"
}


def is_common_password(password: str) -> bool:
    return password.lower() in COMMON_PASSWORDS


# field encryption
def encrypt(value: str | None) -> str | None:
    if value is None:
        return None
    return _fernet.encrypt(value.encode()).decode()


def decrypt(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        # either the ciphertext was modified or the key is wrong
        raise ValueError("Encrypted field failed integrity check")


def normalize_email(email: str) -> str:
    return email.strip().lower()


def email_index(email: str) -> str:
    return hmac.new(config.BLIND_INDEX_KEY, normalize_email(email).encode(), hashlib.sha256).hexdigest()


# sessions
def create_token(user_id: int, role: str) -> tuple[str, str, datetime]:
    now = datetime.now(timezone.utc)
    expires = now + timedelta(minutes=config.TOKEN_TTL_MINUTES)

    jti = uuid.uuid4().hex

    payload = {"sub": str(user_id), "role": role, "iat": now, "exp": expires, "jti": jti}

    return jwt.encode(payload, config.JWT_SECRET, algorithm=JWT_ALGORITHM), jti, expires


def decode_token(token: str) -> dict:
    # algorithms is pinned so that an attacker cannot switch to none or another algorithm
    return jwt.decode(token, config.JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"require": ["exp", "sub", "jti"]})


def mask_ip(ip: str | None) -> str:
    # keep only the network part of an IP address
    # minimize data for logs
    if not ip:
        return "unknown"
    if ":" in ip: # for IPv6, only keep the first 3 groups
        return ":".join(ip.split(":")[:3]) + "::/48"
    parts = ip.split(".")
    return ".".join(parts[:3]) + ".0/24" if len(parts) == 4 else "unknown"
