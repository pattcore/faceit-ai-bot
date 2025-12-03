import logging
from typing import Optional

import aiohttp

from ..config.settings import settings

logger = logging.getLogger(__name__)


class CaptchaProviderError(Exception):
    """Infrastructure or configuration error while talking to CAPTCHA provider."""


class CaptchaService:
    """Service for verifying CAPTCHA tokens (e.g. Cloudflare Turnstile).

    If CAPTCHA is not configured via settings, verification is effectively disabled
    and all requests are treated as passed.
    """

    def __init__(self) -> None:
        self.provider: str = (getattr(settings, "CAPTCHA_PROVIDER", "") or "").lower()
        self.turnstile_secret_key: Optional[str] = getattr(
            settings, "TURNSTILE_SECRET_KEY", None
        )
        self.smartcaptcha_secret_key: Optional[str] = getattr(
            settings, "SMARTCAPTCHA_SECRET_KEY", None
        )

    def is_enabled(self) -> bool:
        """Return True if CAPTCHA checks should be enforced."""
        if self.provider == "turnstile":
            return bool(self.turnstile_secret_key)

        if self.provider in ("smartcaptcha", "yandex_smartcaptcha", "yandex"):
            return bool(self.smartcaptcha_secret_key)

        return False

    async def verify_token(
        self,
        token: Optional[str],
        remote_ip: Optional[str] = None,
        action: Optional[str] = None,
        fail_open_on_error: bool = False,
    ) -> bool:
        """Verify CAPTCHA token.

        Returns True if verification passes or CAPTCHA is disabled.
        Returns False if verification fails.
        """
        if not self.is_enabled():
            # CAPTCHA is not configured – treat as passed
            return True

        if not token:
            return False

        try:
            if self.provider == "turnstile":
                return await self._verify_turnstile(
                    token,
                    remote_ip=remote_ip,
                    action=action,
                )

            if self.provider in ("smartcaptcha", "yandex_smartcaptcha", "yandex"):
                return await self._verify_smartcaptcha(
                    token,
                    remote_ip=remote_ip,
                )
        except CaptchaProviderError as exc:
            logger.error("CAPTCHA provider error for %s: %s", self.provider, exc)
            # For login-like flows we may choose fail-open (do not block user),
            # while for registration or sensitive operations we fail-closed.
            return True if fail_open_on_error else False

        # Unknown provider – fail open to avoid blocking legit users
        logger.warning("Unknown CAPTCHA provider configured: %s", self.provider)
        return True

    async def _verify_turnstile(
        self,
        token: str,
        remote_ip: Optional[str] = None,
        action: Optional[str] = None,
    ) -> bool:
        """Verify token against Cloudflare Turnstile API."""
        if not self.turnstile_secret_key:
            raise CaptchaProviderError("TURNSTILE_SECRET_KEY is not configured")

        data = {
            "secret": self.turnstile_secret_key,
            "response": token,
        }
        if remote_ip:
            data["remoteip"] = remote_ip

        url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, data=data) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning(
                            "Turnstile verification HTTP %s: %s", resp.status, text
                        )
                        raise CaptchaProviderError(
                            f"HTTP {resp.status}: {text.strip()}"
                        )

                    payload = await resp.json()
        except Exception as exc:  # pragma: no cover - network/SaaS errors
            logger.error("Turnstile verification error: %s", exc)
            raise CaptchaProviderError(str(exc))

        success = bool(payload.get("success"))

        # Optionally check action or hostname if needed in the future
        if not success:
            logger.info("Turnstile verification failed: %s", payload)

        return success

    async def _verify_smartcaptcha(
        self,
        token: str,
        remote_ip: Optional[str] = None,
    ) -> bool:
        """Verify token against Yandex SmartCaptcha API.

        According to current SmartCaptcha docs, validation is done via a
        POST request to https://smartcaptcha.cloud.yandex.ru/validate with
        x-www-form-urlencoded body: secret, token, optional ip.
        """
        if not self.smartcaptcha_secret_key:
            raise CaptchaProviderError("SMARTCAPTCHA_SECRET_KEY is not configured")

        data = {
            "secret": self.smartcaptcha_secret_key,
            "token": token,
        }
        if remote_ip:
            data["ip"] = remote_ip

        url = "https://smartcaptcha.cloud.yandex.ru/validate"

        try:
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, data=data) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        logger.warning(
                            "SmartCaptcha verification HTTP %s: %s", resp.status, text
                        )
                        raise CaptchaProviderError(
                            f"HTTP {resp.status}: {text.strip()}"
                        )

                    payload = await resp.json()
        except Exception as exc:  # pragma: no cover - network/SaaS errors
            logger.error("SmartCaptcha verification error: %s", exc)
            raise CaptchaProviderError(str(exc))

        status = payload.get("status")

        if status != "ok":
            logger.info("SmartCaptcha verification failed: %s", payload)
            return False

        return True


captcha_service = CaptchaService()
