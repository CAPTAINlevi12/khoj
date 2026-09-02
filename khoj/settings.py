"""
Django settings for the khoj project.

Read with os.getenv() from a .env file that is NOT committed to git.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# BASE_DIR is the folder that contains manage.py.
# __file__ is this file -> .resolve() makes it absolute -> .parent walks up.
#   settings.py -> khoj/ -> project#2/
BASE_DIR = Path(__file__).resolve().parent.parent

# Load the key=value pairs from .env into the process environment,
# so os.getenv() can see them.
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# os.getenv always returns a string, so compare against the string "True".
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # our apps
    "accounts",
    "registry",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # LocaleMiddleware decides the active language per request. It must sit
    # AFTER SessionMiddleware (it reads the language from the session) and
    # BEFORE CommonMiddleware (which may redirect using the active language).
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "khoj.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # Project-wide templates live here. App templates are still found
        # automatically because APP_DIRS is True.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                # Puts LANGUAGES and LANGUAGE_CODE in every template context,
                # which the header's language toggle needs.
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "khoj.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST"),
        "PORT": os.getenv("DB_PORT"),
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# THE most important line in this file.
# It tells Django "the User model is accounts.User, not the built-in one".
# Format is "<app_label>.<ModelName>".
AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "home"


LANGUAGE_CODE = "en"
TIME_ZONE = "Asia/Kathmandu"
USE_I18N = True
USE_TZ = True

# The two languages the site offers. A Nepali family is the primary user,
# so an English-only page would fail them; see docs/LANDING_PAGE_BRIEF.md.
LANGUAGES = [
    ("en", "English"),
    ("ne", "नेपाली"),
]

# Where makemessages writes .po files and where compilemessages reads them.
LOCALE_PATHS = [BASE_DIR / "locale"]


# CSS/JS we write ourselves
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Files uploaded by users (photos). Served by Django only while DEBUG=True.
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
