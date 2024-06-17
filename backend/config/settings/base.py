import os.path
from datetime import timedelta
from pathlib import Path

from configurations import Configuration
from configurations.values import BooleanValue, ListValue, Value


class Base(Configuration):
    DEBUG = BooleanValue(True)
    LOGIN_URL = "/login/"
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DOMAIN = Value("http://localhost:8000")
    ALLOWED_HOSTS = ("*",)
    ROOT_URLCONF = "config.urls"
    SECRET_KEY = Value("Development-key")
    INSTALLED_APPS = (
        "jazzmin",
        "pgtrigger",
        "colorfield",
        "solo",
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "rest_framework",
        "rest_framework.authtoken",
        "rest_framework_jwt",
        "django.contrib.sites",
        "django_filters",
        "drf_yasg",
        "corsheaders",
        "smsru",
        "django_celery_beat",
        "apps.user",
        "apps.market",
        "apps.credentials",
        "apps.content",
        "mptt",
        "restdoctor",
        "apps.shipping_and_payment",
        "rest_framework_simplejwt",
        "ckeditor",
        "ckeditor_uploader",
    )
    DATABASES = {
        "default": {
            # Используется PostgreSQL
            "ENGINE": Value(
                environ_name="DEFAULT_DATABASE_ENGINE",
                default="django.db.backends.postgresql",
            ),
            # Имя базы данных
            "NAME": Value(environ_name="DEFAULT_DATABASE_NAME", default="test_task"),
            # Имя пользователя
            "USER": Value(environ_name="DEFAULT_DATABASE_USER", default="test_task"),
            # Пароль пользователя
            "PASSWORD": Value(
                environ_name="DEFAULT_DATABASE_PASSWORD", default="some_pass"
            ),
            # Наименование контейнера для базы данных в Docker Compose
            "HOST": Value(environ_name="DEFAULT_DATABASE_HOST", default="localhost"),
            # Порт базы данных
            "PORT": Value(environ_name="DEFAULT_DATABASE_PORT", default="5436"),
        }
    }
    CELERY_BROKER_URL = Value("redis://localhost:6379")
    CELERY_RESULT_BACKEND = Value("redis://localhost:6379")
    CELERY_BEAT_SCHEDULE: dict = {}
    DISCORD_BOT_TOKEN = Value()
    ALLOW_ASYNC_UNSAFE = BooleanValue(True)
    SOLO_ADMIN_SKIP_OBJECT_LIST_PAGE = True
    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "restdoctor.django.middleware.api_selector.ApiSelectorMiddleware",
    ]

    # restdoctor
    API_FALLBACK_VERSION = "fallback"
    API_FALLBACK_FOR_APPLICATION_JSON_ONLY = False
    API_DEFAULT_VERSION = "v1"
    API_DEFAULT_FORMAT = "full"
    API_PREFIXES = ("/api",)
    API_FORMATS = ("full", "compact")
    API_RESOURCE_DISCRIMINATIVE_PARAM = "view_type"
    API_RESOURCE_DEFAULT = "common"
    API_RESOURCE_SET_PARAM = False
    API_RESOURCE_SET_PARAM_FOR_DEFAULT = False
    API_V1_URLCONF = "api.v1_urls"
    API_VERSIONS = {
        "fallback": ROOT_URLCONF,
        "v1": API_V1_URLCONF,
    }

    CORS_ORIGIN_ALLOW_ALL = True
    CORS_ALLOW_HEADERS = (  # noqa: static object
        "x-requested-with",
        "content-type",
        "accept",
        "origin",
        "authorization",
        "x-csrftoken",
        "token",
        "x-device-id",
        "x-device-type",
        "x-push-id",
        "dataserviceversion",
        "maxdataserviceversion",
        "content-disposition",
    )
    CORS_ALLOW_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS")
    CORS_ORIGIN_WHITELIST = ListValue(
        [
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
            "http://localhost:3000"
        ]
    )
    CSRF_TRUSTED_ORIGINS = ListValue(
        [
            "http://127.0.0.1:3000",
            "http://0.0.0.0:3000",
            "http://localhost:3000",
        ]
    )

    DADATA_API_TOKEN = "asd"

    TRACKER_CLIENTS: list = []

    SMS_RU = {
        "API_ID": Value(
            environ_name="SMS_RU_API_ID"
        ),  # если указан API ключ, логин и пароль пропускаем
        "LOGIN": Value(
            environ_name="SMS_RU_LOGIN"
        ),  # если нет API, то авторизуемся чезер логин и пароль
        "PASSWORD": Value(environ_name="SMS_RU_PASSWORD"),
        "TEST": BooleanValue(environ_name="SMS_RU_TEST", default=DEBUG),
        "SENDER": "GKSport",
    }

    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

    STATICFILES_DIRS = (BASE_DIR / "apps/" / "user/" / "static/",)
    STATIC_URL = "static/"
    STATIC_ROOT = BASE_DIR / "static/"
    MEDIA_ROOT = BASE_DIR / "media/"
    MEDIA_URL = "media/"

    DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
    LANGUAGE_CODE = "ru-RU"
    LANGUAGES = (("ru", "RU"), ("en", "EN"))
    LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)
    TIME_ZONE = "Europe/Moscow"
    USE_I18N = True
    USE_TZ = True

    LOGIN_REDIRECT_URL = "/"
    ACCOUNT_LOGOUT_REDIRECT_URL = "/"
    ACCOUNT_SIGNUP_REDIRECT_URL = "/"
    ACCOUNT_AUTHENTICATED_LOGIN_REDIRECTS = False
    ACCOUNT_AUTHENTICATION_METHOD = "username"

    SITE_ID = 1
    site_name = "GKSport"
    logo = "logo.svg"
    JAZZMIN_SETTINGS: dict = {
        "show_ui_builder": DEBUG,
        # title of the window (Will default to current_admin_site.site_title if absent or None)
        "site_title": site_name,
        # Title on the login screen (19 chars max) (defaults to current_admin_site.site_header if absent or None)
        "site_header": site_name,
        # Title on the brand (19 chars max) (defaults to current_admin_site.site_header if absent or None)
        "site_brand": site_name,
        # Logo to use for your site, must be present in static files, used for brand on top left
        "site_logo": logo,
        # Logo to use for your site, must be present in static files, used for login form logo (defaults to site_logo)
        "login_logo": logo,
        # Logo to use for login form in dark themes (defaults to login_logo)
        "login_logo_dark": logo,
        # CSS classes that are applied to the logo above
        "site_logo_classes": "img-clear",
        # Relative path to a favicon for your site, will default to site_logo if absent (ideally 32x32 px)
        "site_icon": logo,
        # Welcome text on the login screen
        "welcome_sign": "Добро пожаловать в административную панель сайта " + site_name,
        # Copyright on the footer
        "copyright": "GKSport",
        #############
        # Side Menu #
        #############
        # Whether to display the side menu
        "show_sidebar": True,
        # Whether to aut expand the menu
        "navigation_expanded": True,
        # Hide these apps when generating side menu e.g (auth)
        "hide_apps": [
            "sites",
            "authtoken",
            "django_celery_beat",
            "auth",
            "credentials",
            "smsru",
        ],
        # Hide these models when generating side menu (e.g auth.user)
        "hide_models": [],
        "topmenu_links": [
            {"app": "credentials"},
            {"app": "django_celery_beat"},
            {"app": "smsru"},
        ],
        "usermenu_links": [{"app": "market"}],
        # List of apps (and/or models) to base side menu ordering off of (does not need to contain all apps/models)
        # 'order_with_respect_to': ['auth', 'books', 'books.author', 'books.book'],
        # Custom icons for side menu apps/models See
        # https://fontawesome.com/icons?d=gallery&m=free&v=5.0.0,5.0.1,5.0.10,5.0.11,5.0.12,5.0.13,5.0.2,5.0.3,5.0.4,5.0.5,5.0.6,5.0.7,5.0.8,5.0.9,5.1.0,5.1.1,5.2.0,5.3.0,5.3.1,5.4.0,5.4.1,5.4.2,5.13.0,5.12.0,5.11.2,5.11.1,5.10.0,5.9.0,5.8.2,5.8.1,5.7.2,5.7.1,5.7.0,5.6.3,5.5.0,5.4.2
        # for the full list of 5.13.0 free icon classes
        "icons": {"user.user": "fas fa-users", "smsru.log": "fas fa-sms"},
        # Icons that are used when one is not manually specified
        "default_icon_parents": "fas fa-chevron-circle-right",
        "default_icon_children": "fas fa-circle",
        #################
        # Related Modal #
        #################
        # Use modals instead of popups
        "related_modal_active": True,
        #############
        # UI Tweaks #
        #############
        # Relative paths to custom CSS/JS scripts (must be present in static files)
        "custom_css": "jazzmin.css",
        "custom_js": "phone_number_mask.js",
        # Whether to link font from fonts.googleapis.com (use custom_css to supply font otherwise)
        "use_google_fonts_cdn": True,
        # Whether to show the UI customizer on the sidebar
        ###############
        # Change view #
        ###############
        # Render out the change view as a single form, or in tabs, current options are
        # - single
        # - horizontal_tabs (default)
        # - vertical_tabs
        # - collapsible
        # - carousel
        "changeform_format": "horizontal_tabs",
        # override change forms on a per modeladmin basis
        "changeform_format_overrides": {
            "auth.user": "horizontal_tabs",
            "auth.group": "horizontal_tabs",
        },
    }

    JAZZMIN_UI_TWEAKS = {
        "navbar_small_text": False,
        "footer_small_text": False,
        "body_small_text": False,
        "brand_small_text": False,
        "brand_colour": "navbar-dark-navy",
        "accent": "accent-navy",
        "navbar": "navbar-navy navbar-dark",
        "no_navbar_border": True,
        "navbar_fixed": False,
        "layout_boxed": False,
        "footer_fixed": False,
        "sidebar_fixed": False,
        "sidebar": "sidebar-light-navy",
        "sidebar_nav_small_text": False,
        "sidebar_disable_expand": False,
        "sidebar_nav_child_indent": True,
        "sidebar_nav_compact_style": True,
        "sidebar_nav_legacy_style": False,
        "sidebar_nav_flat_style": False,
        "theme": "minty",
        "dark_mode_theme": None,
        "button_classes": {
            "primary": "btn-primary",
            "secondary": "btn-secondary",
            "info": "btn-info",
            "warning": "btn-warning",
            "danger": "btn-danger",
            "success": "btn-success",
        },
        "actions_sticky_top": True,
    }
    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(days=100),
        "REFRESH_TOKEN_LIFETIME": timedelta(days=300),
    }
    # DRF
    REST_FRAMEWORK = {
        "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
        "PAGE_SIZE": 100,
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"
        ],
        "DEFAULT_RENDERER_CLASSES": [
            "rest_framework.renderers.JSONRenderer",
            "rest_framework.renderers.BrowsableAPIRenderer",
        ],
        "DEFAULT_PARSER_CLASSES": [
            "rest_framework.parsers.JSONParser",
            "rest_framework.parsers.FormParser",
            "rest_framework.parsers.MultiPartParser",
        ],
        "DEFAULT_FILTER_BACKENDS": [
            "django_filters.rest_framework.DjangoFilterBackend",
        ],
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework.authentication.BasicAuthentication",
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ),
    }
    SWAGGER_SETTINGS = {"USE_SESSION_AUTH": False}
    REST_USE_JWT = True
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
        "apps.user.auth_backend.PasswordlessAuthBackend",
    ]
    AUTH_PASSWORD_VALIDATORS = [
        {
            "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        },
        {
            "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        },
    ]
    AUTH_USER_MODEL = "user.User"

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": (os.path.join(BASE_DIR, "templates"),),
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "django.template.context_processors.media",
                ],
            },
        },
    ]

    CKEDITOR_UPLOAD_PATH = 'uploads/'
    CKEDITOR_SETTINGS = {'skin': 'moono'}
    CKEDITOR_CONFIGS = {
        'versionCheck': False,
        'default': {
            'toolbar': [
                [
                    'Undo',
                    'Redo',
                    '-',
                    'Bold',
                    'Italic',
                    'Underline',
                    '-',
                    'Link',
                    'Unlink',
                    'Anchor',
                    'NumberedList',
                    'BulletedList',
                ],
                [
                    'JustifyLeft',
                    'JustifyCenter',
                    'JustifyRight',
                    'JustifyBlock',
                    '-',
                    'Outdent',
                    'Indent',
                    'Styles',
                    'TextColor',
                    '-',
                    'HorizontalRule',
                    '-',
                    'Blockquote',
                ],
            ],
            'height': 200,
            'width': '100%',
            'toolbarCanCollapse': False,
            'forcePasteAsPlainText': True,
        }
    }
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'formatter': 'verbose',
                'class': 'logging.handlers.RotatingFileHandler',
                'maxBytes': 10000000,
                'backupCount': 5,
                'filename': os.path.join(BASE_DIR, 'cdek.log'),
            },
        },
        'loggers': {
            'cdek': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            }
        },
        'formatters': {
            'verbose': {
                'format': '{asctime} {levelname} {module} --- {message}',
                'style': '{',
            },
        },
    }
    MPTT_ALLOW_TESTING_GENERATORS = True
    DEFAULT_LEVEL_INDICATOR = 1
