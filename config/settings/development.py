from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

MIDDLEWARE += [
    "apps.core.middleware.log.RequestLoggingMiddleware",
    'silk.middleware.SilkyMiddleware',
]
INSTALLED_APPS += [
    "silk",
]

DEFAULT_PROTOCOL = "http"