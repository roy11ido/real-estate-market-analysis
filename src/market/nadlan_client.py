"""Client for nadlan.gov.il - Israel Government Real Estate Transactions API."""

from __future__ import annotations

import asyncio
import logging
import os
import urllib.parse
from datetime import datetime
from typing import Optional

import httpx

from src.market.models import NadlanQueryParams, NadlanTransaction

logger = logging.getLogger("realestate")

BASE_URL = "https://www.nadlan.gov.il/Nadlan.REST/Main"
SCRAPERAPI_BASE = "http://api.scraperapi.com"


def _get_scraper_key() -> str:
    """Get ScraperAPI key at runtime - checks os.environ and Streamlit secrets."""
    key = os.environ.get("SCRAPERAPI_KEY", "")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("SCRAPERAPI_KEY", "")
        except Exception:
            pass
    return key


def _build_scraper_url(target_url: str) -> str:
    """Wrap a URL through ScraperAPI if key is available."""
    key = _get_scraper_key()
    if key:
        encoded = urllib.parse.quote(target_url, safe="")
        return f"{SCRAPERAPI_BASE}?api_key={key}&url={encoded}&render=false"
    return target_url

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://www.nadlan.gov.il",
    "Referer": "https://www.nadlan.gov.il/",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "Connection": "keep-alive",
}

