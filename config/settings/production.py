from .base import *


REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = (
    'apps.core.authentication.JWTAuthentication',
)

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ["rest_framework.renderers.JSONRenderer"]

DEFAULT_PROTOCOL = "https"

for app in ("django.contrib.admin", "django.contrib.sessions", "django.contrib.messages"):
    del INSTALLED_APPS[INSTALLED_APPS.index(app)]

for middleware in (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
):
    del MIDDLEWARE[MIDDLEWARE.index(middleware)]
