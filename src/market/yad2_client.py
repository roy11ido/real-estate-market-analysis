"""Client for Yad2.co.il - Current real estate listings scraper."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

import httpx

from src.market.models import Yad2Listing

logger = logging.getLogger("realestate")

# Yad2 feed search API (reverse-engineered)
YAD2_FEED_URL = "https://gw.yad2.co.il/feed-search-legacy/realestate/forsale"

HEADERS = {
    "Accept": "application/json",
    "Accept-Language": "he-IL,he;q=0.9",
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.yad2.co.il/realestate/forsale",
    "Origin": "https://www.yad2.co.il",
}

# Yad2 property type codes
PROPERTY_TYPE_MAP = {
    "דירה": "1",
    "דירת גן": "3",
    "פנטהאוז": "4",
    "דופלקס": "7",
    "בית פרטי": "5",
    "קוטג׳": "6",
    "דו-משפחתי": "29",
    "מגרש": "11",
    "טריפלקס": "25",
}

# City codes for common cities (reverse-engineered from yad2 URLs)
CITY_CODE_MAP = {
    "תל אביב": "5000",
    "ירושלים": "3000",
    "חיפה": "4000",
    "רמת גן": "8600",
    "הרצליה": "6400",
    "רעננה": "8700",
    "כפר סבא": "6900",
    "נתניה": "7400",
    "ראשון לציון": "8300",
    "פתח תקווה": "7900",
    "אשדוד": "70",
    "באר שבע": "9000",
    "הוד השרון": "6500",
    "רמת השרון": "8800",
    "גבעתיים": "6300",
    "בת ים": "2100",
    "חולון": "6600",
    "אשקלון": "7100",
    "מודיעין": "1200",
    "נהריה": "7300",
    "עכו": "4100",
}

REQUEST_DELAY = 3.0


def _parse_listing(item: dict) -> Optional[Yad2Listing]:
    """Parse a Yad2 feed item into a Yad2Listing model."""
    try:
        # Extract price
        price_str = str(item.get("price", "0"))
        price = float(re.sub(r"[^\d.]", "", price_str) or "0")

        # Extract images
        images = []
        img_data = item.get("images", []) or item.get("media", {}).get("images", [])
        if isinstance(img_data, list):
            for img in img_data:
                if isinstance(img, dict):
                    url = img.get("src") or img.get("url", "")
                    if url:
                        images.append(url)
                elif isinstance(img, str):
                    images.append(img)

        # Parse date
        date_listed = None
        date_str = item.get("date", "") or item.get("DateUpdated", "")
        if date_str:
            try:
                date_listed = datetime.fromisoformat(str(date_str).replace("Z", "")).date()
            except (ValueError, TypeError):
                pass

        # Build listing
        address_parts = [
            item.get("street", ""),
            item.get("neighborhood", ""),
            item.get("city", ""),
        ]
        address = ", ".join(p for p in address_parts if p)

        listing = Yad2Listing(
            listing_id=str(item.get("id", item.get("token", ""))),
            address=address or item.get("title", ""),
            price=price,
            rooms=float(item.get("rooms", 0) or 0) or None,
            floor=int(item.get("floor", 0) or 0) if item.get("floor") else None,
            size_sqm=float(item.get("square_meters", 0) or item.get("squaremeter", 0) or 0) or None,
            property_type=item.get("property_type_text", item.get("sub_type_text", "")),
            description=item.get("info_text", item.get("description", "")),
            date_listed=date_listed,
            image_urls=images[:5],
            url=item.get("link_token", item.get("link", "")),
            city=item.get("city", ""),
            neighborhood=item.get("neighborhood", ""),
            street=item.get("street", ""),
            is_new_building=bool(item.get("is_new_building") or item.get("isNewBuilding")),
            building_year=int(item.get("building_year", 0) or 0) or None,
        )
        return listing

    except Exception as e:
        logger.debug(f"Failed to parse Yad2 listing: {e}")
        return None


async def search_listings(
    city: str,
    property_type: str = "",
    rooms_min: float = 0,
    rooms_max: float = 0,
    price_min: float = 0,
    price_max: float = 0,
    neighborhood: str = "",
    max_pages: int = 2,
) -> list[Yad2Listing]:
    """
    Search Yad2 for current real estate listings.

    Args:
        city: City name in Hebrew
        property_type: Property type in Hebrew (from PROPERTY_TYPE_MAP)
        rooms_min/max: Room count filter
        price_min/max: Price range filter
        neighborhood: Neighborhood name
        max_pages: Max pages to fetch

    Returns:
        List of Yad2Listing objects
    """
    listings: list[Yad2Listing] = []

    # Build query parameters
    params: dict = {}

    city_code = CITY_CODE_MAP.get(city)
    if city_code:
        params["city"] = city_code

    if property_type and property_type in PROPERTY_TYPE_MAP:
        params["property"] = PROPERTY_TYPE_MAP[property_type]

    if rooms_min > 0:
        params["rooms"] = f"{rooms_min}-{rooms_max if rooms_max > 0 else 12}"

    if price_min > 0:
        params["price"] = f"{int(price_min)}-{int(price_max) if price_max > 0 else 50000000}"

    async with httpx.AsyncClient(timeout=30, headers=HEADERS, follow_redirects=True) as client:
        for page in range(1, max_pages + 1):
            params["page"] = str(page)

            try:
                resp = await client.get(YAD2_FEED_URL, params=params)

                if resp.status_code == 403:
                    logger.warning("Yad2 blocked request (403). Anti-bot detected.")
                    break

                resp.raise_for_status()
                data = resp.json()

                feed = data.get("data", {}).get("feed", {})
                items = feed.get("feed_items", [])

                if not items:
                    logger.info(f"Yad2: No more results at page {page}")
                    break

                page_count = 0
                for item in items:
                    # Skip ads and non-listing items
                    item_type = item.get("type", "")
                    if item_type in ("ad", "banner", "commercialContent"):
                        continue

                    listing = _parse_listing(item)
                    if listing and listing.price > 0:
                        # Filter by neighborhood if specified
                        if neighborhood and neighborhood not in listing.neighborhood:
                            continue
                        listings.append(listing)
                        page_count += 1

                logger.info(f"Yad2 page {page}: {page_count} listings")

                # Check if there are more pages
                total_pages = feed.get("total_pages", 1)
                if page >= total_pages:
                    break

                await asyncio.sleep(REQUEST_DELAY)

            except httpx.HTTPStatusError as e:
                logger.error(f"Yad2 HTTP error page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"Yad2 error page {page}: {e}")
                break

    logger.info(f"Yad2: Total listings fetched: {len(listings)}")
    return listings


async def search_similar_listings(
    city: str,
    property_type: str,
    rooms: Optional[float] = None,
    price: Optional[float] = None,
    neighborhood: str = "",
) -> list[Yad2Listing]:
    """
    Search for similar listings to a subject property.
    Automatically sets reasonable filter ranges based on subject property.
    """
    rooms_min = max(1, (rooms or 3) - 1)
    rooms_max = (rooms or 3) + 1

    if price and price > 0:
        price_min = price * 0.7
        price_max = price * 1.3
    else:
        price_min = 0
        price_max = 0

    return await search_listings(
        city=city,
        property_type=property_type,
        rooms_min=rooms_min,
        rooms_max=rooms_max,
        price_min=price_min,
        price_max=price_max,
        neighborhood=neighborhood,
        max_pages=2,
    )
