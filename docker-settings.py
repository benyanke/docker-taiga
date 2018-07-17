# Importing common provides default settings, see:
# https://github.com/taigaio/taiga-back/blob/master/settings/common.py
from .common import *


# Fetches an environment variable, and treats as a boolean.
# default state = false
#
# input: name of env var
# output: bool
def getenv_bool(envname: str) -> str:
    return envname in os.environ and os.getenv(envname).lower() == 'true'

#########################################
## PRIMARY DATABASE
#########################################

# RDS_* are the environment variables automatically created by
# elastic beanstalk. Specifying these here as backups allow the application
# to be more easily deployed there. They are only ever checked if the TAIGA_DB_*
# env vars don't exist.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('TAIGA_DB_NAME') or os.getenv('RDS_HOSTNAME'),
        'HOST': os.getenv('TAIGA_DB_HOST') or os.getenv('RDS_DB_NAME'),
        'USER': os.getenv('TAIGA_DB_USER') or os.getenv('RDS_USERNAME'),
        'PASSWORD': os.getenv('TAIGA_DB_PASSWORD') or os.getenv('RDS_PASSWORD'),
        'PORT': os.getenv('TAIGA_DB_PORT') or os.getenv('RDS_PORT') or '5432'
    }
}


#########################################
## HOSTNAME CONFIG
#########################################

TAIGA_HOSTNAME = os.getenv('TAIGA_HOSTNAME')

if getenv_bool("TAIGA_SSL") or getenv_bool("TAIGA_SSL_BY_REVERSE_PROXY"):
    PROTOCOL = 'https'
else:
    PROTOCOL = 'http'

SITES['api']['domain'] = TAIGA_HOSTNAME
SITES['front']['domain'] = TAIGA_HOSTNAME

SITES['api']['scheme'] = PROTOCOL
SITES['front']['scheme'] = PROTOCOL

MEDIA_URL  = PROTOCOL + '://' + TAIGA_HOSTNAME + '/media/'
STATIC_URL = PROTOCOL + '://' + TAIGA_HOSTNAME + '/static/'

SECRET_KEY = os.getenv('TAIGA_SECRET_KEY')

#########################################
## EVENTS/WEBSOCKETS
#########################################

if os.getenv('RABBIT_PORT') is not None and os.getenv('REDIS_PORT') is not None:
    from .celery import *

    BROKER_URL = 'amqp://guest:guest@rabbit:5672'
    CELERY_RESULT_BACKEND = 'redis://redis:6379/0'
    CELERY_ENABLED = True

    EVENTS_PUSH_BACKEND = "taiga.events.backends.rabbitmq.EventsPushBackend"
    EVENTS_PUSH_BACKEND_OPTIONS = {"url": "amqp://guest:guest@rabbit:5672//"}

#########################################
## EMAIL
#########################################

