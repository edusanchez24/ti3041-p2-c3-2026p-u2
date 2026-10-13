"""
WSGI config for core project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Vercel carga este callable WSGI para convertir cada petición HTTPS en una
# petición Django y devolver la respuesta HTTP generada por las vistas.
application = get_wsgi_application()
