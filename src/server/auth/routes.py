"""Authentication endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from .schemas import Token, UserResponse
from .security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from .dependencies import get_current_active_user
from ..database.models import User, Subscription, SubscriptionTier
from ..database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    request: Request,
    db: Session = Depends(get_db)
):
    """Register new user"""
    try:
        email = None
        username = None
        password = None
        faceit_id = None

        # Try to parse as FormData first
        try:
            form = await request.form()
            email = form.get("email")
            username = form.get("username")
            password = form.get("password")
            faceit_id = form.get("faceit_id")
        except Exception:
            # Fallback to JSON
            try:
                body = await request.json()
                email = body.get("email")
                username = body.get("username")
                password = body.get("password")
                faceit_id = body.get("faceit_id")
            except Exception as e:
                logger.error(f"Failed to parse request body: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid request format"
                )

        if not email or not username or not password:
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: email, username, password"
            )

        # Validate email format
        if "@" not in email:
            raise HTTPException(
                status_code=400,
                detail="Invalid email format"
            )

        # Validate password length
        if len(password) < 6:
            raise HTTPException(
                status_code=400,
                detail="Password must be at least 6 characters"
            )

        existing = db.execute(
            select(User).where(User.email == email)
        ).scalars().first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Email already registered"
            )

        hashed_password = get_password_hash(password)

        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            faceit_id=faceit_id
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        subscription = Subscription(
            user_id=new_user.id,
            tier=SubscriptionTier.FREE
        )
        db.add(subscription)
        db.commit()

        logger.info(f"New user registered: {new_user.email}")
        return new_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login(
    request: Request,
    db: Session = Depends(get_db)
):
    """Login user"""
    # Try to get form data first
    try:
        form = await request.form()
        if form:
            email = form.get("username")
            password = form.get("password")
        else:
            body = await request.json()
            email = body.get("email")
            password = body.get("password")
    except Exception:
        body = await request.json()
        email = body.get("email")
        password = body.get("password")

    user = db.execute(
        select(User).where(User.email == email)
    ).scalars().first()

    if not user or not verify_password(
        password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="User account is inactive"
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    logger.info(f"User logged in: {user.email}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user info"""
    return current_user
