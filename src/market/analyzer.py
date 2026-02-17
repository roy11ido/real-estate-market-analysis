"""Market analysis engine - processes raw data into insights."""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import datetime
from typing import Optional

from src.market.models import (
    BuildingAgeAnalysis,
    ComparableProperty,
    FloorPriceAnalysis,
    MarketAnalysisReport,
    NadlanTransaction,
    PriceTrend,
    ValueEstimation,
    Yad2Listing,
)

logger = logging.getLogger("realestate")


def parse_address_parts(address: str) -> dict[str, str]:
    """
    Parse a Hebrew address into components: street, city, neighborhood.
    Examples:
        "הרצל 15, תל אביב" -> {"street": "הרצל", "number": "15", "city": "תל אביב"}
        "רחוב ביאליק 7, רמת גן" -> {"street": "ביאליק", "number": "7", "city": "רמת גן"}
    """
    parts = {"street": "", "number": "", "city": "", "neighborhood": ""}

    # Remove "רחוב" prefix
    clean = re.sub(r"^רחוב\s+", "", address.strip())

    # Split by comma
    segments = [s.strip() for s in clean.split(",")]

    if len(segments) >= 2:
        parts["city"] = segments[-1].strip()
        street_part = segments[0].strip()
    elif len(segments) == 1:
        street_part = segments[0].strip()
    else:
        return parts

    # Extract street number
    match = re.search(r"(\d+)", street_part)
    if match:
        parts["number"] = match.group(1)
        parts["street"] = street_part[: match.start()].strip()
    else:
        parts["street"] = street_part

    # Neighborhood - check if there's a middle segment
    if len(segments) == 3:
        parts["neighborhood"] = segments[1].strip()

    return parts


def build_comparables(
    transactions: list[NadlanTransaction],
    listings: list[Yad2Listing],
) -> list[ComparableProperty]:
    """Merge transactions and listings into unified comparable properties."""
    comparables: list[ComparableProperty] = []

    for tx in transactions:
        comp = ComparableProperty(
            source="nadlan.gov.il",
            address=tx.address,
            price=tx.deal_amount,
            rooms=tx.rooms,
            floor=tx.floor,
            size_sqm=tx.size_sqm,
            building_year=tx.building_year,
            deal_date=tx.deal_date,
            property_type=tx.property_type,
            is_listed=False,
        )
        comparables.append(comp)

    for listing in listings:
        comp = ComparableProperty(
            source="yad2",
            address=listing.address,
            price=listing.price,
            rooms=listing.rooms,
            floor=listing.floor,
            size_sqm=listing.size_sqm,
            building_year=listing.building_year,
            deal_date=listing.date_listed,
            property_type=listing.property_type,
            is_listed=True,
        )
        comparables.append(comp)

    return comparables


def analyze_floor_prices(transactions: list[NadlanTransaction]) -> list[FloorPriceAnalysis]:
    """Analyze price differences by floor level."""
    floor_data: dict[int, list[NadlanTransaction]] = defaultdict(list)

    for tx in transactions:
        if tx.floor is not None and tx.deal_amount > 0:
            floor_data[tx.floor].append(tx)

    results: list[FloorPriceAnalysis] = []
    for floor in sorted(floor_data.keys()):
        txs = floor_data[floor]
        sqm_prices = [tx.price_per_sqm for tx in txs if tx.price_per_sqm]
        total_prices = [tx.deal_amount for tx in txs]

        if sqm_prices and total_prices:
            results.append(
                FloorPriceAnalysis(
                    floor=floor,
                    avg_price_per_sqm=round(sum(sqm_prices) / len(sqm_prices)),
                    transaction_count=len(txs),
                    avg_total_price=round(sum(total_prices) / len(total_prices)),
                )
            )

    return results


