import os
import sys
import traceback
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ['DJANGO_SETTINGS_MODULE'] = 'aura_archives.settings.production'

_startup_error = None

try:
    from django.core.wsgi import get_wsgi_application
    _django_app = get_wsgi_application()
except Exception:
    _startup_error = traceback.format_exc()
    print(f"WSGI STARTUP FAILED:\n{_startup_error}", file=sys.stderr)
    _django_app = None

# Serve media files through WhiteNoise so /media/* works via the Lambda
# even if the Vercel CDN static route doesn't intercept first.
if _django_app is not None:
    try:
        from whitenoise import WhiteNoise
        _django_app = WhiteNoise(_django_app, root=str(BASE_DIR / 'static'), prefix='static')
        _django_app.add_files(str(BASE_DIR / 'media'), prefix='media')
    except Exception:
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
