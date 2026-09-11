from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_, func
from typing import Optional, List
import uuid
import structlog

from app.database import get_db
from app.models.db import Listing, Analysis, Alert
from app.models.schemas import (
    ListingOut, AnalysisOut, DealFeedResponse, DealFeedItem,
    ExtensionAnalyzeRequest, ExtensionAnalysisResponse
)
from app.config import settings

logger = structlog.get_logger()
router = APIRouter()


def verify_api_key(x_api_key: str = Header(...)):
    """Verifieer API key voor Chrome extension requests."""
    if x_api_key != settings.extension_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# ─────────────────────────────────────────────────────────────────────────────
# DEAL FEED
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/deals", response_model=DealFeedResponse)
async def get_deals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    city: Optional[str] = None,
    min_score: int = Query(0, ge=0, le=100),
    grade: Optional[str] = None,
    min_profit: int = Query(0, ge=0),
    source: Optional[str] = None,
    klus_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """Haal deal feed op met filters."""
    offset = (page - 1) * per_page

    # Query: join listings met meest recente analyse
    subq = (
        select(Analysis.listing_id, func.max(Analysis.created_at).label("latest"))
        .group_by(Analysis.listing_id)
        .subquery()
    )

    query = (
        select(Listing, Analysis)
        .join(subq, Listing.id == subq.c.listing_id)
        .join(Analysis, and_(
            Analysis.listing_id == subq.c.listing_id,
            Analysis.created_at == subq.c.latest
        ))
        .where(Listing.is_active == True)
        .where(Analysis.deal_score >= min_score)
        .where(Analysis.potential_profit >= min_profit)
    )

    if city:
        query = query.where(Listing.city.ilike(f"%{city}%"))
    if grade:
        query = query.where(Analysis.deal_grade == grade.upper())
    if source:
        query = query.where(Listing.source == source)
    if klus_only:
        query = query.where(Listing.is_klus_likely == True)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    query = query.order_by(desc(Analysis.deal_score)).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for listing, analysis in rows:
        items.append(DealFeedItem(
            listing_id=listing.id,
            address=listing.address,
            city=listing.city,
            postcode=listing.postcode,
            price_ask=listing.price_ask or 0,
            size_sqm=listing.size_sqm,
            year_built=listing.year_built,
            deal_score=analysis.deal_score or 0,
            deal_grade=analysis.deal_grade or "F",
            potential_profit=analysis.potential_profit or 0,
            roi_percentage=analysis.roi_percentage or 0.0,
            reno_cost_mid=analysis.reno_cost_mid or 0,
            estimated_value_after_reno=analysis.estimated_value_after_reno or 0,
            woz_value=listing.woz_value,
            url=listing.url,
            source=listing.source,
            is_klus_likely=listing.is_klus_likely or False,
            scraped_at=listing.scraped_at,
        ))

    return DealFeedResponse(items=items, total=total, page=page, per_page=per_page)


# ─────────────────────────────────────────────────────────────────────────────
# LISTING DETAIL
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/listings/{listing_id}", response_model=ListingOut)
async def get_listing(listing_id: str, db: AsyncSession = Depends(get_db)):
    """Haal één listing op met nieuwste analyse."""
    result = await db.execute(
        select(Listing).where(Listing.id == listing_id)
    )
    listing = result.scalar_one_or_none()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing niet gevonden")

    # Haal nieuwste analyse op
    analysis_result = await db.execute(
        select(Analysis)
        .where(Analysis.listing_id == listing.id)
        .order_by(desc(Analysis.created_at))
        .limit(1)
    )
    analysis = analysis_result.scalar_one_or_none()

    listing_data = ListingOut.model_validate(listing)
    if analysis:
        listing_data.latest_analysis = AnalysisOut.model_validate(analysis)

    return listing_data


