"""Authentication endpoints"""

from datetime import datetime, timedelta
import logging
import secrets
import hashlib
import base64
from urllib.parse import urlencode

import aiohttp
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .schemas import Token, UserResponse, SteamLinkRequest
from .security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    create_refresh_token,
    hash_refresh_token,
)
from .dependencies import get_current_active_user
from ..config.settings import settings
from ..middleware.rate_limiter import rate_limiter
from ..database.connection import get_db
from ..database.models import (
    User,
    Subscription,
    SubscriptionTier,
    TeammateProfile as TeammateProfileDB,
    UserSession,
)
from ..services.captcha_service import captcha_service
from ..metrics_business import ACTIVE_USERS

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"
STEAM_API_PLAYER_SUMMARIES_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"

FACEIT_AUTHORIZATION_URL = "https://accounts.faceit.com"
FACEIT_TOKEN_URL = "https://api.faceit.com/auth/v1/oauth/token"
FACEIT_USERINFO_URL = "https://api.faceit.com/auth/v1/resources/userinfo"


async def verify_steam_openid(query_params) -> str | None:
    """Verify Steam OpenID response and return steam_id if valid.

    This posts back the signed fields to Steam's OpenID endpoint with
    `check_authentication` mode and checks for `is_valid:true` in response.
    """

    params = dict(query_params)

    # Basic sanity check
    if params.get("openid.mode") not in {"id_res", "checkid_immediate", "checkid_setup"}:
        return None

    payload = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "check_authentication",
        "openid.assoc_handle": params.get("openid.assoc_handle", ""),
        "openid.signed": params.get("openid.signed", ""),
        "openid.sig": params.get("openid.sig", ""),
    }

    signed = params.get("openid.signed", "")
    for var in signed.split(","):
        key = f"openid.{var}"
        if key in params:
            payload[key] = params[key]

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(STEAM_OPENID_URL, data=payload) as resp:
                text = await resp.text()
                if "is_valid:true" not in text:
                    logger.warning("Steam OpenID validation failed: %s", text.strip())
                    return None
    except Exception as e:  # pragma: no cover - network errors are logged
        logger.error("Steam OpenID verification error: %s", str(e))
        return None

    claimed_id = params.get("openid.claimed_id")
    if not claimed_id:
        return None

    # Example: https://steamcommunity.com/openid/id/76561198000000000
    steam_id = claimed_id.rstrip("/").split("/")[-1]
    return steam_id or None


async def fetch_steam_persona_name(steam_id: str) -> str | None:
    api_key = getattr(settings, "STEAM_WEB_API_KEY", None)
    if not api_key:
        return None

    params = {
        "key": api_key,
        "steamids": steam_id,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                STEAM_API_PLAYER_SUMMARIES_URL,
                params=params,
            ) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(
                        "Steam GetPlayerSummaries error %s: %s",
                        resp.status,
                        text,
                    )
                    return None
                data = await resp.json()
    except Exception as e:  # pragma: no cover - network errors are logged
        logger.error("Steam GetPlayerSummaries request error: %s", str(e))
        return None

    players = (data.get("response") or {}).get("players") or []
    if not players:
        return None

    persona_name = players[0].get("personaname")
    if not persona_name:
        return None

    return str(persona_name)


@router.get("/steam/login")
async def steam_login(request: Request):
    """Redirect user to Steam OpenID for authentication.

    External entry point used by frontend "Sign in with Steam" button.
    """

    remote_ip = request.client.host if request.client else None
    captcha_token = request.query_params.get("captcha_token")

    # For Steam login we do not want to hard-block users when captcha_token
    # is missing, but we still validate it when present and CAPTCHA is enabled.
    captcha_ok = True
    if captcha_service.is_enabled() and captcha_token:
        captcha_ok = await captcha_service.verify_token(
            token=captcha_token,
            remote_ip=remote_ip,
            action="auth_steam_login",
            fail_open_on_error=True,
        )
    elif captcha_service.is_enabled() and not captcha_token:
        logger.warning(
            "Steam login called without captcha_token while CAPTCHA is enabled",
        )

    if captcha_service.is_enabled() and not captcha_ok:
        raise HTTPException(
            status_code=400,
            detail="CAPTCHA verification failed",
        )

    realm = settings.WEBSITE_URL.rstrip("/")
    # Nginx adds /api prefix for backend, so callback is exposed as /api/auth/steam/callback
    return_to = f"{realm}/api/auth/steam/callback"

    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": return_to,
        "openid.realm": realm,
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
    }

    url = f"{STEAM_OPENID_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/faceit/login")
