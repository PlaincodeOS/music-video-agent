"""ASGI config for Break Records PoC."""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "break_records_web.settings")

application = get_asgi_application()
