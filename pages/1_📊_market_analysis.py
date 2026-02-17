"""דף ניתוח שוק נדל"ן השוואתי - גרסה משודרגת."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.market.orchestrator import run_market_analysis
from src.market.pdf_report import generate_pdf
from src.market.places_autocomplete import address_input_with_autocomplete

st.set_page_config(
    page_title="ניתוח שוק | Real Capital",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Heebo', sans-serif;
    direction: rtl;
    background: #F5F7FA;
}
#MainMenu, footer { visibility: hidden; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0B1F3B !important;
    border-left: none;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.9) !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"],
[data-testid="stSidebar"] .stNumberInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: white !important;
    border-radius: 8px;
    direction: rtl;
}
[data-testid="stSidebar"] .stButton > button {
    background: #1C3F94 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem !important;
    width: 100%;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #4A90D9 !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }

/* Metrics */
div[data-testid="stMetric"] { direction: rtl; }
div[data-testid="stMetricValue"] { color: #0B1F3B; font-weight: 700; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    direction: rtl;
    gap: 0.25rem;
    background: white;
    border-radius: 12px;
    padding: 0.4rem;
    border: 1px solid #E8ECF0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.85rem;
    padding: 0.5rem 1rem;
}
.stTabs [aria-selected="true"] {
    background: #0B1F3B !important;
    color: white !important;
}

/* Report header */
.report-header {
    background: linear-gradient(135deg, #0B1F3B, #1C3F94);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    color: white;
    margin-bottom: 1.5rem;
    direction: rtl;
}
.report-header h2 { color: white; font-size: 1.4rem; font-weight: 800; margin-bottom: 0.25rem; }
.report-header p { color: rgba(255,255,255,0.6); font-size: 0.85rem; }

/* KPI Cards */
.kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
.kpi-card {
    flex: 1;
    background: white;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    border: 1px solid #E8ECF0;
    box-shadow: 0 2px 12px rgba(11,31,59,0.06);
    direction: rtl;
}
.kpi-label { color: #6B7A8D; font-size: 0.78rem; font-weight: 500; margin-bottom: 0.25rem; }
.kpi-value { color: #0B1F3B; font-size: 1.6rem; font-weight: 800; }
.kpi-sub { color: #4A90D9; font-size: 0.75rem; margin-top: 0.1rem; }

/* Sidebar logo */
.sidebar-logo {
    color: white;
    font-size: 1.1rem;
    font-weight: 800;
    padding: 0.5rem 0 1.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 1.5rem;
    direction: rtl;
}
.sidebar-logo span { color: #4A90D9; }
.sidebar-section { color: rgba(255,255,255,0.5) !important; font-size: 0.7rem; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; margin: 1.2rem 0 0.5rem; }

/* Download button */
.stDownloadButton > button {
    background: #0B1F3B !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Dataframe RTL */
.dataframe { direction: rtl; }

/* ── תיקון צבע טקסט: טקסט כהה על רקע בהיר בכל שדות הקלט ─────────────────
   בעיה: ה-wildcard של הסיידבר הדליק color:white גם על אלמנטים ראשיים.
   פתרון: הגדרת overrides מפורשים לכל שדות הקלט מחוץ לסיידבר.
──────────────────────────────────────────────────────────────────────── */

/* Main content – inputs, selects, textareas */
[data-testid="stAppViewContainer"] .stTextInput input,
[data-testid="stAppViewContainer"] .stNumberInput input,
[data-testid="stAppViewContainer"] .stTextArea textarea,
[data-testid="stAppViewContainer"] .stSelectbox div[data-baseweb="select"] > div,
[data-testid="stAppViewContainer"] .stMultiSelect div[data-baseweb="select"] > div {
    color: #0B1F3B !important;
    background-color: #FFFFFF !important;
    border: 1px solid #D1D9E0 !important;
    border-radius: 8px !important;
}

/* Placeholder text */
[data-testid="stAppViewContainer"] .stTextInput input::placeholder,
[data-testid="stAppViewContainer"] .stNumberInput input::placeholder,
[data-testid="stAppViewContainer"] .stTextArea textarea::placeholder {
    color: #9AABBF !important;
    opacity: 1 !important;
}

/* Focus ring */
[data-testid="stAppViewContainer"] .stTextInput input:focus,
[data-testid="stAppViewContainer"] .stNumberInput input:focus,
[data-testid="stAppViewContainer"] .stTextArea textarea:focus {
    border-color: #1C3F94 !important;
    box-shadow: 0 0 0 3px rgba(28,63,148,0.15) !important;
    outline: none !important;
}

/* Select dropdown options */
[data-baseweb="popover"] li,
[data-baseweb="menu"] li,
[data-baseweb="select"] [role="option"] {
    color: #0B1F3B !important;
    background: #FFFFFF !important;
    direction: rtl;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {
    background: #EEF2F8 !important;
}

/* Sidebar inputs stay white text on dark bg */
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
    color: #FFFFFF !important;
    background-color: rgba(255,255,255,0.1) !important;
    border-color: rgba(255,255,255,0.2) !important;
}
[data-testid="stSidebar"] .stTextInput input::placeholder,
[data-testid="stSidebar"] .stNumberInput input::placeholder {
    color: rgba(255,255,255,0.45) !important;
}

/* Labels outside sidebar – dark text */
[data-testid="stAppViewContainer"] .stTextInput label,
[data-testid="stAppViewContainer"] .stNumberInput label,
[data-testid="stAppViewContainer"] .stSelectbox label,
[data-testid="stAppViewContainer"] .stTextArea label,
[data-testid="stAppViewContainer"] .stRadio label,
[data-testid="stAppViewContainer"] .stCheckbox label,
[data-testid="stAppViewContainer"] .stSlider label {
    color: #0B1F3B !important;
    font-weight: 500;
}

/* Error / validation state */
[data-testid="stAppViewContainer"] .stTextInput [data-baseweb="input"][aria-invalid="true"],
[data-testid="stAppViewContainer"] .stTextInput input:invalid {
    border-color: #D32F2F !important;
    background-color: #FFF5F5 !important;
    color: #0B1F3B !important;
}

/* Disabled state */
[data-testid="stAppViewContainer"] .stTextInput input:disabled,
[data-testid="stAppViewContainer"] .stNumberInput input:disabled {
    background-color: #F5F7FA !important;
    color: #9AABBF !important;
    border-color: #E8ECF0 !important;
}

/* Upload widget + info boxes */
[data-testid="stFileUploader"],
[data-testid="stInfo"],
[data-testid="stSuccess"],
[data-testid="stWarning"],
[data-testid="stError"] {
    direction: rtl;
    color: #0B1F3B !important;
}

/* Metric labels in main area */
[data-testid="stAppViewContainer"] [data-testid="stMetricLabel"] p,
[data-testid="stAppViewContainer"] [data-testid="stMetricDelta"] {
    color: #6B7A8D !important;
}
</style>
""", unsafe_allow_html=True)

