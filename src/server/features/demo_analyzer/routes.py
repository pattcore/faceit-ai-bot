import logging
import json
import os
import tempfile
import socket
import ipaddress
import hashlib
import secrets
import time
from urllib.parse import urlparse
from typing import Optional, Union

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx

from ..demo_analyzer.service import DemoAnalyzer
from ..demo_analyzer.models import DemoAnalysis
from ...auth.dependencies import get_optional_current_user
from ...database.connection import get_db
from ...database.models import User
from ...middleware.rate_limiter import rate_limiter
from ...services.rate_limit_service import rate_limit_service
from ...exceptions import DemoAnalysisException
from ...config.settings import settings
from ...tasks import analyze_demo_task

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/demo",
    tags=["demo"]
)

demo_analyzer = DemoAnalyzer()


MAX_DEMO_SIZE_MB = settings.MAX_DEMO_FILE_MB
MAX_DEMO_SIZE_BYTES = MAX_DEMO_SIZE_MB * 1024 * 1024
_SNIFF_BYTES = 4096
_SHARED_TMP_DIR = "/tmp_demos"

_UPLOAD_SESSION_TTL_SECONDS = int(os.getenv("UPLOAD_SESSION_TTL_SECONDS", "1200"))
_BOT_UPLOAD_SESSION_SECRET = os.getenv("BOT_UPLOAD_SESSION_SECRET")
_DEMO_PUBLIC_BASE_URL = os.getenv(
    "DEMO_PUBLIC_BASE_URL",
    "https://uploads.pattmsc.online/demos",
).rstrip("/")


def _upload_session_key(token: str) -> str:
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"upload_session:{digest}"


async def _get_redis_client():
    try:
        import redis.asyncio as redis  # type: ignore
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is not available",
        ) from exc

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="REDIS_URL is not configured",
        )

    return redis.from_url(redis_url, encoding="utf-8", decode_responses=True)


def _require_bot_secret(request: Request) -> None:
    if not _BOT_UPLOAD_SESSION_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="BOT_UPLOAD_SESSION_SECRET is not configured",
        )
    provided = request.headers.get("X-Bot-Secret")
    if not provided or provided != _BOT_UPLOAD_SESSION_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bot secret",
        )