# Delay between API requests (seconds) to avoid rate limiting
REQUEST_DELAY = 2.0


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string from nadlan.gov.il response."""
    if not date_str:
        return None
    # Format: "/Date(1700000000000)/" or "2024-01-15T00:00:00"
    if "/Date(" in str(date_str):
        try:
            ts = int(str(date_str).split("(")[1].split(")")[0].split("+")[0].split("-")[0])
            return datetime.fromtimestamp(ts / 1000).date()
        except (ValueError, IndexError):
            return None
    try:
        return datetime.fromisoformat(str(date_str).replace("Z", "")).date()
    except (ValueError, TypeError):
        return None


def _parse_transaction(raw: dict) -> NadlanTransaction:
    """Parse a raw transaction dict into a NadlanTransaction model."""
    return NadlanTransaction(
        address=raw.get("FULLADRESS", raw.get("DISPLAYADRESS", "")),
        deal_amount=float(raw.get("DEALAMOUNT", 0) or 0),
        deal_date=_parse_date(raw.get("DEALDATETIME") or raw.get("DEALDATE")),
        rooms=float(raw.get("ASSETROOMNUM", 0) or 0) or None,
        floor=int(raw.get("FLOORNO", 0) or 0) if raw.get("FLOORNO") else None,
        size_sqm=float(raw.get("DEALAREAMETER", 0) or raw.get("ASSETAREAMETER", 0) or 0) or None,
        building_year=int(raw.get("BUILDINGYEAR", 0) or 0) or None,
        building_floors=int(raw.get("BUILDINGFLOORS", 0) or 0) or None,
        deal_nature=raw.get("DEALNATUREDESCRIPTION", ""),
        project_name=raw.get("PROJECTNAME", ""),
        gush=str(raw.get("GUSH", "")),
        parcel=str(raw.get("PARCEL", "")),
        property_type=raw.get("NEWPROJECTNAME", raw.get("TYPE", "")),
        trend_negative=raw.get("TREND_IS_NEGATIVE"),
    )


async def resolve_address(query: str) -> Optional[NadlanQueryParams]:
    """
    Resolve a search string into structured nadlan.gov.il query parameters.

    Takes a Hebrew address/city/neighborhood string and returns parameters
    that can be used with get_transactions().
    """
    target_url = f"{BASE_URL}/GetDataByQuery?query={urllib.parse.quote(query)}"
    url = _build_scraper_url(target_url)

    try:
        async with httpx.AsyncClient(timeout=60, headers=HEADERS) as client:
            resp = await client.get(url)
            logger.info(f"resolve_address status={resp.status_code} url={url[:80]}")
            logger.info(f"resolve_address response_text={resp.text[:300]}")
            resp.raise_for_status()
            data = resp.json()

        if not data:
            logger.warning(f"No results for address query: {query}")
            return None

        result = data if isinstance(data, dict) else {}

        query_params = NadlanQueryParams(
            object_id=str(result.get("ObjectID", "")),
            object_id_type=str(result.get("ObjectIDType", "text")),
            object_key=str(result.get("ObjectKey", "UNIQ_ID")),
            current_level=int(result.get("CurrentLavel", 7)),
            result_label=str(result.get("ResultLable", query)),
            result_type=str(result.get("ResultType", "")),
            desc_layer_id=str(result.get("DescLayerID", "")),
            x=float(result.get("X", 0) or 0),
            y=float(result.get("Y", 0) or 0),
            original_search=query,
            gush=str(result.get("Gush", "")),
            parcel=str(result.get("Parcel", "")),
        )

        logger.info(f"Resolved address '{query}' -> level={query_params.current_level}")
        return query_params

    except httpx.HTTPError as e:
        logger.error(f"HTTP error resolving address '{query}': {e}")
        return None
    except Exception as e:
        logger.error(f"Error resolving address '{query}': {e}")
        return None


async def get_transactions(
    params: NadlanQueryParams,
    max_pages: int = 5,
    room_filter: int = 0,
) -> list[NadlanTransaction]:
    """
    Fetch real estate transactions from nadlan.gov.il.

    Args:
        params: Query parameters (from resolve_address)
        max_pages: Maximum number of pages to fetch
        room_filter: Filter by room count (0 = all)

    Returns:
        List of NadlanTransaction objects
    """
    transactions: list[NadlanTransaction] = []
    url = f"{BASE_URL}/GetAssestAndDeals"

    async with httpx.AsyncClient(timeout=60, headers=HEADERS) as client:
        for page in range(1, max_pages + 1):
            payload = {
                "ObjectID": params.object_id,
                "ObjectIDType": params.object_id_type,
                "ObjectKey": params.object_key,
                "CurrentLavel": params.current_level,
                "PageNo": page,
                "MoreAssestsType": 0,
                "FillterRoomNum": room_filter,
                "GridDisplayType": 0,
                "ResultLable": params.result_label,
                "ResultType": params.result_type,
                "DescLayerID": params.desc_layer_id,
                "X": params.x,
                "Y": params.y,
                "OriginalSearchString": params.original_search,
                "OrderByFilled": params.order_by_field,
                "OrderByDescending": params.order_by_descending,
                "Gush": params.gush,
                "Parcel": params.parcel,
                "QueryMapParams": {},
                "isHistorical": params.is_historical,
            }

            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()

                results = data.get("AllResults", [])
                if not results:
                    logger.info(f"No more results at page {page}")
                    break

                for raw in results:
                    tx = _parse_transaction(raw)
                    if tx.deal_amount > 0:
                        transactions.append(tx)

                logger.info(f"Page {page}: fetched {len(results)} transactions")

                is_last = data.get("IsLastPage", True)
                if is_last:
                    break

                # Rate limiting delay
                await asyncio.sleep(REQUEST_DELAY)

            except httpx.HTTPError as e:
                logger.error(f"HTTP error fetching page {page}: {e}")
                break
            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

    logger.info(f"Total transactions fetched: {len(transactions)}")
    return transactions


async def get_transactions_for_address(
    address: str,
    max_pages: int = 5,
    room_filter: int = 0,
) -> list[NadlanTransaction]:
    """
    Convenience function: resolve address and fetch transactions in one call.
    """
    params = await resolve_address(address)
    if not params:
        return []
    return await get_transactions(params, max_pages=max_pages, room_filter=room_filter)


async def search_neighborhood(city: str, neighborhood: str, max_pages: int = 3) -> list[NadlanTransaction]:
    """Fetch transactions for a specific neighborhood."""
    query = f"{neighborhood}, {city}"
    return await get_transactions_for_address(query, max_pages=max_pages)


async def search_city(city: str, max_pages: int = 2) -> list[NadlanTransaction]:
    """Fetch transactions for an entire city (limited)."""
    return await get_transactions_for_address(city, max_pages=max_pages)


async def get_streets_for_city(city: str) -> list[str]:
    """Get list of streets in a city."""
    url = f"{BASE_URL}/GetStreetsListByCityAndStartsWith"
    params = {"CityName": city, "startWithKey": "-1"}

    try:
        async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return [s.get("Text", "") for s in data if s.get("Text")]
    except Exception as e:
        logger.error(f"Error fetching streets for {city}: {e}")
        return []


async def get_neighborhoods_for_city(city: str) -> list[str]:
    """Get list of neighborhoods in a city."""
    url = f"{BASE_URL}/GetNeighborhoodsListByCity"
    params = {"CityName": city}

    try:
        async with httpx.AsyncClient(timeout=30, headers=HEADERS) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            return [n.get("Text", "") for n in data if n.get("Text")]
    except Exception as e:
        logger.error(f"Error fetching neighborhoods for {city}: {e}")
        return []
