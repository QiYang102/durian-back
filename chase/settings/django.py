import os
import environ
from datetime import datetime

from .version import PROJECT_CODE, PROJECT_VERSION, PROJECT_ENVIRONMENT

PROJECT_NAME = "Durian Is Ok"

PROCESS_ID = os.getpid()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))

ROOT_DIR = (
    environ.Path(__file__) - 3
)
APPS_DIR = ROOT_DIR.path(PROJECT_CODE)

env = environ.Env()

# This part will read env file if it exists
env_filename = f'setting-{PROJECT_CODE}.{PROJECT_ENVIRONMENT}.env'

if os.path.exists(env_filename):
    env.read_env(env_filename)
else:
    print(f'{env_filename} is missing')


SECRET_KEY = env.str(
    'SECRET_KEY', 'this-is-a-dummy-secret-key-for-django-development!')
DEBUG = env.bool('DEBUG', False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['127.0.0.1'])
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True
CORS_EXPOSE_HEADERS = ['content-disposition']
CORS_ALLOW_HEADERS = ['x-secret-key','authorization', 'content-type', 'accept', 'origin', 'x-requested-with', 'x-csrftoken']
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

DEV_TEST = env.bool('DEV_TEST', False)
# set True to skip if running for database migration
SKIP_SCHEDULER = env.bool('SKIP_SCHEDULER', False)

# Application definition
DEFAULT_DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

# Third party library or utility
THIRD_PARTY_APPS = [
    'rest_framework',   # django-rest-framework
    'dynamic_rest',
    'corsheaders',
    'django_extensions',
    'django_fsm',
    'storages',
    'easyaudit',
    'sequences.apps.SequencesConfig',
    'dj_rest_auth',
    'dj_rest_auth.registration',
    'allauth',
    'allauth.account',

]

# Current project apps
LOCAL_APPS = [
    'core.apps.CoreConfig',
    'durian_store.apps.DurianStoreConfig',
]

# AUTHENTICATION_BACKENDS = [
#     # Needed to login by username in Django admin, regardless of `allauth`
#     'django.contrib.auth.backends.ModelBackend',

#     # `allauth` specific authentication methods, such as login by e-mail
#     'allauth.account.auth_backends.AuthenticationBackend',
# ]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'easyaudit.middleware.easyaudit.EasyAuditMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

INSTALLED_APPS = DEFAULT_DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

ROOT_URLCONF = f'{PROJECT_CODE}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates'), os.path.join(BASE_DIR, 'core/templates')],
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

WSGI_APPLICATION = f'{PROJECT_CODE}.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3'),
    'extra': env.db('SQLITE_URL', default='sqlite:///db.extra.sqlite3')
}

if DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
    DATABASES['default']['OPTIONS'] = {
        'charset': 'utf8mb4',
        'ssl': {'ca': os.path.join(ROOT_DIR, 'BaltimoreCyberTrustRoot.crt.pem')}
    }

DATABASE_URL = env.str('DATABASE_URL', env.str(
    'SQLITE_URL', 'sqlite:////db.sqlite3'))
DATABASE_SSL_CERT = os.path.join(ROOT_DIR, 'BaltimoreCyberTrustRoot.crt.pem')


# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# CUSTOM USER
# ------------------------------------------------------------------------------
AUTH_USER_MODEL = 'core.User'
REST_AUTH_TOKEN_MODEL = None
LOGIN_REDIRECT_URL = '/index.html'
LOCAL_ADMIN_USERNAME = env.str('LOCAL_ADMIN_USERNAME', None)
LOCAL_ADMIN_PASSWORD = env.str('LOCAL_ADMIN_PASSWORD', None)
USER_VERIFICATION = env.bool('USER_VERIFICATION', True)
USER_VERIFICATION_EXPIRE_MINUTE = env.int(
    'USER_VERIFICATION_EXPIRE_MINUTE', 60)


# FILE
# ------------------------------------------------------------------------------
# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/
MEDIA_ROOT = ROOT_DIR(env.str('MEDIA_RELATIVE_PATH', default='media'))
MEDIA_URL = env.str('MEDIA_URL', default='/media/')
STATIC_ROOT = ROOT_DIR(env.str('STATIC_RELATIVE_PATH', default='static'))
STATIC_URL = env.str('STATIC_URL', default='/static/')

FILE_UPLOAD_PERMISSIONS = 0o644
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240


# EMAIL
# ------------------------------------------------------------------------------
EMAIL_CONFIG = env.email_url(
    'EMAIL_URL', default='smtp+tls://4dde290438de75:2b1ece1e453936@smtp.mailtrap.io:587')

vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env.str(
    'DEFAULT_FROM_EMAIL', 'no reply <noreply@codetinker.com>')


LOG_ROOT = os.path.join(BASE_DIR, 'log-files', PROJECT_VERSION)
os.makedirs(LOG_ROOT, exist_ok=True)
START_TIME = datetime.now()

if PROJECT_ENVIRONMENT == 'dev':
    LOG_FILE = os.path.join(LOG_ROOT, 'debug.log')
else:
    LOG_FILE = os.path.join(
        LOG_ROOT, f'v{PROJECT_VERSION}-{START_TIME.strftime("%Y.%m.%d-%I.%M.%S-%p")}-p{PROCESS_ID}.log')


# LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'maxBytes': 1024*1024*10,   # 10 MB
            'backupCount': 20,
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO'
        },
    },
}


if DEBUG:
    from rich.console import Console
    console = Console()

    console.print()
    console.print('[yellow]Version:[/yellow]',
                  f'v{PROJECT_VERSION}-{PROJECT_ENVIRONMENT}')
    console.print('[red]Warning:[/red]', 'You are in DEBUG mode')
    console.print()

    INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']
    MIDDLEWARE = MIDDLEWARE + \
        ['debug_toolbar.middleware.DebugToolbarMiddleware']
