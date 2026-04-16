import base64
import hashlib
import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG", "False") == "True"

# Vault: Fernet key for VaultEntry password encryption. Set ENTRY_ENCRYPTION_KEY in .env for production.
# In DEBUG, if unset, derive a stable key from SECRET_KEY so local dev works without extra env vars.
_vault_enc = (os.getenv("ENTRY_ENCRYPTION_KEY") or "").strip()
if not _vault_enc and DEBUG and SECRET_KEY:
    _vault_enc = base64.urlsafe_b64encode(
        hashlib.sha256(f"vault-entry-fernet:{SECRET_KEY}".encode()).digest()
    ).decode()
ENTRY_ENCRYPTION_KEY = _vault_enc

ALLOWED_HOSTS = ["*"]

# When DEBUG=False, still serve /media/ in small deployments (set True); production should use nginx.
FORCE_SERVE_MEDIA = os.getenv("FORCE_SERVE_MEDIA", "True" if DEBUG else "False") == "True"

# CSRF: required for POST + multipart (fetch/FormData). Include every origin you use in the browser.
_csrf_origins = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost",
    "http://127.0.0.1",
    "http://[::1]:8000",
    "http://[::1]",
]
_extra_csrf = (os.getenv("CSRF_TRUSTED_ORIGINS") or "").strip()
if _extra_csrf:
    _csrf_origins.extend([x.strip() for x in _extra_csrf.split(",") if x.strip()])
CSRF_TRUSTED_ORIGINS = list(dict.fromkeys(_csrf_origins))

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "auth_tenants",
    "notification",
    "hrm",
    "recruitment",
    "foundation",
    "inventory",
    "finance",
    "purchase",
    "sales",
    "production",
    "jiraclone",
    "vault",
    "channels",
    "chat",
    "pos",
    "support",
    "screenhot",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Django Channels — chat WebSockets (InMemory ok for single process / dev; use Redis in production)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

# ── Database ──────────────────────────────────────────────────────────────────
if os.getenv("DB_ENGINE") == "django.db.backends.postgresql":
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / os.getenv("DB_NAME", "db.sqlite3"),
    }}

AUTH_USER_MODEL = "auth_tenants.User"
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Dhaka"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Media (user uploads) ──────────────────────────────────────────────────────
MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Chat / uploads (images, voice notes) — ASGI + multipart
DATA_UPLOAD_MAX_MEMORY_SIZE = 26_214_400  # 25 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 26_214_400
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10_000
FILE_UPLOAD_TEMP_DIR = str(BASE_DIR / "tmp_uploads")
# Ensure dirs exist (Windows + Docker)
for _d in (MEDIA_ROOT, Path(FILE_UPLOAD_TEMP_DIR)):
    try:
        Path(_d).mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

# ── DRF ───────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# ── JWT ───────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_LIFETIME_MINUTES", 60))),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_LIFETIME_DAYS", 7))),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

# ── Email ─────────────────────────────────────────────────────────────────────
# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND   = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST      = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT      = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS   = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER     = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL  = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# ── CORS ──────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
]
