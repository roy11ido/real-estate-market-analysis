"""
מודול עסקאות נדל"ן — ניהול, יבוא, ניתוח עסקאות השוואתיות (Comps).

מקורות נתמכים
──────────────
1. nadlan_api   – ה-REST API הרשמי של www.nadlan.gov.il (כבר מקושר)
2. manual_csv   – יבוא CSV/Excel שייצא המשתמש ידנית מ-nadlan.gov.il / GovMap
3. manual_entry – הזנה ידנית

עמדת ציות
──────────
• nadlan.gov.il/Nadlan.REST/Main — נקודת קצה רשמית ודוקומנטרית חלקית
  (משמשת ממשק הציבור של האתר, לא דורשת אימות, rate-limit ידוע).
• האתר השני: nadlan.taxes.gov.il — ממשק WEB בלבד, ללא API מתועד,
  מוגן ב-CAPTCHA ו-POST עם session nonce. אין יבוא API תקין.
  → fallback: ייצוא ידני (Excel) על-ידי המשתמש + יבוא כאן.
• GovMap (govmap.gov.il) — שכבת מפה ממשלתית. מציג נתונים ממקורות שונים.
  אין REST API ציבורי מתועד לנדל"ן. הנתונים מוגנים.
  → fallback: ייצוא ידני (הורדת Excel מהאתר) + יבוא כאן.
"""
from __future__ import annotations

import csv
import io
import json
import math
import re
from datetime import date, datetime
from typing import Any

import pandas as pd
from pydantic import BaseModel, Field, field_validator


# ── מודלים ───────────────────────────────────────────────────────────────────

class Transaction(BaseModel):
    """עסקת נדל"ן אחת — מקור כלשהו."""

    # זיהוי
    id: str = ""
    source: str = "nadlan_api"   # nadlan_api | manual_csv | manual_entry

    # כתובת
    formatted_address: str = ""
    street: str = ""
    city: str = ""
    neighborhood: str = ""
    postal_code: str = ""
    lat: float | None = None
    lng: float | None = None

    # נכס
    property_type: str = "דירה"
    rooms: float | None = None
    floor: int | None = None
    size_sqm: float | None = None
    building_year: int | None = None
    floors_in_building: int | None = None

    # עסקה
    deal_amount: float = 0.0
    deal_date: date | None = None
    deal_nature: str = "מכירה"    # מכירה | שכירות | חכירה

    # מגרש
    gush: str = ""
    parcel: str = ""

    # מקור חיצוני
    source_url: str = ""
    source_ref: str = ""
    imported_at: datetime = Field(default_factory=datetime.now)

    @field_validator("deal_date", mode="before")
    @classmethod
    def parse_deal_date(cls, v):
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d"):
                try:
                    return datetime.strptime(v, fmt).date()
                except ValueError:
                    pass
            # /Date(milliseconds)/ format from nadlan API
            m = re.search(r"/Date\((\d+)", v)
            if m:
                return datetime.fromtimestamp(int(m.group(1)) / 1000).date()
        return None

    @property
    def price_per_sqm(self) -> float | None:
        if self.size_sqm and self.size_sqm > 0 and self.deal_amount > 0:
            return self.deal_amount / self.size_sqm
        return None

    @property
    def formatted_price(self) -> str:
        if self.deal_amount <= 0:
            return "לא ידוע"
        return f"₪{self.deal_amount:,.0f}"

    @property
    def formatted_date(self) -> str:
        if not self.deal_date:
            return "לא ידוע"
        return self.deal_date.strftime("%d/%m/%Y")

    @property
    def formatted_price_per_sqm(self) -> str:
        ppsqm = self.price_per_sqm
        if ppsqm is None:
            return "—"
        return f"₪{ppsqm:,.0f}/מ\"ר"

    def distance_km(self, lat: float, lng: float) -> float | None:
        """מרחק בק"מ מנקודת מוצא (Haversine)."""
        if self.lat is None or self.lng is None:
            return None
        R = 6371.0
        dlat = math.radians(self.lat - lat)
        dlng = math.radians(self.lng - lng)
        a = (math.sin(dlat / 2) ** 2
             + math.cos(math.radians(lat)) * math.cos(math.radians(self.lat))
             * math.sin(dlng / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))


# ── נורמליזציה מה-NadlanTransaction ──────────────────────────────────────────

