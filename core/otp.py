import logging
import secrets

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def _key(phone: str, purpose: str) -> str:
    return f"otp:{purpose}:{phone}"


def send_otp(phone: str, purpose: str = "auth") -> str:
    code = f"{secrets.randbelow(10**6):06d}"
    cache.set(_key(phone, purpose), code, timeout=settings.OTP_TTL)
    logger.info("OTP for %s [%s]: %s", phone, purpose, code)
    return code


def verify_otp(phone: str, code: str, purpose: str = "auth") -> bool:
    cheat = getattr(settings, "OTP_CHEAT_CODE", "")
    # в debug пропускаем по тестовому коду, чтобы не зависеть от отправки sms
    if cheat and settings.DEBUG and secrets.compare_digest(str(code), str(cheat)):
        return True

    key = _key(phone, purpose)
    stored = cache.get(key)
    if stored and secrets.compare_digest(str(stored), str(code)):
        cache.delete(key)
        return True
    return False
