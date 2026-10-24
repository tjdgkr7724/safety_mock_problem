"""Production settings; secrets must be supplied by the hosting environment."""

import os

from .settings import *  # noqa: F403

DEBUG = False
DESKTOP_MODE = False
SECRET_KEY = os.environ['SAFETY_QUIZ_SECRET']
ALLOWED_HOSTS = [os.environ['SAFETY_QUIZ_HOST']]
STATIC_ROOT = BASE_DIR / 'staticfiles'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600
