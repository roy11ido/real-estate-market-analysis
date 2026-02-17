"""AI-powered market analysis summary using Claude API."""

from __future__ import annotations

import logging
import os

from src.market.models import MarketAnalysisReport

logger = logging.getLogger("realestate")


def _build_prompt(report: MarketAnalysisReport) -> str:
    """Build a Hebrew prompt for Claude based on report data."""

    # Transaction summary
    tx_summary = ""
    if report.transactions:
        prices = [t.deal_amount for t in report.transactions if t.deal_amount > 0]
        sqm_prices = [t.price_per_sqm for t in report.transactions if t.price_per_sqm]
        tx_summary = f"""
עסקאות שנמצאו: {len(report.transactions)}
טווח מחירים: {min(prices):,.0f} - {max(prices):,.0f} ש"ח
ממוצע מחיר למ"ר: {sum(sqm_prices)/len(sqm_prices):,.0f} ש"ח (מתוך {len(sqm_prices)} עסקאות)
"""
        # Recent transactions
        recent = sorted(
            [t for t in report.transactions if t.deal_date],
            key=lambda t: t.deal_date,
            reverse=True,
        )[:10]
        if recent:
            tx_summary += "\nעסקאות אחרונות:\n"
            for t in recent:
                tx_summary += (
                    f"  - {t.address} | {t.formatted_price} | "
                    f"{t.rooms or '?'} חד' | קומה {t.floor or '?'} | "
                    f"{t.size_sqm or '?'} מ\"ר | "
                    f"שנת בנייה {t.building_year or '?'} | "
                    f"{t.formatted_date}\n"
                )

    # Floor analysis
    floor_summary = ""
    if report.floor_analysis:
        floor_summary = "\nניתוח לפי קומה:\n"
        for fa in report.floor_analysis:
            floor_summary += (
                f"  - קומה {fa.floor}: ממוצע {fa.avg_price_per_sqm:,.0f} ש\"ח/מ\"ר "
                f"({fa.transaction_count} עסקאות)\n"
            )

    # Building age analysis
    age_summary = ""
    if report.building_age_analysis:
        age_summary = "\nניתוח לפי גיל בניין:\n"
        for ba in report.building_age_analysis:
            premium = f" ({ba.price_premium_pct:+.1f}%)" if ba.price_premium_pct is not None else ""
            age_summary += (
                f"  - {ba.category}: {ba.avg_price_per_sqm:,.0f} ש\"ח/מ\"ר{premium} "
                f"({ba.transaction_count} עסקאות)\n"
            )

    # Price trends
    trend_summary = ""
    if report.price_trends:
        trend_summary = "\nמגמות מחיר (לפי רבעון):\n"
        for pt in report.price_trends[-8:]:  # Last 8 quarters
            change = f" ({pt.change_pct:+.1f}%)" if pt.change_pct is not None else ""
            trend_summary += (
                f"  - {pt.period}: {pt.avg_price_per_sqm:,.0f} ש\"ח/מ\"ר{change}\n"
            )

    # Current listings
    listings_summary = ""
    if report.current_listings:
        listings_summary = f"\nנכסים מפורסמים כרגע ביד2: {len(report.current_listings)}\n"
        for l in report.current_listings[:5]:
            listings_summary += (
                f"  - {l.address} | {l.formatted_price} | "
                f"{l.rooms or '?'} חד' | {l.size_sqm or '?'} מ\"ר\n"
            )

    # Value estimation
    value_summary = ""
    if report.value_estimation:
        ve = report.value_estimation
        value_summary = f"""
הערכת שווי (אלגוריתמית):
  טווח: {ve.formatted_range}
  מחיר ממוצע למ"ר: {ve.estimated_price_per_sqm:,.0f} ש"ח
  רמת ביטחון: {ve.confidence}
  מבוסס על: {ve.comparable_count} נכסים
"""

    prompt = f"""אתה מומחה נדל"ן בישראל. כתוב ניתוח שוק מקצועי בעברית עבור הנכס הבא:

נכס: {report.subject_address}
סוג: {report.subject_property_type}
עיר: {report.subject_city}
שכונה: {report.subject_neighborhood}
רחוב: {report.subject_street}

=== נתוני שוק ===
{tx_summary}
{floor_summary}
{age_summary}
{trend_summary}
{listings_summary}
{value_summary}

=== הנחיות לכתיבה ===

כתוב דו"ח ניתוח שוק מקצועי הכולל:

1. **סקירת שוק כללית** - מגמות המחירים באזור, האם השוק עולה/יורד/יציב
2. **השוואה לנכסים דומים** - הבדלים בולטים בין הנכסים, מה משפיע על מחיר
3. **ישן מול חדש** - הפרשי מחירים בין בניינים ישנים לחדשים, האם יש פרמיית חדש
4. **השפעת קומה** - האם ובכמה הקומה משפיעה על המחיר באזור
5. **חוזקות וחולשות** - יתרונות וחסרונות של הנכס/האזור
6. **המלצת תמחור** - טווח מחיר מומלץ עם הסבר

כללי כתיבה:
- כתוב בעברית מקצועית וברורה
- הימנע מהכללות ריקות, התבסס על הנתונים
- ציין מספרים ספציפיים כשרלוונטי
- אורך: 300-500 מילים
- אל תמציא נתונים שלא ניתנו לך
- אם אין מספיק נתונים לסעיף מסוים, ציין זאת
"""
    return prompt


async def generate_ai_summary(report: MarketAnalysisReport) -> str:
    """
    Generate an AI-powered market analysis summary using Claude API.

    Returns Hebrew text summary with market insights.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set - skipping AI summary")
        return "סיכום AI לא זמין - יש להגדיר ANTHROPIC_API_KEY בקובץ .env"

    prompt = _build_prompt(report)

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        summary = message.content[0].text
        logger.info(f"AI summary generated: {len(summary)} chars")
        return summary

    except ImportError:
        logger.error("anthropic package not installed. Run: pip install anthropic")
        return "סיכום AI לא זמין - יש להתקין את חבילת anthropic"
    except Exception as e:
        logger.error(f"Error generating AI summary: {e}")
        return f"שגיאה ביצירת סיכום AI: {str(e)}"