# ─────────────────────────────────────────────────────────────────────────────
# CHROME EXTENSION — ANALYSE ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze", response_model=ExtensionAnalysisResponse)
async def analyze_listing_from_extension(
    request: ExtensionAnalyzeRequest,
    api_key: str = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyseer een listing live vanuit de Chrome extensie.
    Geeft direct een volledige analyse terug.
    """
    from app.scrapers.woz_fetcher import WOZFetcher
    from app.services.klus_detector import KlusDetector
    from app.services.renovation_cost import RenovationCostEstimator
    from app.services.market_value import MarketValuationEngine
    from app.services.deal_scorer import DealScorer

    price_ask = request.price_ask or 0
    size_sqm = request.size_sqm or 80
    city = request.city or "Rotterdam"
    postcode = request.postcode

    # 1. Check cache — bestaat listing al?
    existing = await db.execute(
        select(Listing, Analysis)
        .join(Analysis, Listing.id == Analysis.listing_id, isouter=True)
        .where(Listing.url == request.url)
        .order_by(desc(Analysis.created_at))
        .limit(1)
    )
    row = existing.first()
    if row and row[1]:
        listing, analysis = row
        return _build_extension_response(listing, analysis, cached=True)

    # 2. WOZ ophalen
    woz_value = None
    woz_year = None
    if postcode and request.address:
        try:
            woz_fetcher = WOZFetcher()
            woz_data = await woz_fetcher.get_woz(request.address, postcode)
            if woz_data:
                woz_value = woz_data.get("woz_value")
                woz_year = woz_data.get("woz_year")
        except Exception as e:
            logger.warning("WOZ fetch fout in extension", error=str(e))

    # 3. Klus detectie
    klus_detector = KlusDetector(settings.anthropic_api_key)
    klus_result = await klus_detector.analyze(
        description=request.description,
        title="",
        image_urls=request.image_urls,
        year_built=request.year_built,
    )

    # 4. Renovatiekosten
    reno_estimator = RenovationCostEstimator()
    reno_result = reno_estimator.estimate_from_probability(
        klus_probability=klus_result["klus_probability"],
        size_sqm=size_sqm,
        year_built=request.year_built,
        city=city,
    )

    # 5. Marktwaarde
    valuation_engine = MarketValuationEngine(db)
    valuation_result = await valuation_engine.estimate(
        price_ask=price_ask,
        size_sqm=size_sqm,
        city=city,
        postcode=postcode,
        woz_value=woz_value,
        year_built=request.year_built,
        rooms=request.rooms,
        klus_probability=klus_result["klus_probability"],
        reno_cost_mid=reno_result["cost_mid"],
    )

    # 6. Deal score
    scorer = DealScorer()
    score_result = scorer.score(
        price_ask=price_ask,
        woz_value=woz_value,
        neighborhood_price_per_sqm=valuation_result["neighborhood_price_per_sqm"],
        price_per_sqm_ask=valuation_result["price_per_sqm_ask"],
        reno_cost_mid=reno_result["cost_mid"],
        estimated_value_after_reno=valuation_result["estimated_value_after_reno"],
        klus_probability=klus_result["klus_probability"],
        size_sqm=size_sqm,
    )

    # 7. Sla op in DB voor cache
    listing = Listing(
        source=request.source,
        source_id=f"{request.source}_{hash(request.url)}",
        url=request.url,
        title=request.address or "Via extensie",
        price_ask=price_ask,
        address=request.address or "",
        city=city,
        postcode=postcode,
        size_sqm=size_sqm,
        rooms=request.rooms,
        bedrooms=request.bedrooms,
        year_built=request.year_built,
        description=request.description,
        image_urls=request.image_urls,
        is_klus_likely=klus_result["klus_probability"] >= 0.4,
        klus_confidence=klus_result["klus_probability"],
        klus_keywords=klus_result["klus_keywords"],
        woz_value=woz_value,
        woz_year=woz_year,
        analysis_status="done",
    )
    db.add(listing)
    await db.flush()

    analysis = Analysis(
        listing_id=listing.id,
        klus_probability=klus_result["klus_probability"],
        klus_description=klus_result["description"],
        reno_cost_min=reno_result["cost_min"],
        reno_cost_mid=reno_result["cost_mid"],
        reno_cost_max=reno_result["cost_max"],
        reno_breakdown=reno_result["breakdown_mid"],
        estimated_value_after_reno=valuation_result["estimated_value_after_reno"],
        market_value_comparable=valuation_result["estimated_current_value"],
        price_per_sqm=valuation_result["price_per_sqm_ask"],
        neighborhood_price_per_sqm=valuation_result["neighborhood_price_per_sqm"],
        total_investment=score_result["total_investment"],
        potential_profit=score_result["potential_profit"],
        roi_percentage=score_result["roi_percentage"],
        deal_score=score_result["deal_score"],
        deal_grade=score_result["deal_grade"],
        score_components=score_result["score_components"],
        model_version="1.0",
        analyzed_by="extension",
    )
    db.add(analysis)
    await db.commit()

    return ExtensionAnalysisResponse(
        address=request.address or "",
        city=city,
        price_ask=price_ask,
        size_sqm=size_sqm,
        woz_value=woz_value,
        woz_year=woz_year,
        woz_diff=(woz_value - price_ask) if woz_value else None,
        is_klus=klus_result["klus_probability"] >= 0.4,
        klus_confidence=klus_result["klus_probability"],
        klus_keywords=klus_result["klus_keywords"],
        reno_cost_min=reno_result["cost_min"],
        reno_cost_mid=reno_result["cost_mid"],
        reno_cost_max=reno_result["cost_max"],
        reno_breakdown=reno_result["breakdown_mid"],
        price_per_sqm=valuation_result["price_per_sqm_ask"],
        neighborhood_price_per_sqm=valuation_result["neighborhood_price_per_sqm"],
        estimated_value_after_reno=valuation_result["estimated_value_after_reno"],
        total_investment=score_result["total_investment"],
        potential_profit=score_result["potential_profit"],
        roi_percentage=score_result["roi_percentage"],
        deal_score=score_result["deal_score"],
        deal_grade=score_result["deal_grade"],
        score_components=score_result["score_components"],
        listing_id=str(listing.id),
        cached=False,
    )


def _build_extension_response(listing, analysis, cached: bool = True) -> ExtensionAnalysisResponse:
    """Bouw response vanuit bestaande DB data."""
    price_ask = listing.price_ask or 0
    woz_value = listing.woz_value

    return ExtensionAnalysisResponse(
        address=listing.address,
        city=listing.city,
        price_ask=price_ask,
        size_sqm=listing.size_sqm,
        woz_value=woz_value,
        woz_year=listing.woz_year,
        woz_diff=(woz_value - price_ask) if woz_value else None,
        is_klus=listing.is_klus_likely or False,
        klus_confidence=listing.klus_confidence or 0.0,
        klus_keywords=listing.klus_keywords or [],
        reno_cost_min=analysis.reno_cost_min or 0,
        reno_cost_mid=analysis.reno_cost_mid or 0,
        reno_cost_max=analysis.reno_cost_max or 0,
        reno_breakdown=analysis.reno_breakdown or {},
        price_per_sqm=analysis.price_per_sqm,
        neighborhood_price_per_sqm=analysis.neighborhood_price_per_sqm,
        estimated_value_after_reno=analysis.estimated_value_after_reno or 0,
        total_investment=analysis.total_investment or 0,
        potential_profit=analysis.potential_profit or 0,
        roi_percentage=analysis.roi_percentage or 0.0,
        deal_score=analysis.deal_score or 0,
        deal_grade=analysis.deal_grade or "F",
        score_components=analysis.score_components or {},
        listing_id=str(listing.id),
        cached=cached,
    )


# ─────────────────────────────────────────────────────────────────────────────
# ADMIN / TRIGGER ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/admin/scrape/{source}")
async def trigger_scrape(
    source: str,
    api_key: str = Depends(verify_api_key),
):
    """Handmatig een scrape triggeren."""
    from app.queue.worker import enqueue_job

    job_map = {
        "pararius": "app.queue.jobs.scrape_pararius",
        "jaap": "app.queue.jobs.scrape_jaap",
        "huislijn": "app.queue.jobs.scrape_huislijn",
    }

    if source not in job_map:
        raise HTTPException(status_code=400, detail=f"Onbekende source: {source}")

    job_id = enqueue_job(job_map[source])
    return {"status": "queued", "job_id": job_id, "source": source}


@router.post("/admin/analyze/{listing_id}")
async def trigger_analyze(
    listing_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Handmatig een analyse triggeren."""
    from app.queue.worker import enqueue_job
    job_id = enqueue_job("app.queue.jobs.analyze_listing", listing_id=listing_id)
    return {"status": "queued", "job_id": job_id}


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Platformstatistieken."""
    total_listings = await db.execute(select(func.count()).select_from(Listing))
    total_analyses = await db.execute(select(func.count()).select_from(Analysis))
    top_deals = await db.execute(
        select(Analysis.deal_grade, func.count().label("count"))
        .group_by(Analysis.deal_grade)
    )
    avg_score = await db.execute(select(func.avg(Analysis.deal_score)).select_from(Analysis))

    return {
        "total_listings": total_listings.scalar(),
        "total_analyses": total_analyses.scalar(),
        "avg_deal_score": round(avg_score.scalar() or 0, 1),
        "deals_by_grade": {row[0]: row[1] for row in top_deals.all()},
    }
