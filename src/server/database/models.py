"""SQLAlchemy database models"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Enum
)
from sqlalchemy.orm import relationship, declarative_base
import enum

Base = declarative_base()


class SubscriptionTier(enum.Enum):
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ELITE = "elite"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class ProDemoStatus(enum.Enum):
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    DOWNLOADED = "downloaded"
    PARSED = "parsed"
    FAILED = "failed"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    faceit_id = Column(String(100), unique=True, index=True, nullable=True)
    steam_id = Column(String(100), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    subscription = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    teammate_profile = relationship(
        "TeammateProfile", back_populates="user", uselist=False
    )


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="subscription")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="RUB")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    provider = Column(String(50))
    provider_payment_id = Column(String(100), unique=True, index=True, nullable=True)
    subscription_tier = Column(Enum(SubscriptionTier), nullable=True)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="payments")


class TeammateProfile(Base):
    """Teammate search profile linked to a user.

    Stores basic Faceit-related info and preferences for internal matchmaking.
    """

    __tablename__ = "teammate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)

    faceit_nickname = Column(String(100), nullable=True)
    elo = Column(Integer, nullable=True)
    level = Column(Integer, nullable=True)

    # Comma-separated lists for simplicity (e.g. "entry,support")
    roles = Column(String(255), nullable=True)
    languages = Column(String(50), nullable=True)
    preferred_maps = Column(String(255), nullable=True)

    play_style = Column(String(50), nullable=True)  # aggressive/balanced/passive
    voice_required = Column(Boolean, default=True, nullable=False)
    about = Column(String(500), nullable=True)
    availability = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="teammate_profile")


class ProDemo(Base):
    __tablename__ = "pro_demos"

    id = Column(Integer, primary_key=True, index=True)
    faceit_match_id = Column(String(100), unique=True, index=True, nullable=False)
    faceit_player_id = Column(String(100), index=True, nullable=True)
    faceit_nickname = Column(String(100), nullable=True)
    map_name = Column(String(50), nullable=True)
    elo_avg = Column(Integer, nullable=True)
    started_at = Column(DateTime, nullable=True)
    demo_url = Column(String(500), nullable=True)
    storage_path = Column(String(500), nullable=True)
    status = Column(Enum(ProDemoStatus), default=ProDemoStatus.QUEUED, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    features = relationship("DemoFeature", back_populates="pro_demo")


class DemoFeature(Base):
    __tablename__ = "demo_features"

    id = Column(Integer, primary_key=True, index=True)
    pro_demo_id = Column(Integer, ForeignKey("pro_demos.id"), index=True, nullable=True)
    source = Column(String(20), default="pro", nullable=False)

    round_number = Column(Integer, nullable=True)
    steam_id = Column(String(100), index=True, nullable=True)
    faceit_player_id = Column(String(100), index=True, nullable=True)
    team = Column(String(10), nullable=True)

    # Core stats
    kills = Column(Integer, nullable=True)
    deaths = Column(Integer, nullable=True)
    assists = Column(Integer, nullable=True)
    damage = Column(Float, nullable=True)
    adr = Column(Float, nullable=True)
    kast = Column(Float, nullable=True)
    rating_2_0 = Column(Float, nullable=True)
    opening_duels_won = Column(Integer, nullable=True)
    multikills = Column(Integer, nullable=True)
    clutches_won = Column(Integer, nullable=True)
    trade_kills = Column(Integer, nullable=True)

    # Positioning
    avg_distance_to_teammates = Column(Float, nullable=True)
    avg_distance_to_bombsite = Column(Float, nullable=True)
    time_in_aggressive_positions = Column(Float, nullable=True)
    time_in_passive_positions = Column(Float, nullable=True)

    # Decision making
    early_round_pushes = Column(Integer, nullable=True)
    late_round_rotations = Column(Integer, nullable=True)
    save_rounds = Column(Integer, nullable=True)
    suicidal_peeks = Column(Integer, nullable=True)

    # Utility usage
    nades_thrown = Column(Integer, nullable=True)
    flashes_thrown = Column(Integer, nullable=True)
    flash_assists = Column(Integer, nullable=True)
    smokes_thrown = Column(Integer, nullable=True)
    smokes_blocking_time = Column(Float, nullable=True)
    molotovs_thrown = Column(Integer, nullable=True)
    molotovs_area_denial_time = Column(Float, nullable=True)

    # Economy
    avg_money_spent = Column(Float, nullable=True)
    eco_rounds_played = Column(Integer, nullable=True)
    force_buy_rounds = Column(Integer, nullable=True)
    full_buy_rounds = Column(Integer, nullable=True)
    weapon_tier_score = Column(Float, nullable=True)

    # Aggregate impact scores
    round_impact_score = Column(Float, nullable=True)
    clutch_impact = Column(Float, nullable=True)
    entry_impact = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    pro_demo = relationship("ProDemo", back_populates="features")