# ─── קבועים ─────────────────────────────────────────────────────────────────
PROPERTY_TYPES = [
    "דירה", "דירת גן", "פנטהאוז", "דופלקס",
    "בית פרטי", "קוטג׳", "דו-משפחתי", "טריפלקס", "מגרש",
]

ROOMS_OPTIONS = ["לא צוין", "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5", "5.5", "6", "7+"]
FLOOR_OPTIONS = ["לא צוין", "קרקע", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                 "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
                 "21-25", "26-30", "פנטהאוז"]
CONDITION_OPTIONS = ["לא צוין", "חדש מקבלן", "משופץ", "מצב טוב", "דורש שיפוץ"]

PRICE_RANGES = {
    "לא צוין": 0,
    "עד 1,000,000 ₪": 1_000_000,
    "1-1.5M ₪": 1_500_000,
    "1.5-2M ₪": 2_000_000,
    "2-3M ₪": 3_000_000,
    "3-5M ₪": 5_000_000,
    "5-8M ₪": 8_000_000,
    "מעל 8M ₪": 12_000_000,
}


def _floor_to_int(floor_str: str):
    """המרת בחירת קומה למספר."""
    if floor_str in ("לא צוין", ""):
        return None
    if floor_str == "קרקע":
        return 0
    if floor_str == "פנטהאוז":
        return 30
    if "-" in floor_str:
        return int(floor_str.split("-")[0])
    try:
        return int(floor_str)
    except ValueError:
        return None


