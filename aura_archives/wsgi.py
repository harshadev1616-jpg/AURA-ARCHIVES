import os
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

IS_VERCEL = os.getenv('VERCEL') == '1'
DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'

if IS_VERCEL or not DEBUG_MODE:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.development')

# On Vercel, ensure DATABASE_URL points to writable /tmp if not set
if IS_VERCEL and not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL'] = 'sqlite:////tmp/db.sqlite3'

try:
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception as exc:
    # Surface the full traceback so Vercel logs show the real cause
    tb = traceback.format_exc()
    print(f"WSGI STARTUP FAILED:\n{tb}", file=sys.stderr)

    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        return [f"Server startup error:\n{tb}".encode()]

if IS_VERCEL:
    try:
        from django.core.management import call_command
        call_command('createcachetable', verbosity=0)
    except Exception:
        pass

try:
    from whitenoise.wsgi import WhiteNoise
    application = WhiteNoise(
        application,
        root=str(BASE_DIR / 'staticfiles'),
        max_age=31536000,
    )
except (ImportError, FileNotFoundError):
    pass

app = application
