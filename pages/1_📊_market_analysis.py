"""ניתוח שוק נדל"ן השוואתי — Real Capital."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import nest_asyncio
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.market.orchestrator import run_market_analysis
from src.market.pdf_report import generate_pdf

nest_asyncio.apply()

st.set_page_config(
    page_title="ניתוח שוק | Real Capital",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap');

/* ── בסיס ─────────────────────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Heebo', sans-serif !important;
    direction: rtl;
    background: #F0F2F7;
    color: #0B1F3B;
}
#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }

/* ── Sidebar ──────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081629 0%, #0B1F3B 60%, #0D2347 100%) !important;
    border-left: none !important;
    box-shadow: -4px 0 20px rgba(0,0,0,0.3);
}
[data-testid="stSidebar"] > div { padding-top: 0 !important; }

/* כל הטקסט בסיידבר לבן */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown div,
[data-testid="stSidebar"] .stCaption p,
[data-testid="stSidebar"] small {
    color: rgba(255,255,255,0.75) !important;
    font-family: 'Heebo', sans-serif !important;
}

/* שדות קלט בסיידבר */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="input"] input {
    background: rgba(255,255,255,0.1) !important;
    border: 1.5px solid rgba(255,255,255,0.2) !important;
    color: #FFFFFF !important;
    border-radius: 10px !important;
    font-family: 'Heebo', sans-serif !important;
    font-size: 0.95rem !important;
    direction: rtl !important;
    caret-color: #C9A84C !important;
}
[data-testid="stSidebar"] input::placeholder {
    color: rgba(255,255,255,0.38) !important;
    direction: rtl;
}
[data-testid="stSidebar"] input:focus {
    border-color: #C9A84C !important;
    box-shadow: 0 0 0 3px rgba(201,168,76,0.2) !important;
    outline: none !important;
    background: rgba(255,255,255,0.14) !important;
}

/* Selectbox בסיידבר */
[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="select"] [data-testid="stSelectbox"] {
    background: rgba(255,255,255,0.1) !important;
    border: 1.5px solid rgba(255,255,255,0.2) !important;
    border-radius: 10px !important;
    color: white !important;
    direction: rtl !important;
}
[data-testid="stSidebar"] [data-baseweb="select"] span,
[data-testid="stSidebar"] [data-baseweb="select"] div {
    color: white !important;
}

/* כפתורים בסיידבר */
[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #1C3F94, #2756C8) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.8rem 1.5rem !important;
    width: 100% !important;
    letter-spacing: 0.5px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 12px rgba(28,63,148,0.4) !important;
    font-family: 'Heebo', sans-serif !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #2756C8, #4A90D9) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(28,63,148,0.5) !important;
}
[data-testid="stSidebar"] .stButton > button:disabled {
    background: rgba(255,255,255,0.1) !important;
    color: rgba(255,255,255,0.35) !important;
    transform: none !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.08) !important;
    margin: 1rem 0 !important;
}
[data-testid="stSidebar"] .stNumberInput button {
    background: rgba(255,255,255,0.1) !important;
    color: white !important;
    border: none !important;
}

/* ── שדות קלט באזור הראשי ────────────────────────────────── */
/* כלל ברזל: כל input מחוץ לסיידבר — טקסט כהה על רקע לבן */
[data-testid="stAppViewContainer"]:not([data-testid="stSidebar"]) input,
.main input,
[data-testid="stMain"] input {
    color: #0B1F3B !important;
    background: #FFFFFF !important;
    border: 1.5px solid #D1D9E0 !important;
    border-radius: 10px !important;
    direction: rtl !important;
    font-family: 'Heebo', sans-serif !important;
}
[data-testid="stAppViewContainer"]:not([data-testid="stSidebar"]) input::placeholder,
.main input::placeholder {
    color: #9AABBF !important;
    opacity: 1 !important;
}
[data-testid="stAppViewContainer"] .stTextInput input,
[data-testid="stAppViewContainer"] .stNumberInput input {
    color: #0B1F3B !important;
    background: #FFFFFF !important;
    border: 1.5px solid #D1D9E0 !important;
    border-radius: 10px !important;
    direction: rtl !important;
}
[data-testid="stAppViewContainer"] .stTextInput input::placeholder,
[data-testid="stAppViewContainer"] .stNumberInput input::placeholder {
    color: #9AABBF !important;
    opacity: 1 !important;
}
[data-testid="stAppViewContainer"] .stTextInput input:focus,
[data-testid="stAppViewContainer"] .stNumberInput input:focus {
    border-color: #1C3F94 !important;
    box-shadow: 0 0 0 3px rgba(28,63,148,0.12) !important;
    outline: none !important;
}
[data-testid="stAppViewContainer"] label {
    color: #0B1F3B !important;
    font-weight: 600 !important;
    font-family: 'Heebo', sans-serif !important;
}

/* Selectbox dropdown */
[data-baseweb="popover"] li,
[data-baseweb="menu"] li,
[data-baseweb="select"] [role="option"] {
    color: #0B1F3B !important;
    background: #FFFFFF !important;
    direction: rtl !important;
    font-family: 'Heebo', sans-serif !important;
}
[data-baseweb="popover"] li:hover,
[data-baseweb="menu"] li:hover {
    background: #EEF2F8 !important;
}

/* ── אזור ראשי ────────────────────────────────────────────── */
[data-testid="stMain"] { padding: 0 !important; }
[data-testid="block-container"] {
    padding: 1.5rem 2rem 2rem !important;
    max-width: 1400px;
}

/* ── כרטיסי KPI ──────────────────────────────────────────── */
.kpi-card {
    background: white;
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    border: 1px solid #E8ECF0;
    box-shadow: 0 2px 16px rgba(11,31,59,0.06);
    direction: rtl;
    position: relative;
    overflow: hidden;
    transition: transform 0.15s, box-shadow 0.15s;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 24px rgba(11,31,59,0.1); }
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 4px; height: 100%;
    background: linear-gradient(180deg, #1C3F94, #4A90D9);
    border-radius: 0 16px 16px 0;
}
.kpi-label { color: #7B8FA3; font-size: 0.78rem; font-weight: 600; margin-bottom: 0.4rem; letter-spacing: 0.3px; text-transform: uppercase; }
.kpi-value { color: #0B1F3B; font-size: 1.65rem; font-weight: 800; line-height: 1.1; }
.kpi-sub   { color: #4A90D9; font-size: 0.75rem; margin-top: 0.3rem; font-weight: 500; }

/* ── כותרת דוח ───────────────────────────────────────────── */
.report-header {
    background: linear-gradient(135deg, #081629 0%, #0B1F3B 50%, #1C3F94 100%);
    border-radius: 20px;
    padding: 2rem 2.5rem;
    color: white;
    margin-bottom: 2rem;
    direction: rtl;
    position: relative;
    overflow: hidden;
}
.report-header::after {
    content: '📊';
    position: absolute;
    left: 2rem; top: 50%;
    transform: translateY(-50%);
    font-size: 5rem;
    opacity: 0.08;
    pointer-events: none;
}
.report-header h2 { color: white; font-size: 1.6rem; font-weight: 800; margin: 0 0 0.3rem; }
.report-header p  { color: rgba(255,255,255,0.55); font-size: 0.85rem; margin: 0; }
.report-badge {
    display: inline-block;
    background: rgba(201,168,76,0.18);
    border: 1px solid rgba(201,168,76,0.4);
    color: #C9A84C;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    letter-spacing: 1px;
}

/* ── לשוניות ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    direction: rtl;
    gap: 0.3rem;
    background: #FFFFFF;
    border-radius: 14px;
    padding: 0.4rem;
    border: 1px solid #E8ECF0;
    box-shadow: 0 2px 8px rgba(11,31,59,0.05);
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.83rem;
    padding: 0.55rem 1.1rem;
    color: #6B7A8D !important;
    font-family: 'Heebo', sans-serif;
    transition: all 0.15s;
}
.stTabs [data-baseweb="tab"]:hover { background: #F0F4FF !important; color: #1C3F94 !important; }
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0B1F3B, #1C3F94) !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(11,31,59,0.25);
}

/* ── כפתור הורדה PDF ───────────────────────────────────────── */
.stDownloadButton > button {
    background: linear-gradient(135deg, #0B1F3B, #1C3F94) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-weight: 700 !important;
    padding: 0.65rem 1.5rem !important;
    font-family: 'Heebo', sans-serif !important;
    box-shadow: 0 4px 12px rgba(11,31,59,0.25) !important;
    transition: all 0.2s !important;
}
.stDownloadButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(11,31,59,0.35) !important;
}

/* ── טבלאות ─────────────────────────────────────────────────── */
.dataframe { direction: rtl; font-size: 0.83rem; }
[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }

/* ── Metric ──────────────────────────────────────────────────── */
[data-testid="stMetric"] { direction: rtl; }
[data-testid="stMetricValue"] { color: #0B1F3B; font-weight: 800; }
[data-testid="stMetricLabel"] p { color: #7B8FA3 !important; font-size: 0.8rem; }

/* ── Info/warning boxes ────────────────────────────────────────── */
[data-testid="stInfo"], [data-testid="stSuccess"],
[data-testid="stWarning"], [data-testid="stError"] {
    direction: rtl;
    border-radius: 10px;
    font-family: 'Heebo', sans-serif;
}

/* ── כרטיס AI ──────────────────────────────────────────────────── */
.ai-card {
    background: white;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    border: 1px solid #E8ECF0;
    box-shadow: 0 2px 16px rgba(11,31,59,0.06);
    direction: rtl;
    line-height: 2;
    color: #2D3748;
    font-size: 0.95rem;
}

/* ── Welcome cards ──────────────────────────────────────────────── */
.welcome-card {
    background: white;
    border-radius: 16px;
    padding: 1.75rem 1.5rem;
    text-align: center;
    border: 1px solid #E8ECF0;
    box-shadow: 0 2px 12px rgba(11,31,59,0.05);
    transition: all 0.2s;
    direction: rtl;
    height: 100%;
}
.welcome-card:hover { transform: translateY(-3px); box-shadow: 0 8px 30px rgba(11,31,59,0.1); }
.welcome-card-icon { font-size: 2.2rem; margin-bottom: 0.75rem; }
.welcome-card-title { color: #0B1F3B; font-weight: 700; font-size: 1rem; margin-bottom: 0.3rem; }
.welcome-card-sub { color: #7B8FA3; font-size: 0.82rem; line-height: 1.5; }

/* ── section divider ───────────────────────────────────────── */
.section-label {
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.4);
    padding: 1rem 0 0.4rem;
    direction: rtl;
}

/* fix toggle */
[data-testid="stSidebar"] .stToggle label { color: rgba(255,255,255,0.75) !important; }
</style>
""", unsafe_allow_html=True)