if getenv_bool('TAIGA_ENABLE_EMAIL'):


    DEFAULT_FROM_EMAIL = os.getenv('TAIGA_EMAIL_FROM')
    SERVER_EMAIL = os.getenv('TAIGA_EMAIL_FROM')

    # In seconds
    CHANGE_NOTIFICATIONS_MIN_INTERVAL = int(os.getenv('TAIGA_EMAIL_NOTIFICATIONS_INTERVAL') or 0)

    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    EMAIL_USE_TLS = getenv_bool('TAIGA_EMAIL_USE_TLS')
    EMAIL_HOST = os.getenv('TAIGA_EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('TAIGA_EMAIL_PORT'))
    EMAIL_HOST_USER = os.getenv('TAIGA_EMAIL_USER')
    EMAIL_HOST_PASSWORD = os.getenv('TAIGA_EMAIL_PASS')


#########################################
## REGISTRATION
#########################################

# Allow registration
PUBLIC_REGISTER_ENABLED = getenv_bool('PUBLIC_REGISTER_ENABLED')

# LIMIT ALLOWED DOMAINS FOR REGISTER AND INVITE
# None or [] values in USER_EMAIL_ALLOWED_DOMAINS means allow any domain
# USER_EMAIL_ALLOWED_DOMAINS = os.getenv('ALLOWED_REGISTER_DOMAINS').split(",") or None
if 'ALLOWED_REGISTER_DOMAINS' in os.environ:
    USER_EMAIL_ALLOWED_DOMAINS = os.getenv('ALLOWED_REGISTER_DOMAINS').split(",")
else:
    USER_EMAIL_ALLOWED_DOMAINS = None

DEBUG = getenv_bool('DEBUG')

# TEMPLATE_DEBUG = os.getenv('TEMPLATE_DEBUG'].lower() == 'true'

#########################################
## SLACK
#########################################

if getenv_bool('SLACK_ENABLED'):
    ## Slack
    # https://github.com/taigaio/taiga-contrib-slack
    INSTALLED_APPS += ["taiga_contrib_slack"]

#########################################
## LDAP
#########################################

if getenv_bool('LDAP_ENABLED'):

    ## Original LDAP
    # see https://github.com/ensky/taiga-contrib-ldap-auth
    # INSTALLED_APPS += ["taiga_contrib_ldap_auth"]

    ## Better LDAP plugin
    # see https://github.com/Monogramm/taiga-contrib-ldap-auth-ext
    # see https://github.com/benyanke/taiga-contrib-ldap-auth-ext
    INSTALLED_APPS += ["taiga_contrib_ldap_auth_ext"]

    LDAP_START_TLS = getenv_bool('LDAP_START_TLS')

    if getenv_bool('LDAP_USE_SSL'):
        LDAP_PROTOCOL = 'ldaps'
    else:
        LDAP_PROTOCOL = 'ldap'

    LDAP_SERVER = LDAP_PROTOCOL + '://' + os.getenv('LDAP_HOST')

    if os.getenv('LDAP_PORT') is not None:
        LDAP_PORT = int(os.getenv('LDAP_PORT'))

    # Full DN of the service account use to connect to LDAP server and search for login user's account entry
    # If LDAP_BIND_DN is not specified, or is blank, then an anonymous bind is attempated
    LDAP_BIND_DN = os.getenv('LDAP_BIND_DN')
    LDAP_BIND_PASSWORD = os.getenv('LDAP_BIND_PW')

    # Starting point within LDAP structure to search for login user
    LDAP_SEARCH_BASE = os.getenv('LDAP_SEARCH_BASE')


    ############
    # USED BY taiga_contrib_ldap_auth
    ###########

    LDAP_SEARCH_PROPERTY = os.getenv('LDAP_ATTR_EMAIL')
    LDAP_SEARCH_SUFFIX = None # for example: '@example.com'

    # Names of LDAP properties on user account to get email and full name
    LDAP_EMAIL_PROPERTY = os.getenv('LDAP_ATTR_EMAIL')
    LDAP_FULL_NAME_PROPERTY = os.getenv('LDAP_ATTR_FULLNAME')

    ############
    # USED BY taiga_contrib_ldap_auth_ext
    ###########

    # Extra LDAP filter to use when searching for user account
    LDAP_SEARCH_FILTER_ADDITIONAL = os.getenv('LDAP_SEARCH_FILTER')

    # Names of LDAP properties on user account to get email nd full name
    LDAP_USERNAME_ATTRIBUTE = os.getenv('LDAP_ATTR_USERNAME')
    LDAP_EMAIL_ATTRIBUTE = os.getenv('LDAP_ATTR_EMAIL')
    LDAP_FULL_NAME_ATTRIBUTE = os.getenv('LDAP_ATTR_FULLNAME')

    # This setting allows users to authenticate using local auth as well (external users not in LDAP)
    if getenv_bool("LDAP_ALLOW_NON_LDAP_LOGIN"):
        LDAP_FALLBACK = "normal"

    # MAP TO LOWERCASE
    # TODO: CLEANUP THESE FUNCTIONS
    def _ldap_slugify(id: str) -> str:
        # print("MODIFIER: " + id)
        # example: force lower-case
        id = id.lower()
        return id

    def _ldap_lc(id: str) -> str:
        # example: force lower-case
        id = id.lower()
        return id

    def _lowercase(id: str) -> str:
        # example: force lower-case
        id = id.lower()
        return id

    LDAP_MAP_USERNAME_TO_UID = _ldap_slugify

    USERNAME_MAPPER = _lowercase
    MAIL_MAPPER = _lowercase



#########################################
## FEEDBACK
#########################################

# Note: See config in taiga-front too
FEEDBACK_ENABLED = False
#FEEDBACK_EMAIL = "support@taiga.io"



#########################################
## STATS
#########################################

#STATS_ENABLED = False
#FRONT_SITEMAP_CACHE_TIMEOUT = 60*60  # In second


#########################################
## CELERY
#########################################
# Set to True to enable celery and work in async mode or False
# to disable it and work in sync mode. You can find the celery
# settings in settings/celery.py and settings/celery-local.py
#CELERY_ENABLED = True


#########################################
## IMPORTERS
#########################################

# Configuration for the GitHub importer
# Remember to enable it in the front client too.
#IMPORTERS["github"] = {
#    "active": True, # Enable or disable the importer
#    "client_id": "XXXXXX_get_a_valid_client_id_from_github_XXXXXX",
#    "client_secret": "XXXXXX_get_a_valid_client_secret_from_github_XXXXXX"
#}

# Configuration for the Trello importer
# Remember to enable it in the front client too.
#IMPORTERS["trello"] = {
#    "active": True, # Enable or disable the importer
#    "api_key": "XXXXXX_get_a_valid_api_key_from_trello_XXXXXX",
#    "secret_key": "XXXXXX_get_a_valid_secret_key_from_trello_XXXXXX"
#}

# Configuration for the Jira importer
# Remember to enable it in the front client too.
#IMPORTERS["jira"] = {
#    "active": True, # Enable or disable the importer
#    "consumer_key": "XXXXXX_get_a_valid_consumer_key_from_jira_XXXXXX",
#    "cert": "XXXXXX_get_a_valid_cert_from_jira_XXXXXX",
#    "pub_cert": "XXXXXX_get_a_valid_pub_cert_from_jira_XXXXXX"
#}

# Configuration for the Asane importer
# Remember to enable it in the front client too.
#IMPORTERS["asana"] = {
#    "active": True, # Enable or disable the importer
#    "callback_url": "{}://{}/project/new/import/asana".format(SITES["front"]["scheme"],
 #                                                              SITES["front"]["domain"]),
#    "app_id": "XXXXXX_get_a_valid_app_id_from_asana_XXXXXX",
#    "app_secret": "XXXXXX_get_a_valid_app_secret_from_asana_XXXXXX"
#}






#########################################
## MAIL SYSTEM SETTINGS
#########################################

#DEFAULT_FROM_EMAIL = "john@doe.com"
#CHANGE_NOTIFICATIONS_MIN_INTERVAL = 300 #seconds

# EMAIL SETTINGS EXAMPLE
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_USE_TLS = False
#EMAIL_USE_SSL = False # You cannot use both (TLS and SSL) at the same time!
#EMAIL_HOST = 'localhost'
#EMAIL_PORT = 25
#EMAIL_HOST_USER = 'user'
#EMAIL_HOST_PASSWORD = 'password'

# GMAIL SETTINGS EXAMPLE
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
#EMAIL_USE_TLS = True
#EMAIL_HOST = 'smtp.gmail.com'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'youremail@gmail.com'
#EMAIL_HOST_PASSWORD = 'yourpassword'


# PUCLIC OR PRIVATE NUMBER OF PROJECT PER USER
#MAX_PRIVATE_PROJECTS_PER_USER = None # None == no limit
#MAX_PUBLIC_PROJECTS_PER_USER = None # None == no limit
#MAX_MEMBERSHIPS_PRIVATE_PROJECTS = None # None == no limit
#MAX_MEMBERSHIPS_PUBLIC_PROJECTS = None # None == no limit

# GITHUB SETTINGS
#GITHUB_URL = "https://github.com/"
#GITHUB_API_URL = "https://api.github.com/"
#GITHUB_API_CLIENT_ID = "yourgithubclientid"
#GITHUB_API_CLIENT_SECRET = "yourgithubclientsecret"


#########################################
## THROTTLING
#########################################

#REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
#    "anon-write": "20/min",
#    "user-write": None,
#    "anon-read": None,
#    "user-read": None,
#    "import-mode": None,
#    "import-dump-mode": "1/minute",
#    "create-memberships": None,
#    "login-fail": None,
#    "register-success": None,
#    "user-detail": None,
#    "user-update": None,
#}

# This list should containt:
#  - Tiga users IDs
#  - Valid clients IP addresses (X-Forwarded-For header)
#REST_FRAMEWORK["DEFAULT_THROTTLE_WHITELIST"] = []

#SITE_ID = "api"


#########################################
## GENERIC
#########################################

#ADMINS = (
#    ("Admin", "example@example.com"),
#)

# DATABASES = {
#    'default': {
#        'ENGINE': 'django.db.backends.postgresql',
#        'NAME': 'taiga',
#        'USER': 'taiga',
#        'PASSWORD': 'changeme',
#        'HOST': '',
#        'PORT': '',
#    }
#}


#SITES = {
#    "api": {
#       "scheme": "http",
#       "domain": "localhost:8000",
#       "name": "api"
#    },
#    "front": {
#       "scheme": "http",
#       "domain": "localhost:9001",
#       "name": "front"
#    },
#}

#SITE_ID = "api"

#MEDIA_ROOT = '/home/taiga/media'
#STATIC_ROOT = '/home/taiga/static'
