"""
Django settings for pneushop project.
"""

from pathlib import Path
import os
from datetime import timedelta
from decouple import config
import dj_database_url  # ✅ Add this line
import cloudinary
import cloudinary.uploader
import cloudinary.api
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-your-secret-key-here'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    'localhost', 
    '127.0.0.1', 
    'pneushop-backend.vercel.app', 
    'pneushop.tn', 
    'www.pneushop.tn', 
    'localhost:3000', 
    '102.211.210.215',
    'soulaima16.obg.com.tn',  # Add the missing domain from logs
    '*.obg.com.tn',
    '*',  # Temporary - allow all hosts for debugging
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework.authtoken',
    'corsheaders',
    'accounts',
    'products',
    'cart',
    'favorites',
    'orders',
    "suppliers",
    'cloudinary',
    'cloudinary_storage',
]

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Cloudinary Storage configuration (required by django-cloudinary-storage)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': config('CLOUDINARY_API_KEY'),
    'API_SECRET': config('CLOUDINARY_API_SECRET')
}

# Cloudinary configuration (for direct cloudinary.uploader usage)
cloudinary.config(
    cloud_name = config('CLOUDINARY_CLOUD_NAME'),
    api_key = config('CLOUDINARY_API_KEY'),
    api_secret = config('CLOUDINARY_API_SECRET'),
    secure=True,
)
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pneushop.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'pneushop.wsgi.application'



# For using Sql lite
# Database
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


#For using Postgres Locally
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': config('DB_NAME', default='pneushop_db'),
#         'USER': config('DB_USER', default='postgres'),
#         'PASSWORD': config('DB_PASSWORD', default=''),
#         'HOST': config('DB_HOST', default='localhost'),
#         'PORT': config('DB_PORT', default='5432'),
#     }
# }


DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL')
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model configuration
AUTH_USER_MODEL = 'accounts.CustomUser'

# Internationalization
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Tunis'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings for large Excel files
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000  # For Excel with many rows

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
}

# CORS settings - Temporary fix for deployment debugging
CORS_ALLOW_ALL_ORIGINS = True

# Specific origins (use this instead of CORS_ALLOW_ALL_ORIGINS in production)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://102.211.210.215",
    "https://102.211.210.215",
    "http://soulaima16.obg.com.tn",
    "https://soulaima16.obg.com.tn",
]

CORS_ALLOW_CREDENTIALS = True

# Email configuration (for development/student project)
# Choose email backend - set EMAIL_BACKEND in .env file
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'simontechengineer@gmail.com'
EMAIL_HOST_PASSWORD = 'okrb rvmi rhky tjz               '
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
DEFAULT_FROM_EMAIL = 'simontechengineer@gmail.com'
# Alternative SMTP providers settings (uncomment and configure as needed):
# 
# Gmail: EMAIL_HOST='smtp.gmail.com', EMAIL_PORT=587, EMAIL_USE_TLS=True
# Outlook: EMAIL_HOST='smtp-mail.outlook.com', EMAIL_PORT=587, EMAIL_USE_TLS=True
# SendGrid: EMAIL_HOST='smtp.sendgrid.net', EMAIL_PORT=587, EMAIL_USE_TLS=True
# Yahoo: EMAIL_HOST='smtp.mail.yahoo.com', EMAIL_PORT=587, EMAIL_USE_TLS=True

# Password reset token validity (in seconds)
PASSWORD_RESET_TIMEOUT = 3600  # 1 hour
