"""Unit tests for CaptchaService behavior."""

import pytest

from src.server.services.captcha_service import (
    CaptchaService,
    CaptchaProviderError,
)


@pytest.mark.asyncio
async def test_verify_token_returns_true_when_disabled(monkeypatch):
    service = CaptchaService()
    monkeypatch.setattr(service, "is_enabled", lambda: False)

    ok = await service.verify_token(token=None)

    assert ok is True


@pytest.mark.asyncio
async def test_verify_token_missing_token_returns_false_when_enabled(monkeypatch):
    service = CaptchaService()
    monkeypatch.setattr(service, "is_enabled", lambda: True)

    ok = await service.verify_token(token=None)

    assert ok is False


@pytest.mark.asyncio
async def test_verify_token_delegates_to_turnstile_success(monkeypatch):
    service = CaptchaService()
    monkeypatch.setattr(service, "is_enabled", lambda: True)
    monkeypatch.setattr(service, "provider", "turnstile")

    async def fake_verify(token: str, remote_ip=None, action=None):  # noqa: ARG001
        assert token == "token123"
        return True

    monkeypatch.setattr(service, "_verify_turnstile", fake_verify)

    ok = await service.verify_token(token="token123")

    assert ok is True


@pytest.mark.asyncio
async def test_verify_token_provider_error_fail_open(monkeypatch):
    service = CaptchaService()
    monkeypatch.setattr(service, "is_enabled", lambda: True)
    monkeypatch.setattr(service, "provider", "turnstile")

    async def fake_verify(token: str, remote_ip=None, action=None):  # noqa: ARG001
        raise CaptchaProviderError("temporary error")

    monkeypatch.setattr(service, "_verify_turnstile", fake_verify)

    ok = await service.verify_token(token="token123", fail_open_on_error=True)

    assert ok is True


@pytest.mark.asyncio
async def test_verify_token_provider_error_fail_closed(monkeypatch):
    service = CaptchaService()
    monkeypatch.setattr(service, "is_enabled", lambda: True)
    monkeypatch.setattr(service, "provider", "turnstile")

    async def fake_verify(token: str, remote_ip=None, action=None):  # noqa: ARG001
        raise CaptchaProviderError("temporary error")

    monkeypatch.setattr(service, "_verify_turnstile", fake_verify)

    ok = await service.verify_token(token="token123", fail_open_on_error=False)

    assert ok is False


@pytest.mark.asyncio
async def test_verify_token_unknown_provider_fails_open(monkeypatch):
    service = CaptchaService()
    monkeypatch.setattr(service, "is_enabled", lambda: True)
    monkeypatch.setattr(service, "provider", "unknown_provider")

    ok = await service.verify_token(token="any")

    assert ok is True
