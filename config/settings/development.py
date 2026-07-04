from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

MIDDLEWARE += [
    "apps.core.middleware.log.RequestLoggingMiddleware"
]