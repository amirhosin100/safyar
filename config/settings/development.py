from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

MIDDLEWARE += [
    'silk.middleware.SilkyMiddleware',
]
INSTALLED_APPS += [
    "silk",
]

DEFAULT_PROTOCOL = "http"