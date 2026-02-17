"""PDF report generator for market analysis."""

from __future__ import annotations

import logging
import os
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

from src.market.models import MarketAnalysisReport

logger = logging.getLogger("realestate")

# Hebrew month names
HEBREW_MONTHS = {
    1: "ינואר", 2: "פברואר", 3: "מרץ", 4: "אפריל",
    5: "מאי", 6: "יוני", 7: "יולי", 8: "אוגוסט",
    9: "ספטמבר", 10: "אוקטובר", 11: "נובמבר", 12: "דצמבר",
}


def _format_hebrew_date(dt: datetime) -> str:
    """Format date in Hebrew."""
    return f"{dt.day} ב{HEBREW_MONTHS[dt.month]} {dt.year}"


def generate_pdf(report: MarketAnalysisReport) -> BytesIO:
    """
    Generate a PDF report from market analysis data.

    Uses fpdf2 with Hebrew font support.
    Returns BytesIO buffer containing the PDF.
    """
    from fpdf import FPDF

    class HebrewPDF(FPDF):
        """Custom PDF class with Hebrew support."""

        def __init__(self):
            super().__init__()
            # Try to load a Hebrew-supporting font
            font_path = _find_hebrew_font()
            if font_path:
                self.add_font("Hebrew", "", font_path, uni=True)
                self.add_font("Hebrew", "B", font_path, uni=True)
                self._hebrew_font = "Hebrew"
            else:
                self._hebrew_font = "Helvetica"
                logger.warning("No Hebrew font found, PDF may not display Hebrew correctly")

        def header(self):
            self.set_font(self._hebrew_font, "B", 10)
            self.set_text_color(128, 128, 128)
            self.cell(0, 8, "Real Capital | Roy Ido", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)

        def footer(self):
            self.set_y(-15)
            self.set_font(self._hebrew_font, "", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"{self.page_no()}/{{nb}}", align="C")

        def rtl_cell(self, w, h, txt, **kwargs):
            """Write RTL text (reverse for PDF rendering)."""
            reversed_text = _reshape_hebrew(txt)
            self.cell(w, h, reversed_text, **kwargs)

        def section_title(self, title: str):
            self.ln(3)
            self.set_font(self._hebrew_font, "B", 14)
            self.set_text_color(44, 62, 80)
            self.cell(0, 10, _reshape_hebrew(title), align="R", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(52, 152, 219)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(3)

        def body_text(self, text: str):
            self.set_font(self._hebrew_font, "", 10)
            self.set_text_color(0, 0, 0)
            for line in text.split("\n"):
                if line.strip():
                    self.cell(0, 6, _reshape_hebrew(line.strip()), align="R", new_x="LMARGIN", new_y="NEXT")
                else:
                    self.ln(3)

    pdf = HebrewPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Title Page ---
    pdf.set_font(pdf._hebrew_font, "B", 24)
    pdf.set_text_color(44, 62, 80)
    pdf.ln(30)
    pdf.cell(0, 15, _reshape_hebrew("דו\"ח ניתוח שוק השוואתי"), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(pdf._hebrew_font, "", 16)
    pdf.set_text_color(52, 152, 219)
    pdf.ln(10)
    pdf.cell(0, 12, _reshape_hebrew(report.subject_address), align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(pdf._hebrew_font, "", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.ln(5)
    pdf.cell(
        0, 10,
        _reshape_hebrew(f"סוג נכס: {report.subject_property_type}"),
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.cell(
        0, 10,
        _reshape_hebrew(f"תאריך הפקה: {_format_hebrew_date(report.report_date)}"),
        align="C", new_x="LMARGIN", new_y="NEXT",
    )

    pdf.ln(20)
    pdf.set_font(pdf._hebrew_font, "", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(
        0, 8,
        _reshape_hebrew(f"מקורות נתונים: {', '.join(report.data_sources_used)}"),
        align="C", new_x="LMARGIN", new_y="NEXT",
    )
    pdf.cell(
        0, 8,
        _reshape_hebrew(f"סה\"כ עסקאות: {report.total_transactions} | נכסים מפורסמים: {report.total_listings}"),
        align="C", new_x="LMARGIN", new_y="NEXT",
    )

    # --- Page 2: Transaction Data ---
    pdf.add_page()
    pdf.section_title("עסקאות דומות שנמצאו")

    if report.transactions:
        # Table header
        pdf.set_font(pdf._hebrew_font, "B", 9)
        pdf.set_fill_color(52, 152, 219)
        pdf.set_text_color(255, 255, 255)

        col_widths = [55, 30, 20, 15, 20, 25, 25]
        headers = ["כתובת", "מחיר", "חדרים", "קומה", "מ\"ר", "שנת בנייה", "תאריך"]

        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 8, _reshape_hebrew(header), border=1, fill=True, align="C")
        pdf.ln()

        # Table rows
        pdf.set_font(pdf._hebrew_font, "", 8)
        pdf.set_text_color(0, 0, 0)

        for j, tx in enumerate(report.transactions[:30]):  # Max 30 rows
            if j % 2 == 0:
                pdf.set_fill_color(240, 248, 255)
            else:
                pdf.set_fill_color(255, 255, 255)

            addr = tx.address[:25] + "..." if len(tx.address) > 25 else tx.address
            row = [
                _reshape_hebrew(addr),
                f"{int(tx.deal_amount):,}",
                str(tx.rooms or "-"),
                str(tx.floor if tx.floor is not None else "-"),
                str(int(tx.size_sqm)) if tx.size_sqm else "-",
                str(tx.building_year or "-"),
                tx.formatted_date or "-",
            ]

            for i, cell_text in enumerate(row):
                pdf.cell(col_widths[i], 7, cell_text, border=1, fill=True, align="C")
            pdf.ln()
    else:
        pdf.body_text("לא נמצאו עסקאות.")

    # --- Floor Analysis ---
    if report.floor_analysis:
        pdf.add_page()
        pdf.section_title("ניתוח מחיר לפי קומה")

        pdf.set_font(pdf._hebrew_font, "B", 9)
        pdf.set_fill_color(46, 204, 113)
        pdf.set_text_color(255, 255, 255)

        floor_cols = [30, 45, 45, 40]
        floor_headers = ["קומה", "ממוצע למ\"ר", "ממוצע סה\"כ", "עסקאות"]

        for i, header in enumerate(floor_headers):
            pdf.cell(floor_cols[i], 8, _reshape_hebrew(header), border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(pdf._hebrew_font, "", 9)
        pdf.set_text_color(0, 0, 0)

        for fa in report.floor_analysis:
            pdf.set_fill_color(245, 255, 245)
            row = [
                str(fa.floor),
                f"{int(fa.avg_price_per_sqm):,}",
                f"{int(fa.avg_total_price):,}",
                str(fa.transaction_count),
            ]
            for i, cell_text in enumerate(row):
                pdf.cell(floor_cols[i], 7, cell_text, border=1, fill=True, align="C")
            pdf.ln()

    # --- Building Age Analysis ---
    if report.building_age_analysis:
        pdf.ln(10)
        pdf.section_title("השוואת ישן מול חדש")

        pdf.set_font(pdf._hebrew_font, "B", 9)
        pdf.set_fill_color(155, 89, 182)
        pdf.set_text_color(255, 255, 255)

        age_cols = [50, 40, 35, 40]
        age_headers = ["קטגוריה", "ממוצע למ\"ר", "פרמיה/הנחה", "עסקאות"]

        for i, header in enumerate(age_headers):
            pdf.cell(age_cols[i], 8, _reshape_hebrew(header), border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(pdf._hebrew_font, "", 9)
        pdf.set_text_color(0, 0, 0)

        for ba in report.building_age_analysis:
            pdf.set_fill_color(245, 240, 255)
            premium = f"{ba.price_premium_pct:+.1f}%" if ba.price_premium_pct is not None else "-"
            row = [
                _reshape_hebrew(ba.category),
                f"{int(ba.avg_price_per_sqm):,}",
                premium,
                str(ba.transaction_count),
            ]
            for i, cell_text in enumerate(row):
                pdf.cell(age_cols[i], 7, cell_text, border=1, fill=True, align="C")
            pdf.ln()

    # --- Price Trends ---
    if report.price_trends:
        pdf.add_page()
        pdf.section_title("מגמות מחיר")

        pdf.set_font(pdf._hebrew_font, "B", 9)
        pdf.set_fill_color(230, 126, 34)
        pdf.set_text_color(255, 255, 255)

        trend_cols = [40, 45, 40, 40]
        trend_headers = ["תקופה", "ממוצע למ\"ר", "שינוי", "עסקאות"]

        for i, header in enumerate(trend_headers):
            pdf.cell(trend_cols[i], 8, _reshape_hebrew(header), border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(pdf._hebrew_font, "", 9)
        pdf.set_text_color(0, 0, 0)

        for pt in report.price_trends[-12:]:
            pdf.set_fill_color(255, 248, 240)
            change = f"{pt.change_pct:+.1f}%" if pt.change_pct is not None else "-"
            row = [
                pt.period,
                f"{int(pt.avg_price_per_sqm):,}",
                change,
                str(pt.transaction_count),
            ]
            for i, cell_text in enumerate(row):
                pdf.cell(trend_cols[i], 7, cell_text, border=1, fill=True, align="C")
            pdf.ln()

    # --- Value Estimation ---
    if report.value_estimation:
        pdf.add_page()
        pdf.section_title("הערכת שווי")

        ve = report.value_estimation
        pdf.set_font(pdf._hebrew_font, "B", 14)
        pdf.set_text_color(44, 62, 80)
        pdf.ln(5)
        pdf.cell(
            0, 12,
            _reshape_hebrew(f"טווח מחיר מוערך: {ve.formatted_range}"),
            align="C", new_x="LMARGIN", new_y="NEXT",
        )

        pdf.set_font(pdf._hebrew_font, "", 11)
        pdf.ln(5)
        pdf.cell(
            0, 8,
            _reshape_hebrew(f"מחיר ממוצע למ\"ר: {ve.estimated_price_per_sqm:,.0f} ש\"ח"),
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        pdf.cell(
            0, 8,
            _reshape_hebrew(f"רמת ביטחון: {ve.confidence} | מבוסס על {ve.comparable_count} נכסים"),
            align="C", new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(5)
        pdf.body_text(ve.methodology)

    # --- AI Summary ---
    if report.ai_summary and report.ai_summary != "":
        pdf.add_page()
        pdf.section_title("ניתוח AI - סיכום מקצועי")
        pdf.body_text(report.ai_summary)

    # --- Current Listings ---
    if report.current_listings:
        pdf.add_page()
        pdf.section_title("נכסים מפורסמים כרגע (יד2)")

        pdf.set_font(pdf._hebrew_font, "B", 9)
        pdf.set_fill_color(41, 128, 185)
        pdf.set_text_color(255, 255, 255)

        list_cols = [55, 30, 20, 15, 20, 25]
        list_headers = ["כתובת", "מחיר", "חדרים", "קומה", "מ\"ר", "סוג"]

        for i, header in enumerate(list_headers):
            pdf.cell(list_cols[i], 8, _reshape_hebrew(header), border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(pdf._hebrew_font, "", 8)
        pdf.set_text_color(0, 0, 0)

        for listing in report.current_listings[:20]:
            pdf.set_fill_color(235, 245, 255)
            addr = listing.address[:25] + "..." if len(listing.address) > 25 else listing.address
            row = [
                _reshape_hebrew(addr),
                f"{int(listing.price):,}",
                str(listing.rooms or "-"),
                str(listing.floor if listing.floor is not None else "-"),
                str(int(listing.size_sqm)) if listing.size_sqm else "-",
                _reshape_hebrew(listing.property_type[:10] if listing.property_type else "-"),
            ]
            for i, cell_text in enumerate(row):
                pdf.cell(list_cols[i], 7, cell_text, border=1, fill=True, align="C")
            pdf.ln()

    # Generate PDF bytes
    buffer = BytesIO()
    pdf_bytes = pdf.output()
    buffer.write(pdf_bytes)
    buffer.seek(0)

    logger.info(f"PDF report generated: {len(pdf_bytes)} bytes")
    return buffer


def _find_hebrew_font() -> Optional[str]:
    """Find a Hebrew-supporting font on the system."""
    possible_paths = [
        # macOS
        "/System/Library/Fonts/Supplemental/Arial Hebrew.ttf",
        "/System/Library/Fonts/Supplemental/ArialHB.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/SFHebrew.ttf",
        "/System/Library/Fonts/Supplemental/Tahoma.ttf",
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        # Project local
        str(Path(__file__).parent.parent.parent / "data" / "fonts" / "NotoSansHebrew.ttf"),
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def _reshape_hebrew(text: str) -> str:
    """
    Basic Hebrew text reshaping for PDF.
    Reverses Hebrew character sequences for RTL display in LTR PDF.
    """
    try:
        from arabic_reshaper import reshape
        from bidi.algorithm import get_display
        reshaped = reshape(text)
        return get_display(reshaped)
    except ImportError:
        # Fallback: simple reversal for Hebrew-only text
        # This is imperfect but works for basic cases
        return text