def _rooms_to_float(rooms_str: str):
    """המרת בחירת חדרים למספר."""
    if rooms_str in ("לא צוין", ""):
        return None
    if rooms_str == "7+":
        return 7.0
    try:
        return float(rooms_str)
    except ValueError:
        return None


def main():
    # ─── Sidebar ───────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem 0 1rem 0;">
            <div style="width:42px;height:42px;background:#1C3F94;border-radius:8px;border:1.5px solid #C9A84C;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-size:1.3rem;font-weight:700;color:#fff;flex-shrink:0;">R</div>
            <div>
                <div style="color:#fff;font-size:1rem;font-weight:800;line-height:1.1;">Real Capital</div>
                <div style="color:#C9A84C;font-size:0.65rem;letter-spacing:2px;text-transform:uppercase;margin-top:2px;">ניתוח שוק</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sidebar-section">📍 כתובת הנכס</div>', unsafe_allow_html=True)

        # ── Google Places Autocomplete ──────────────────────────────────────
        place_result = address_input_with_autocomplete(key_prefix="cma_addr")

        # שדה fallback גלוי רק כשאין מפתח API (הwidget מציג fallback פנימי)
        if place_result:
            address = place_result.get("formatted_address", "")
            # שמור קואורדינטות ב-session_state לשימוש עתידי (מפה, סינון רדיוס)
            st.session_state["subject_lat"] = place_result.get("lat")
            st.session_state["subject_lng"] = place_result.get("lng")
            st.session_state["subject_city"] = place_result.get("city", "")
        else:
            address = ""

        st.markdown('<div class="sidebar-section">🏠 פרטי הנכס</div>', unsafe_allow_html=True)
        property_type = st.selectbox("סוג נכס", options=PROPERTY_TYPES, index=0)

        col1, col2 = st.columns(2)
        with col1:
            rooms_sel = st.selectbox("חדרים", options=ROOMS_OPTIONS, index=0)
        with col2:
            floor_sel = st.selectbox("קומה", options=FLOOR_OPTIONS, index=0)

        size_sqm = st.number_input(
            "שטח (מ\"ר)",
            min_value=0, max_value=2000, step=5, value=0,
            help="השטח הכולל של הנכס",
        )

        condition = st.selectbox("מצב הנכס", options=CONDITION_OPTIONS, index=0)

        st.markdown('<div class="sidebar-section">💰 מחיר</div>', unsafe_allow_html=True)
        price_range_sel = st.selectbox("טווח מחיר מוערך", options=list(PRICE_RANGES.keys()), index=0)

        st.markdown('<div class="sidebar-section">🏗️ בניין</div>', unsafe_allow_html=True)
        building_year = st.number_input(
            "שנת בנייה",
            min_value=1900, max_value=2025, step=1, value=2000,
        )

        st.markdown("---")
        include_ai = st.toggle("🤖 סיכום AI", value=True, help="יצירת סיכום ניתוח חכם בעברית")

        st.markdown("---")
        analyze_btn = st.button(
            "🔍 הפק דו\"ח ניתוח",
            type="primary",
            use_container_width=True,
            disabled=not bool(address),
        )

        if not address:
            st.caption("💡 הכנס כתובת כדי להתחיל")

    # ─── Main Content ──────────────────────────────────────────────────────
    if not address:
        _show_welcome()
        return

    rooms = _rooms_to_float(rooms_sel)
    floor = _floor_to_int(floor_sel)
    price = PRICE_RANGES.get(price_range_sel, 0) or None
    size = size_sqm if size_sqm > 0 else None
    year = building_year if building_year > 1900 else None

    if analyze_btn:
        _run_analysis(
            address=address,
            property_type=property_type,
            rooms=rooms,
            floor=floor,
            size_sqm=size,
            building_year=year,
            price=price,
            include_ai=include_ai,
        )
    elif "report" in st.session_state:
        _display_report(st.session_state["report"])


