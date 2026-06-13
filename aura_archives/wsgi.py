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

_err = _startup_error


def _bootstrap_admin():
    """One-time superuser bootstrap for environments (e.g. Vercel) where you
    can't run `createsuperuser` interactively.

    Set BOOTSTRAP_ADMIN_PASSWORD (and optionally BOOTSTRAP_ADMIN_EMAIL) as env
    vars and redeploy: on the next cold start this creates the admin or resets
    its password — idempotently. Remove the env var once you've logged in.
    Wrapped so it can never take the app down.
    """
    password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD')
    if not password or _django_app is None:
        return
    try:
        from django.contrib.auth import get_user_model
        email = os.environ.get('BOOTSTRAP_ADMIN_EMAIL', 'apexpredatoradmins64@gmail.com')
        User = get_user_model()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'first_name': 'Aura', 'last_name': 'Admin'},
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.set_password(password)
        user.save()
        print(f"ADMIN BOOTSTRAP ok: email={email} created={created}", file=sys.stderr)
    except Exception:
        print(f"ADMIN BOOTSTRAP FAILED:\n{traceback.format_exc()}", file=sys.stderr)


_bootstrap_admin()


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
