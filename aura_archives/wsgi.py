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

# Serve static and media files via WhiteNoise from the Lambda filesystem.
# static/ → /static/*  (CSS, JS, images)
# media/  → /media/*   (uploaded product images)
if _django_app is not None:
    try:
        from whitenoise import WhiteNoise
        _static_dir = str(BASE_DIR / 'static')
        _media_dir = str(BASE_DIR / 'media')
        _django_app = WhiteNoise(_django_app, root=_static_dir, prefix='static', max_age=86400)
        _django_app.add_files(_media_dir, prefix='media')
        print(f"[wsgi] WhiteNoise serving static={_static_dir} media={_media_dir}", file=sys.stderr)
    except Exception:
        print(f"[wsgi] WhiteNoise init failed: {traceback.format_exc()}", file=sys.stderr)

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
