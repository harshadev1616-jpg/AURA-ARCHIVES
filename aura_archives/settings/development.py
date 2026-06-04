from .base import *

DEBUG = True

INSTALLED_APPS += ['debug_toolbar']

MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']

INTERNAL_IPS = ['127.0.0.1']

# Keep the debug toolbar available but hidden by default (it clutters the UI).
# Append ?djdt=1 to any URL to show it when you actually need it.
DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: request.GET.get('djdt') == '1',
    'IS_RUNNING_TESTS': False,
}

# Use console email in dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable cache in dev
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'
