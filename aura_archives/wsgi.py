import os
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

IS_VERCEL = os.getenv('VERCEL') == '1'
DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'

if IS_VERCEL:
    os.environ['DJANGO_SETTINGS_MODULE'] = 'aura_archives.settings.production'
elif not DEBUG_MODE:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.development')

# On Vercel, ensure DATABASE_URL points to writable /tmp if not set
if IS_VERCEL and not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:////tmp/db.sqlite3'

_startup_error = None

try:
    from django.core.wsgi import get_wsgi_application
    _django_app = get_wsgi_application()
except Exception:
    _startup_error = traceback.format_exc()
    print(f"WSGI STARTUP FAILED:\n{_startup_error}", file=sys.stderr)
    _django_app = None

if IS_VERCEL:
    try:
        from django.core.management import call_command
        call_command('createcachetable', verbosity=0)
    except Exception:
        pass

if _django_app is not None:
    try:
        from whitenoise.wsgi import WhiteNoise
        _django_app = WhiteNoise(
            _django_app,
            root=str(BASE_DIR / 'staticfiles'),
            max_age=31536000,
        )
    except (ImportError, FileNotFoundError, Exception):
        pass

_err = _startup_error


def application(environ, start_response):
    if _django_app is None:
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [(f"Server startup error:\n{_err}").encode()]
    try:
        return _django_app(environ, start_response)
    except Exception:
        tb = traceback.format_exc()
        print(f"REQUEST ERROR:\n{tb}", file=sys.stderr)
        try:
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        except Exception:
            pass
        return [(f"Request error:\n{tb}").encode()]


app = application
