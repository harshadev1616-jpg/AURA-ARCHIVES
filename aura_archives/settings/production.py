from .base import *
import os

DEBUG = False

# Vercel serverless environment detection
IS_VERCEL = os.getenv('VERCEL') == '1'

# --- Security hardening (relaxed for Vercel) ---
if not IS_VERCEL:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REFERRER_POLICY = 'same-origin'
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = 'DENY'
else:
    # Vercel handles SSL/HTTPS, so relax security settings
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'

# CSRF trusted origins — include a wildcard for Vercel preview/deployment URLs
# so form POSTs (e.g. admin login) work on those hosts too, not just the main one.
csrf_origins = env.list('CSRF_TRUSTED_ORIGINS', default=[])
if not csrf_origins:
    csrf_origins = ['https://aura-archives.vercel.app', 'https://*.vercel.app', SITE_URL]
CSRF_TRUSTED_ORIGINS = csrf_origins

# --- Cache & sessions: force database-backed, never Redis ---
# Vercel has no Redis; base.py's auto-detection can fall through to a
# localhost:6379 Redis config, which then 500s every request that saves a
# session (homepage, shop) with "Connection refused". Pin DB-backed cache and
# sessions here unconditionally — both tables (django_cache_table,
# django_session) already exist in the production DB.
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache_table',
    }
}
SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# --- Sentry (optional — only if installed AND a DSN is configured) ---
SENTRY_DSN = env('SENTRY_DSN', default='')
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[DjangoIntegration()],
            traces_sample_rate=0.1,
            send_default_pii=False,
        )
    except ImportError:
        pass
