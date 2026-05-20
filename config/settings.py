"""
Django settings for config project.
"""

from pathlib import Path
from dotenv import load_dotenv
import os
import cloudinary

load_dotenv()

from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-)!oe+(pobv4_mtz@pyq$at1t@%o^7+_s(8pvb@e0!ynw^8&r4r'

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
ALLOWED_HOSTS = [h.strip() for h in ALLOWED_HOSTS]


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


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

# Modelo de usuario personalizado
AUTH_USER_MODEL = 'usuarios.Usuario'

# Configuración de Django REST Framework
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

# Configuración de CORS para desarrollo local
CORS_ALLOWED_ORIGINS = [
    'http://localhost:4200',
]

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Configuración de JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# Configuración de correo: imprime en consola durante desarrollo
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25
DEFAULT_FROM_EMAIL = 'AgroConecta <noreply@agroconecta.com>'

cloudinary.config(
    cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
    api_key=os.getenv('CLOUDINARY_API_KEY'),
    api_secret=os.getenv('CLOUDINARY_API_SECRET'),
    secure=True
)

# Headers de seguridad HTTP
X_FRAME_OPTIONS = 'DENY'                    # Protege contra clickjacking
SECURE_BROWSER_XSS_FILTER = True            # Protege contra XSS (legacy, inofensivo)
SECURE_CONTENT_TYPE_NOSNIFF = True          # Evita sniffing de tipos MIME

# Configuración de django-axes
AXES_FAILURE_LIMIT = 5                        # Bloquear después de 5 intentos fallidos
AXES_COOLOFF_DURATION = timedelta(hours=1)    # Bloquear por 1 hora
AXES_COOLOFF_TIME = AXES_COOLOFF_DURATION     # Alias requerido por helpers de axes
AXES_LOCK_OUT_AT_FAILURE = True               # Bloquear automáticamente
AXES_HTTP_RESPONSE_CODE = 429
AXES_COOLOFF_MESSAGE = (
    'Demasiados intentos fallidos. Tu acceso ha sido bloqueado temporalmente. '
    'Intenta nuevamente más tarde.'
)
# Respuesta JSON con tiempo restante para el frontend Angular
AXES_LOCKOUT_CALLABLE = 'usuarios.lockout_utils.axes_lockout_callable'

AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]
