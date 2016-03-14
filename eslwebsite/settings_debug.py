"""
Django settings for DjangoWebProject project.
"""

# Celery settings

from __future__ import absolute_import
# ^^^ The above is required if you want to import from the celery
# library.  If you don't have this then `from celery.schedules import`
# becomes `proj.celery.schedules` in Python 2.x since it allows
# for relative imports by default.

# Celery settings

# BROKER_URL = 'django://'
BROKER_URL = 'amqp://'
# CELERY_RESULT_BACKEND = 'djcelery.backends.cache:CacheBackend'
# CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'

# Only add pickle to this list if your broker is secured
# from unwanted access (see userguide/security.html)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


# Registration settings

REGISTRATION_OPEN = True
ACCOUNT_ACTIVATION_DAYS = 7
REGISTRATION_AUTO_LOGIN = True
LOGIN_URL = '/accounts/login/'
# LOGIN_REDIRECT_URL = '/accounts/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_URL = '/'


from os import path
PROJECT_ROOT = path.dirname(path.abspath(path.dirname(__file__)))
DATA_ROOT = PROJECT_ROOT
MEDIA_ROOT = path.join(DATA_ROOT, 'media')

DATA_DIR = path.join(DATA_ROOT, 'data')
CORPORA_DIR = path.join(DATA_DIR, 'corpora')
LIB_DIR = path.join(PROJECT_ROOT, 'libs')
PDFTOTEXT = 'pdftotext'  #path.join(LIB_DIR, 'pdftotext')
STANFORD_CORENLP = path.join(LIB_DIR, 'stanford-corenlp')
STANFORD_CORENLP_CP = path.join(STANFORD_CORENLP, '*')
# JAVA = path.join(path.expandvars('%JAVA_HOME%'), 'bin', 'java')
JAVA = 'java'

# Uploads Directory
UPLOAD_DIR = path.join(MEDIA_ROOT, 'uploads')
CHUNKS_DIR = path.join(MEDIA_ROOT, 'chunks')
PAPERS_DIR = path.join(MEDIA_ROOT, 'papers')

# Preprocess Directory
EXTRACTED_DIR = path.join(MEDIA_ROOT, 'extracted')
REFINED_DIR = path.join(MEDIA_ROOT, 'refined')
PARSED_DIR = path.join(MEDIA_ROOT, 'parsed')
COMPRESSED_DIR = path.join(MEDIA_ROOT, 'compressed')


DEBUG = True

ALLOWED_HOSTS = (
    '*',
)

ADMINS = (
    ('admin', 'eslwriter@foxmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': path.join(DATA_ROOT, 'db.sqlite3'),
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
    # 'default': {
    #     'ENGINE': 'sql_server.pyodbc',
    #     'NAME': 'esl',
    #     'USER': 'admin@windowsazure.com@esl',
    #     'PASSWORD': 'ESLWriter123',
    #     'HOST': 'esl.database.windows.net',
    #     'PORT': '1433',
    #     'OPTIONS': {
    #         'driver': 'SQL Server Native Client 11.0',
    #         'MARS_Connection': 'True',
    #     }
    # }
}


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Asia/Shanghai'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = path.join(PROJECT_ROOT, 'static').replace('\\', '/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/esl/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'n(bd1f1c%e8=_xad02x5qtfn%wgwpi492e$8_erx+d)!tpeoim'

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'eslwebsite.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'eslwebsite.wsgi_debug.application'


INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'common',
    # 'fine_uploader',
    # 'corpus_building',
    'eslwriter',
    # 'monitor',
    'registration',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    # 'djcelery',
    # 'kombu.transport.django',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            # 'email_backend': 'django.core.mail.backends.console.EmailBackend'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

# Specify the default test runner.
TEST_RUNNER = 'django.test.runner.DiscoverRunner'


# MongoDB Settings
from pymongo import MongoClient
# from django.contrib.sites.models import Site
# CURRENT_SITE = Site.objects.get_current()
# DBC = MongoClient(CURRENT_SITE.domain.split(':')[0])
DBC = MongoClient('166.111.139.15')
# DBC = MongoClient()
try:
    DBC.database_names()
except:
    DBC.admin.authenticate('root', 'root')
print 'connected to', DBC
MAX_GROUP_COUNT = 100   #TODO: choose top N groups instead of random
MAX_SENTENCE_COUNT = 100
MAX_RESULT_LENGTH = 1000
MAX_QUERY_LENGTH = 100
DEFAULT_FID = 1
DEFAULT_CIDS = [c['_id'] for c in DBC.common.corpora.find({'field': DEFAULT_FID, 'status': 2}, {'_id': 1})]
