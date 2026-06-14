"""Local preview settings.

DEBUG=True is incompatible with this project's media-under-static layout
(MEDIA_URL = /static/media/ nested in STATIC_URL = /static/), because
StaticFilesStorage.check_settings() rejects it whenever DEBUG is True.

So preview runs with DEBUG=False and lets WhiteNoise serve the collected
static files (run `collectstatic` first). SQLite is the default DB.
"""
from .base import *  # noqa

DEBUG = False

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]', 'testserver', '*']

# Email: use whatever EMAIL_BACKEND the environment / .env sets (base.py reads
# it), so configuring Gmail SMTP in .env makes the preview actually send mail.
# Falls back to the console backend when nothing is configured.
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")

CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Un-hashed WhiteNoise static storage so freshly built assets load without a
# manifest rebuild; the ?v= cache-bust query handles freshness. Override the
# single STATICFILES_STORAGE that base.py sets (defining STORAGES too would
# raise "STATICFILES_STORAGE/STORAGES are mutually exclusive").
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'
