import logging
from typing import Optional

import aiohttp

from ..config.settings import settings

logger = logging.getLogger(__name__)


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

    def is_enabled(self) -> bool:
        """Return True if CAPTCHA checks should be enforced."""
        return self.provider == "turnstile" and bool(self.turnstile_secret_key)

    async def verify_token(
        self,
        token: Optional[str],
        remote_ip: Optional[str] = None,
        action: Optional[str] = None,
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

        if self.provider == "turnstile":
            return await self._verify_turnstile(token, remote_ip=remote_ip, action=action)

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
            return False

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
                        return False

                    payload = await resp.json()
        except Exception as exc:  # pragma: no cover - network/SaaS errors
            logger.error("Turnstile verification error: %s", exc)
            return False

        success = bool(payload.get("success"))

        # Optionally check action or hostname if needed in the future
        if not success:
            logger.info("Turnstile verification failed: %s", payload)

        return success


captcha_service = CaptchaService()