def analyze_building_age(transactions: list[NadlanTransaction]) -> list[BuildingAgeAnalysis]:
    """Analyze price differences by building age category."""
    categories = {
        "חדש (0-5 שנים)": (0, 5),
        "חדש יחסית (6-15 שנים)": (6, 15),
        "ותיק (16-30 שנים)": (16, 30),
        "ישן (30+ שנים)": (31, 200),
    }

    age_data: dict[str, list[NadlanTransaction]] = defaultdict(list)
    current_year = datetime.now().year

    for tx in transactions:
        if tx.building_year and tx.building_year > 1900 and tx.deal_amount > 0:
            age = current_year - tx.building_year
            for cat_name, (low, high) in categories.items():
                if low <= age <= high:
                    age_data[cat_name].append(tx)
                    break

    # Calculate overall average for premium calculation
    all_sqm_prices = []
    for txs in age_data.values():
        all_sqm_prices.extend([tx.price_per_sqm for tx in txs if tx.price_per_sqm])
    overall_avg = sum(all_sqm_prices) / len(all_sqm_prices) if all_sqm_prices else 0

    results: list[BuildingAgeAnalysis] = []
    for cat_name in categories:
        txs = age_data.get(cat_name, [])
        if not txs:
            continue

        sqm_prices = [tx.price_per_sqm for tx in txs if tx.price_per_sqm]
        years = [tx.building_year for tx in txs if tx.building_year]

        if sqm_prices:
            avg_sqm = sum(sqm_prices) / len(sqm_prices)
            premium = ((avg_sqm - overall_avg) / overall_avg * 100) if overall_avg > 0 else None

            results.append(
                BuildingAgeAnalysis(
                    category=cat_name,
                    avg_price_per_sqm=round(avg_sqm),
                    transaction_count=len(txs),
                    avg_building_year=round(sum(years) / len(years)) if years else None,
                    price_premium_pct=round(premium, 1) if premium is not None else None,
                )
            )

    return results


def analyze_price_trends(transactions: list[NadlanTransaction]) -> list[PriceTrend]:
    """Analyze price trends over time by quarter."""
    quarter_data: dict[str, list[float]] = defaultdict(list)

    for tx in transactions:
        if tx.deal_date and tx.price_per_sqm:
            quarter = (tx.deal_date.month - 1) // 3 + 1
            period = f"{tx.deal_date.year}-Q{quarter}"
            quarter_data[period].append(tx.price_per_sqm)

    sorted_periods = sorted(quarter_data.keys())
    results: list[PriceTrend] = []
    prev_avg = None

    for period in sorted_periods:
        prices = quarter_data[period]
        avg = round(sum(prices) / len(prices))

        change = None
        if prev_avg and prev_avg > 0:
            change = round((avg - prev_avg) / prev_avg * 100, 1)

        results.append(
            PriceTrend(
                period=period,
                avg_price_per_sqm=avg,
                transaction_count=len(prices),
                change_pct=change,
            )
        )
        prev_avg = avg

    return results