async def enforce_demo_analyze_rate_limit(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    if current_user is None:
        return

    await rate_limit_service.enforce_user_operation_limit(
        db=db,
        user_id=int(current_user.id),
        operation="demo_analyze",
    )


class DemoAnalyzeUrlRequest(BaseModel):
    url: str
    language: str = "ru"
    user_id: Optional[Union[str, int]] = None


class CreateUploadSessionRequest(BaseModel):
    platform: str
    platform_user_id: str
    language: str = "ru"


class UploadDemoResponse(BaseModel):
    demo_url: str


def _is_private_address(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
        return bool(
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        pass

    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return True

    for info in infos:
        addr = info[4][0]
        try:
            ip = ipaddress.ip_address(addr)
        except ValueError:
            return True
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return True
    return False


async def _download_demo_to_shared_tmp(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise DemoAnalysisException(
            detail="Invalid URL. Only http/https are supported.",
            error_code="INVALID_URL",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if not parsed.hostname:
        raise DemoAnalysisException(
            detail="Invalid URL host.",
            error_code="INVALID_URL",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    if _is_private_address(parsed.hostname):
        raise DemoAnalysisException(
            detail="URL host is not allowed.",
            error_code="INVALID_URL_HOST",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    os.makedirs(_SHARED_TMP_DIR, exist_ok=True)

    tmp_path: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=_SHARED_TMP_DIR,
            prefix="demo_url_",
            suffix=".dem",
            delete=False,
        ) as tmp_file:
            tmp_path = tmp_file.name

            timeout = httpx.Timeout(connect=10.0, read=60.0, write=60.0, pool=10.0)
            limits = httpx.Limits(max_connections=5, max_keepalive_connections=5)
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=timeout,
                limits=limits,
                headers={"User-Agent": "faceit-ai-bot/1.0"},
            ) as client:
                async with client.stream("GET", url) as resp:
                    resp.raise_for_status()
                    content_length = resp.headers.get("Content-Length")
                    if content_length and content_length.isdigit():
                        if int(content_length) > MAX_DEMO_SIZE_BYTES:
                            raise DemoAnalysisException(
                                detail=f"File too large. Maximum allowed size is {MAX_DEMO_SIZE_MB} MB.",
                                error_code="FILE_TOO_LARGE",
                                status_code=status.HTTP_400_BAD_REQUEST,
                            )

                    total = 0
                    async for chunk in resp.aiter_bytes(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > MAX_DEMO_SIZE_BYTES:
                            raise DemoAnalysisException(
                                detail=f"File too large. Maximum allowed size is {MAX_DEMO_SIZE_MB} MB.",
                                error_code="FILE_TOO_LARGE",
                                status_code=status.HTTP_400_BAD_REQUEST,
                            )
                        tmp_file.write(chunk)

        return tmp_path
    except DemoAnalysisException:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise
    except httpx.HTTPError:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise DemoAnalysisException(
            detail="Failed to download demo from URL.",
            error_code="DEMO_DOWNLOAD_FAILED",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        logger.exception("Failed to download demo from URL")
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download demo from URL",
        )


@router.post(
    "/analyze",
    response_model=DemoAnalysis,
    summary="Demo file analysis",
    description=(
        "Analyzes uploaded CS2 demo file and "
        "returns detailed analysis"
    ),
    responses={
        200: {
            "description": "Analysis completed successfully"
        },
        400: {
            "description": "Invalid file",
            "content": {
                "application/json": {
                    "example": {
                        "error": "Invalid file format. Only .dem files are supported",
                        "error_code": "INVALID_FILE_FORMAT"
                    }
                }
            }
        },
        500: {
            "description": "Internal server error"
        }
    }
)
async def analyze_demo(
    demo: UploadFile = File(...),
    language: str = "ru",
    _: None = Depends(rate_limiter),
    __: None = Depends(enforce_demo_analyze_rate_limit),
):
    """
    CS2 demo file analysis

    Accepts demo file in .dem format and returns detailed game analysis,
    including player performance, round analysis and recommendations.
    """

    filename = (demo.filename or "").lower()
    if not filename.endswith(".dem"):
        raise DemoAnalysisException(
            detail="Invalid file format. Only .dem files are supported.",
            error_code="INVALID_FILE_FORMAT",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Read file into memory once to check size and basic content, then rewind
    content = await demo.read(MAX_DEMO_SIZE_BYTES + 1)

    if not content:
        raise DemoAnalysisException(
            detail="Empty file. Please upload a valid CS2 demo.",
            error_code="EMPTY_FILE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(content) > MAX_DEMO_SIZE_BYTES:
        raise DemoAnalysisException(
            detail=f"File too large. Maximum allowed size is {MAX_DEMO_SIZE_MB} MB.",
            error_code="FILE_TOO_LARGE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Very basic content sanity check: reject obviously textual/script files
    sniff = content[:_SNIFF_BYTES]
    lowered_sniff = sniff.lower()
    suspicious_markers = [
        b"<html",
        b"<script",
        b"<?php",
        b"#!/bin/bash",
        b"#!/usr/bin/env",
        b"import os",
        b"import sys",
    ]
    if any(marker in lowered_sniff for marker in suspicious_markers):
        raise DemoAnalysisException(
            detail="Invalid file content. Expected a binary CS2 demo file.",
            error_code="INVALID_FILE_CONTENT",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Rewind file so DemoAnalyzer can read it from the beginning
    demo.file.seek(0)

    return await demo_analyzer.analyze_demo(demo, language=language)


@router.post(
    "/analyze/background",
    summary="Demo file analysis in background",
)
async def analyze_demo_background(
    demo: UploadFile = File(...),
    language: str = "ru",
    _: None = Depends(rate_limiter),
    __: None = Depends(enforce_demo_analyze_rate_limit),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    filename = (demo.filename or "").lower()
    if not filename.endswith(".dem"):
        raise DemoAnalysisException(
            detail="Invalid file format. Only .dem files are supported.",
            error_code="INVALID_FILE_FORMAT",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    content = await demo.read(MAX_DEMO_SIZE_BYTES + 1)

    if not content:
        raise DemoAnalysisException(
            detail="Empty file. Please upload a valid CS2 demo.",
            error_code="EMPTY_FILE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(content) > MAX_DEMO_SIZE_BYTES:
        raise DemoAnalysisException(
            detail=f"File too large. Maximum allowed size is {MAX_DEMO_SIZE_MB} MB.",
            error_code="FILE_TOO_LARGE",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    sniff = content[:_SNIFF_BYTES]
    lowered_sniff = sniff.lower()
    suspicious_markers = [
        b"<html",
        b"<script",
        b"<?php",
        b"#!/bin/bash",
        b"#!/usr/bin/env",
        b"import os",
        b"import sys",
    ]
    if any(marker in lowered_sniff for marker in suspicious_markers):
        raise DemoAnalysisException(
            detail="Invalid file content. Expected a binary CS2 demo file.",
            error_code="INVALID_FILE_CONTENT",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    tmp_path: Optional[str] = None
    try:
        os.makedirs(_SHARED_TMP_DIR, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            dir=_SHARED_TMP_DIR,
            prefix="demo_",
            suffix=".dem",
            delete=False,
        ) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name

        user_id_value = None
        if current_user is not None and current_user.id is not None:
            user_id_value = str(current_user.id)

        task = analyze_demo_task.delay(
            demo_file_path=tmp_path,
            user_id=user_id_value,
            language=language,
        )

        return {
            "task_id": task.id,
            "status": "submitted",
        }
    except Exception:
        logger.exception("Failed to submit demo analysis task")
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit demo analysis task",
        )


@router.post(
    "/upload-sessions",
    summary="Create one-time upload session for bot demo upload",
)
async def create_upload_session(
    payload: CreateUploadSessionRequest,
    http_request: Request,
    _: None = Depends(rate_limiter),
):
    _require_bot_secret(http_request)
    language = payload.language
    if language not in {"ru", "en"}:
        language = "ru"
    token = secrets.token_urlsafe(32)
    key = _upload_session_key(token)
    redis_client = await _get_redis_client()
    value = {
        "status": "pending",
        "platform": payload.platform,
        "platform_user_id": payload.platform_user_id,
        "language": language,
        "created_at": int(time.time()),
    }
    await redis_client.setex(key, _UPLOAD_SESSION_TTL_SECONDS, json.dumps(value))
    return {
        "token": token,
        "expires_in_seconds": _UPLOAD_SESSION_TTL_SECONDS,
    }


@router.post(
    "/upload-sessions/{token}/claim",
    summary="Claim completed upload session (bot-only)",
)
async def claim_upload_session(
    token: str,
    http_request: Request,
    _: None = Depends(rate_limiter),
):
    _require_bot_secret(http_request)
    key = _upload_session_key(token)
    redis_client = await _get_redis_client()
    raw = await redis_client.get(key)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    try:
        data = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session")
    if data.get("status") != "ready":
        return {"status": data.get("status", "pending")}
    demo_url = data.get("demo_url")
    if not demo_url:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing demo_url")
    await redis_client.delete(key)
    return {
        "status": "ready",
        "demo_url": demo_url,
        "language": data.get("language", "ru"),
        "platform": data.get("platform"),
        "platform_user_id": data.get("platform_user_id"),
    }


@router.post(
    "/upload",
    response_model=UploadDemoResponse,
    summary="Upload demo file to shared storage (token required)",
)
async def upload_demo_file(
    demo: UploadFile = File(...),
    token: str = "",
    _: None = Depends(rate_limiter),
):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    key = _upload_session_key(token)
    redis_client = await _get_redis_client()
    raw = await redis_client.get(key)
    if not raw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    try:
        session_data = json.loads(raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session")

    if session_data.get("status") != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is not pending",
        )

    filename = (demo.filename or "").lower()
    if not filename.endswith(".dem"):
        raise DemoAnalysisException(
            detail="Invalid file format. Only .dem files are supported.",
            error_code="INVALID_FILE_FORMAT",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    os.makedirs(_SHARED_TMP_DIR, exist_ok=True)

    tmp_path: Optional[str] = None
    total = 0
    first_bytes = b""
    try:
        with tempfile.NamedTemporaryFile(
            dir=_SHARED_TMP_DIR,
            prefix="demo_upload_",
            suffix=".dem",
            delete=False,
        ) as tmp_file:
            tmp_path = tmp_file.name
            while True:
                chunk = await demo.read(1024 * 1024)
                if not chunk:
                    break
                if not first_bytes:
                    first_bytes = chunk[:_SNIFF_BYTES]
                total += len(chunk)
                if total > MAX_DEMO_SIZE_BYTES:
                    raise DemoAnalysisException(
                        detail=f"File too large. Maximum allowed size is {MAX_DEMO_SIZE_MB} MB.",
                        error_code="FILE_TOO_LARGE",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )
                tmp_file.write(chunk)

        lowered_sniff = (first_bytes or b"").lower()
        suspicious_markers = [
            b"<html",
            b"<script",
            b"<?php",
            b"#!/bin/bash",
            b"#!/usr/bin/env",
            b"import os",
            b"import sys",
        ]
        if any(marker in lowered_sniff for marker in suspicious_markers):
            raise DemoAnalysisException(
                detail="Invalid file content. Expected a binary CS2 demo file.",
                error_code="INVALID_FILE_CONTENT",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        public_name = os.path.basename(tmp_path)
        demo_url = f"{_DEMO_PUBLIC_BASE_URL}/{public_name}"

        session_data["status"] = "ready"
        session_data["demo_url"] = demo_url
        session_data["ready_at"] = int(time.time())
        await redis_client.setex(key, _UPLOAD_SESSION_TTL_SECONDS, json.dumps(session_data))

        return {"demo_url": demo_url}

    except DemoAnalysisException as exc:
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
            detail=getattr(exc, "detail", "Upload failed"),
        )
    except Exception:
        logger.exception("Failed to upload demo")
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload demo",
        )


@router.post(
    "/analyze/url/background",
    summary="Demo URL analysis in background",
)
async def analyze_demo_url_background(
    request: DemoAnalyzeUrlRequest,
    _: None = Depends(rate_limiter),
):
    tmp_path: Optional[str] = None
    try:
        tmp_path = await _download_demo_to_shared_tmp(request.url)

        user_id_value: Optional[str] = None
        if request.user_id is not None:
            user_id_value = str(request.user_id)

        task = analyze_demo_task.delay(
            demo_file_path=tmp_path,
            user_id=user_id_value,
            language=request.language,
        )
        return {
            "task_id": task.id,
            "status": "submitted",
        }
    except DemoAnalysisException as exc:
        raise HTTPException(
            status_code=getattr(exc, "status_code", status.HTTP_400_BAD_REQUEST),
            detail=getattr(exc, "detail", "Failed to submit demo analysis task"),
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to submit demo URL analysis task")
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit demo analysis task",
        )
