import os

from celery import Celery
from configurations import importer
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
if not os.environ.get("DJANGO_CONFIGURATION", None):
    os.environ.setdefault("DJANGO_CONFIGURATION", "Development")

importer.install()
app = Celery("apps.config.celery")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(settings.INSTALLED_APPS, related_name="tasks")
app.conf.broker_connection_retry_on_startup = True