def from_nadlan_transaction(tx: Any) -> Transaction:
    """המרת NadlanTransaction → Transaction.

    NadlanTransaction fields: address, deal_amount, deal_date, rooms,
    floor, size_sqm, building_year, building_floors, deal_nature,
    project_name, gush, parcel, property_type.
    """
    raw_addr = getattr(tx, "address", "") or ""
    # נסה לחלץ עיר מהכתובת ("רחוב מספר, עיר")
    city = ""
    street = ""
    if "," in raw_addr:
        parts = raw_addr.split(",")
        street = parts[0].strip()
        city   = parts[-1].strip()

    return Transaction(
        id=f"nadlan_{getattr(tx,'gush','')}_{getattr(tx,'parcel','')}_{tx.deal_date}",
        source="nadlan_api",
        formatted_address=raw_addr,
        street=street,
        city=city,
        neighborhood="",
        lat=None,  # nadlan API לא מחזיר lat/lng ישירות
        lng=None,
        property_type=getattr(tx, "property_type", "") or "דירה",
        rooms=getattr(tx, "rooms", None),
        floor=getattr(tx, "floor", None),
        size_sqm=getattr(tx, "size_sqm", None),
        building_year=getattr(tx, "building_year", None),
        floors_in_building=getattr(tx, "building_floors", None),
        deal_amount=tx.deal_amount,
        deal_date=tx.deal_date,
        deal_nature=getattr(tx, "deal_nature", "") or "מכירה",
        gush=getattr(tx, "gush", "") or "",
        parcel=getattr(tx, "parcel", "") or "",
        source_url="https://www.nadlan.gov.il/",
    )


# ── ייבוא CSV / Excel ─────────────────────────────────────────────────────────

