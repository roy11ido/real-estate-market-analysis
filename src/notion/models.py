"""Pydantic models for real estate property data from Notion."""

from __future__ import annotations

from pydantic import BaseModel, Field


PROPERTY_TYPE_EMOJI = {
    "דירה": "🏠",
    "פנטהאוז": "🏙️",
    "בית פרטי": "🏡",
    "קוטג׳": "🏡",
    "דירת גן": "🌿",
    "דופלקס": "🏠",
    "דו-משפחתי": "🏘️",
    "טריפלקס": "🏠",
    "מגרש": "📐",
}

CITY_HASHTAGS = {
    "תל אביב": "#תלאביב",
    "ירושלים": "#ירושלים",
    "חיפה": "#חיפה",
    "רמת גן": "#רמתגן",
    "הרצליה": "#הרצליה",
    "רעננה": "#רעננה",
    "כפר סבא": "#כפרסבא",
    "נתניה": "#נתניה",
    "ראשון לציון": "#ראשוןלציון",
    "פתח תקווה": "#פתחתקווה",
    "אשדוד": "#אשדוד",
    "באר שבע": "#באר_שבע",
    "הוד השרון": "#הודהשרון",
    "רמת השרון": "#רמתהשרון",
    "גבעתיים": "#גבעתיים",
}


class Property(BaseModel):
    """Represents a real estate property from Notion database."""

    page_id: str
    address: str
    price: float | None = None
    rooms: float | None = None
    size_sqm: float | None = None
    floor: float | None = None
    description: str = ""
    image_urls: list[str] = Field(default_factory=list)
    property_type: str = "דירה"
    property_url: str | None = None
    fb_status: str | None = None

    @property
    def formatted_price(self) -> str:
        """Format price with Hebrew conventions: 1,500,000 ש\"ח"""
        if self.price is None:
            return "לא צוין"
        return f"{int(self.price):,} ש\"ח"

    @property
    def emoji(self) -> str:
        """Get emoji for property type."""
        return PROPERTY_TYPE_EMOJI.get(self.property_type, "🏠")

    def get_hashtags(self) -> str:
        """Generate relevant Hebrew hashtags based on property data."""
        tags = ["#נדלן", "#למכירה"]

        # Add city hashtag
        for city, tag in CITY_HASHTAGS.items():
            if city in self.address:
                tags.append(tag)
                break

        # Add property type hashtag
        type_tags = {
            "דירה": "#דירהלמכירה",
            "פנטהאוז": "#פנטהאוז",
            "בית פרטי": "#ביתפרטי",
            "קוטג׳": "#קוטג",
            "דירת גן": "#דירתגן",
            "דופלקס": "#דופלקס",
            "מגרש": "#מגרש",
        }
        if self.property_type in type_tags:
            tags.append(type_tags[self.property_type])

        return " ".join(tags)

    @property
    def display_summary(self) -> str:
        """Short summary for GUI display."""
        parts = [self.address]
        if self.property_type:
            parts.append(f"({self.property_type})")
        if self.price:
            parts.append(f"- {self.formatted_price}")
        if self.rooms:
            parts.append(f"- {self.rooms} חד'")
        return " ".join(parts)
