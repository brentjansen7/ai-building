from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, ARRAY, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.database import Base


class Listing(Base):
    __tablename__ = "listings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50), nullable=False)         # 'pararius', 'jaap', 'huislijn', 'funda'
    source_id = Column(String(255), nullable=False, unique=True)
    url = Column(String(2048), nullable=False)
    title = Column(String(500), nullable=False)
    price_ask = Column(Integer)                         # in euros
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    postcode = Column(String(10))
    lat = Column(Float)
    lng = Column(Float)

    # Woning details
    size_sqm = Column(Integer)
    rooms = Column(Integer)
    bedrooms = Column(Integer)
    bathrooms = Column(Integer)
    year_built = Column(Integer)
    property_type = Column(String(50))                  # appartement, tussenwoning, hoekwoning, etc.
    energy_label = Column(String(5))                    # A, B, C, D, E, F, G

    # Content
    description = Column(Text)
    images_count = Column(Integer)
    image_urls = Column(JSON)                           # list of URLs

    # Klus detection
    is_klus_likely = Column(Boolean, default=False)
    klus_confidence = Column(Float, default=0.0)
    klus_keywords = Column(JSON)                        # list of keywords

    # WOZ
    woz_value = Column(Integer)
    woz_year = Column(Integer)

    # Analysis status
    analysis_status = Column(String(50), default="pending")  # pending, analyzing, done, failed
    analyzed_at = Column(DateTime(timezone=True))

    # Metadata
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)           # False = van website gehaald

    # Relaties
    analyses = relationship("Analysis", back_populates="listing", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="listing")

    __table_args__ = (
        Index("idx_listings_source_date", "source", "scraped_at"),
        Index("idx_listings_postcode_price", "postcode", "price_ask"),
        Index("idx_listings_city", "city"),
        Index("idx_listings_klus", "is_klus_likely"),
        Index("idx_listings_status", "analysis_status"),
    )


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False)

    # Klus beoordeling
    klus_probability = Column(Float)                    # 0.0-1.0
    klus_description = Column(Text)

    # Renovatie schatting
    reno_cost_min = Column(Integer)
    reno_cost_mid = Column(Integer)
    reno_cost_max = Column(Integer)
    reno_breakdown = Column(JSON)                       # {keuken: 8000, badkamer: 6000, ...}

    # Marktwaarde
    estimated_value_after_reno = Column(Integer)
    market_value_comparable = Column(Integer)
    price_per_sqm = Column(Integer)
    neighborhood_price_per_sqm = Column(Integer)

    # Deal metrics
    total_investment = Column(Integer)                  # vraagprijs + reno_mid
    potential_profit = Column(Integer)                  # waarde - investering
    roi_percentage = Column(Float)
    deal_score = Column(Integer)                        # 1-100
    deal_grade = Column(String(5))                      # A, B, C, D, F

    # Score breakdown
    score_components = Column(JSON)                     # {price_vs_woz: 15, ...}

    # Metadata
    model_version = Column(String(50))
    analyzed_by = Column(String(50))                    # 'claude', 'rule_based'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaties
    listing = relationship("Listing", back_populates="analyses")
    alerts = relationship("Alert", back_populates="analysis")

    __table_args__ = (
        Index("idx_analyses_listing", "listing_id"),
        Index("idx_analyses_score", "deal_score"),
        Index("idx_analyses_grade", "deal_grade"),
    )


class Comp(Base):
    """Vergelijkbare verkopen voor marktwaardebepaling."""
    __tablename__ = "comps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    postcode = Column(String(10), nullable=False)
    postcode4 = Column(String(4))                       # eerste 4 cijfers voor bredere matching
    city = Column(String(100))

    sold_price = Column(Integer)
    sold_date = Column(DateTime(timezone=True))
    size_sqm = Column(Integer)
    bedrooms = Column(Integer)
    property_type = Column(String(50))

    source = Column(String(50))                         # 'funda_api', 'manual', 'kadaster'
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_comps_postcode_date", "postcode", "sold_date"),
        Index("idx_comps_postcode4", "postcode4"),
    )


class WOZCache(Base):
    """Cache voor WOZ waarden."""
    __tablename__ = "woz_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    address = Column(String(255), nullable=False, unique=True)
    postcode = Column(String(10))
    city = Column(String(100))

    woz_value = Column(Integer)
    woz_year = Column(Integer)
    bag_id = Column(String(100))

    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))        # Jaarlijks vernieuwen

    __table_args__ = (
        Index("idx_woz_postcode", "postcode"),
    )


class Alert(Base):
    """Verstuurde deal alerts."""
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    listing_id = Column(UUID(as_uuid=True), ForeignKey("listings.id"), nullable=False)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"))

    alert_type = Column(String(50))                     # 'telegram', 'discord', 'email'
    deal_grade = Column(String(5))
    deal_score = Column(Integer)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_to = Column(String(500))
    success = Column(Boolean, default=True)
    error_msg = Column(Text)

    listing = relationship("Listing", back_populates="alerts")
    analysis = relationship("Analysis", back_populates="alerts")

    __table_args__ = (
        Index("idx_alerts_listing", "listing_id"),
        Index("idx_alerts_sent_at", "sent_at"),
    )


class ScraperLog(Base):
    """Log van scrape jobs."""
    __tablename__ = "scraper_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(50))
    job_started_at = Column(DateTime(timezone=True))
    job_completed_at = Column(DateTime(timezone=True))

    total_listed = Column(Integer, default=0)
    new_listings = Column(Integer, default=0)
    updated_listings = Column(Integer, default=0)
    errors = Column(Integer, default=0)

    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_scraper_logs_source", "source", "job_started_at"),
    )
