"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from decouple import config
from django.core.asgi import get_asgi_application

# according to current enviroment it apply the settings either local or prod , we made it dynamic
settings_module = f"config.settings.{config('DJANGO_ENV', default='local')}"
os.environ.setdefault('DJANGO_SETTINGS_MODULE', settings_module)

application = get_asgi_application()