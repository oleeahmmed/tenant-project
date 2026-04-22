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

# ── Django Apps Organization ─────────────────────────────────────────────────

# Django built-in apps (staticfiles must come after daphne)
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

# Third-party apps (daphne must come before staticfiles)
THIRD_PARTY_APPS = [
    "daphne",
    "corsheaders",
    "rest_framework",
    "drf_spectacular", 
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "channels",
]

# Local apps (your custom modules)
LOCAL_APPS = [
    "auth_tenants",      # Core tenant & auth system
    "foundation",        # Base models (Customer, Product, etc.)
    "notification",      # Notification system
    "chat",             # Chat & messaging
    
    # Business modules
    "hrm",              # Human Resource Management
    "recruitment",      # Recruitment & hiring
    "inventory",        # Inventory management
    "finance",          # Financial management
    "purchase",         # Purchase management
    "sales",            # Sales management
    "production",       # Production management
    "pos",              # Point of Sale
    "rental_management", # Rental management
    "school",           # School management
    
    # Utility modules
    "jiraclone",        # Project management
    "vault",            # Secure storage
    "support",          # Support system
    "screenhot",        # Screen monitoring
]

# Combine all apps (daphne must be first, before staticfiles)
INSTALLED_APPS = THIRD_PARTY_APPS + DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "auth_tenants.middleware.SubscriptionMiddleware",  # Subscription access control
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
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "WA Automotion API",
    "DESCRIPTION": "Tenant-scoped API for auth, chat, jira clone, screenhot and related modules.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
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


# ── SMS Gateway (Rental Management) ───────────────────────────────────────────
SMS_GATEWAY_URL = os.getenv("SMS_GATEWAY_URL", "")
SMS_API_KEY = os.getenv("SMS_API_KEY", "")
SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "")
