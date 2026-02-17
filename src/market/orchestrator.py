"""Market analysis orchestrator - coordinates all data fetching and analysis."""

from __future__ import annotations

import asyncio
import logging
from typing import Callable, Optional

from src.market.analyzer import generate_report, parse_address_parts
from src.market.ai_summary import generate_ai_summary
from src.market.models import MarketAnalysisReport
from src.market.nadlan_client import (
    get_transactions_for_address,
    search_neighborhood,
    search_city,
)
from src.market.yad2_client import search_similar_listings

logger = logging.getLogger("realestate")


async def run_market_analysis(
    address: str,
    property_type: str,
    rooms: Optional[float] = None,
    floor: Optional[int] = None,
    size_sqm: Optional[float] = None,
    building_year: Optional[int] = None,
    price: Optional[float] = None,
    include_ai: bool = True,
    progress_callback: Optional[Callable[[str, float], None]] = None,
) -> MarketAnalysisReport:
    """
    Run a complete market analysis for a property.

    Args:
        address: Full property address (Hebrew)
        property_type: Property type (Hebrew)
        rooms: Number of rooms (optional, improves accuracy)
        floor: Floor number (optional)
        size_sqm: Size in sqm (optional)
        building_year: Building year (optional)
        price: Known/asking price (optional)
        include_ai: Whether to generate AI summary
        progress_callback: Optional callback (message, progress_pct)

    Returns:
        MarketAnalysisReport with all analysis data
    """
    def _progress(msg: str, pct: float):
        logger.info(msg)
        if progress_callback:
            progress_callback(msg, pct)

    _progress("מתחיל ניתוח שוק...", 0.0)

    # Parse address
    addr_parts = parse_address_parts(address)
    city = addr_parts.get("city", "")
    neighborhood = addr_parts.get("neighborhood", "")
    street = addr_parts.get("street", "")

    errors: list[str] = []

    # --- Step 1: Fetch transactions from nadlan.gov.il ---
    _progress("שולף עסקאות מ-nadlan.gov.il (רחוב)...", 0.05)

    # Search at street level
    try:
        transactions_street = await get_transactions_for_address(
            address, max_pages=5
        )
        _progress(f"נמצאו {len(transactions_street)} עסקאות ברחוב", 0.15)
    except Exception as e:
        logger.error(f"Error fetching street transactions: {e}")
        transactions_street = []
        errors.append(f"שגיאה בשליפת עסקאות ברחוב: {str(e)}")

    await asyncio.sleep(1)

    # Search at neighborhood level
    transactions_neighborhood = []
    if city and neighborhood:
        _progress(f"שולף עסקאות בשכונה: {neighborhood}...", 0.20)
        try:
            transactions_neighborhood = await search_neighborhood(
                city, neighborhood, max_pages=3
            )
            _progress(f"נמצאו {len(transactions_neighborhood)} עסקאות בשכונה", 0.30)
        except Exception as e:
            logger.error(f"Error fetching neighborhood transactions: {e}")
            errors.append(f"שגיאה בשליפת עסקאות בשכונה: {str(e)}")

    await asyncio.sleep(1)

    # Search at city level
    transactions_city = []
    if city:
        _progress(f"שולף עסקאות בעיר: {city}...", 0.35)
        try:
            transactions_city = await search_city(city, max_pages=2)
            _progress(f"נמצאו {len(transactions_city)} עסקאות בעיר", 0.45)
        except Exception as e:
            logger.error(f"Error fetching city transactions: {e}")
            errors.append(f"שגיאה בשליפת עסקאות בעיר: {str(e)}")

    # --- Step 2: Fetch current listings from Yad2 ---
    _progress("שולף נכסים מפורסמים מיד2...", 0.50)
    listings = []
    if city:
        try:
            listings = await search_similar_listings(
                city=city,
                property_type=property_type,
                rooms=rooms,
                price=price,
                neighborhood=neighborhood,
            )
            _progress(f"נמצאו {len(listings)} נכסים מפורסמים", 0.60)
        except Exception as e:
            logger.error(f"Error fetching Yad2 listings: {e}")
            errors.append(f"שגיאה בשליפת נכסים מיד2: {str(e)}")

    # --- Step 3: Run analysis ---
    _progress("מנתח נתונים...", 0.65)

    report = await generate_report(
        address=address,
        property_type=property_type,
        transactions_street=transactions_street,
        transactions_neighborhood=transactions_neighborhood,
        transactions_city=transactions_city,
        listings=listings,
        subject_rooms=rooms,
        subject_floor=floor,
        subject_size=size_sqm,
        subject_building_year=building_year,
    )

    report.errors = errors
    _progress("ניתוח נתונים הושלם", 0.75)

    # --- Step 4: Generate AI summary ---
    if include_ai:
        _progress("מייצר סיכום AI...", 0.80)
        report.ai_summary = await generate_ai_summary(report)
        _progress("סיכום AI הושלם", 0.95)

    _progress("הדו\"ח מוכן!", 1.0)

    logger.info(
        f"Analysis complete: {report.total_transactions} transactions, "
        f"{report.total_listings} listings, "
        f"{len(report.comparables)} comparables"
    )

    return report
