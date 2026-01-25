"""Handlers package."""
from aiogram import Dispatcher

from .start import register_start_handlers
from .download import register_download_handlers
from .stats import register_stats_handlers
from .premium import register_premium_handlers


def register_handlers(dp: Dispatcher) -> None:
    """Register all handlers."""
    register_start_handlers(dp)
    register_download_handlers(dp)
    register_stats_handlers(dp)
    register_premium_handlers(dp)
