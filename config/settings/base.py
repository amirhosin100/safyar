from pathlib import Path
import os

from dotenv import load_dotenv
from datetime import timedelta

from django.utils.translation import gettext_lazy as _

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
CORS_ALLOW_ALL_ORIGINS = DEBUG

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.sites",
    # internal apps
    "apps.core",
    "apps.account",
    "apps.owner",
    "apps.smoothing",
    "apps.wallet",
    "apps.costumer",
    "apps.project",
    "apps.report",
    # other packages
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "azbankgateways",
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware'
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases


POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_USER = os.getenv("POSTGRES_USER")

if POSTGRES_PASSWORD and POSTGRES_DB and POSTGRES_USER:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "USER": os.getenv("POSTGRES_USER"),
            "PORT": os.getenv("POSTGRES_EXTERNAL_PORT"),
            "HOST": os.getenv("POSTGRES_HOST"),
        }
    }
else:
    raise EnvironmentError(
        "Please set POSTGRES_DB and POSTGRES_PASSWORD and POSTGRES_USER"
        "in .env file"
    )

REDIS_URL = os.getenv("REDIS_URL")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
        }
    }
else:
    raise EnvironmentError(
        "Please set REDIS_URL in .env file"
    )

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {"min_length": 6},
    }
]

# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True

USE_TZ = True

LANGUAGES = [
    ('fa', _('Persian')),
    ('en-us', _('English')),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'

MEDIA_ROOT = BASE_DIR / 'media/'
MEDIA_URL = '/media/'
TEST_MEDIA_ROOT = BASE_DIR / "test_media/"

AUTH_USER_MODEL = "account.User"

WALLET_WARNING_STOCK = 100000
WALLET_EMPTY_STOCK = 1000

EXCLUDE_MODELS = {
    "LogEntity",
    "Session",
    "Group",
    "Token",
    "ContentType",
    "Migration",
    "SupportInformation",
    "WalletTransaction",
    "Wallet",
    "SmsLog",
    "FixArea",
    "MainPart",
}

EXCLUDE_APPS = {
    "log",
    "admin",
    "auth",
    "contenttypes",
    "sessions",
    "messages",
    "authtoken",
    "axes",
    "account",
    "silk",
    "sites",
    "azbankgateways"
}

# REST_FRAMEWORK
# WARNING : just JWTAuthentication checks `is_active_smoothing`
# so don't use SessionAuthentication in production

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'apps.core.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "ROTATE_REFRESH_TOKENS": False,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": False,
}
SPECTACULAR_SETTINGS = {
    'TITLE': 'Safyar Project',
    'DESCRIPTION': 'Smoothing',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
}

AZ_IRANIAN_BANK_GATEWAYS = {
    "GATEWAYS": {
        "ASANPARDAKHT": {
            "MERCHANT_CONFIGURATION_ID": os.environ.get("MERCHANT_CONFIGURATION_ID"),
            "USERNAME": os.environ.get("GATEWAY_USERNAME"),
            "PASSWORD": os.environ.get("GATEWAY_PASSWORD"),
        }
    },
    "IS_SAFE_GET_GATEWAY_PAYMENT": True,
    "DEFAULT": "ASANPARDAKHT",
    "BANK_PRIORITIES": [
        "ASANPARDAKHT"
    ],
}

SITE_ID = 1
