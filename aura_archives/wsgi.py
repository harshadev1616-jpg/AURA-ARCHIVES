import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Determine environment
IS_VERCEL = os.getenv('VERCEL') == '1'
DEBUG_MODE = os.getenv('DEBUG', 'False').lower() == 'true'

# Set Django settings module based on environment
if IS_VERCEL or not DEBUG_MODE:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.development')

try:
    # Get WSGI application
    application = get_wsgi_application()
    
    # Add WhiteNoise for static file handling
    try:
        from whitenoise.wsgi import WhiteNoise
        application = WhiteNoise(
            application,
            root=str(BASE_DIR / 'staticfiles'),
            max_age=31536000  # 1 year cache for static files
        )
    except (ImportError, FileNotFoundError):
        pass
except Exception as e:
    print(f"WSGI initialization error: {e}")
    import traceback
    traceback.print_exc()
    raise

