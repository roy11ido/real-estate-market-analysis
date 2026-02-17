"""Pydantic models for market analysis data."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, computed_field


class PropertyType(str, Enum):
    """סוגי נכסים."""
    APARTMENT = "דירה"
    PENTHOUSE = "פנטהאוז"
    HOUSE = "בית פרטי"
    COTTAGE = "קוטג׳"
    GARDEN_APT = "דירת גן"
    DUPLEX = "דופלקס"
    SEMI_DETACHED = "דו-משפחתי"
    TRIPLEX = "טריפלקס"
    LAND = "מגרש"


class DealNature(str, Enum):
    """סוגי עסקאות."""
    SALE = "מכירה"
    NEW_FROM_CONTRACTOR = "מכירה מקבלן"
    COMBINATION = "קומבינציה"
    GIFT = "מתנה"
    OTHER = "אחר"


# --- nadlan.gov.il data models ---


class NadlanTransaction(BaseModel):
    """עסקת נדל\"ן מ-nadlan.gov.il."""

    address: str = ""
    deal_amount: float = 0
    deal_date: Optional[date] = None
    rooms: Optional[float] = None
    floor: Optional[int] = None
    size_sqm: Optional[float] = None
    building_year: Optional[int] = None
    building_floors: Optional[int] = None
    deal_nature: str = ""
    project_name: str = ""
    gush: str = ""
    parcel: str = ""
    property_type: str = ""
    trend_negative: Optional[bool] = None

    @computed_field
    @property
    def price_per_sqm(self) -> Optional[float]:
        if self.size_sqm and self.size_sqm > 0 and self.deal_amount > 0:
            return round(self.deal_amount / self.size_sqm)
        return None

    @computed_field
    @property
    def building_age(self) -> Optional[int]:
        if self.building_year and self.building_year > 1900:
            return datetime.now().year - self.building_year
        return None

    @computed_field
    @property
    def formatted_price(self) -> str:
        if self.deal_amount <= 0:
            return "לא צוין"
        return f"{int(self.deal_amount):,} ש\"ח"

    @computed_field
    @property
    def formatted_date(self) -> str:
        if self.deal_date is None:
            return ""
        return self.deal_date.strftime("%d/%m/%Y")


class NadlanQueryParams(BaseModel):
    """פרמטרים לשאילתה ב-nadlan.gov.il."""

    object_id: str = ""
    object_id_type: str = "text"
    object_key: str = "UNIQ_ID"
    current_level: int = 7  # ADDRESS level
    page_no: int = 1
    filter_room_num: int = 0
    result_label: str = ""
    result_type: str = ""
    desc_layer_id: str = ""
    x: float = 0
    y: float = 0
    original_search: str = ""
    order_by_field: str = ""
    order_by_descending: bool = True
    gush: str = ""
    parcel: str = ""
    is_historical: bool = False


# --- Yad2 listing models ---


class Yad2Listing(BaseModel):
    """נכס מפורסם ביד2."""

    listing_id: str = ""
    address: str = ""
    price: float = 0
    rooms: Optional[float] = None
    floor: Optional[int] = None
    size_sqm: Optional[float] = None
    property_type: str = ""
    description: str = ""
    date_listed: Optional[date] = None
    image_urls: List[str] = Field(default_factory=list)
    url: str = ""
    city: str = ""
    neighborhood: str = ""
    street: str = ""
    is_new_building: bool = False
    building_year: Optional[int] = None

    @computed_field
    @property
    def price_per_sqm(self) -> Optional[float]:
        if self.size_sqm and self.size_sqm > 0 and self.price > 0:
            return round(self.price / self.size_sqm)
        return None

    @computed_field
    @property
    def formatted_price(self) -> str:
        if self.price <= 0:
            return "לא צוין"
        return f"{int(self.price):,} ש\"ח"


# --- Analysis result models ---


class FloorPriceAnalysis(BaseModel):
    """ניתוח מחיר לפי קומה."""

    floor: int
    avg_price_per_sqm: float
    transaction_count: int
    avg_total_price: float

    @computed_field
    @property
    def formatted_avg_price(self) -> str:
        return f"{int(self.avg_total_price):,} ש\"ח"


