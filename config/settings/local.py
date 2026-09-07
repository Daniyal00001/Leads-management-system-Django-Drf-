from .base import *  # noqa
from decouple import config

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INSTALLED_APPS += [
    "django_extensions",  # gives some extra features at dev phase (shell_plus etc.)
]

# Use console backend so you can SEE emails in terminal
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CORS_ALLOW_ALL_ORIGINS = True

INTERNAL_IPS = ["127.0.0.1"]