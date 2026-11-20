"""
Settings for the secure backend

Secrets:
  FIELD_ENCRYPTION_KEY: Fernet key used to encrypt personal/health fields at rest
  BLIND_INDEX_KEY: HMAC key used to look up users by email without storing it in plaintext
  JWT_SECRET: HMAC key used to sign session tokens

These secrets are read from env vars. If they are missing, a random value is generated once and saved to secure_backend/.secrets.json which is gitignored

In a real live deployment these secrets would be in a key management service ex. Hashicorp Vault
"""
import json
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent
SECRETS_FILE = BASE_DIR / ".secrets.json"

DATABASE_URL = os.environ.get("SECURE_DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'secure_app.db'}")
FRONTEND_FILE = BASE_DIR.parent / "frontend" / "newWebpage.html"

TOKEN_TTL_MINUTES = int(os.environ.get("TOKEN_TTL_MINUTES", "30"))
MAX_FAILED_LOGINS = int(os.environ.get("MAX_FAILED_LOGINS", "5"))
LOCKOUT_MINUTES = int(os.environ.get("LOCKOUT_MINUTES", "15"))
RATE_LIMIT_PER_MINUTE = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "30"))
AUDIT_RETENTION_DAYS = int(os.environ.get("AUDIT_RETENTION_DAYS", "365"))
PRIVACY_POLICY_VERSION = "2026-11-01"


def _load_secrets() -> dict:
    stored = {}
    # try to get secrets
    if SECRETS_FILE.exists():
        stored = json.loads(SECRETS_FILE.read_text())

    generators = {
        "FIELD_ENCRYPTION_KEY": lambda: Fernet.generate_key().decode(),
        "BLIND_INDEX_KEY": lambda: secrets.token_urlsafe(32),
        "JWT_SECRET": lambda: secrets.token_urlsafe(32),
    }
    values, changed = {}, False
    for name, gen in generators.items():
        if os.environ.get(name):
            values[name] = os.environ[name]
        elif name in stored:
            values[name] = stored[name]
        else:
            values[name] = stored[name] = gen()
            changed = True

    if changed:
        SECRETS_FILE.write_text(json.dumps(stored, indent=2))
        os.chmod(SECRETS_FILE, 0o600)
        print(f"[config] Generated new secret keys in {SECRETS_FILE.name}, the file should be kept private")
    return values


_secrets = _load_secrets()
FIELD_ENCRYPTION_KEY: str = _secrets["FIELD_ENCRYPTION_KEY"]
BLIND_INDEX_KEY: bytes = _secrets["BLIND_INDEX_KEY"].encode()
JWT_SECRET: str = _secrets["JWT_SECRET"]
