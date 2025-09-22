# apps.py
from django.apps import AppConfig
import threading

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        from telegram_bot import run_bot
        threading.Thread(target=run_bot, daemon=True).start()
