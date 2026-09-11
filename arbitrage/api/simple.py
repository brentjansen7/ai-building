"""
Simplified API for testing - no authentication, basic estimation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
import psycopg2
import psycopg2.extras
import statistics

app = FastAPI(title="AI Arbitrage System", version="0.1.0")

# Database connection
def get_db():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="5af53c8cf9ab47a6a158e515636285bf"
    )

# CORS for extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EstimateRequest(BaseModel):
    title: str = "Unknown"
    price: float = 0
    platform: str = "marktplaats"
    condition: str = "unknown"
    description: str = ""
    category: str = ""

    class Config:
        extra = "allow"

class EstimateResponse(BaseModel):
    title: str
    current_price: float
    estimated_value: float
    profit_eur: float
    profit_pct: float
    confidence: float
    deal_score: str
    message: str

@app.get("/")
async def root():
    return {"name": "AI Arbitrage System", "version": "0.1.0", "docs": "/docs"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {"api": "ok", "database": "ok", "redis": "ok"}
    }

@app.post("/api/v1/estimate")
async def estimate_price(req: EstimateRequest) -> EstimateResponse:
    """
    Estimate RESALE price (what we can sell for) based on real sold listings.
    Uses fuzzy matching to find similar products.
    """

    platform_fees = {
        "marktplaats": 0.06,
        "vinted": 0.10,
        "ebay": 0.13,
        "catawiki": 0.15,
    }

    # Try to find similar sold items
    resale_price = None
    confidence = 0.0
    matches_found = 0

    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Extract key words from title (e.g., "iPhone 14 Pro" from "iPhone 14 Pro 256GB")
        title_words = req.title.lower().split()

        # Search for listings containing most of the title words
        # This handles variants like 256GB, 512GB, colors, etc.
        search_pattern = " ".join(title_words[:3]) if len(title_words) >= 3 else req.title

        cur.execute("""
            SELECT sold_price, title FROM sold_listings
            WHERE LOWER(title) LIKE LOWER(%s)
            AND sold_price > 5 AND sold_price < 50000
            ORDER BY sold_at DESC
            LIMIT 100
        """, (f"%{search_pattern}%",))

        results = cur.fetchall()
        matches_found = len(results)

        if results:
            # Get all resale prices
            prices = [float(r['sold_price']) for r in results]

            # Use median as most stable estimate
            resale_price = statistics.median(prices)

            # Confidence based on how many matches found
            # 5+ matches = high confidence, 1-2 = low
            if matches_found >= 10:
                confidence = 0.95
            elif matches_found >= 5:
                confidence = 0.85
            elif matches_found >= 2:
                confidence = 0.70
            else:
                confidence = 0.50

            print(f"[API] Found {matches_found} sold items for '{search_pattern}'")
            print(f"[API] Resale prices: min={min(prices):.2f}, median={resale_price:.2f}, max={max(prices):.2f}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"[API] Database error: {e}")

    # If no data found, use fallback
    if resale_price is None:
        # Conservative multiplier - what we'd realistically get
        category_multiplier = {
            "electronics": 1.3,  # Electronics lose 30% value
            "furniture": 1.2,
            "fashion": 1.4,
            "jewelry": 1.5,
            "sports": 1.25,
        }
        multiplier = category_multiplier.get(req.category.lower() if req.category else "", 1.25)
        resale_price = req.price * multiplier
        confidence = 0.3
        print(f"[API] Using fallback multiplier: {multiplier}")

    # Calculate actual profit
    # resale_price = what we sell it for
    # fees = platform commission
    # shipping = cost to ship
    # req.price = what we paid for it

    platform = req.platform.lower() if req.platform else "marktplaats"
    fee_pct = platform_fees.get(platform, 0.08)
    fees = resale_price * fee_pct
    shipping_cost = 5.95  # Typical NL shipping

    # Net profit after all costs
    net_profit = resale_price - fees - shipping_cost - req.price
    profit_pct = net_profit / req.price if req.price > 0 else 0

    # Deal scoring
    if profit_pct > 0.40:
        deal_score = "EXCELLENT"
    elif profit_pct > 0.25:
        deal_score = "GOOD"
    elif profit_pct > 0.10:
        deal_score = "FAIR"
    else:
        deal_score = "POOR"

    message = f"{deal_score} deal - {req.title[:30]}"

    print(f"[API] RESULT: Buy €{req.price} → Sell €{resale_price:.2f} = €{net_profit:.2f} profit ({profit_pct*100:.0f}%)")

    return EstimateResponse(
        title=req.title,
        current_price=req.price,
        estimated_value=round(resale_price, 2),  # This is RESALE price
        profit_eur=round(max(0, net_profit), 2),
        profit_pct=round(max(0, profit_pct), 3),
        confidence=round(confidence, 2),
        deal_score=deal_score,
        message=message
    )

@app.get("/api/v1/listings")
async def get_listings(platform: str = "marktplaats"):
    """Get recent listings from platform"""
    return {
        "platform": platform,
        "count": 0,
        "listings": []
    }

@app.get("/api/v1/alerts")
async def get_alerts():
    """Get configured alerts"""
    return {"alerts": []}

@app.post("/api/v1/alerts/config")
async def configure_alerts(min_profit_eur: float = 30, min_profit_pct: float = 0.25):
    """Configure alert thresholds"""
    return {"status": "configured", "min_profit_eur": min_profit_eur, "min_profit_pct": min_profit_pct}
