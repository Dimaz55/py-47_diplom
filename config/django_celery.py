import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery("diplom")

app.config_from_object(settings, namespace="CELERY")
app.autodiscover_tasks(['users', 'main'])