def _show_welcome():
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem; direction:rtl;">
        <div style="font-size:4rem; margin-bottom:1rem;">📊</div>
        <h2 style="color:#0B1F3B; font-size:2rem; font-weight:800; margin-bottom:0.75rem;">
            ניתוח שוק נדל"ן השוואתי
        </h2>
        <p style="color:#6B7A8D; font-size:1.05rem; max-width:500px; margin:0 auto 2rem; line-height:1.8;">
            הכנס כתובת נכס בסרגל הצד הימני וקבל דו"ח ניתוח שוק מקיף עם עסקאות אמיתיות, גרפים, ומגמות.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("📈", "עסקאות אמיתיות", "נדל\"ן.gov.il"),
        ("🏘️", "נכסים מפורסמים", "יד2"),
        ("📊", "ניתוח מעמיק", "קומה, גיל בניין, מגמות"),
        ("🤖", "סיכום AI", "Claude בעברית"),
    ]
    for col, (icon, title, sub) in zip([c1, c2, c3, c4], cards):
        with col:
            st.markdown(f"""
            <div style="background:white;border-radius:12px;padding:1.5rem;text-align:center;
                        border:1px solid #E8ECF0;direction:rtl;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">{icon}</div>
                <div style="font-weight:700;color:#0B1F3B;font-size:0.95rem;">{title}</div>
                <div style="color:#6B7A8D;font-size:0.8rem;margin-top:0.25rem;">{sub}</div>
            </div>
            """, unsafe_allow_html=True)


def _run_analysis(address, property_type, rooms, floor, size_sqm, building_year, price, include_ai):
    progress_bar = st.progress(0, text="מתחיל ניתוח שוק...")
    status_text = st.empty()

    def progress_callback(message, pct):
        progress_bar.progress(min(pct, 1.0), text=message)
        status_text.info(f"⏳ {message}")

    try:
        import nest_asyncio
        nest_asyncio.apply()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        report = loop.run_until_complete(
            run_market_analysis(
                address=address,
                property_type=property_type,
                rooms=rooms,
                floor=floor,
                size_sqm=size_sqm,
                building_year=building_year,
                price=price,
                include_ai=include_ai,
                progress_callback=progress_callback,
            )
        )

        progress_bar.progress(1.0, text="הדו\"ח מוכן!")
        status_text.empty()
        st.session_state["report"] = report

        if report.errors:
            with st.expander("⚠️ הערות", expanded=False):
                for err in report.errors:
                    st.warning(err)

        if report.total_transactions == 0 and report.total_listings == 0:
            st.error("""
**לא נמצאו נתונים לכתובת זו.**

💡 **טיפים:**
- ודא שהכתובת נכונה עם שם העיר (לדוגמה: **הרצל 15 תל אביב**)
- נסה לציין רק את שם הרחוב והעיר ללא מספר בית
- נסה שוב בעוד כמה שניות
""")
            return

        _display_report(report)

    except Exception as e:
        st.error(f"שגיאה: {e}")
        progress_bar.empty()
        status_text.empty()


