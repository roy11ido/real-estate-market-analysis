"""דף עסקאות נדל"ן — ייבוא, חיפוש, ניתוח השוואתי (Comps)."""
from __future__ import annotations

import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import nest_asyncio
import pandas as pd
import plotly.express as px
import streamlit as st

from src.market.transactions import (
    Transaction,
    CompsAnalysis,
    add_transactions_to_session,
    analyze_comps,
    clear_session_transactions,
    filter_transactions,
    from_nadlan_transaction,
    get_session_transactions,
    import_transactions_from_bytes,
)

nest_asyncio.apply()

st.set_page_config(
    page_title="עסקאות | Real Capital",
    page_icon="📋",
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
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.9) !important; }
[data-testid="stSidebar"] .stTextInput input,
[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div,
[data-testid="stSidebar"] .stNumberInput input,
[data-testid="stSidebar"] .stDateInput input {
    background: rgba(255,255,255,0.1) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
    color: white !important;
    border-radius: 8px;
    direction: rtl;
}
[data-testid="stSidebar"] .stTextInput input::placeholder,
[data-testid="stSidebar"] .stNumberInput input::placeholder {
    color: rgba(255,255,255,0.4) !important;
}
[data-testid="stSidebar"] .stButton > button {
    background: #1C3F94 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    width: 100%;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: #4A90D9 !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.1) !important; }

/* Main inputs */
[data-testid="stAppViewContainer"] .stTextInput input,
[data-testid="stAppViewContainer"] .stNumberInput input,
[data-testid="stAppViewContainer"] .stTextArea textarea,
[data-testid="stAppViewContainer"] .stSelectbox div[data-baseweb="select"] > div {
    color: #0B1F3B !important;
    background-color: #FFFFFF !important;
    border: 1px solid #D1D9E0 !important;
    border-radius: 8px !important;
}
[data-testid="stAppViewContainer"] .stTextInput input::placeholder,
[data-testid="stAppViewContainer"] .stNumberInput input::placeholder,
[data-testid="stAppViewContainer"] .stTextArea textarea::placeholder {
    color: #9AABBF !important;
}
[data-testid="stAppViewContainer"] label,
[data-testid="stAppViewContainer"] p {
    color: #0B1F3B !important;
}

/* Page header */
.page-header {
    background: linear-gradient(135deg, #0B1F3B, #1C3F94);
    border-radius: 16px;
    padding: 1.5rem 2rem;
    color: white;
    margin-bottom: 1.5rem;
    direction: rtl;
}
.page-header h1 { color: white; font-size: 1.6rem; font-weight: 800; margin-bottom: 0.2rem; }
.page-header p  { color: rgba(255,255,255,0.6); font-size: 0.85rem; }

/* KPI */
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    border: 1px solid #E8ECF0;
    box-shadow: 0 2px 12px rgba(11,31,59,0.06);
    direction: rtl;
    text-align: right;
}
.kpi-label { color: #6B7A8D; font-size: 0.78rem; font-weight: 500; margin-bottom: 0.25rem; }
.kpi-value { color: #0B1F3B; font-size: 1.5rem; font-weight: 800; }
.kpi-sub   { color: #4A90D9; font-size: 0.75rem; margin-top: 0.1rem; }

/* Source tabs */
.stTabs [data-baseweb="tab-list"] {
    direction: rtl; gap: 0.25rem; background: white;
    border-radius: 12px; padding: 0.4rem; border: 1px solid #E8ECF0;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px; font-weight: 600; font-size: 0.85rem; padding: 0.5rem 1rem;
    color: #0B1F3B !important;
}
.stTabs [aria-selected="true"] {
    background: #0B1F3B !important; color: white !important;
}

/* Confidence badge */
.confidence-high   { color:#1B5E20; background:#E8F5E9; border:1px solid #A5D6A7; }
.confidence-medium { color:#6D4C41; background:#FFF3E0; border:1px solid #FFB74D; }
.confidence-low    { color:#B71C1C; background:#FFEBEE; border:1px solid #EF9A9A; }
.confidence-badge  { border-radius:20px; padding:2px 10px; font-size:0.78rem; font-weight:600; display:inline-block; }

/* Table */
.dataframe { direction: rtl; font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)

# ─── קבועים ─────────────────────────────────────────────────────────────────
PROPERTY_TYPES = ["הכל", "דירה", "דירת גן", "פנטהאוז", "דופלקס",
                  "בית פרטי", "קוטג׳", "דו-משפחתי", "טריפלקס"]

SOURCE_LABELS = {
    "nadlan_api":    "🏛️ רשות המיסים (API)",
    "manual_csv":    "📊 ייבוא קובץ (רשות המיסים / GovMap)",
    "manual_entry":  "✏️ הזנה ידנית",
}

CONFIDENCE_CLASS = {"גבוהה": "confidence-high", "בינונית": "confidence-medium", "נמוכה": "confidence-low"}


# ─── Sidebar ─────────────────────────────────────────────────────────────────
def _sidebar_filters() -> dict:
    with st.sidebar:
        # לוגו
        st.markdown("""
        <div style="display:flex;align-items:center;gap:0.7rem;padding:0.5rem 0 1rem 0;">
            <div style="width:42px;height:42px;background:#1C3F94;border-radius:8px;border:1.5px solid #C9A84C;
                display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;
                font-size:1.3rem;font-weight:700;color:#fff;flex-shrink:0;">R</div>
            <div>
                <div style="color:#fff;font-size:1rem;font-weight:800;line-height:1.1;">Real Capital</div>
                <div style="color:#C9A84C;font-size:0.65rem;letter-spacing:2px;text-transform:uppercase;margin-top:2px;">עסקאות</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.7rem;font-weight:600;letter-spacing:1px;text-transform:uppercase;">🔍 סינון עסקאות</p>', unsafe_allow_html=True)

        city_filter    = st.text_input("עיר", placeholder="כל הערים", label_visibility="collapsed", key="tx_city")
        street_filter  = st.text_input("רחוב", placeholder="כל הרחובות", label_visibility="collapsed", key="tx_street")
        ptype_filter   = st.selectbox("סוג נכס", PROPERTY_TYPES, key="tx_ptype")

        st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.7rem;margin-top:0.8rem;">📐 שטח (מ"ר)</p>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            min_sqm = st.number_input("מינ׳", min_value=0, max_value=1000, value=0, step=10, label_visibility="collapsed", key="tx_minsqm")
        with c2:
            max_sqm = st.number_input("מקס׳", min_value=0, max_value=1000, value=0, step=10, label_visibility="collapsed", key="tx_maxsqm")

        st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.7rem;margin-top:0.8rem;">🛏️ חדרים</p>', unsafe_allow_html=True)
        c3, c4 = st.columns(2)
        with c3:
            min_rooms = st.number_input("מינ׳ חדרים", min_value=0.0, max_value=10.0, value=0.0, step=0.5, label_visibility="collapsed", key="tx_minrm")
        with c4:
            max_rooms = st.number_input("מקס׳ חדרים", min_value=0.0, max_value=10.0, value=0.0, step=0.5, label_visibility="collapsed", key="tx_maxrm")

        st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.7rem;margin-top:0.8rem;">📅 תאריכים</p>', unsafe_allow_html=True)
        date_from = st.date_input("מתאריך", value=date.today() - timedelta(days=365*2), key="tx_datefrom")
        date_to   = st.date_input("עד תאריך", value=date.today(), key="tx_dateto")

        st.markdown('<p style="color:rgba(255,255,255,0.5);font-size:0.7rem;margin-top:0.8rem;">💰 מחיר (₪)</p>', unsafe_allow_html=True)
        c5, c6 = st.columns(2)
        with c5:
            min_price = st.number_input("מינ׳ מחיר", min_value=0, value=0, step=100000, label_visibility="collapsed", key="tx_minprice")
        with c6:
            max_price = st.number_input("מקס׳ מחיר", min_value=0, value=0, step=100000, label_visibility="collapsed", key="tx_maxprice")

        st.markdown("---")
        radius_km = st.slider("רדיוס חיפוש (ק\"מ)", 0.0, 10.0, 0.0, 0.5,
                              help="פעיל רק אם בוצע ניתוח שוק עם כתובת נבחרת", key="tx_radius")

        apply_btn = st.button("🔍 החל סינון", use_container_width=True)
        clear_btn = st.button("🗑️ נקה עסקאות", use_container_width=True)

    return dict(
        city=city_filter or None,
        street=street_filter or None,
        property_type=ptype_filter if ptype_filter != "הכל" else None,
        min_sqm=min_sqm or None,
        max_sqm=max_sqm or None,
        min_rooms=min_rooms or None,
        max_rooms=max_rooms or None,
        date_from=date_from,
        date_to=date_to,
        min_price=min_price or None,
        max_price=max_price or None,
        radius_km=radius_km or None,
        apply=apply_btn,
        clear=clear_btn,
    )


# ─── יבוא נתונים ────────────────────────────────────────────────────────────
def _import_section():
    """לשונית: ייבוא נתונים ממקורות שונים."""

    st.markdown("""
    <div style="background:#EEF2F8;border-right:4px solid #1C3F94;border-radius:8px;padding:1rem 1.2rem;margin-bottom:1rem;direction:rtl;">
        <strong>📊 מקורות נתונים תואמים</strong><br/>
        <span style="color:#6B7A8D;font-size:0.85rem;">
        הנתונים מגיעים מרשות המיסים ו-GovMap. אנא ייצא קובץ Excel מהאתר הרשמי והעלה כאן.
        </span>
    </div>
    """, unsafe_allow_html=True)

    src_tabs = st.tabs([
        "🏛️ רשות המיסים (ייצוא קובץ)",
        "🗺️ GovMap (ייצוא קובץ)",
        "✏️ הזנה ידנית",
        "🔗 nadlan.gov.il API (אוטומטי)",
    ])

    # ── רשות המיסים ──────────────────────────────────────────────────────────
    with src_tabs[0]:
        st.markdown("""
        **כיצד לייצא מרשות המיסים:**

        1. פתח את [nadlan.gov.il](https://www.nadlan.gov.il/) ← לא את האתר הישן
        2. חפש עיר / שכונה / רחוב
        3. לחץ **"ייצוא לאקסל"** בתחתית הטבלה
        4. העלה את הקובץ כאן ↓
        """)

        st.info("💡 הורד את הקובץ ישירות מ-nadlan.gov.il — זה המקור הרשמי והחוקי.")

        nadlan_file = st.file_uploader(
            "העלאת קובץ מרשות המיסים (Excel / CSV)",
            type=["xlsx", "xls", "csv"],
            key="upload_nadlan",
            label_visibility="collapsed",
        )
        if nadlan_file:
            _handle_upload(nadlan_file, "manual_csv")

    # ── GovMap ────────────────────────────────────────────────────────────────
    with src_tabs[1]:
        st.markdown("""
        **כיצד לייצא מ-GovMap:**

        1. פתח את [govmap.gov.il](https://www.govmap.gov.il/)
        2. הפעל שכבת **"עסקאות נדל"ן"** מתפריט השכבות
        3. סמן אזור בעזרת כלי הבחירה
        4. לחץ **"הורד נתונים"** / **"ייצוא Excel"** (אם זמין באזורך)
        5. העלה את הקובץ כאן ↓
        """)

        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.warning("""
            ⚠️ **הערת ציות:** GovMap אינו מספק REST API ציבורי מתועד לנדל"ן.
            הנתונים הגלויים בו מגיעים ממקורות ממשלתיים שונים.
            ייצוא ידני + העלאה כאן הוא השיטה התקינה.
            """)
        with col_b:
            st.link_button(
                "פתח GovMap ↗",
                url="https://www.govmap.gov.il/?c=219143.61,618345.06&lay=16",
            )

        govmap_file = st.file_uploader(
            "העלאת קובץ מ-GovMap (Excel / CSV)",
            type=["xlsx", "xls", "csv"],
            key="upload_govmap",
            label_visibility="collapsed",
        )
        if govmap_file:
            _handle_upload(govmap_file, "manual_csv")

    # ── הזנה ידנית ────────────────────────────────────────────────────────────
    with src_tabs[2]:
        st.markdown("**הזנת עסקה ידנית:**")

        with st.form("manual_tx_form"):
            c1, c2 = st.columns(2)
            with c1:
                m_address  = st.text_input("כתובת מלאה *", placeholder="הרצל 15, תל אביב")
                m_city     = st.text_input("עיר *", placeholder="תל אביב")
                m_street   = st.text_input("רחוב", placeholder="הרצל")
                m_ptype    = st.selectbox("סוג נכס", PROPERTY_TYPES[1:])
                m_rooms    = st.number_input("חדרים", min_value=0.0, max_value=15.0, step=0.5, value=3.0)
            with c2:
                m_price    = st.number_input("מחיר עסקה (₪) *", min_value=0, step=10000)
                m_sqm      = st.number_input("שטח (מ\"ר)", min_value=0, step=5)
                m_floor    = st.number_input("קומה", min_value=0, max_value=50, step=1)
                m_year     = st.number_input("שנת בנייה", min_value=1900, max_value=2025, value=2000)
                m_date     = st.date_input("תאריך עסקה *", value=date.today())

            m_source_ref = st.text_input("מקור / הפניה", placeholder="לדוגמה: גוש 6756 חלקה 12")
            submitted    = st.form_submit_button("➕ הוסף עסקה", type="primary")

        if submitted:
            if not m_address or not m_city or m_price <= 0:
                st.error("⛔ יש למלא: כתובת, עיר ומחיר עסקה.")
            else:
                tx = Transaction(
                    id=f"manual_{m_address}_{m_date}",
                    source="manual_entry",
                    formatted_address=m_address,
                    city=m_city,
                    street=m_street,
                    property_type=m_ptype,
                    rooms=m_rooms or None,
                    floor=m_floor or None,
                    size_sqm=float(m_sqm) if m_sqm else None,
                    building_year=m_year or None,
                    deal_amount=float(m_price),
                    deal_date=m_date,
                    source_ref=m_source_ref,
                )
                n = add_transactions_to_session([tx])
                st.success(f"✅ עסקה נוספה בהצלחה! (סה\"כ: {len(get_session_transactions())} עסקאות)")
                st.rerun()

    # ── API אוטומטי ────────────────────────────────────────────────────────────
    with src_tabs[3]:
        st.markdown("""
        **טעינה אוטומטית דרך ה-API של nadlan.gov.il:**

        אם ביצעת ניתוח שוק (בדף "ניתוח שוק"), העסקאות שנמשכו מה-API
        מאוחסנות אוטומטית ב-session ומוצגות כאן.
        """)

        report = st.session_state.get("report")
        if report:
            all_txs = list(report.transactions_street or []) + list(report.transactions_neighborhood or [])
            if all_txs:
                converted = []
                for tx in all_txs:
                    try:
                        converted.append(from_nadlan_transaction(tx))
                    except Exception:
                        pass
                if st.button("📥 ייבא עסקאות מהדו\"ח הנוכחי", type="primary"):
                    n = add_transactions_to_session(converted)
                    st.success(f"✅ יובאו {n} עסקאות חדשות.")
                    st.rerun()
                st.info(f"💡 {len(converted)} עסקאות זמינות מדו\"ח ניתוח השוק האחרון.")
            else:
                st.info("אין עסקאות בדו\"ח הנוכחי.")
        else:
            st.info("הפעל ניתוח שוק תחילה כדי לטעון עסקאות אוטומטית.")


def _handle_upload(uploaded_file, source_label: str):
    """קרא קובץ שהועלה, יבא עסקאות, הצג תוצאות."""
    raw = uploaded_file.read()
    with st.spinner("מעבד קובץ..."):
        txs, errors = import_transactions_from_bytes(raw, uploaded_file.name, source_label)

    if errors:
        with st.expander(f"⚠️ {len(errors)} שגיאות בייבוא"):
            for e in errors[:20]:
                st.caption(e)

    if txs:
        n = add_transactions_to_session(txs)
        st.success(f"✅ יובאו {n} עסקאות חדשות מתוך {len(txs)} שנקראו מהקובץ.")
        st.rerun()
    else:
        st.error("❌ לא נמצאו עסקאות תקינות בקובץ. בדוק את פורמט הקובץ.")


# ─── טבלת עסקאות ────────────────────────────────────────────────────────────
def _transactions_table(transactions: list[Transaction]):
    if not transactions:
        st.markdown("""
        <div style="text-align:center;padding:3rem;color:#9AABBF;direction:rtl;">
            <div style="font-size:2.5rem;margin-bottom:0.5rem;">📋</div>
            <div style="font-size:1rem;font-weight:600;">אין עסקאות לתצוגה</div>
            <div style="font-size:0.85rem;margin-top:0.25rem;">ייבא עסקאות מלשונית "ייבוא נתונים"</div>
        </div>
        """, unsafe_allow_html=True)
        return None

    rows = []
    for tx in transactions:
        rows.append({
            "כתובת":         tx.formatted_address or tx.city,
            "עיר":           tx.city,
            "שכונה":         tx.neighborhood,
            "סוג נכס":       tx.property_type,
            "חדרים":         tx.rooms,
            "קומה":          tx.floor,
            "שטח מ\"ר":     tx.size_sqm,
            "מחיר (₪)":     tx.deal_amount if tx.deal_amount > 0 else None,
            "מחיר/מ\"ר":    tx.price_per_sqm,
            "תאריך":         tx.formatted_date,
            "מקור":          SOURCE_LABELS.get(tx.source, tx.source),
            "_id":           tx.id,
        })

    df = pd.DataFrame(rows)

    # עמודות להצגה
    display_cols = ["כתובת", "עיר", "סוג נכס", "חדרים", "שטח מ\"ר", "מחיר (₪)", "מחיר/מ\"ר", "תאריך", "מקור"]
    df_show = df[display_cols].copy()

    # פורמט מספרים
    if "מחיר (₪)" in df_show.columns:
        df_show["מחיר (₪)"] = df_show["מחיר (₪)"].apply(
            lambda x: f"₪{x:,.0f}" if pd.notna(x) and x else "—"
        )
    if "מחיר/מ\"ר" in df_show.columns:
        df_show["מחיר/מ\"ר"] = df_show["מחיר/מ\"ר"].apply(
            lambda x: f"₪{x:,.0f}" if pd.notna(x) and x else "—"
        )
    if "שטח מ\"ר" in df_show.columns:
        df_show["שטח מ\"ר"] = df_show["שטח מ\"ר"].apply(
            lambda x: f"{x:.0f}" if pd.notna(x) and x else "—"
        )
    if "חדרים" in df_show.columns:
        df_show["חדרים"] = df_show["חדרים"].apply(
            lambda x: f"{x:g}" if pd.notna(x) and x else "—"
        )

    # סימון שורות לניתוח
    selected_ids = st.session_state.get("selected_comp_ids", set())

    # MultiSelect בתצוגה
    st.dataframe(df_show, use_container_width=True, hide_index=True)

    # בחירת comps לניתוח
    st.markdown("**בחר עסקאות לניתוח השוואתי (Comps):**")
    labels = [
        f"{row['כתובת']} | {row['מחיר (₪)']} | {row['תאריך']}"
        for _, row in df_show.iterrows()
    ]
    id_list = df["_id"].tolist()

    selected_labels = st.multiselect(
        "בחר עסקאות",
        options=labels,
        label_visibility="collapsed",
        key="comps_multiselect",
    )
    selected_idxs   = [labels.index(l) for l in selected_labels if l in labels]
    selected_tx     = [transactions[i] for i in selected_idxs]
    st.session_state["selected_comps"] = selected_tx

    return df


# ─── ניתוח Comps ────────────────────────────────────────────────────────────
def _comps_analysis_section(selected_txs: list[Transaction]):
    if not selected_txs:
        st.info("💡 בחר עסקאות מהטבלה לעיל לניתוח השוואתי")
        return

    # קלט נכס נושא
    with st.expander("⚙️ פרטי הנכס הנבדק (לחישוב הערכה)", expanded=True):
        ca, cb = st.columns(2)
        with ca:
            subject_price = st.number_input("מחיר מבוקש / מוצע (₪)",
                min_value=0, step=50000, value=0, key="comp_subj_price")
        with cb:
            subject_sqm = st.number_input("שטח נכס (מ\"ר)",
                min_value=0.0, step=5.0, value=0.0, key="comp_subj_sqm")

    analysis = analyze_comps(
        selected_txs,
        subject_price=float(subject_price) if subject_price > 0 else None,
        subject_sqm=float(subject_sqm)    if subject_sqm   > 0 else None,
    )

    # KPI row
    conf_cls = CONFIDENCE_CLASS.get(analysis.confidence, "confidence-low")
    st.markdown(f"""
    <div style="display:flex;gap:1rem;margin:1rem 0;direction:rtl;flex-wrap:wrap;">
        <div class="kpi-card" style="flex:1;min-width:140px;">
            <div class="kpi-label">מספר עסקאות</div>
            <div class="kpi-value">{analysis.count}</div>
            <div class="kpi-sub"><span class="confidence-badge {conf_cls}">אמינות: {analysis.confidence}</span></div>
        </div>
        <div class="kpi-card" style="flex:1;min-width:140px;">
            <div class="kpi-label">מחיר ממוצע</div>
            <div class="kpi-value">₪{analysis.avg_price:,.0f}</div>
            <div class="kpi-sub">מדיאן: ₪{analysis.median_price:,.0f}</div>
        </div>
        <div class="kpi-card" style="flex:1;min-width:140px;">
            <div class="kpi-label">מחיר ממוצע/מ"ר</div>
            <div class="kpi-value">₪{analysis.avg_price_per_sqm:,.0f}</div>
            <div class="kpi-sub">טווח: ₪{analysis.min_price:,.0f} — ₪{analysis.max_price:,.0f}</div>
        </div>
        {"" if analysis.estimated_value is None else f'''
        <div class="kpi-card" style="flex:1;min-width:140px;">
            <div class="kpi-label">הערכת שווי (לפי מ"ר)</div>
            <div class="kpi-value">₪{analysis.estimated_value:,.0f}</div>
            <div class="kpi-sub">{"" if analysis.subject_delta_pct is None
                else ("⬆️ " if analysis.subject_delta_pct > 0 else "⬇️ ") +
                f"{abs(analysis.subject_delta_pct):.1f}% מהממוצע"}</div>
        </div>
        '''}
    </div>
    """, unsafe_allow_html=True)

    # גרף פיזור מחירים
    if analysis.count >= 2:
        prices = [t.deal_amount for t in selected_txs if t.deal_amount > 0]
        addrs  = [t.formatted_address or t.city for t in selected_txs if t.deal_amount > 0]
        dates  = [t.formatted_date for t in selected_txs if t.deal_amount > 0]

        fig = px.bar(
            x=addrs,
            y=prices,
            text=[f"₪{p:,.0f}" for p in prices],
            labels={"x": "כתובת", "y": "מחיר (₪)"},
            title="השוואת מחירי עסקאות נבחרות",
            color=prices,
            color_continuous_scale=["#4A90D9", "#0B1F3B"],
        )
        fig.update_traces(textposition="outside")
        fig.update_layout(
            font_family="Heebo",
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False,
            coloraxis_showscale=False,
            xaxis_tickangle=-30,
            yaxis_tickformat=",",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ייצוא comps ל-CMA
    if st.button("📤 שלח Comps לדו\"ח ניתוח שוק", type="primary"):
        st.session_state["cma_comps"] = selected_txs
        st.success(f"✅ {len(selected_txs)} עסקאות הועברו לדו\"ח ניתוח השוק.")


# ─── KPIs מסוכמים ───────────────────────────────────────────────────────────
def _summary_kpis(transactions: list[Transaction]):
    n = len(transactions)
    if n == 0:
        return

    valid_prices = [t.deal_amount for t in transactions if t.deal_amount > 0]
    avg_price    = sum(valid_prices) / len(valid_prices) if valid_prices else 0
    ppsqm_list   = [t.price_per_sqm for t in transactions if t.price_per_sqm]
    avg_ppsqm    = sum(ppsqm_list) / len(ppsqm_list) if ppsqm_list else 0

    c1, c2, c3, c4 = st.columns(4)
    for col, label, val in [
        (c1, "סה\"כ עסקאות", str(n)),
        (c2, "מחיר ממוצע", f"₪{avg_price:,.0f}" if avg_price else "—"),
        (c3, "ממוצע/מ\"ר", f"₪{avg_ppsqm:,.0f}" if avg_ppsqm else "—"),
        (c4, "ערים", str(len({t.city for t in transactions if t.city}))),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{val}</div>
            </div>
            """, unsafe_allow_html=True)
            st.write("")  # spacing


# ─── ראשי ───────────────────────────────────────────────────────────────────
def main():
    # Sidebar filters
    filters = _sidebar_filters()

    if filters["clear"]:
        clear_session_transactions()
        st.session_state.pop("selected_comps", None)
        st.rerun()

    # Page header
    st.markdown("""
    <div class="page-header">
        <h1>📋 עסקאות נדל"ן</h1>
        <p>ניהול, ייבוא וניתוח עסקאות השוואתיות (Comps)</p>
    </div>
    """, unsafe_allow_html=True)

    # Main tabs
    tab_view, tab_import, tab_comps = st.tabs([
        "📊 עסקאות",
        "📥 ייבוא נתונים",
        "📈 ניתוח Comps",
    ])

    # ── ייבוא ────────────────────────────────────────────────────────────────
    with tab_import:
        _import_section()

    # ── עסקאות ───────────────────────────────────────────────────────────────
    with tab_view:
        all_txs = get_session_transactions()

        # החל פילטרים
        center_lat = st.session_state.get("subject_lat")
        center_lng = st.session_state.get("subject_lng")

        filtered = filter_transactions(
            all_txs,
            city=filters["city"],
            street=filters["street"],
            property_type=filters["property_type"],
            min_sqm=filters["min_sqm"],
            max_sqm=filters["max_sqm"],
            min_rooms=filters["min_rooms"],
            max_rooms=filters["max_rooms"],
            date_from=filters["date_from"],
            date_to=filters["date_to"],
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            radius_km=filters["radius_km"] if center_lat else None,
            center_lat=center_lat,
            center_lng=center_lng,
        )

        st.markdown(f"**{len(filtered):,} עסקאות** מתוך {len(all_txs):,} סה\"כ")
        _summary_kpis(filtered)
        _transactions_table(filtered)

    # ── ניתוח Comps ───────────────────────────────────────────────────────────
    with tab_comps:
        selected = st.session_state.get("selected_comps", [])
        _comps_analysis_section(selected)


main()
