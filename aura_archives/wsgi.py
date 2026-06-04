import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aura_archives.settings.production')

# Get WSGI application
application = get_wsgi_application()

# Vercel-specific middleware wrapper for proper request handling
try:
    from whitenoise.wsgi import WhiteNoise
    application = WhiteNoise(application, root=os.path.join(BASE_DIR, 'staticfiles'))
except ImportError:
    pass

