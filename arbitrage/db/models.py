"""
SQLAlchemy ORM models for the arbitrage system.
Matches schema.sql exactly.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, BigInteger, String, Text, Numeric, ARRAY,
    DateTime, Boolean, Integer, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


class Listing(Base):
    """Main listings table - all incoming data from all platforms."""
    __tablename__ = "listings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    condition = Column(String(20))
    category = Column(String(100), index=True)
    brand = Column(String(100))
    seller_id = Column(String(100))
    location = Column(String(200))
    url = Column(Text, nullable=False)
    image_urls = Column(ARRAY(Text))
    posted_at = Column(DateTime(timezone=True))
    scraped_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    embedding = Column(Vector(1024))
    image_embedding = Column(Vector(512))
    metadata = Column(JSONB)

    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_listing_platform_external"),
    )

    # Relationships
    price_history = relationship("PriceHistory", back_populates="listing", cascade="all, delete-orphan")
    estimate = relationship("Estimate", back_populates="listing", uselist=False, cascade="all, delete-orphan")
    alerts = relationship("AlertLog", back_populates="listing", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "platform": self.platform,
            "external_id": self.external_id,
            "title": self.title,
            "description": self.description,
            "price": float(self.price) if self.price else None,
            "condition": self.condition,
            "category": self.category,
            "brand": self.brand,
            "seller_id": self.seller_id,
            "location": self.location,
            "url": self.url,
            "image_urls": self.image_urls or [],
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "metadata": self.metadata or {},
        }


class SoldListing(Base):
    """Sold/completed listings - price reference data."""
    __tablename__ = "sold_listings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False, index=True)
    external_id = Column(String(255))
    title = Column(Text, nullable=False)
    sold_price = Column(Numeric(10, 2), nullable=False)
    condition = Column(String(20))
    category = Column(String(100), index=True)
    brand = Column(String(100))
    sold_at = Column(DateTime(timezone=True), index=True)
    embedding = Column(Vector(1024))

    __table_args__ = (
        UniqueConstraint("platform", "external_id", name="uq_sold_platform_external"),
    )


class PriceHistory(Base):
    """Price history time-series (TimescaleDB hypertable)."""
    __tablename__ = "price_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    listing_id = Column(BigInteger, ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    price = Column(Numeric(10, 2))
    bid_count = Column(Integer)
    observed_at = Column(DateTime(timezone=True), nullable=False, index=True)

    listing = relationship("Listing", back_populates="price_history")


class Estimate(Base):
    """Price estimates for listings."""
    __tablename__ = "estimates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    listing_id = Column(BigInteger, ForeignKey("listings.id", ondelete="CASCADE"), unique=True)
    estimated_value = Column(Numeric(10, 2))
    resale_price = Column(Numeric(10, 2))
    profit_score = Column(Numeric(10, 2))
    profit_pct = Column(Numeric(5, 4))
    confidence = Column(Numeric(4, 3))
    platform_fee = Column(Numeric(10, 2))
    shipping_est = Column(Numeric(10, 2))
    comparable_count = Column(Integer)
    comparable_ids = Column(ARRAY(BigInteger))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    listing = relationship("Listing", back_populates="estimate")

    def to_dict(self):
        return {
            "estimated_value": float(self.estimated_value) if self.estimated_value else None,
            "resale_price": float(self.resale_price) if self.resale_price else None,
            "profit_score": float(self.profit_score) if self.profit_score else None,
            "profit_pct": float(self.profit_pct) if self.profit_pct else None,
            "confidence": float(self.confidence) if self.confidence else None,
        }


class AlertLog(Base):
    """Log of sent alerts."""
    __tablename__ = "alerts_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    listing_id = Column(BigInteger, ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    channel = Column(String(20))
    message = Column(Text)
    profit_at_send = Column(Numeric(10, 2))
    sent_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)

    listing = relationship("Listing", back_populates="alerts")


class NichePerformance(Base):
    """Auto-tracked category performance metrics."""
    __tablename__ = "niche_performance"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    category = Column(String(100))
    platform = Column(String(20))
    avg_margin = Column(Numeric(10, 2))
    deal_count = Column(Integer)
    success_rate = Column(Numeric(4, 3))
    listings_seen = Column(Integer)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("category", "platform", name="uq_niche_category_platform"),
    )


class ScraperRun(Base):
    """Track scraper job execution."""
    __tablename__ = "scraper_runs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    platform = Column(String(20), nullable=False, index=True)
    started_at = Column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    completed_at = Column(DateTime(timezone=True))
    listings_found = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    status = Column(String(20), default="running")
    error_message = Column(Text)