def estimate_value(
    comparables: list[ComparableProperty],
    subject_rooms: Optional[float] = None,
    subject_floor: Optional[int] = None,
    subject_size: Optional[float] = None,
    subject_building_year: Optional[int] = None,
) -> Optional[ValueEstimation]:
    """
    Estimate property value based on comparable transactions.

    Uses weighted average with adjustments for:
    - Recency (newer transactions weighted more)
    - Similarity in rooms, floor, size
    """
    # Filter to actual transactions (not current listings) with price per sqm
    valid = [c for c in comparables if not c.is_listed and c.price_per_sqm and c.price > 0]

    if len(valid) < 3:
        # Fall back to including listings
        valid = [c for c in comparables if c.price_per_sqm and c.price > 0]

    if not valid:
        return None

    # Calculate weighted average price per sqm
    weighted_prices: list[float] = []
    weights: list[float] = []

    current_year = datetime.now().year

    for comp in valid:
        weight = 1.0

        # Recency bonus: transactions from last 12 months get 1.5x weight
        if comp.deal_date:
            months_ago = (datetime.now().date() - comp.deal_date).days / 30
            if months_ago <= 6:
                weight *= 1.5
            elif months_ago <= 12:
                weight *= 1.2
            elif months_ago > 36:
                weight *= 0.6

        # Room similarity bonus
        if subject_rooms and comp.rooms:
            room_diff = abs(subject_rooms - comp.rooms)
            if room_diff == 0:
                weight *= 1.3
            elif room_diff <= 1:
                weight *= 1.0
            else:
                weight *= 0.7

        # Floor similarity
        if subject_floor is not None and comp.floor is not None:
            floor_diff = abs(subject_floor - comp.floor)
            if floor_diff <= 1:
                weight *= 1.2
            elif floor_diff > 5:
                weight *= 0.8

        # Building age similarity
        if subject_building_year and comp.building_year:
            age_diff = abs(subject_building_year - comp.building_year)
            if age_diff <= 5:
                weight *= 1.2
            elif age_diff > 20:
                weight *= 0.8

        weighted_prices.append(comp.price_per_sqm * weight)
        weights.append(weight)

    if not weights:
        return None

    avg_price_sqm = sum(weighted_prices) / sum(weights)

    # Use subject size or average from comparables
    size = subject_size
    if not size:
        sizes = [c.size_sqm for c in valid if c.size_sqm and c.size_sqm > 0]
        size = sum(sizes) / len(sizes) if sizes else 80  # default 80 sqm

    mid_price = avg_price_sqm * size
    low_price = mid_price * 0.92  # -8%
    high_price = mid_price * 1.08  # +8%

    # Determine confidence
    if len(valid) >= 10:
        confidence = "גבוה"
    elif len(valid) >= 5:
        confidence = "בינוני"
    else:
        confidence = "נמוך"

    return ValueEstimation(
        estimated_price_low=round(low_price),
        estimated_price_mid=round(mid_price),
        estimated_price_high=round(high_price),
        estimated_price_per_sqm=round(avg_price_sqm),
        confidence=confidence,
        comparable_count=len(valid),
        methodology="ממוצע משוקלל של עסקאות דומות עם התאמות לגודל, קומה, גיל בניין ועדכניות",
    )


async def generate_report(
    address: str,
    property_type: str,
    transactions_street: list[NadlanTransaction],
    transactions_neighborhood: list[NadlanTransaction],
    transactions_city: list[NadlanTransaction],
    listings: list[Yad2Listing],
    subject_rooms: Optional[float] = None,
    subject_floor: Optional[int] = None,
    subject_size: Optional[float] = None,
    subject_building_year: Optional[int] = None,
) -> MarketAnalysisReport:
    """
    Generate a comprehensive market analysis report.

    Combines data from multiple sources and runs all analyses.
    """
    address_parts = parse_address_parts(address)

    # Combine all transactions (prioritize street > neighborhood > city)
    all_transactions = []
    seen_keys = set()

    for tx_list in [transactions_street, transactions_neighborhood, transactions_city]:
        for tx in tx_list:
            key = f"{tx.address}_{tx.deal_amount}_{tx.deal_date}"
            if key not in seen_keys:
                seen_keys.add(key)
                all_transactions.append(tx)

    # Build comparables
    comparables = build_comparables(all_transactions, listings)

    # Run analyses
    floor_analysis = analyze_floor_prices(all_transactions)
    building_age = analyze_building_age(all_transactions)
    price_trends = analyze_price_trends(all_transactions)

    # Value estimation
    value_est = estimate_value(
        comparables,
        subject_rooms=subject_rooms,
        subject_floor=subject_floor,
        subject_size=subject_size,
        subject_building_year=subject_building_year,
    )

    # Build report
    data_sources = ["nadlan.gov.il"]
    if listings:
        data_sources.append("yad2.co.il")

    report = MarketAnalysisReport(
        subject_address=address,
        subject_property_type=property_type,
        subject_city=address_parts.get("city", ""),
        subject_neighborhood=address_parts.get("neighborhood", ""),
        subject_street=address_parts.get("street", ""),
        transactions=all_transactions,
        current_listings=listings,
        comparables=comparables,
        floor_analysis=floor_analysis,
        building_age_analysis=building_age,
        price_trends=price_trends,
        value_estimation=value_est,
        data_sources_used=data_sources,
    )

    logger.info(
        f"Report generated: {len(all_transactions)} transactions, "
        f"{len(listings)} listings, "
        f"{len(comparables)} comparables"
    )

    return report
