import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shahnameh_game.settings')
app = Celery('shahnameh_game')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
