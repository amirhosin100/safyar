from .base import *

# force disable DEBUG

DEBUG = False

REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'apps.core.authentication.JWTAuthentication',
)
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ["rest_framework.renderers.JSONRenderer"]

DEFAULT_PROTOCOL = "https"

del INSTALLED_APPS[INSTALLED_APPS.index("django.contrib.admin")]
del INSTALLED_APPS[INSTALLED_APPS.index("django.contrib.sessions")]
del INSTALLED_APPS[INSTALLED_APPS.index("django.contrib.messages")]

del MIDDLEWARE[MIDDLEWARE.index('django.contrib.sessions.middleware.SessionMiddleware')]
del MIDDLEWARE[MIDDLEWARE.index('django.contrib.messages.middleware.MessageMiddleware')]
del MIDDLEWARE[MIDDLEWARE.index('django.contrib.auth.middleware.AuthenticationMiddleware')]