# ─── קבועים ─────────────────────────────────────────────────────────────────
PROPERTY_TYPES = [
    "דירה", "דירת גן", "פנטהאוז", "דופלקס",
    "בית פרטי", "קוטג׳", "דו-משפחתי", "טריפלקס", "מגרש",
]
ROOMS_OPTIONS  = ["לא צוין", "1", "1.5", "2", "2.5", "3", "3.5",
                  "4", "4.5", "5", "5.5", "6", "7+"]
FLOOR_OPTIONS  = ["לא צוין", "קרקע", "1", "2", "3", "4", "5", "6",
                  "7", "8", "9", "10", "11", "12", "13", "14", "15",
                  "16", "17", "18", "19", "20", "21-25", "26-30", "פנטהאוז"]
CONDITION_OPTIONS = ["לא צוין", "חדש מקבלן", "משופץ", "מצב טוב", "דורש שיפוץ"]
PRICE_RANGES = {
    "לא צוין":         0,
    "עד 1,000,000 ₪":  1_000_000,
    "1–1.5 מיליון ₪":  1_500_000,
    "1.5–2 מיליון ₪":  2_000_000,
    "2–3 מיליון ₪":    3_000_000,
    "3–5 מיליון ₪":    5_000_000,
    "5–8 מיליון ₪":    8_000_000,
    "מעל 8 מיליון ₪": 12_000_000,
}