class BuildingAgeAnalysis(BaseModel):
    """ניתוח מחיר לפי גיל בניין."""

    category: str  # "חדש (0-5)", "בינוני (6-15)", "ישן (16-30)", "ישן מאוד (30+)"
    avg_price_per_sqm: float
    transaction_count: int
    avg_building_year: Optional[int] = None
    price_premium_pct: Optional[float] = None  # אחוז פרמיה/הנחה ביחס לממוצע


class PriceTrend(BaseModel):
    """מגמת מחיר לאורך זמן."""

    period: str  # "2024-Q1", "2024-Q2", etc.
    avg_price_per_sqm: float
    transaction_count: int
    change_pct: Optional[float] = None  # שינוי באחוזים מהתקופה הקודמת


class NearbyPlace(BaseModel):
    """מקום בסביבת הנכס."""

    name: str
    category: str  # "חינוך", "תחבורה", "מסחר", "פנאי", "בריאות"
    distance_meters: Optional[float] = None


class ComparableProperty(BaseModel):
    """נכס להשוואה - מאוחד ממקורות שונים."""

    source: str  # "nadlan.gov.il", "yad2"
    address: str
    price: float
    rooms: Optional[float] = None
    floor: Optional[int] = None
    size_sqm: Optional[float] = None
    building_year: Optional[int] = None
    deal_date: Optional[date] = None
    property_type: str = ""
    is_listed: bool = False  # True = מפורסם עכשיו, False = עסקה שנסגרה

    @computed_field
    @property
    def price_per_sqm(self) -> Optional[float]:
        if self.size_sqm and self.size_sqm > 0 and self.price > 0:
            return round(self.price / self.size_sqm)
        return None

    @computed_field
    @property
    def formatted_price(self) -> str:
        return f"{int(self.price):,} ש\"ח"

    @computed_field
    @property
    def building_age(self) -> Optional[int]:
        if self.building_year and self.building_year > 1900:
            return datetime.now().year - self.building_year
        return None


class ValueEstimation(BaseModel):
    """הערכת שווי."""

    estimated_price_low: float
    estimated_price_mid: float
    estimated_price_high: float
    estimated_price_per_sqm: float
    confidence: str = "בינוני"  # "נמוך", "בינוני", "גבוה"
    comparable_count: int = 0
    methodology: str = ""

    @computed_field
    @property
    def formatted_range(self) -> str:
        low = f"{int(self.estimated_price_low):,}"
        high = f"{int(self.estimated_price_high):,}"
        return f"{low} - {high} ש\"ח"


class MarketAnalysisReport(BaseModel):
    """דו\"ח ניתוח שוק מלא."""

    # פרטי הנכס הנבדק
    subject_address: str
    subject_property_type: str
    subject_city: str = ""
    subject_neighborhood: str = ""
    subject_street: str = ""

    # נתונים גולמיים
    transactions: List[NadlanTransaction] = Field(default_factory=list)
    current_listings: List[Yad2Listing] = Field(default_factory=list)
    comparables: List[ComparableProperty] = Field(default_factory=list)

    # ניתוחים
    floor_analysis: List[FloorPriceAnalysis] = Field(default_factory=list)
    building_age_analysis: List[BuildingAgeAnalysis] = Field(default_factory=list)
    price_trends: List[PriceTrend] = Field(default_factory=list)
    nearby_places: List[NearbyPlace] = Field(default_factory=list)

    # הערכת שווי
    value_estimation: Optional[ValueEstimation] = None

    # סיכום AI
    ai_summary: str = ""

    # מטא-דאטה
    report_date: datetime = Field(default_factory=datetime.now)
    data_sources_used: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    @computed_field
    @property
    def avg_price_per_sqm_street(self) -> Optional[float]:
        """ממוצע מחיר למ\"ר ברחוב."""
        sqm_prices = [t.price_per_sqm for t in self.transactions if t.price_per_sqm]
        if sqm_prices:
            return round(sum(sqm_prices) / len(sqm_prices))
        return None

    @computed_field
    @property
    def total_transactions(self) -> int:
        return len(self.transactions)

    @computed_field
    @property
    def total_listings(self) -> int:
        return len(self.current_listings)
