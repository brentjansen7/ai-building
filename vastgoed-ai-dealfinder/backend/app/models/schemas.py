from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


# ── Listing ──────────────────────────────────────────────────────────────────

class ListingBase(BaseModel):
    source: str
    url: str
    title: str
    price_ask: Optional[int] = None
    address: str
    city: str
    postcode: Optional[str] = None
    size_sqm: Optional[int] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    year_built: Optional[int] = None
    property_type: Optional[str] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None


class ListingCreate(ListingBase):
    source_id: str


class ListingOut(ListingBase):
    id: UUID
    source_id: str
    is_klus_likely: bool
    klus_confidence: float
    klus_keywords: Optional[List[str]] = None
    woz_value: Optional[int] = None
    woz_year: Optional[int] = None
    analysis_status: str
    scraped_at: datetime
    latest_analysis: Optional["AnalysisOut"] = None

    class Config:
        from_attributes = True


# ── Analysis ─────────────────────────────────────────────────────────────────

class AnalysisOut(BaseModel):
    id: UUID
    listing_id: UUID

    klus_probability: Optional[float] = None
    klus_description: Optional[str] = None

    reno_cost_min: Optional[int] = None
    reno_cost_mid: Optional[int] = None
    reno_cost_max: Optional[int] = None
    reno_breakdown: Optional[Dict[str, int]] = None

    estimated_value_after_reno: Optional[int] = None
    market_value_comparable: Optional[int] = None
    price_per_sqm: Optional[int] = None
    neighborhood_price_per_sqm: Optional[int] = None

    total_investment: Optional[int] = None
    potential_profit: Optional[int] = None
    roi_percentage: Optional[float] = None
    deal_score: Optional[int] = None
    deal_grade: Optional[str] = None
    score_components: Optional[Dict[str, Any]] = None

    created_at: datetime

    class Config:
        from_attributes = True


# ── Extension API ─────────────────────────────────────────────────────────────

class ExtensionAnalyzeRequest(BaseModel):
    url: str
    address: Optional[str] = None
    price_ask: Optional[int] = None
    size_sqm: Optional[int] = None
    rooms: Optional[int] = None
    bedrooms: Optional[int] = None
    year_built: Optional[int] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    description: Optional[str] = None
    image_urls: Optional[List[str]] = None
    source: str = "manual"


class ExtensionAnalysisResponse(BaseModel):
    # Listing info
    address: str
    city: str
    price_ask: int
    size_sqm: Optional[int] = None

    # WOZ
    woz_value: Optional[int] = None
    woz_year: Optional[int] = None
    woz_diff: Optional[int] = None              # woz - vraagprijs

    # Klus
    is_klus: bool
    klus_confidence: float
    klus_keywords: List[str] = []

    # Renovatie
    reno_cost_min: int
    reno_cost_mid: int
    reno_cost_max: int
    reno_breakdown: Dict[str, int]

    # Waarde
    price_per_sqm: Optional[int] = None
    neighborhood_price_per_sqm: Optional[int] = None
    estimated_value_after_reno: int

    # Deal metrics
    total_investment: int
    potential_profit: int
    roi_percentage: float
    deal_score: int
    deal_grade: str
    score_components: Dict[str, Any]

    # Meta
    listing_id: Optional[str] = None
    cached: bool = False


# ── Deal Feed ─────────────────────────────────────────────────────────────────

class DealFeedItem(BaseModel):
    listing_id: UUID
    address: str
    city: str
    postcode: Optional[str] = None
    price_ask: int
    size_sqm: Optional[int] = None
    year_built: Optional[int] = None
    deal_score: int
    deal_grade: str
    potential_profit: int
    roi_percentage: float
    reno_cost_mid: int
    estimated_value_after_reno: int
    woz_value: Optional[int] = None
    url: str
    source: str
    is_klus_likely: bool
    scraped_at: datetime

    class Config:
        from_attributes = True


class DealFeedResponse(BaseModel):
    items: List[DealFeedItem]
    total: int
    page: int
    per_page: int


ListingOut.model_rebuild()
