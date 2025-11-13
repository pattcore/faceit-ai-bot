"""Authentication endpoints"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .schemas import UserRegister, Token, UserResponse
from .security import (
    verify_password,
    get_password_hash,
    create_access_token
)
from .dependencies import get_current_active_user
from ..database.models import User, Subscription, SubscriptionTier
from ..database.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register new user"""
    existing = db.query(User).filter(
        User.email == user_data.email
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    hashed_password = get_password_hash(user_data.password)

    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        faceit_id=user_data.faceit_id
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
            email = form.get("username")  # Frontend sends username as email
            password = form.get("password")
        else:
            # Fallback to JSON
            body = await request.json()
            email = body.get("email")
            password = body.get("password")
    except Exception:
        # If both fail, try JSON
        body = await request.json()
        email = body.get("email")
        password = body.get("password")
    
    user = db.query(User).filter(
        User.email == email
    ).first()

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