# מיפוי שמות עמודות אפשריים (nadlan.gov.il Excel export / GovMap export)
_COLUMN_ALIASES: dict[str, list[str]] = {
    "formatted_address":  ["כתובת", "כתובת מלאה", "address", "כתובת הנכס"],
    "street":             ["רחוב", "שם רחוב", "street"],
    "city":               ["עיר", "ישוב", "city"],
    "neighborhood":       ["שכונה", "neighborhood"],
    "deal_amount":        ["סכום עסקה", "מחיר", "price", "deal_amount", "ערך עסקה"],
    "deal_date":          ["תאריך עסקה", "תאריך", "date", "deal_date"],
    "size_sqm":           ["שטח", "שטח מ\"ר", "שטח (מ\"ר)", "area", "size_sqm"],
    "rooms":              ["חדרים", "מספר חדרים", "rooms"],
    "floor":              ["קומה", "floor"],
    "building_year":      ["שנת בנייה", "שנה", "year_built"],
    "property_type":      ["סוג נכס", "property_type", "type"],
    "gush":               ["גוש", "gush"],
    "parcel":             ["חלקה", "parcel"],
    "lat":                ["latitude", "lat", "קו רוחב"],
    "lng":                ["longitude", "lng", "lon", "קו אורך"],
    "source_ref":         ["מקור", "reference", "מזהה"],
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """שנה שמות עמודות ל-canonical names."""
    rename_map: dict[str, str] = {}
    col_lower = {c.strip().lower(): c for c in df.columns}

    for canon, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias.strip().lower() in col_lower:
                rename_map[col_lower[alias.strip().lower()]] = canon
                break

    return df.rename(columns=rename_map)


def _safe_float(v: Any) -> float | None:
    try:
        s = str(v).replace(",", "").replace("₪", "").replace("מ\"ר", "").strip()
        return float(s) if s else None
    except (ValueError, TypeError):
        return None


def _safe_int(v: Any) -> int | None:
    f = _safe_float(v)
    return int(f) if f is not None else None


def import_transactions_from_bytes(
    raw: bytes,
    file_name: str,
    source_label: str = "manual_csv",
) -> tuple[list[Transaction], list[str]]:
    """
    קרא קובץ CSV או Excel ממחרוזת bytes.

    מחזיר:
        (transactions, errors)  — errors הן שורות שנכשלו
    """
    errors: list[str] = []
    transactions: list[Transaction] = []

    # קריאת הקובץ
    try:
        if file_name.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(raw))
        else:
            # נסה קידודים שונים
            for enc in ("utf-8-sig", "utf-8", "cp1255", "iso-8859-8"):
                try:
                    df = pd.read_csv(io.BytesIO(raw), encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                return [], ["שגיאה: לא ניתן לקרוא את הקובץ (בדוק קידוד)"]
    except Exception as e:
        return [], [f"שגיאה בקריאת הקובץ: {e}"]

    df = _normalize_columns(df)

    for i, row in df.iterrows():
        try:
            def g(col, default=None):
                return row.get(col, default)

            deal_amount = _safe_float(g("deal_amount")) or 0.0
            if deal_amount <= 0:
                errors.append(f"שורה {i+2}: סכום עסקה לא תקין — מדולגת")
                continue

            tx = Transaction(
                id=f"{source_label}_{i}",
                source=source_label,
                formatted_address=str(g("formatted_address", "") or ""),
                street=str(g("street", "") or ""),
                city=str(g("city", "") or ""),
                neighborhood=str(g("neighborhood", "") or ""),
                lat=_safe_float(g("lat")),
                lng=_safe_float(g("lng")),
                property_type=str(g("property_type", "דירה") or "דירה"),
                rooms=_safe_float(g("rooms")),
                floor=_safe_int(g("floor")),
                size_sqm=_safe_float(g("size_sqm")),
                building_year=_safe_int(g("building_year")),
                deal_amount=deal_amount,
                deal_date=g("deal_date"),
                deal_nature="מכירה",
                gush=str(g("gush", "") or ""),
                parcel=str(g("parcel", "") or ""),
                source_ref=str(g("source_ref", "") or ""),
                source_url="",
            )
            transactions.append(tx)
        except Exception as e:
            errors.append(f"שורה {i+2}: {e}")

    return transactions, errors


# ── פילטור ───────────────────────────────────────────────────────────────────

def filter_transactions(
    transactions: list[Transaction],
    city: str | None = None,
    street: str | None = None,
    min_rooms: float | None = None,
    max_rooms: float | None = None,
    min_sqm: float | None = None,
    max_sqm: float | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    radius_km: float | None = None,
    center_lat: float | None = None,
    center_lng: float | None = None,
    property_type: str | None = None,
) -> list[Transaction]:
    """סנן רשימת עסקאות לפי פרמטרים."""
    result = transactions

    if city:
        result = [t for t in result if city in t.city]
    if street:
        result = [t for t in result if street in t.street]
    if property_type and property_type != "הכל":
        result = [t for t in result if t.property_type == property_type]
    if min_rooms is not None:
        result = [t for t in result if t.rooms is not None and t.rooms >= min_rooms]
    if max_rooms is not None:
        result = [t for t in result if t.rooms is not None and t.rooms <= max_rooms]
    if min_sqm is not None:
        result = [t for t in result if t.size_sqm is not None and t.size_sqm >= min_sqm]
    if max_sqm is not None:
        result = [t for t in result if t.size_sqm is not None and t.size_sqm <= max_sqm]
    if min_price is not None:
        result = [t for t in result if t.deal_amount >= min_price]
    if max_price is not None:
        result = [t for t in result if t.deal_amount <= max_price]
    if date_from is not None:
        result = [t for t in result if t.deal_date is not None and t.deal_date >= date_from]
    if date_to is not None:
        result = [t for t in result if t.deal_date is not None and t.deal_date <= date_to]
    if radius_km is not None and center_lat is not None and center_lng is not None:
        result = [
            t for t in result
            if (d := t.distance_km(center_lat, center_lng)) is not None and d <= radius_km
        ]

    return result


# ── ניתוח Comps ──────────────────────────────────────────────────────────────

class CompsAnalysis(BaseModel):
    """ניתוח עסקאות השוואתיות."""
    transactions: list[Transaction]
    count: int = 0
    avg_price: float = 0.0
    median_price: float = 0.0
    avg_price_per_sqm: float = 0.0
    min_price: float = 0.0
    max_price: float = 0.0
    confidence: str = "נמוכה"   # נמוכה / בינונית / גבוהה
    estimated_value: float | None = None
    subject_delta_pct: float | None = None


def analyze_comps(
    transactions: list[Transaction],
    subject_price: float | None = None,
    subject_sqm: float | None = None,
) -> CompsAnalysis:
    """חישוב מדדים מ-comps שנבחרו."""
    valid = [t for t in transactions if t.deal_amount > 0]
    if not valid:
        return CompsAnalysis(transactions=transactions)

    prices = sorted(t.deal_amount for t in valid)
    n = len(prices)
    avg = sum(prices) / n
    median = (prices[n // 2 - 1] + prices[n // 2]) / 2 if n % 2 == 0 else prices[n // 2]

    ppsqm_list = [t.price_per_sqm for t in valid if t.price_per_sqm]
    avg_ppsqm = sum(ppsqm_list) / len(ppsqm_list) if ppsqm_list else 0.0

    # confidence
    confidence = "נמוכה" if n < 3 else ("בינונית" if n < 7 else "גבוהה")

    # הערכה אם יש שטח
    estimated = None
    delta = None
    if subject_sqm and avg_ppsqm:
        estimated = avg_ppsqm * subject_sqm
    if subject_price and estimated:
        delta = (subject_price - estimated) / estimated * 100

    return CompsAnalysis(
        transactions=transactions,
        count=n,
        avg_price=avg,
        median_price=median,
        avg_price_per_sqm=avg_ppsqm,
        min_price=min(prices),
        max_price=max(prices),
        confidence=confidence,
        estimated_value=estimated,
        subject_delta_pct=delta,
    )


# ── Session state helpers ─────────────────────────────────────────────────────

def get_session_transactions() -> list[Transaction]:
    """קרא עסקאות מ-Streamlit session state."""
    import streamlit as st
    return st.session_state.get("transactions_store", [])


def add_transactions_to_session(new_txs: list[Transaction]) -> int:
    """הוסף עסקאות ל-session state, מניעת כפילויות לפי ID."""
    import streamlit as st
    existing = st.session_state.get("transactions_store", [])
    existing_ids = {t.id for t in existing}
    added = [t for t in new_txs if t.id not in existing_ids]
    st.session_state["transactions_store"] = existing + added
    return len(added)


def clear_session_transactions():
    import streamlit as st
    st.session_state["transactions_store"] = []
