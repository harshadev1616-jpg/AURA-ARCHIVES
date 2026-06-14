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


def _bootstrap_seed_reviews():
    """One-time seed of approved customer reviews on the live DB (whose
    DATABASE_URL is a Sensitive Vercel env var, unreachable locally).
    Runs only the fixed, idempotent `seed_reviews` command when SEED_REVIEWS=1.
    Remove the env var after the reviews appear. Fully guarded."""
    if os.environ.get('SEED_REVIEWS') != '1' or _django_app is None:
        return
    try:
        from django.core import management
        management.call_command('seed_reviews')
        print("SEED_REVIEWS bootstrap: done", file=sys.stderr)
    except Exception:
        print(f"SEED_REVIEWS bootstrap FAILED:\n{traceback.format_exc()}", file=sys.stderr)


_bootstrap_seed_reviews()


_deploy_tasks_done = False


def _bootstrap_deploy_tasks():
    """Run deploy-time DB tasks at startup, once per process.

    Vercel ignores the dashboard Build Command while a legacy `builds` array
    exists in vercel.json (it prints the "unused-build-settings" warning), so
    `build.sh` never runs and migrations / the admin user are never applied at
    build time. Running them here on first boot makes deploys reproducible with
    no manual env-var flips. Set DISABLE_DEPLOY_TASKS=1 to opt out.

    Each step is idempotent and individually guarded so a failure can never
    take the site down:
      - migrate           → brings the Neon schema up to date
      - createcachetable  → ensures the DatabaseCache table exists
      - ensure_admin      → creates/updates the superuser from
                            ADMIN_EMAIL / ADMIN_PASSWORD (self-skips if unset)
    """
    global _deploy_tasks_done
    if _deploy_tasks_done or _django_app is None:
        return
    if os.environ.get('DISABLE_DEPLOY_TASKS') == '1':
        return
    _deploy_tasks_done = True
    from django.core import management
    steps = (
        ('migrate', {'interactive': False}),
        ('createcachetable', {}),
        ('ensure_admin', {}),
    )
    for cmd, kwargs in steps:
        try:
            management.call_command(cmd, **kwargs)
            print(f"deploy bootstrap: {cmd} ok", file=sys.stderr)
        except Exception:
            print(f"deploy bootstrap: {cmd} FAILED:\n{traceback.format_exc()}", file=sys.stderr)


_bootstrap_deploy_tasks()


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
