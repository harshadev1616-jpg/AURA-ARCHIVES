from .base import *

DEBUG = True

INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar']

MIDDLEWARE = list(MIDDLEWARE) + ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']

# Keep the debug toolbar available but hidden by default (it clutters the UI).
# Append ?djdt=1 to any URL to show it when you actually need it.
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: request.GET.get('djdt') == '1',
    'IS_RUNNING_TESTS': False,
}

# This project serves media from within STATIC_URL (MEDIA_URL = /static/media/).
# debug_toolbar's StaticFilesPanel instantiates StaticFilesStorage at startup,
# which calls check_settings() and rejects that layout under DEBUG. Drop just
# that panel so the toolbar (and runserver) work with this media-under-static setup.
from debug_toolbar.settings import PANELS_DEFAULTS as _DJDT_PANELS  # noqa: E402
DEBUG_TOOLBAR_PANELS = [p for p in _DJDT_PANELS if 'StaticFilesPanel' not in p]

# Use console email in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable cache in dev
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
