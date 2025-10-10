"""Celery application bootstrap with a graceful fallback for local dev."""

from __future__ import annotations

import os
from typing import Any

try:  # pragma: no cover - best effort import for full Celery support
    from celery import Celery  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - triggered in constrained envs
    class Celery:  # type: ignore[override]
        """Lightweight stand-in so local tooling can run without Celery."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            self.args = args
            self.kwargs = kwargs

        def config_from_object(self, *args: Any, **kwargs: Any) -> None:
            """Accept the call but perform no configuration."""

        def autodiscover_tasks(self, *args: Any, **kwargs: Any) -> None:
            """No-op task discovery when Celery is unavailable."""


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shahnameh_game.settings")
app = Celery("shahnameh_game")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
