"""ASGI config for sobreaviso project."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sobreaviso.settings")

application = get_asgi_application()
