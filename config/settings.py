"""
Django settings for config project.
"""

from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import os
import cloudinary

# Cargar .env solo en desarrollo local
if os.path.exists('.env'):
    load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# Hosts permitidos
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
]

if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Configuración necesaria para Render (proxy HTTPS)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
USE_X_FORWARDED_HOST = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Librerías instaladas
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'cloudinary',
    'cloudinary_storage',
    'axes',

    # Apps de AgroConecta
    'usuarios',
    'productos',
    'negociacion',
    'pedidos',
    'notificaciones',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Base de datos
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

# Validadores de contraseña
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

# Internacionalización
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Archivos estáticos
STATIC_URL = 'static/'

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),

    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),

    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 12,

    # Rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'config.throttling.GuestExplorationThrottle',
        'config.throttling.AuthenticatedUserRateThrottle',
    ],

    'DEFAULT_THROTTLE_RATES': {
        'guest_exploration': '100/day',
        'user': '1000/day',
    },

    'EXCEPTION_HANDLER': 'config.exceptions.custom_exception_handler',
}

# CORS
CORS_ALLOWED_ORIGINS = [
    'http://localhost:4200',
    'https://agroconecta-frontend-sigma.vercel.app',
]

# Cloudinary
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Correo (API HTTP de Resend — ver usuarios/email_service.py y docs/EMAIL_RESEND.md)
# Para enviar a CUALQUIER usuario: verifica un dominio propio en Resend y usa
# RESEND_FROM_EMAIL con una dirección de ese dominio (ej. noreply@tudominio.com).
# onboarding@resend.dev solo sirve en desarrollo y solo a tu propio correo.
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
RESEND_FROM_EMAIL = os.getenv('RESEND_FROM_EMAIL') or os.getenv('DEFAULT_FROM_EMAIL')
if RESEND_FROM_EMAIL:
    DEFAULT_FROM_EMAIL = RESEND_FROM_EMAIL
elif DEBUG:
    DEFAULT_FROM_EMAIL = 'AgroConecta <onboarding@resend.dev>'
else:
    DEFAULT_FROM_EMAIL = ''

FRONTEND_URL = os.getenv(
    'FRONTEND_URL',
    'http://localhost:4200'
)

# Seguridad HTTP
X_FRAME_OPTIONS = 'DENY'
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# django-axes
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_DURATION = timedelta(hours=1)
AXES_COOLOFF_TIME = AXES_COOLOFF_DURATION
AXES_LOCK_OUT_AT_FAILURE = True
AXES_HTTP_RESPONSE_CODE = 429

AXES_COOLOFF_MESSAGE = (
    'Demasiados intentos fallidos. Tu acceso ha sido bloqueado temporalmente. '
    'Intenta nuevamente más tarde.'
)

# Respuesta JSON para Angular
AXES_LOCKOUT_CALLABLE = 'usuarios.lockout_utils.axes_lockout_callable'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]