import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

IS_VERCEL = os.getenv('VERCEL') == '1'
DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'

if IS_VERCEL or not DEBUG_MODE:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.development')

application = get_wsgi_application()

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
