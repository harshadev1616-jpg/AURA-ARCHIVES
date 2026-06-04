import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1', 'aura-archives.vercel.app']),
)

# Read .env file if it exists (development only)
env_file = os.path.join(BASE_DIR, '.env')
if os.path.exists(env_file):
    environ.Env.read_env(env_file)

SECRET_KEY = env('SECRET_KEY', default='django-insecure-change-me-in-production')
DEBUG = env('DEBUG', default=False)
ALLOWED_HOSTS = env('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', 'aura-archives.vercel.app'])

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.humanize',
]

THIRD_PARTY_APPS = [
    'django_extensions',
    'django_filters',
    'corsheaders',
    'storages',
    'imagekit',
    'import_export',
    'colorfield',
    'rangefilter',
    'crispy_forms',
    'crispy_tailwind',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
]

LOCAL_APPS = [
    'apps.core',
    'apps.products',
    'apps.orders',
    'apps.accounts',
    'apps.reviews',
    'apps.wishlist',
    'apps.coupons',
    'apps.blog',
    'apps.cms',
    'apps.analytics',
    'apps.notifications',
    'apps.shipping',
    'apps.seo',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'apps.analytics.middleware.PageViewMiddleware',
]

ROOT_URLCONF = 'aura_archives.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.site_settings',
                'apps.core.context_processors.cart_info',
                'apps.core.context_processors.recently_viewed',
                'apps.cms.context_processors.cms_content',
            ],
        },
    },
]

WSGI_APPLICATION = 'aura_archives.wsgi.application'

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

MEDIA_URL = '/static/media/'
MEDIA_ROOT = BASE_DIR / 'static' / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'accounts.User'

SITE_ID = 1

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/accounts/dashboard/'
LOGOUT_REDIRECT_URL = '/'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = 'tailwind'
CRISPY_TEMPLATE_PACK = 'tailwind'

# Allauth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'  # legacy allauth compat

# Email
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = env('EMAIL_HOST', default='')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='Aura Archives <hello@aura-archives.com>')

# Razorpay
RAZORPAY_KEY_ID = env('RAZORPAY_KEY_ID', default='')
RAZORPAY_KEY_SECRET = env('RAZORPAY_KEY_SECRET', default='')

# Redis
REDIS_URL = env('REDIS_URL', default='' if os.getenv('VERCEL') == '1' else 'redis://localhost:6379/0')

# Cache configuration with fallback support
# On Vercel, skip Redis entirely since it's not available on free tier
IS_VERCEL = os.getenv('VERCEL') == '1'

if not IS_VERCEL:
    try:
        # Try Redis cache first
        if REDIS_URL and REDIS_URL.startswith('redis://'):
            CACHES = {
                'default': {
                    'BACKEND': 'django_redis.cache.RedisCache',
                    'LOCATION': REDIS_URL,
                    'OPTIONS': {
                        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                        'CONNECTION_POOL_KWARGS': {'max_connections': 5},
                        'SOCKET_CONNECT_TIMEOUT': 5,
                        'SOCKET_TIMEOUT': 5,
                    }
                }
            }
            SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
            SESSION_CACHE_ALIAS = 'default'
        else:
            raise ValueError("REDIS_URL not configured")
    except Exception as e:
        # Fallback to database cache if Redis unavailable
        print(f"Redis cache unavailable ({e}), using database cache")
        CACHES = {
            'default': {
                'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
                'LOCATION': 'django_cache_table',
            }
        }
        SESSION_ENGINE = 'django.contrib.sessions.backends.db'
else:
    # Vercel: No Redis available on free tier - use database cache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache_table',
        }
    }
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Celery configuration
try:
    # Use Redis for Celery if available
    if REDIS_URL and REDIS_URL.startswith('redis://'):
        CELERY_BROKER_URL = REDIS_URL
        CELERY_RESULT_BACKEND = REDIS_URL
    else:
        # Fallback broker
        CELERY_BROKER_URL = 'memory://'
        CELERY_RESULT_BACKEND = 'db+sqlite:////tmp/celery.db'
except Exception as e:
    print(f"Celery Redis configuration failed ({e}), using memory broker")
    CELERY_BROKER_URL = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+db://default/'

CELERY_TIMEZONE = TIME_ZONE

# API Keys
UNSPLASH_ACCESS_KEY = env('UNSPLASH_ACCESS_KEY', default='')
PEXELS_API_KEY = env('PEXELS_API_KEY', default='')

# Site Info
SITE_URL = env('SITE_URL', default='http://localhost:8000')
SITE_NAME = env('SITE_NAME', default='Aura Archives')

# Brand Colors for use in templates
BRAND_COLORS = {
    'ivory': '#F8F4EF',
    'blush': '#E8CFCF',
    'lavender': '#D8D0E8',
    'gold': '#C9A86A',
    'charcoal': '#333333',
}

# AWS S3
USE_S3 = env.bool('USE_S3', default=False)
if USE_S3:
    AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='ap-south-1')
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