async def faceit_login(request: Request):
    """Redirect user to FACEIT OAuth2 for authentication.

    Uses Authorization Code flow. After successful login FACEIT will redirect
    back to /api/auth/faceit/callback with a temporary code and our signed
    state token.
    """

    remote_ip = request.client.host if request.client else None
    captcha_token = request.query_params.get("captcha_token")

    captcha_ok = True
    if captcha_service.is_enabled() and captcha_token:
        captcha_ok = await captcha_service.verify_token(
            token=captcha_token,
            remote_ip=remote_ip,
            action="auth_faceit_login",
            fail_open_on_error=True,
        )
    elif captcha_service.is_enabled() and not captcha_token:
        logger.warning(
            "Faceit login called without captcha_token while CAPTCHA is enabled",
        )

    if captcha_service.is_enabled() and not captcha_ok:
        raise HTTPException(
            status_code=400,
            detail="CAPTCHA verification failed",
        )

    client_id = getattr(settings, "FACEIT_CLIENT_ID", None)
    client_secret = getattr(settings, "FACEIT_CLIENT_SECRET", None)
    if not client_id or not client_secret:
        logger.error("FACEIT OAuth is not configured: missing client id/secret")
        raise HTTPException(
            status_code=500,
            detail="Faceit OAuth is not configured",
        )

    redirect_uri = f"{settings.WEBSITE_URL.rstrip('/')}/api/auth/faceit/callback"

    # PKCE: generate code_verifier and code_challenge (S256)
    code_verifier = secrets.token_urlsafe(64)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode("utf-8")).digest()
    ).rstrip(b"=").decode("ascii")

    # Short-lived signed state to protect against CSRF
    state_token = create_access_token(
        data={"sub": "faceit_oauth", "cv": code_verifier},
        expires_delta=timedelta(minutes=10),
    )

    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state_token,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }

    url = f"{FACEIT_AUTHORIZATION_URL}?{urlencode(params)}"
    return RedirectResponse(url)


