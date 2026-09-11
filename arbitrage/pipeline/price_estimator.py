"""
Price estimation engine.
KNN weighted average on pgvector similarity search.
XGBoost fallback when confidence is low.
"""

import logging
import os
from typing import List, Optional, Tuple
import numpy as np

from sqlalchemy import text
from db.database import get_session

logger = logging.getLogger(__name__)

# Condition multipliers — reduce estimated value based on wear
CONDITION_MULTIPLIER = {
    "new": 1.0,
    "like_new": 0.88,
    "good": 0.72,
    "fair": 0.52,
    "poor": 0.30,
    "unknown": 0.70,
}

# Platform fees (fraction of sale price)
PLATFORM_FEES = {
    "marktplaats": 0.00,     # Free to sell basic
    "vinted": 0.05,
    "ebay": 0.13,
    "catawiki": 0.125,       # 12.5% buyer's premium (deducted from resale estimate)
    "bva_auctions": 0.15,
    "troostwijk": 0.15,
    "auctionet": 0.18,
    "facebook": 0.00,
    "tweedehands_be": 0.00,
    "online_veiling": 0.17,
}

SHIPPING_ESTIMATE_EUR = 7.50  # Average NL pakket


class PriceEstimator:
    """
    Estimate market value of a listing using:
    1. KNN similarity search on sold_listings via pgvector
    2. XGBoost regression fallback (when similarity confidence is low)
    """

    def __init__(self):
        self._xgb_model = None  # Loaded lazily

    async def estimate(
        self,
        title: str,
        description: str,
        condition: str,
        platform: str,
        embedding: List[float],
        category: Optional[str] = None,
    ) -> dict:
        """
        Full estimation pipeline for a single listing.

        Args:
            title: Listing title
            description: Listing description
            condition: Normalized condition string
            platform: Platform name
            embedding: Pre-computed 1024-dim vector
            category: Optional category filter

        Returns:
            {
                estimated_value: float,
                resale_price: float,
                confidence: float,
                comparable_count: int,
                method: str,
            }
        """
        comparables = await self._find_comparables(embedding, category, limit=20)

        if not comparables:
            logger.debug(f"No comparables found for: {title}")
            return self._fallback_estimate(condition, platform)

        # KNN weighted average
        similarities = np.array([c["similarity"] for c in comparables])
        prices = np.array([c["sold_price"] for c in comparables])

        # Confidence = max similarity of best match
        confidence = float(similarities[0]) if len(similarities) > 0 else 0.0

        # Weight by similarity score (squared to amplify best matches)
        weights = similarities ** 2
        base_estimate = float(np.average(prices, weights=weights))

        # Apply condition multiplier
        multiplier = CONDITION_MULTIPLIER.get(condition, 0.70)
        estimated_value = base_estimate * multiplier

        # Use XGBoost if best match similarity < 0.72 (low confidence)
        method = "knn"
        if confidence < 0.72:
            xgb_estimate = self._xgboost_estimate(title, category, condition)
            if xgb_estimate:
                # Blend: 40% xgb, 60% knn for low-confidence cases
                estimated_value = 0.6 * estimated_value + 0.4 * xgb_estimate
                method = "knn+xgb"
                confidence *= 0.8  # Reduce confidence since we blended

        # Resale price = what you can realistically sell for
        platform_fee = PLATFORM_FEES.get(platform, 0.05)
        resale_price = estimated_value * (1.0 - platform_fee)

        return {
            "estimated_value": round(estimated_value, 2),
            "resale_price": round(resale_price, 2),
            "confidence": round(confidence, 3),
            "comparable_count": len(comparables),
            "method": method,
            "comparable_prices": [float(p) for p in prices[:5]],
        }

    async def _find_comparables(
        self,
        embedding: List[float],
        category: Optional[str],
        limit: int = 20,
    ) -> List[dict]:
        """
        Find most similar sold listings using pgvector cosine similarity.
        """
        async with get_session() as session:
            # Format embedding for pgvector
            vec_str = "[" + ",".join(str(x) for x in embedding) + "]"

            if category:
                sql = text("""
                    SELECT sold_price, condition, sold_at,
                           1 - (embedding <=> :embedding::vector) AS similarity
                    FROM sold_listings
                    WHERE category = :category
                      AND embedding IS NOT NULL
                      AND sold_price > 0
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :limit
                """)
                result = await session.execute(sql, {
                    "embedding": vec_str,
                    "category": category,
                    "limit": limit,
                })
            else:
                sql = text("""
                    SELECT sold_price, condition, sold_at,
                           1 - (embedding <=> :embedding::vector) AS similarity
                    FROM sold_listings
                    WHERE embedding IS NOT NULL
                      AND sold_price > 0
                    ORDER BY embedding <=> :embedding::vector
                    LIMIT :limit
                """)
                result = await session.execute(sql, {
                    "embedding": vec_str,
                    "limit": limit,
                })

            rows = result.fetchall()
            return [
                {
                    "sold_price": float(row[0]),
                    "condition": row[1],
                    "sold_at": row[2],
                    "similarity": float(row[3]),
                }
                for row in rows
                if float(row[3]) > 0.55  # Filter out irrelevant matches
            ]

    def _xgboost_estimate(
        self,
        title: str,
        category: Optional[str],
        condition: str,
    ) -> Optional[float]:
        """
        XGBoost fallback estimate.
        Returns None if model not available.
        """
        model_path = os.getenv("XGB_MODEL_PATH", "models/price_model.json")

        if self._xgb_model is None:
            try:
                import xgboost as xgb
                model = xgb.Booster()
                model.load_model(model_path)
                self._xgb_model = model
            except Exception as e:
                logger.debug(f"XGBoost model not available: {e}")
                return None

        try:
            import xgboost as xgb
            # Simple feature engineering
            features = self._extract_features(title, category, condition)
            dmatrix = xgb.DMatrix([features])
            prediction = self._xgb_model.predict(dmatrix)
            return float(prediction[0])
        except Exception as e:
            logger.debug(f"XGBoost prediction failed: {e}")
            return None

    def _extract_features(
        self,
        title: str,
        category: Optional[str],
        condition: str,
    ) -> List[float]:
        """Extract numerical features for XGBoost from title + metadata."""
        title_lower = title.lower()

        return [
            len(title),
            CONDITION_MULTIPLIER.get(condition, 0.70),
            # Brand signals (1.0 = premium brand mentioned)
            1.0 if any(b in title_lower for b in ["apple", "sony", "canon", "nikon", "rolex", "omega"]) else 0.0,
            1.0 if any(b in title_lower for b in ["samsung", "lg", "philips", "bosch"]) else 0.0,
            # Category encoding
            hash(category or "unknown") % 100 / 100.0,
        ]

    def _fallback_estimate(self, condition: str, platform: str) -> dict:
        """Return low-confidence fallback when no comparables found."""
        return {
            "estimated_value": None,
            "resale_price": None,
            "confidence": 0.0,
            "comparable_count": 0,
            "method": "none",
            "comparable_prices": [],
        }