def _floor_to_int(s: str):
    if s in ("לא צוין", ""):  return None
    if s == "קרקע":           return 0
    if s == "פנטהאוז":        return 30
    if "-" in s:              return int(s.split("-")[0])
    try:                      return int(s)
    except ValueError:        return None


def _rooms_to_float(s: str):
    if s in ("לא צוין", ""): return None
    if s == "7+":             return 7.0
    try:                      return float(s)
    except ValueError:        return None


# ─── Sidebar ─────────────────────────────────────────────────────────────────
def _sidebar() -> dict:
    with st.sidebar:
        # לוגו
        st.markdown("""
        <div style="padding:1.5rem 1rem 1.25rem;border-bottom:1px solid rgba(255,255,255,0.08);
                    margin-bottom:0.5rem;">
            <div style="display:flex;align-items:center;gap:0.85rem;">
                <div style="width:46px;height:46px;background:linear-gradient(135deg,#1C3F94,#2756C8);
                    border-radius:10px;border:1.5px solid #C9A84C;display:flex;align-items:center;
                    justify-content:center;font-family:Georgia,serif;font-size:1.4rem;font-weight:700;
                    color:#fff;flex-shrink:0;box-shadow:0 4px 12px rgba(0,0,0,0.3);">R</div>
                <div>
                    <div style="color:#fff;font-size:1.05rem;font-weight:800;line-height:1.1;">Real Capital</div>
                    <div style="color:#C9A84C;font-size:0.63rem;letter-spacing:2.5px;
                                text-transform:uppercase;margin-top:3px;">ניתוח שוק השוואתי</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # כתובת הנכס
        st.markdown('<div class="section-label">📍 כתובת הנכס</div>', unsafe_allow_html=True)
        address = st.text_input(
            "כתובת",
            placeholder="למשל: הרצל 15, תל אביב",
            label_visibility="collapsed",
            key="address_input",
        )

        # פרטי הנכס
        st.markdown('<div class="section-label">🏠 פרטי הנכס</div>', unsafe_allow_html=True)
        property_type = st.selectbox("סוג נכס", PROPERTY_TYPES, index=0,
                                     label_visibility="visible")

        c1, c2 = st.columns(2)
        with c1:
            rooms_sel = st.selectbox("חדרים", ROOMS_OPTIONS, index=0,
                                     label_visibility="visible")
        with c2:
            floor_sel = st.selectbox("קומה", FLOOR_OPTIONS, index=0,
                                     label_visibility="visible")

        size_sqm = st.number_input("שטח (מ\"ר)", min_value=0, max_value=2000,
                                   step=5, value=0, label_visibility="visible")
        condition = st.selectbox("מצב הנכס", CONDITION_OPTIONS, index=0,
                                 label_visibility="visible")

        # מחיר
        st.markdown('<div class="section-label">💰 מחיר</div>', unsafe_allow_html=True)
        price_range_sel = st.selectbox("טווח מחיר", list(PRICE_RANGES.keys()),
                                       index=0, label_visibility="collapsed")

        # בניין
        st.markdown('<div class="section-label">🏗️ בניין</div>', unsafe_allow_html=True)
        building_year = st.number_input("שנת בנייה", min_value=1900,
                                        max_value=2025, step=1, value=2000,
                                        label_visibility="visible")

        # AI
        st.markdown('<div style="margin-top:0.5rem"></div>', unsafe_allow_html=True)
        include_ai = st.toggle("🤖 סיכום AI חכם", value=True,
                               help="יצירת ניתוח שוק מקצועי בעברית באמצעות Claude AI")
        st.markdown("---")

        # כפתור
        analyze_btn = st.button(
            "🔍  הפק דו\"ח ניתוח",
            type="primary",
            use_container_width=True,
            disabled=not bool(address.strip()),
        )
        if not address.strip():
            st.markdown(
                '<p style="color:rgba(255,255,255,0.38);font-size:0.8rem;'
                'text-align:center;margin-top:0.5rem;">הכנס כתובת כדי להתחיל</p>',
                unsafe_allow_html=True,
            )

    return dict(
        address=address.strip(),
        property_type=property_type,
        rooms=_rooms_to_float(rooms_sel),
        floor=_floor_to_int(floor_sel),
        size_sqm=size_sqm if size_sqm > 0 else None,
        condition=condition,
        price=PRICE_RANGES.get(price_range_sel, 0) or None,
        building_year=building_year if building_year > 1900 else None,
        include_ai=include_ai,
        analyze=analyze_btn,
    )


# ─── Welcome ─────────────────────────────────────────────────────────────────
def _show_welcome():
    st.markdown("""
    <div style="text-align:center;padding:3rem 1rem 2rem;direction:rtl;">
        <div style="display:inline-flex;align-items:center;gap:0.75rem;
                    background:rgba(28,63,148,0.07);border:1px solid rgba(28,63,148,0.15);
                    border-radius:30px;padding:0.4rem 1.25rem;margin-bottom:1.75rem;">
            <span style="color:#1C3F94;font-size:0.8rem;font-weight:700;letter-spacing:1px;">
                ⚡ פלטפורמת נדל"ן מקצועית
            </span>
        </div>
        <h1 style="font-size:2.4rem;font-weight:900;color:#0B1F3B;margin:0 0 0.75rem;line-height:1.2;">
            ניתוח שוק נדל"ן השוואתי
        </h1>
        <p style="color:#7B8FA3;font-size:1.05rem;max-width:520px;margin:0 auto 3rem;line-height:1.8;">
            הכנס כתובת נכס בסרגל הצד וקבל דו"ח ניתוח שוק מקיף עם עסקאות אמיתיות,
            גרפים, מגמות מחיר וסיכום בינה מלאכותית.
        </p>
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    cards = [
        ("📈", "עסקאות אמיתיות",   "נדלן.gov.il — מאגר עסקאות ממשלתי רשמי"),
        ("🏘️", "נכסים מפורסמים",  "יד2 — מחירי שוק עדכניים בזמן אמת"),
        ("📊", "ניתוח מעמיק",      "קומה, גיל בניין, מגמות, השוואה"),
        ("🤖", "סיכום AI בעברית", "Claude מנתח ומסכם את נתוני השוק"),
    ]
    for col, (icon, title, sub) in zip(cols, cards):
        with col:
            st.markdown(f"""
            <div class="welcome-card">
                <div class="welcome-card-icon">{icon}</div>
                <div class="welcome-card-title">{title}</div>
                <div class="welcome-card-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top:3rem'></div>", unsafe_allow_html=True)

    # הסבר תהליך
    st.markdown("""
    <div style="background:white;border-radius:20px;padding:2rem 2.5rem;
                border:1px solid #E8ECF0;direction:rtl;
                box-shadow:0 2px 16px rgba(11,31,59,0.05);">
        <h3 style="color:#0B1F3B;font-weight:800;margin:0 0 1.5rem;">כיצד זה עובד?</h3>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1.5rem;">
            <div style="text-align:center;">
                <div style="width:48px;height:48px;background:linear-gradient(135deg,#1C3F94,#4A90D9);
                    border-radius:12px;margin:0 auto 0.75rem;display:flex;align-items:center;
                    justify-content:center;font-size:1.3rem;">1️⃣</div>
                <div style="font-weight:700;color:#0B1F3B;margin-bottom:0.3rem;">הכנס כתובת</div>
                <div style="color:#7B8FA3;font-size:0.82rem;line-height:1.5;">
                    הקלד כתובת מלאה כולל שם העיר
                </div>
            </div>
            <div style="text-align:center;">
                <div style="width:48px;height:48px;background:linear-gradient(135deg,#1C3F94,#4A90D9);
                    border-radius:12px;margin:0 auto 0.75rem;display:flex;align-items:center;
                    justify-content:center;font-size:1.3rem;">2️⃣</div>
                <div style="font-weight:700;color:#0B1F3B;margin-bottom:0.3rem;">בחר פרטי נכס</div>
                <div style="color:#7B8FA3;font-size:0.82rem;line-height:1.5;">
                    סוג נכס, חדרים, שטח וקומה
                </div>
            </div>
            <div style="text-align:center;">
                <div style="width:48px;height:48px;background:linear-gradient(135deg,#1C3F94,#4A90D9);
                    border-radius:12px;margin:0 auto 0.75rem;display:flex;align-items:center;
                    justify-content:center;font-size:1.3rem;">3️⃣</div>
                <div style="font-weight:700;color:#0B1F3B;margin-bottom:0.3rem;">קבל דו"ח מלא</div>
                <div style="color:#7B8FA3;font-size:0.82rem;line-height:1.5;">
                    עסקאות, גרפים, הערכת שווי ו-PDF
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── ניתוח ───────────────────────────────────────────────────────────────────
def _run_analysis(cfg: dict):
    container = st.empty()
    with container.container():
        progress_bar = st.progress(0, text="⏳ מתחיל ניתוח שוק...")
        status_box   = st.empty()

    def cb(msg, pct):
        progress_bar.progress(min(pct, 1.0), text=f"⏳ {msg}")
        status_box.info(msg)

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        report = loop.run_until_complete(
            run_market_analysis(
                address=cfg["address"],
                property_type=cfg["property_type"],
                rooms=cfg["rooms"],
                floor=cfg["floor"],
                size_sqm=cfg["size_sqm"],
                building_year=cfg["building_year"],
                price=cfg["price"],
                include_ai=cfg["include_ai"],
                progress_callback=cb,
            )
        )
        loop.close()
    except Exception as e:
        container.empty()
        st.error(f"שגיאה בניתוח: {e}")
        return

    container.empty()
    st.session_state["report"] = report

    if report.errors:
        with st.expander("⚠️ הערות טכניות", expanded=False):
            for err in report.errors:
                st.caption(err)

    if report.total_transactions == 0 and report.total_listings == 0:
        st.error("""
**לא נמצאו נתונים לכתובת זו.**

💡 **טיפים לשיפור התוצאות:**
- ודא שהכתובת כוללת שם עיר — לדוגמה: **הרצל 15, תל אביב**
- נסה רק שם הרחוב והעיר ללא מספר בית
- בדוק שאין שגיאות כתיב בשם הרחוב
- נסה שנית בעוד מספר שניות
        """)
        return

    _display_report(report)


# ─── תצוגת דוח ───────────────────────────────────────────────────────────────
def _display_report(report):
    avg_sqm = report.avg_price_per_sqm_street
    val_str = report.value_estimation.formatted_range if report.value_estimation else "—"

    # כותרת
    st.markdown(f"""
    <div class="report-header">
        <div class="report-badge">📊 דו"ח ניתוח שוק</div>
        <h2>{report.subject_address}</h2>
        <p>{report.subject_property_type} &nbsp;|&nbsp; {report.subject_city}
           &nbsp;|&nbsp; מקורות: {", ".join(report.data_sources_used)}</p>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    kpis = [
        ("עסקאות שנמצאו",   str(report.total_transactions),    "מ-nadlan.gov.il"),
        ("נכסים מפורסמים",  str(report.total_listings),        "מ-יד2"),
        ("ממוצע למ\"ר",     f"₪{avg_sqm:,.0f}" if avg_sqm else "—",  "ברחוב"),
        ("הערכת שווי",      val_str,                           "על בסיס נתונים"),
    ]
    for col, (lbl, val, sub) in zip([c1, c2, c3, c4], kpis):
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{lbl}</div>
                <div class="kpi-value">{val}</div>
                <div class="kpi-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)
            st.write("")

    # כפתור PDF
    st.markdown("<div style='margin:1rem 0 0.5rem'></div>", unsafe_allow_html=True)
    col_pdf, _, _ = st.columns([1, 1, 2])
    with col_pdf:
        try:
            pdf_buf  = generate_pdf(report)
            safe_addr = report.subject_address.replace(" ", "_").replace(",", "")
            st.download_button(
                label="📄  הורד דו\"ח PDF",
                data=pdf_buf,
                file_name=f"ניתוח_שוק_{safe_addr}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception:
            pass

    st.markdown("---")

    # לשוניות
    tab_labels = [
        "📋 עסקאות", "🏢 קומה vs מחיר", "🏗️ ישן vs חדש",
        "📈 מגמות", "🏘️ מפורסמים", "💰 הערכת שווי", "🤖 סיכום AI",
    ]
    tabs = st.tabs(tab_labels)
    with tabs[0]: _tab_transactions(report)
    with tabs[1]: _tab_floors(report)
    with tabs[2]: _tab_age(report)
    with tabs[3]: _tab_trends(report)
    with tabs[4]: _tab_listings(report)
    with tabs[5]: _tab_value(report)
    with tabs[6]: _tab_ai(report)


# ─── לשוניות ─────────────────────────────────────────────────────────────────
def _chart_layout(fig, title="", yaxis_title="", xaxis_title=""):
    fig.update_layout(
        title=dict(text=title, font=dict(size=15, family="Heebo", color="#0B1F3B")),
        font=dict(family="Heebo", color="#0B1F3B"),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(gridcolor="#F0F2F7", title=xaxis_title),
        yaxis=dict(gridcolor="#F0F2F7", title=yaxis_title, tickformat=","),
        margin=dict(t=50, r=20, b=40, l=20),
        showlegend=True,
    )
    return fig


def _tab_transactions(report):
    txs = report.transactions
    if not txs:
        st.info("לא נמצאו עסקאות ברחוב זה. נסה לחפש בכתובת שונה.")
        return

    prices     = [tx.deal_amount   for tx in txs if tx.deal_amount > 0]
    sqm_prices = [tx.price_per_sqm for tx in txs if tx.price_per_sqm]

    c1, c2, c3 = st.columns(3)
    with c1:
        if prices:
            st.metric("מחיר ממוצע", f"₪{int(sum(prices)/len(prices)):,}")
    with c2:
        if sqm_prices:
            st.metric("ממוצע למ\"ר", f"₪{int(sum(sqm_prices)/len(sqm_prices)):,}")
    with c3:
        if prices:
            st.metric("טווח מחירים", f"₪{int(min(prices)):,} – ₪{int(max(prices)):,}")

    st.markdown("<div style='margin:1rem 0 0.5rem'></div>", unsafe_allow_html=True)

    data = [{
        "כתובת":       tx.address,
        "מחיר (₪)":   f"₪{int(tx.deal_amount):,}",
        "חדרים":       tx.rooms or "—",
        "קומה":        tx.floor if tx.floor is not None else "—",
        "מ\"ר":        int(tx.size_sqm) if tx.size_sqm else "—",
        "מחיר/מ\"ר":  f"₪{int(tx.price_per_sqm):,}" if tx.price_per_sqm else "—",
        "שנת בנייה":   tx.building_year or "—",
        "תאריך":       tx.formatted_date,
    } for tx in txs]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    if sqm_prices and len(sqm_prices) >= 3:
        fig = px.histogram(
            x=sqm_prices, nbins=15,
            labels={"x": "מחיר למ\"ר (₪)", "y": "מספר עסקאות"},
            color_discrete_sequence=["#1C3F94"],
        )
        st.plotly_chart(_chart_layout(fig, "התפלגות מחיר למ\"ר",
                                      "מספר עסקאות", "מחיר למ\"ר (₪)"),
                        use_container_width=True)


def _tab_floors(report):
    fa_list = report.floor_analysis
    if not fa_list:
        st.info("אין מספיק נתונים לניתוח לפי קומה (נדרשות לפחות 3 עסקאות עם נתוני קומה)")
        return

    floors = [f"קומה {fa.floor}" for fa in fa_list]
    avgs   = [fa.avg_price_per_sqm for fa in fa_list]
    fig = go.Figure(go.Bar(
        x=floors, y=avgs,
        text=[f"₪{p:,.0f}" for p in avgs], textposition="outside",
        marker_color="#1C3F94",
        marker_line_color="#0B1F3B", marker_line_width=0.5,
        hovertemplate="<b>%{x}</b><br>ממוצע: ₪%{y:,.0f}/מ\"ר<extra></extra>",
    ))
    st.plotly_chart(_chart_layout(fig, "ממוצע מחיר למ\"ר לפי קומה",
                                  "מחיר ממוצע למ\"ר (₪)", "קומה"),
                    use_container_width=True)

    floor_data = [{
        "קומה":           fa.floor,
        "ממוצע למ\"ר":   f"₪{int(fa.avg_price_per_sqm):,}",
        "ממוצע כולל":    fa.formatted_avg_price,
        "מספר עסקאות":   fa.transaction_count,
    } for fa in fa_list]
    st.dataframe(pd.DataFrame(floor_data), use_container_width=True, hide_index=True)


def _tab_age(report):
    ba_list = report.building_age_analysis
    if not ba_list:
        st.info("אין מספיק נתונים לניתוח לפי גיל בניין")
        return

    cats    = [ba.category for ba in ba_list]
    avgs    = [ba.avg_price_per_sqm for ba in ba_list]
    prems   = [ba.price_premium_pct for ba in ba_list]
    colors  = ["#2ECC71" if (p or 0) > 0 else "#E74C3C" if p is not None else "#95A5A6"
               for p in prems]

    fig = go.Figure(go.Bar(
        x=cats, y=avgs,
        text=[f"₪{p:,.0f}" + (f"\n({pr:+.1f}%)" if pr is not None else "")
              for p, pr in zip(avgs, prems)],
        textposition="outside",
        marker_color=colors,
        hovertemplate="<b>%{x}</b><br>ממוצע: ₪%{y:,.0f}/מ\"ר<extra></extra>",
    ))
    st.plotly_chart(_chart_layout(fig, "ממוצע מחיר למ\"ר לפי גיל בניין",
                                  "מחיר ממוצע למ\"ר (₪)"),
                    use_container_width=True)

    cols = st.columns(len(ba_list))
    for i, ba in enumerate(ba_list):
        with cols[i]:
            delta = (f"{'📈' if (ba.price_premium_pct or 0) > 0 else '📉'} "
                     f"{ba.price_premium_pct:+.1f}%") if ba.price_premium_pct is not None else ""
            st.metric(ba.category, f"₪{int(ba.avg_price_per_sqm):,}/מ\"ר", delta)
            st.caption(f"{ba.transaction_count} עסקאות")


def _tab_trends(report):
    trends = report.price_trends
    if not trends:
        st.info("אין מספיק נתונים להצגת מגמות מחיר")
        return

    periods = [pt.period for pt in trends]
    prices  = [pt.avg_price_per_sqm for pt in trends]

    fig = go.Figure(go.Scatter(
        x=periods, y=prices, mode="lines+markers",
        line=dict(color="#1C3F94", width=3),
        marker=dict(size=9, color="#0B1F3B", symbol="circle"),
        fill="tozeroy", fillcolor="rgba(28,63,148,0.06)",
        hovertemplate="<b>%{x}</b><br>ממוצע: ₪%{y:,.0f}/מ\"ר<extra></extra>",
    ))
    st.plotly_chart(_chart_layout(fig, "מגמת מחיר למ\"ר לאורך זמן",
                                  "מחיר ממוצע למ\"ר (₪)", "תקופה"),
                    use_container_width=True)

    if len(trends) >= 2:
        first, last = trends[0], trends[-1]
        chg = ((last.avg_price_per_sqm - first.avg_price_per_sqm)
               / first.avg_price_per_sqm * 100)
        c1, c2, c3 = st.columns(3)
        with c1: st.metric(f"מחיר {first.period}", f"₪{int(first.avg_price_per_sqm):,}/מ\"ר")
        with c2: st.metric(f"מחיר {last.period}",  f"₪{int(last.avg_price_per_sqm):,}/מ\"ר")
        with c3: st.metric("שינוי מצטבר", f"{chg:+.1f}%")


def _tab_listings(report):
    listings = report.current_listings
    if not listings:
        st.info("לא נמצאו נכסים מפורסמים דומים ביד2")
        return

    data = [{
        "כתובת":      l.address,
        "מחיר (₪)":  f"₪{int(l.price):,}" if l.price > 0 else "—",
        "חדרים":      l.rooms or "—",
        "קומה":       l.floor if l.floor is not None else "—",
        "מ\"ר":       int(l.size_sqm) if l.size_sqm else "—",
        "מחיר/מ\"ר": f"₪{int(l.price_per_sqm):,}" if l.price_per_sqm else "—",
        "סוג נכס":    l.property_type,
    } for l in listings]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    tx_sqm   = [tx.price_per_sqm for tx in report.transactions if tx.price_per_sqm]
    list_sqm = [l.price_per_sqm  for l  in listings           if l.price_per_sqm]
    if tx_sqm and list_sqm:
        fig = go.Figure()
        fig.add_trace(go.Box(y=tx_sqm,   name="עסקאות שנסגרו",  marker_color="#0B1F3B"))
        fig.add_trace(go.Box(y=list_sqm, name="מפורסמים (יד2)", marker_color="#4A90D9"))
        st.plotly_chart(_chart_layout(fig, "השוואת מחיר למ\"ר: עסקאות vs מפורסמים",
                                      "מחיר למ\"ר (₪)"),
                        use_container_width=True)


def _tab_value(report):
    ve = report.value_estimation
    if not ve:
        st.warning("אין מספיק נתונים להערכת שווי (נדרשות לפחות 3 עסקאות דומות)")
        return

    c1, c2, c3 = st.columns(3)
    with c1: st.metric("🔻 מחיר מינימלי",  f"₪{int(ve.estimated_price_low):,}")
    with c2: st.metric("🎯 הערכת שווי",    f"₪{int(ve.estimated_price_mid):,}")
    with c3: st.metric("🔺 מחיר מקסימלי", f"₪{int(ve.estimated_price_high):,}")

    c4, c5 = st.columns(2)
    with c4: st.metric("מחיר למ\"ר", f"₪{int(ve.estimated_price_per_sqm):,}")
    with c5:
        emoji = {"גבוה": "🟢", "בינוני": "🟡", "נמוך": "🔴"}.get(ve.confidence, "⚪")
        st.metric("רמת ביטחון", f"{emoji} {ve.confidence}")
    st.caption(f"מבוסס על {ve.comparable_count} נכסים | {ve.methodology}")

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=ve.estimated_price_mid,
        number={"suffix": " ₪", "valueformat": ",.0f",
                "font": {"size": 28, "family": "Heebo"}},
        gauge={
            "axis": {"range": [ve.estimated_price_low * 0.8,
                                ve.estimated_price_high * 1.2],
                     "tickformat": ","},
            "bar": {"color": "#1C3F94", "thickness": 0.3},
            "steps": [
                {"range": [ve.estimated_price_low * 0.8, ve.estimated_price_low], "color": "#FADBD8"},
                {"range": [ve.estimated_price_low, ve.estimated_price_high],      "color": "#D5F5E3"},
                {"range": [ve.estimated_price_high, ve.estimated_price_high * 1.2],"color": "#FADBD8"},
            ],
            "threshold": {"line": {"color": "#C9A84C", "width": 3},
                          "value": ve.estimated_price_mid},
        },
        title={"text": "הערכת שווי הנכס", "font": {"size": 16, "family": "Heebo"}},
    ))
    fig.update_layout(height=340, font=dict(family="Heebo"),
                      paper_bgcolor="white", margin=dict(t=60, b=20))
    st.plotly_chart(fig, use_container_width=True)


def _tab_ai(report):
    if not report.ai_summary:
        st.info("סיכום AI לא נוצר — הפעל את האפשרות 'סיכום AI חכם' בסרגל הצד ונסה שוב.")
        return
    st.markdown(
        f'<div class="ai-card">{report.ai_summary.replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    cfg = _sidebar()

    if not cfg["address"]:
        _show_welcome()
        return

    if cfg["analyze"]:
        _run_analysis(cfg)
    elif "report" in st.session_state:
        _display_report(st.session_state["report"])
    else:
        _show_welcome()


main()
