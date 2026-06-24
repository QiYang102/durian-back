from .django import *
import datetime

import firebase_admin
from firebase_admin import credentials
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# JSON Web Token Authentication
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': datetime.timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': datetime.timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,  # set to true to obtain next refresh token
}

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'dynamic_rest.renderers.DynamicBrowsableAPIRenderer',
    ],
    # Parser classes priority-wise for Swagger
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
        # 'rest_framework.permissions.IsAdminUser'
    ],
    'EXCEPTION_HANDLER': 'core.utility.exception_handler',
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    # 'PAGE_SIZE': env.int('PAGE_SIZE', 10)

}

DYNAMIC_REST = {
    # DEBUG: enable/disable internal debugging
    'DEBUG': env.bool('DEBUG', False),

    # ENABLE_BROWSABLE_API: enable/disable the browsable API.
    # It can be useful to disable it in production.
    'ENABLE_BROWSABLE_API': env.bool('DEBUG', False),

    # ENABLE_LINKS: enable/disable relationship links
    'ENABLE_LINKS': True,

    # ENABLE_SERIALIZER_CACHE: enable/disable caching of related serializers
    'ENABLE_SERIALIZER_CACHE': True,

    # ENABLE_SERIALIZER_OPTIMIZATIONS: enable/disable representation speedups
    'ENABLE_SERIALIZER_OPTIMIZATIONS': True,

    # DEFER_MANY_RELATIONS: automatically defer many-relations, unless
    # `deferred=False` is explicitly set on the field.
    'DEFER_MANY_RELATIONS': False,

    # MAX_PAGE_SIZE: global setting for max page size.
    # Can be overriden at the viewset level.
    'MAX_PAGE_SIZE': None,

    # PAGE_QUERY_PARAM: global setting for the pagination query parameter.
    # Can be overriden at the viewset level.
    'PAGE_QUERY_PARAM': 'page',

    # PAGE_SIZE: global setting for page size.
    # Can be overriden at the viewset level.
    'PAGE_SIZE': env.int('PAGE_SIZE', 10),

    # PAGE_SIZE_QUERY_PARAM: global setting for the page size query parameter.
    # Can be overriden at the viewset level.
    'PAGE_SIZE_QUERY_PARAM': 'per_page',

    # ADDITIONAL_PRIMARY_RESOURCE_PREFIX: String to prefix additional
    # instances of the primary resource when sideloading.
    'ADDITIONAL_PRIMARY_RESOURCE_PREFIX': '+',

    # Enables host-relative links.  Only compatible with resources registered
    # through the dynamic router.  If a resource doesn't have a canonical
    # path registered, links will default back to being resource-relative urls
    'ENABLE_HOST_RELATIVE_LINKS': True
}

# django-debug-toolbar
INTERNAL_IPS = ('127.0.0.1',)

# django-auth
REST_USE_JWT = True
OLD_PASSWORD_FIELD_ENABLED = True

REST_AUTH_SERIALIZERS = {
    'LOGIN_SERIALIZER': 'core.serializers.CustomLoginSerializer',
    'PASSWORD_RESET_SERIALIZER': 'core.serializers.CustomPasswordResetSerializer',
    'USER_DETAILS_SERIALIZER': 'core.serializers.JWTUserSerializer'
}

# Sentry setting
sentry_dsn = env.str('SENTRY_DSN', None)

if sentry_dsn:
    sentry_sdk.init(
        environment='development',
        dsn=sentry_dsn,
        integrations=[DjangoIntegration()],

        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=1.0,

        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True
    )

# Azure setting
AZURE_ACCOUNT_NAME = env.str('AZURE_ACCOUNT_NAME', None)
AZURE_ACCOUNT_KEY = env.str('AZURE_ACCOUNT_KEY', None)
AZURE_CUSTOM_DOMAIN = env.str('AZURE_CUSTOM_DOMAIN', None)
AZURE_CONTAINER = env.str('AZURE_CONTAINER', None)
AZURE_EXPIRE_SECOND = env.int('AZURE_EXPIRE_SECOND', None)

if AZURE_ACCOUNT_NAME and AZURE_ACCOUNT_KEY and AZURE_CUSTOM_DOMAIN and AZURE_CONTAINER:
    STATIC_URL = 'https://{0}/{1}/static/'.format(
        AZURE_CUSTOM_DOMAIN, AZURE_CONTAINER)
    MEDIA_URL = 'https://{0}/{1}/media/'.format(
        AZURE_CUSTOM_DOMAIN, AZURE_CONTAINER)

    STATICFILES_STORAGE = 'cqc.azure.PublicStaticAzureStorage'
    DEFAULT_FILE_STORAGE = 'cqc.azure.PublicMediaAzureStorage'

# Easy Audit
# ------------------------------------------------------------------------------
DJANGO_EASY_AUDIT_UNREGISTERED_URLS_DEFAULT = [
    r'^/admin/', r'^/static/', r'^/favicon.ico$', r'/media/']
DJANGO_EASY_AUDIT_READONLY_EVENTS = True
DJANGO_EASY_AUDIT_UNREGISTERED_CLASSES_EXTRA = [
    'core.Tenant', 'sequences.Sequence']


# Firebase
FIREBASE_PROJECT_ID = env.str('FIREBASE_PROJECT_ID', None)
FIREBASE_PRIVATE_KEY_ID = env.str('FIREBASE_PRIVATE_KEY_ID', None)
FIREBASE_PRIVATE_KEY = env.str('FIREBASE_PRIVATE_KEY', '')
FIREBASE_CLIENT_EMAIL = env.str('FIREBASE_CLIENT_EMAIL', None)
FIREBASE_CLIENT_ID = env.str('FIREBASE_CLIENT_ID', None)
FIREBASE_CLIENT_CERT_URL = env.str('FIREBASE_CLIENT_CERT_URL', None)
FIREBASE_DATABASE_URL = env.str('FIREBASE_DATABASE_URL', None)
FIREBASE_PATH_PREFIX = env.str('FIREBASE_PATH_PREFIX', '')
FIREBASE_CLOUD_MESSAGE_KEY = env.str('FIREBASE_CLOUD_MESSAGE_KEY', None)
FIREBASE_DEFAULT_APP = None
FIREBASE_UID = env.str('FIREBASE_UID', None)

if FIREBASE_PROJECT_ID and FIREBASE_PRIVATE_KEY and FIREBASE_PRIVATE_KEY_ID and FIREBASE_DATABASE_URL and not firebase_admin._apps:
    credential = credentials.Certificate(
        {
            'type': 'service_account',
            'project_id': FIREBASE_PROJECT_ID,
            'private_key_id': FIREBASE_PRIVATE_KEY_ID,
            'private_key': FIREBASE_PRIVATE_KEY.replace('\\n', '\n'),
            'client_email': FIREBASE_CLIENT_EMAIL,
            'client_id': FIREBASE_CLIENT_ID,
            'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
            'token_uri': 'https://accounts.google.com/o/oauth2/token',
            'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
            'client_x509_cert_url': FIREBASE_CLIENT_CERT_URL,
        }
    )

    FIREBASE_DEFAULT_APP = firebase_admin.initialize_app(
        credential,
        {
            'databaseURL': FIREBASE_DATABASE_URL,
            'databaseAuthVariableOverride': {'uid': FIREBASE_UID}
        })
