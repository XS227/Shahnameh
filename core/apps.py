"""Core application configuration."""

from __future__ import annotations

import logging
import threading

from django.apps import AppConfig

logger = logging.getLogger(__name__)


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self) -> None:  # pragma: no cover - side effects on startup
        """Start the Telegram bot if the optional dependency is available."""

        try:
            from telegram_bot import run_bot
        except ModuleNotFoundError:
            logger.info("telegram_bot dependencies not installed; skipping bot startup")
            return
        except Exception as exc:  # noqa: BLE001 - log unexpected startup issues
            logger.warning("Unable to start telegram bot: %s", exc)
            return

        threading.Thread(target=run_bot, daemon=True).start()
