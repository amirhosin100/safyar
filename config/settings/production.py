from .base import *

# force disable DEBUG

DEBUG = False

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'apps.core.authentication.JWTAuthentication',
)

DEFAULT_PROTOCOL = "https"