@router.get("/faceit/callback")
async def faceit_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle FACEIT OAuth2 callback, create/find user and issue JWT.

    On success redirects back to frontend /auth with faceit_token and auto=1
    to trigger automatic player analysis for the logged-in user.
    """

    params = dict(request.query_params)
    code = params.get("code")
    state = params.get("state")

    if not code or not state:
        raise HTTPException(
            status_code=400,
            detail="Missing authorization code or state",
        )

    state_payload = decode_access_token(state)
    if not state_payload or state_payload.get("sub") != "faceit_oauth":
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    code_verifier = state_payload.get("cv")
    if not code_verifier:
        logger.error("FACEIT OAuth state missing code_verifier")
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    client_id = getattr(settings, "FACEIT_CLIENT_ID", None)
    client_secret = getattr(settings, "FACEIT_CLIENT_SECRET", None)
    if not client_id or not client_secret:
        logger.error("FACEIT OAuth is not configured: missing client id/secret")
        raise HTTPException(
            status_code=500,
            detail="Faceit OAuth is not configured",
        )

    redirect_uri = f"{settings.WEBSITE_URL.rstrip('/')}/api/auth/faceit/callback"

    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            token_data = None
            # Exchange code for tokens
            async with session.post(
                FACEIT_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier,
                },
                headers={"Accept": "application/json"},
                auth=aiohttp.BasicAuth(client_id, client_secret),
            ) as token_resp:
                if token_resp.status != 200:
                    text = await token_resp.text()
                    logger.error(
                        "FACEIT token endpoint error %s: %s",
                        token_resp.status,
                        text,
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Faceit authentication failed",
                    )
                token_data = await token_resp.json()

            access_token_faceit = token_data.get("access_token")
            if not access_token_faceit:
                logger.error("FACEIT token response missing access_token: %s", token_data)
                raise HTTPException(
                    status_code=400,
                    detail="Faceit authentication failed",
                )

            # Fetch user info
            async with session.get(
                FACEIT_USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token_faceit}",
                    "Accept": "application/json",
                },
            ) as userinfo_resp:
                if userinfo_resp.status != 200:
                    text = await userinfo_resp.text()
                    logger.error(
                        "FACEIT userinfo endpoint error %s: %s",
                        userinfo_resp.status,
                        text,
                    )
                    raise HTTPException(
                        status_code=400,
                        detail="Faceit authentication failed",
                    )
                userinfo = await userinfo_resp.json()
    except HTTPException:
        raise
    except Exception as e:  # pragma: no cover - network errors are logged
        logger.error("FACEIT OAuth callback error: %s", str(e))
        raise HTTPException(
            status_code=400,
            detail="Faceit authentication failed",
        )

    faceit_guid = (
        userinfo.get("guid")
        or userinfo.get("sub")
        or userinfo.get("user_id")
    )
    if not faceit_guid:
        logger.error("FACEIT userinfo missing guid/sub/user_id: %s", userinfo)
        raise HTTPException(
            status_code=400,
            detail="Faceit authentication failed",
        )

    email = userinfo.get("email")
    nickname = (
        userinfo.get("nickname")
        or userinfo.get("preferred_username")
        or userinfo.get("name")
        or f"faceit_{faceit_guid}"
    )

    # Try to find existing user by faceit_id
    user = db.execute(
        select(User).where(User.faceit_id == faceit_guid)
    ).scalars().first()

    if not user and email:
        # Try to link to existing account with same email
        user = db.execute(
            select(User).where(User.email == email)
        ).scalars().first()
        if user and user.faceit_id and user.faceit_id != faceit_guid:
            logger.warning(
                "Email %s already linked to a different FACEIT id %s",
                email,
                user.faceit_id,
            )
            raise HTTPException(
                status_code=400,
                detail="This email is already linked to another Faceit account",
            )

    if not user:
        # Create synthetic email if needed or if it's already taken
        if email:
            existing_email_user = db.execute(
                select(User).where(User.email == email)
            ).scalars().first()
            if existing_email_user:
                email = None

        if not email:
            email = f"faceit_{faceit_guid}@faceit.local"

        # Ensure unique username
        base_username = nickname
        username = base_username
        suffix = 1
        while db.execute(
            select(User).where(User.username == username)
        ).scalars().first():
            username = f"{base_username}_{suffix}"
            suffix += 1

        random_password = secrets.token_urlsafe(16)
        hashed_password = get_password_hash(random_password)

        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            faceit_id=faceit_guid,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE)
        db.add(subscription)
        db.commit()
    else:
        updated = False

        # Link FACEIT account if not already linked
        if not user.faceit_id:
            user.faceit_id = faceit_guid
            updated = True

        # If user still has legacy faceit_<id> username, try to replace it with nickname
        if nickname and user.username:
            legacy_prefix = f"faceit_{faceit_guid}"
            if user.username == legacy_prefix:
                base_username = nickname
                username = base_username
                suffix = 1
                while db.execute(
                    select(User).where(User.username == username)
                ).scalars().first():
                    username = f"{base_username}_{suffix}"
                    suffix += 1
                user.username = username
                updated = True

        if updated:
            db.add(user)
            db.commit()
            db.refresh(user)

    # Sync teammate search profile with Faceit data for this user
    try:
        from ..integrations.faceit_client import FaceitAPIClient

        faceit_client = FaceitAPIClient()
        faceit_player = await faceit_client.get_player_by_nickname(nickname)

        elo = None
        level = None
        if isinstance(faceit_player, dict):
            game_data = (faceit_player.get("games") or {}).get("cs2") or {}
            elo = game_data.get("faceit_elo")
            level = game_data.get("skill_level")

        profile = (
            db.query(TeammateProfileDB)
            .filter(TeammateProfileDB.user_id == user.id)
            .first()
        )
        if not profile:
            profile = TeammateProfileDB(user_id=user.id)
            db.add(profile)

        profile.faceit_nickname = nickname
        if elo is not None:
            profile.elo = elo
        if level is not None:
            profile.level = level
        profile.updated_at = datetime.utcnow()

        db.commit()
    except Exception:
        logger.exception("Failed to sync teammate profile from Faceit on login")
        db.rollback()

    try:
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update login activity for user {user.id}: {str(e)}")

    try:
        ACTIVE_USERS.inc()
    except Exception:
        pass

    access_token = create_access_token(data={"sub": str(user.id)})

    # Issue refresh token session for Faceit login as well
    refresh_token = create_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    now = datetime.utcnow()
    session = UserSession(
        user_id=user.id,
        token_hash=refresh_hash,
        created_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=(request.headers.get("user-agent") or "")[:255],
        ip_address=request.client.host if request.client else None,
    )
    try:
        db.add(session)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create refresh session for Faceit login user %s: %s",
            user.id,
            str(e),
        )
        session = None

    redirect_url = f"{settings.WEBSITE_URL.rstrip('/')}/auth?faceit_token={access_token}&auto=1"

    response = RedirectResponse(redirect_url)
    secure_cookie = settings.WEBSITE_URL.startswith("https://") and (
        request.url.hostname not in ("testserver", "localhost")
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    if session is not None:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    return response


@router.get("/steam/callback")
async def steam_callback(
    request: Request,
    db: Session = Depends(get_db),
):
    """Handle Steam OpenID callback, create/find user and issue JWT.

    On success redirects back to frontend /auth with steam_token and auto=1
    to trigger automatic player analysis for the logged-in user.
    """

    steam_id = await verify_steam_openid(request.query_params)
    if not steam_id:
        raise HTTPException(status_code=400, detail="Steam authentication failed")

    steam_persona_name = await fetch_steam_persona_name(steam_id)

    # Find existing user by steam_id, or create a new one
    user = db.execute(
        select(User).where(User.steam_id == steam_id)
    ).scalars().first()

    if not user:
        # Create synthetic email based on steam_id
        email = f"steam_{steam_id}@steam.local"

        # Prefer real Steam persona name as username when available
        base_username = steam_persona_name or f"steam_{steam_id}"
        username = base_username
        suffix = 1
        while db.execute(
            select(User).where(User.username == username)
        ).scalars().first():
            username = f"{base_username}_{suffix}"
            suffix += 1

        random_password = secrets.token_urlsafe(16)
        hashed_password = get_password_hash(random_password)

        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            steam_id=steam_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        subscription = Subscription(user_id=user.id, tier=SubscriptionTier.FREE)
        db.add(subscription)
        db.commit()
    else:
        # Ensure steam_id is stored if user existed without it
        updated = False
        if not user.steam_id:
            user.steam_id = steam_id
            updated = True

        # If user still has legacy steam_<id> username, try to replace it with persona name
        if steam_persona_name and user.username:
            legacy_prefix = f"steam_{steam_id}"
            if user.username == legacy_prefix:
                base_username = steam_persona_name
                username = base_username
                suffix = 1
                while db.execute(
                    select(User).where(User.username == username)
                ).scalars().first():
                    username = f"{base_username}_{suffix}"
                    suffix += 1
                user.username = username
                updated = True

        if updated:
            db.add(user)
            db.commit()
            db.refresh(user)

    try:
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update login activity for user {user.id}: {str(e)}")

    try:
        ACTIVE_USERS.inc()
    except Exception:
        pass

    access_token = create_access_token(data={"sub": str(user.id)})

    # Issue refresh token session for Steam login as well
    refresh_token = create_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    now = datetime.utcnow()
    session = UserSession(
        user_id=user.id,
        token_hash=refresh_hash,
        created_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=(request.headers.get("user-agent") or "")[:255],
        ip_address=request.client.host if request.client else None,
    )
    try:
        db.add(session)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create refresh session for Steam login user %s: %s",
            user.id,
            str(e),
        )
        session = None

    # Redirect back to frontend auth page, which will store the token and
    # then redirect to /analysis?auto=1 for immediate player analysis.
    redirect_url = f"{settings.WEBSITE_URL.rstrip('/')}/auth?steam_token={access_token}&auto=1"

    response = RedirectResponse(redirect_url)
    secure_cookie = settings.WEBSITE_URL.startswith("https://") and (
        request.url.hostname not in ("testserver", "localhost")
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    if session is not None:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    return response


@router.post("/register", response_model=Token)
async def register(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    """Register new user"""
    try:
        email = None
        username = None
        password = None
        faceit_id = None

        # Parse request body - try FormData first, then JSON
        content_type = request.headers.get("content-type", "")

        is_form = (
            "multipart/form-data" in content_type
            or "application/x-www-form-urlencoded" in content_type
        )
        if is_form:
            form = await request.form()
            email = form.get("email")
            username = form.get("username")
            password = form.get("password")
            faceit_id = form.get("faceit_id")
            captcha_token = form.get("captcha_token")
        else:
            body = await request.json()
            email = body.get("email")
            username = body.get("username")
            password = body.get("password")
            faceit_id = body.get("faceit_id")
            captcha_token = body.get("captcha_token")

        if not email or not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: email, username, password",
            )

        remote_ip = request.client.host if request.client else None
        captcha_ok = await captcha_service.verify_token(
            token=captcha_token,
            remote_ip=remote_ip,
            action="auth_register",
        )
        if not captcha_ok:
            raise HTTPException(
                status_code=400,
                detail="CAPTCHA verification failed",
            )

        # Validate email format
        if "@" not in email:
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Validate password strength: length + basic complexity
        password_error = (
            "Password must be at least 8 characters long and contain "
            "at least one letter and one digit"
        )
        if len(password) < 8:
            raise HTTPException(
                status_code=400,
                detail=password_error,
            )

        if not any(c.isalpha() for c in password) or not any(c.isdigit() for c in password):
            raise HTTPException(
                status_code=400,
                detail=password_error,
            )

        existing = db.execute(
            select(User).where(User.email == email)
        ).scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = get_password_hash(password)

        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            faceit_id=faceit_id,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        subscription = Subscription(
            user_id=new_user.id, tier=SubscriptionTier.FREE
        )
        db.add(subscription)
        db.commit()

        try:
            new_user.last_login = datetime.utcnow()
            new_user.login_count = (new_user.login_count or 0) + 1
            db.add(new_user)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to update login activity for newly registered user %s: %s",
                new_user.id,
                exc,
            )

        access_token = create_access_token(data={"sub": str(new_user.id)})
        refresh_token = create_refresh_token()
        refresh_hash = hash_refresh_token(refresh_token)
        now = datetime.utcnow()
        session = UserSession(
            user_id=new_user.id,
            token_hash=refresh_hash,
            created_at=now,
            expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            user_agent=(request.headers.get("user-agent") or "")[:255],
            ip_address=remote_ip,
        )
        try:
            db.add(session)
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.error(
                "Failed to create refresh session for newly registered user %s: %s",
                new_user.id,
                exc,
            )
            session = None

        secure_cookie = settings.WEBSITE_URL.startswith("https://") and (
            request.url.hostname not in ("testserver", "localhost")
        )
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=60 * 60 * 24 * 30,
        )

        if session is not None:
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=secure_cookie,
                samesite="lax",
                max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            )

        try:
            ACTIVE_USERS.inc()
        except Exception:
            pass

        logger.info(f"New user registered: {new_user.email}")

        return Token(access_token=access_token, token_type="bearer")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    """Login user"""
    # Try to get form data first
    captcha_token = None
    try:
        form = await request.form()
        if form:
            # Support both email and username
            email = form.get("email") or form.get("username")
            password = form.get("password")
            captcha_token = form.get("captcha_token")
        else:
            body = await request.json()
            # Support both email and username
            email = body.get("email") or body.get("username")
            password = body.get("password")
            captcha_token = body.get("captcha_token")
    except Exception:
        body = await request.json()
        # Support both email and username
        email = body.get("email") or body.get("username")
        password = body.get("password")
        captcha_token = body.get("captcha_token")

    origin = request.headers.get("origin") or ""
    skip_captcha_for_extension = origin.startswith("chrome-extension://")

    remote_ip = request.client.host if request.client else None
    if not skip_captcha_for_extension:
        captcha_ok = await captcha_service.verify_token(
            token=captcha_token,
            remote_ip=remote_ip,
            action="auth_login",
            fail_open_on_error=True,
        )
        if not captcha_ok:
            raise HTTPException(
                status_code=400,
                detail="CAPTCHA verification failed",
            )

    user = db.execute(
        select(User).where(User.email == email)
    ).scalars().first()

    if not user or not verify_password(password, user.hashed_password):
        try:
            if rate_limiter.redis_client is not None:
                client_ip = rate_limiter._get_client_ip(request)
                await rate_limiter._register_violation_and_maybe_ban(
                    client_ip,
                    None,
                )
        except Exception:
            logger.exception("Failed to register login rate limit violation")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400, detail="User account is inactive"
        )

    try:
        user.last_login = datetime.utcnow()
        user.login_count = (user.login_count or 0) + 1
        db.add(user)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update login activity for user {user.id}: {str(e)}")

    try:
        ACTIVE_USERS.inc()
    except Exception:
        pass

    access_token = create_access_token(data={"sub": str(user.id)})

    # Create refresh token session
    refresh_token = create_refresh_token()
    refresh_hash = hash_refresh_token(refresh_token)
    now = datetime.utcnow()
    session = UserSession(
        user_id=user.id,
        token_hash=refresh_hash,
        created_at=now,
        expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=(request.headers.get("user-agent") or "")[:255],
        ip_address=remote_ip,
    )
    try:
        db.add(session)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(
            "Failed to create refresh session for user %s during login: %s",
            user.id,
            str(e),
        )
        session = None

    # Set httpOnly cookie for 30 days in addition to returning the token in JSON
    secure_cookie = settings.WEBSITE_URL.startswith("https://") and (
        request.url.hostname not in ("testserver", "localhost")
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )

    if session is not None:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=secure_cookie,
            samesite="lax",
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )

    logger.info(f"User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
):
    """Get current user info"""
    return current_user


@router.post("/logout")
async def logout_user(request: Request, response: Response, db: Session = Depends(get_db)):
    """Logout user by clearing auth cookies and revoking refresh session if present"""

    refresh_cookie = request.cookies.get("refresh_token")
    if refresh_cookie:
        token_hash = hash_refresh_token(refresh_cookie)
        try:
            session = (
                db.execute(
                    select(UserSession).where(UserSession.token_hash == token_hash)
                )
                .scalars()
                .first()
            )
            if session and session.revoked_at is None:
                session.revoked_at = datetime.utcnow()
                db.add(session)
                db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to revoke refresh token on logout: {str(e)}")

    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"detail": "Logged out"}


@router.post("/refresh")
async def refresh_access_token(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Refresh access token using a valid refresh_token cookie and active session."""

    raw_refresh = request.cookies.get("refresh_token")
    if not raw_refresh:
        # Clear any stale refresh cookie and return 401
        response.delete_cookie(key="refresh_token")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"detail": "Not authenticated"}

    token_hash = hash_refresh_token(raw_refresh)
    now = datetime.utcnow()

    session = (
        db.execute(
            select(UserSession)
            .where(UserSession.token_hash == token_hash)
            .where(UserSession.revoked_at.is_(None))
            .where(UserSession.expires_at > now)
        )
        .scalars()
        .first()
    )

    if not session:
        # Invalid or expired refresh token: clear cookie and return 401
        response.delete_cookie(key="refresh_token")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"detail": "Invalid or expired refresh token"}

    user = db.execute(select(User).where(User.id == session.user_id)).scalars().first()
    if not user or not user.is_active:
        session.revoked_at = now
        try:
            db.add(session)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(
                "Failed to revoke session for missing/inactive user %s: %s",
                session.user_id,
                str(e),
            )
        # User is missing or inactive: revoke session, clear cookie and return 401
        response.delete_cookie(key="refresh_token")
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"detail": "User not found or inactive"}

    # Rotate refresh token: revoke old session and create a new one
    new_refresh = create_refresh_token()
    new_hash = hash_refresh_token(new_refresh)
    new_expires = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    session.revoked_at = now
    new_session = UserSession(
        user_id=user.id,
        token_hash=new_hash,
        created_at=now,
        expires_at=new_expires,
        user_agent=(request.headers.get("user-agent") or "")[:255],
        ip_address=request.client.host if request.client else None,
    )

    try:
        db.add(session)
        db.add(new_session)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("Failed to rotate refresh token for user %s: %s", user.id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not refresh token",
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    secure_cookie = settings.WEBSITE_URL.startswith("https://") and (
        request.url.hostname not in ("testserver", "localhost")
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=secure_cookie,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/steam/link", response_model=UserResponse)
async def link_steam_account(
    payload: SteamLinkRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Link a Steam account to the currently authenticated user.

    Expects a payload with steam_id. If this steam_id is already linked to
    another user, returns 400.
    """

    # Check if steam_id is already used by another user
    existing = db.execute(
        select(User).where(User.steam_id == payload.steam_id)
    ).scalars().first()

    if existing and existing.id != current_user.id:
        raise HTTPException(
            status_code=400,
            detail="This Steam account is already linked to another user",
        )

    current_user.steam_id = payload.steam_id
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)


@router.post("/steam/unlink", response_model=UserResponse)
async def unlink_steam_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Unlink Steam account from the current user (if any)."""

    current_user.steam_id = None
    db.add(current_user)
    db.commit()
    db.refresh(current_user)

    return UserResponse.model_validate(current_user)
