"""Business hours logic for Kalemera.

The store stops accepting orders at 23:00 Africa/Cairo time every day.
The open/closed state is computed from SERVER time in the configured
timezone, never from the client clock.
"""
import logging
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.config import settings

BUSINESS_TIMEZONE = "Africa/Cairo"
CLOSE_HOUR = 23  # 11:00 PM
CLOSED_MESSAGE_AR = "المكان خارج ساعات العمل"

_cairo_fallback_tz = timezone(timedelta(hours=2), "Africa/Cairo_approx")
_logger = logging.getLogger("kalmera.business_hours")


def get_settings_timezone() -> str:
    """Return the configured business timezone (respects Settings override)."""
    configured = getattr(settings, "BUSINESS_TIMEZONE", None)
    return configured or BUSINESS_TIMEZONE


def get_business_hours_enabled() -> bool:
    """Return whether business-hours enforcement is enabled."""
    return bool(getattr(settings, "ENABLE_BUSINESS_HOURS", True))


def _resolve_business_tz():
    """Return a ZoneInfo for the configured timezone.

    Falls back to an approximate Africa/Cairo offset (UTC+2) with a warning if the
    IANA database is unavailable (e.g. a platform without system tzdata). The app
    ships `tzdata` in requirements.txt so this should never happen in practice.
    """
    try:
        return ZoneInfo(get_settings_timezone())
    except (ZoneInfoNotFoundError, ValueError):
        _logger.warning(
            "IANA timezone database unavailable for %s; falling back to UTC+2 approximation.",
            get_settings_timezone(),
        )
        return _cairo_fallback_tz


def now_in_business_timezone() -> datetime:
    return datetime.now(_resolve_business_tz())


def is_store_closed(now: datetime | None = None) -> bool:
    """Return True when the store is closed (cannot accept new orders)."""
    if not get_business_hours_enabled():
        return False
    current = now or now_in_business_timezone()
    close_hour = int(getattr(settings, "BUSINESS_CLOSE_HOUR", CLOSE_HOUR))
    return current.hour >= close_hour


def closed_message() -> str:
    return CLOSED_MESSAGE_AR