def _display_report(report):
    # Header
    st.markdown(f"""
    <div class="report-header">
        <h2>📊 דו"ח ניתוח שוק — {report.subject_address}</h2>
        <p>סוג נכס: {report.subject_property_type} | עיר: {report.subject_city} | מקורות: {", ".join(report.data_sources_used)}</p>
    </div>
    """, unsafe_allow_html=True)

    # KPI Row
    avg_sqm = report.avg_price_per_sqm_street
    val_str = report.value_estimation.formatted_range if report.value_estimation else "—"

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("עסקאות שנמצאו", report.total_transactions)
    with col2:
        st.metric("נכסים מפורסמים", report.total_listings)
    with col3:
        st.metric("ממוצע למ\"ר", f"{avg_sqm:,.0f} ₪" if avg_sqm else "—")
    with col4:
        st.metric("הערכת שווי", val_str)

    # PDF Download
    col_pdf, _ = st.columns([1, 3])
    with col_pdf:
        try:
            pdf_buffer = generate_pdf(report)
            safe_addr = report.subject_address.replace(" ", "_").replace(",", "")
            st.download_button(
                label="📄 הורד דו\"ח PDF",
                data=pdf_buffer,
                file_name=f"ניתוח_שוק_{safe_addr}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            pass

    st.markdown("---")

    # Tabs
    tabs = st.tabs([
        "📋 עסקאות", "🏢 קומה vs מחיר", "🏗️ ישן vs חדש",
        "📈 מגמות", "🏘️ מפורסמים", "💰 הערכת שווי", "🤖 סיכום AI",
    ])

    with tabs[0]: _render_transactions_tab(report)
    with tabs[1]: _render_floor_tab(report)
    with tabs[2]: _render_age_tab(report)
    with tabs[3]: _render_trends_tab(report)
    with tabs[4]: _render_listings_tab(report)
    with tabs[5]: _render_value_tab(report)
    with tabs[6]: _render_ai_tab(report)


def _render_transactions_tab(report):
    if not report.transactions:
        st.info("לא נמצאו עסקאות ברחוב זה")
        return

    prices = [tx.deal_amount for tx in report.transactions if tx.deal_amount > 0]
    sqm_prices = [tx.price_per_sqm for tx in report.transactions if tx.price_per_sqm]

    c1, c2, c3 = st.columns(3)
    with c1:
        if prices:
            st.metric("מחיר ממוצע", f"{int(sum(prices)/len(prices)):,} ₪")
    with c2:
        if sqm_prices:
            st.metric("ממוצע למ\"ר", f"{int(sum(sqm_prices)/len(sqm_prices)):,} ₪")
    with c3:
        if prices:
            st.metric("טווח מחירים", f"{int(min(prices)):,} – {int(max(prices)):,} ₪")

    data = [{
        "כתובת": tx.address,
        "מחיר (₪)": f"{int(tx.deal_amount):,}",
        "חדרים": tx.rooms or "—",
        "קומה": tx.floor if tx.floor is not None else "—",
        "מ\"ר": int(tx.size_sqm) if tx.size_sqm else "—",
        "מחיר/מ\"ר": f"{int(tx.price_per_sqm):,}" if tx.price_per_sqm else "—",
        "שנת בנייה": tx.building_year or "—",
        "תאריך": tx.formatted_date,
    } for tx in report.transactions]

    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    if sqm_prices and len(sqm_prices) >= 3:
        fig = px.histogram(
            x=sqm_prices, nbins=15,
            labels={"x": "מחיר למ\"ר (₪)", "y": "מספר עסקאות"},
            title="התפלגות מחיר למ\"ר",
            color_discrete_sequence=["#1C3F94"],
        )
        fig.update_layout(font_family="Arial", xaxis_title="מחיר למ\"ר (₪)", yaxis_title="מספר עסקאות")
        st.plotly_chart(fig, use_container_width=True)


def _render_floor_tab(report):
    if not report.floor_analysis:
        st.info("אין מספיק נתונים לניתוח לפי קומה (נדרשות לפחות 3 עסקאות עם נתוני קומה)")
        return

    floors = [f"קומה {fa.floor}" for fa in report.floor_analysis]
    avg_prices = [fa.avg_price_per_sqm for fa in report.floor_analysis]

    fig = go.Figure(go.Bar(
        x=floors, y=avg_prices,
        text=[f"{p:,.0f} ₪" for p in avg_prices], textposition="auto",
        marker_color="#0B1F3B",
        hovertemplate="<b>%{x}</b><br>ממוצע: %{y:,.0f} ₪/מ\"ר<extra></extra>",
    ))
    fig.update_layout(
        title="ממוצע מחיר למ\"ר לפי קומה",
        xaxis_title="קומה", yaxis_title="מחיר ממוצע למ\"ר (₪)",
        font_family="Arial", plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

    floor_data = [{
        "קומה": fa.floor,
        "ממוצע למ\"ר (₪)": f"{int(fa.avg_price_per_sqm):,}",
        "ממוצע סה\"כ": fa.formatted_avg_price,
        "מספר עסקאות": fa.transaction_count,
    } for fa in report.floor_analysis]
    st.dataframe(pd.DataFrame(floor_data), use_container_width=True, hide_index=True)


def _render_age_tab(report):
    if not report.building_age_analysis:
        st.info("אין מספיק נתונים לניתוח לפי גיל בניין")
        return

    categories = [ba.category for ba in report.building_age_analysis]
    avg_prices = [ba.avg_price_per_sqm for ba in report.building_age_analysis]
    premiums = [ba.price_premium_pct for ba in report.building_age_analysis]
    colors = ["#2ecc71" if (p or 0) > 0 else "#e74c3c" if p is not None else "#95a5a6" for p in premiums]

    fig = go.Figure(go.Bar(
        x=categories, y=avg_prices,
        text=[f"{p:,.0f} ₪\n({pr:+.1f}%)" if pr is not None else f"{p:,.0f} ₪"
              for p, pr in zip(avg_prices, premiums)],
        textposition="auto", marker_color=colors,
    ))
    fig.update_layout(
        title="ממוצע מחיר למ\"ר לפי גיל בניין",
        xaxis_title="קטגוריית גיל", yaxis_title="מחיר ממוצע למ\"ר (₪)",
        font_family="Arial", plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

    cols = st.columns(len(report.building_age_analysis))
    for i, ba in enumerate(report.building_age_analysis):
        with cols[i]:
            pr = f"{'📈' if ba.price_premium_pct and ba.price_premium_pct > 0 else '📉'} {ba.price_premium_pct:+.1f}%" if ba.price_premium_pct is not None else ""
            st.metric(ba.category, f"{int(ba.avg_price_per_sqm):,} ₪/מ\"ר", pr)
            st.caption(f"{ba.transaction_count} עסקאות")


def _render_trends_tab(report):
    if not report.price_trends:
        st.info("אין מספיק נתונים למגמות מחיר")
        return

    periods = [pt.period for pt in report.price_trends]
    prices = [pt.avg_price_per_sqm for pt in report.price_trends]

    fig = go.Figure(go.Scatter(
        x=periods, y=prices, mode="lines+markers",
        line=dict(color="#1C3F94", width=3), marker=dict(size=8, color="#0B1F3B"),
        hovertemplate="<b>%{x}</b><br>ממוצע: %{y:,.0f} ₪/מ\"ר<extra></extra>",
        fill="tozeroy", fillcolor="rgba(28,63,148,0.05)",
    ))
    fig.update_layout(
        title="מגמת מחיר למ\"ר לאורך זמן",
        xaxis_title="תקופה", yaxis_title="מחיר ממוצע למ\"ר (₪)",
        font_family="Arial", plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

    if len(report.price_trends) >= 2:
        first, last = report.price_trends[0], report.price_trends[-1]
        total_change = ((last.avg_price_per_sqm - first.avg_price_per_sqm) / first.avg_price_per_sqm) * 100
        c1, c2, c3 = st.columns(3)
        with c1: st.metric(f"מחיר {first.period}", f"{int(first.avg_price_per_sqm):,} ₪/מ\"ר")
        with c2: st.metric(f"מחיר {last.period}", f"{int(last.avg_price_per_sqm):,} ₪/מ\"ר")
        with c3: st.metric("שינוי מצטבר", f"{total_change:+.1f}%")


def _render_listings_tab(report):
    if not report.current_listings:
        st.info("לא נמצאו נכסים מפורסמים דומים ביד2")
        return

    data = [{
        "כתובת": l.address,
        "מחיר (₪)": f"{int(l.price):,}" if l.price > 0 else "—",
        "חדרים": l.rooms or "—",
        "קומה": l.floor if l.floor is not None else "—",
        "מ\"ר": int(l.size_sqm) if l.size_sqm else "—",
        "מחיר/מ\"ר": f"{int(l.price_per_sqm):,}" if l.price_per_sqm else "—",
        "סוג": l.property_type,
    } for l in report.current_listings]

    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    if report.transactions:
        tx_sqm = [tx.price_per_sqm for tx in report.transactions if tx.price_per_sqm]
        list_sqm = [l.price_per_sqm for l in report.current_listings if l.price_per_sqm]
        if tx_sqm and list_sqm:
            fig = go.Figure()
            fig.add_trace(go.Box(y=tx_sqm, name="עסקאות שנסגרו", marker_color="#0B1F3B"))
            fig.add_trace(go.Box(y=list_sqm, name="מפורסמים (יד2)", marker_color="#4A90D9"))
            fig.update_layout(
                title="השוואת מחיר למ\"ר: עסקאות vs מפורסמים",
                yaxis_title="מחיר למ\"ר (₪)", font_family="Arial", plot_bgcolor="white",
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_value_tab(report):
    if not report.value_estimation:
        st.warning("אין מספיק נתונים להערכת שווי (נדרשות לפחות 3 עסקאות דומות)")
        return

    ve = report.value_estimation
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🔻 מחיר מינימלי", f"{int(ve.estimated_price_low):,} ₪")
    with c2: st.metric("🎯 הערכת שווי", f"{int(ve.estimated_price_mid):,} ₪")
    with c3: st.metric("🔺 מחיר מקסימלי", f"{int(ve.estimated_price_high):,} ₪")

    c1, c2 = st.columns(2)
    with c1: st.metric("מחיר למ\"ר", f"{int(ve.estimated_price_per_sqm):,} ₪")
    with c2:
        emoji = {"גבוה": "🟢", "בינוני": "🟡", "נמוך": "🔴"}.get(ve.confidence, "⚪")
        st.metric("רמת ביטחון", f"{emoji} {ve.confidence}")

    st.caption(f"מבוסס על {ve.comparable_count} נכסים | {ve.methodology}")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=ve.estimated_price_mid,
        number={"suffix": " ₪", "valueformat": ",.0f"},
        gauge={
            "axis": {"range": [ve.estimated_price_low * 0.8, ve.estimated_price_high * 1.2]},
            "bar": {"color": "#1C3F94"},
            "steps": [
                {"range": [ve.estimated_price_low * 0.8, ve.estimated_price_low], "color": "#fadbd8"},
                {"range": [ve.estimated_price_low, ve.estimated_price_high], "color": "#d5f5e3"},
                {"range": [ve.estimated_price_high, ve.estimated_price_high * 1.2], "color": "#fadbd8"},
            ],
        },
        title={"text": "הערכת שווי הנכס (₪)"},
    ))
    fig.update_layout(height=350, font_family="Arial")
    st.plotly_chart(fig, use_container_width=True)


def _render_ai_tab(report):
    if not report.ai_summary:
        st.info("סיכום AI לא נוצר — הפעל את האפשרות 'סיכום AI' בסרגל הצד ונסה שוב.")
        return

    st.markdown(f"""
    <div style="background:white;border-radius:12px;padding:2rem;border:1px solid #E8ECF0;
                direction:rtl;line-height:1.9;color:#2d3748;font-size:0.95rem;">
        {report.ai_summary.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)


main()