def calculate_profit(
    listing_price: float,
    estimated_value: float,
    platform: str,
    include_shipping: bool = True,
) -> dict:
    """
    Calculate profit for a listing.

    Args:
        listing_price: Current asking price (what you pay)
        estimated_value: Estimated resale market value
        platform: Platform where you'll RESELL (usually marktplaats or ebay)
        include_shipping: Whether to deduct shipping estimate

    Returns:
        {profit_eur, profit_pct, platform_fee, shipping_est, resale_platform_fee}
    """
    resale_fee_pct = PLATFORM_FEES.get("marktplaats", 0.0)  # Resell on Marktplaats by default
    resale_fee_eur = estimated_value * resale_fee_pct
    shipping_est = SHIPPING_ESTIMATE_EUR if include_shipping else 0.0

    # Conservative: assume you resell at 85% of estimated value
    resale_price = estimated_value * 0.85

    profit_eur = resale_price - listing_price - resale_fee_eur - shipping_est
    profit_pct = profit_eur / listing_price if listing_price > 0 else 0.0

    return {
        "profit_eur": round(profit_eur, 2),
        "profit_pct": round(profit_pct, 4),
        "resale_price": round(resale_price, 2),
        "platform_fee_eur": round(resale_fee_eur, 2),
        "shipping_est": shipping_est,
        "is_profitable": profit_eur > 0,
    }


def is_deal(
    profit_eur: float,
    profit_pct: float,
    confidence: float,
    min_profit_eur: float = 30.0,
    min_profit_pct: float = 0.25,
    min_confidence: float = 0.65,
) -> Tuple[bool, str]:
    """
    Decide if a listing is worth alerting.

    Returns (should_alert, reason)
    """
    if confidence < min_confidence:
        return False, f"Low confidence ({confidence:.0%})"

    if profit_eur < min_profit_eur:
        return False, f"Profit too low (€{profit_eur:.0f} < €{min_profit_eur:.0f})"

    if profit_pct < min_profit_pct:
        return False, f"Margin too low ({profit_pct:.0%} < {min_profit_pct:.0%})"

    if profit_eur >= 100 and profit_pct >= 0.50:
        return True, "EXCELLENT"
    elif profit_eur >= 50:
        return True, "GOOD"
    else:
        return True, "FAIR"
