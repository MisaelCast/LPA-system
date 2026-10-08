"""Helpers de tiempo con la zona horaria del negocio (configurable)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.config import settings


def zona_business() -> ZoneInfo:
    return ZoneInfo(settings.business_timezone)


def ahora_business() -> datetime:
    """Momento actual en la zona horaria del negocio."""
    return datetime.now(zona_business())


def hoy_business() -> date:
    """Fecha actual en la zona horaria del negocio."""
    return ahora_business().date()