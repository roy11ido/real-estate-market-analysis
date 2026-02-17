"""Streamlit page for Market Analysis Report generation."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from src.market.orchestrator import run_market_analysis
from src.market.pdf_report import generate_pdf
from src.market.models import MarketAnalysisReport

# --- Page Configuration ---
st.set_page_config(
    page_title="ניתוח שוק נדל\"ן",
    page_icon="📊",
    layout="wide",
)

# --- Custom CSS ---
st.markdown(
    """
    <style>
    .rtl-text {
        direction: rtl;
        text-align: right;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 1.8rem;
        font-weight: bold;
    }
    .metric-card p {
        margin: 0.3rem 0 0;
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .section-divider {
        border-top: 3px solid #e0e0e0;
        margin: 2rem 0;
    }
    div[data-testid="stMetric"] {
        direction: rtl;
    }
    .stTabs [data-baseweb="tab-list"] {
        direction: rtl;
    }
    .stButton > button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Property types ---
PROPERTY_TYPES = [
    "דירה", "פנטהאוז", "בית פרטי", "קוטג׳",
    "דירת גן", "דופלקס", "דו-משפחתי", "טריפלקס", "מגרש",
]


def main():
    st.title("📊 ניתוח שוק נדל\"ן השוואתי")
    st.markdown("**Real Capital** | רוי עידו")
    st.divider()

    # --- Sidebar: Input Form ---
    with st.sidebar:
        st.header("🏠 פרטי הנכס")

        address = st.text_input(
            "כתובת הנכס",
            placeholder="לדוגמה: הרצל 15, תל אביב",
            help="הכנס כתובת מלאה כולל עיר",
        )

        property_type = st.selectbox(
            "סוג הנכס",
            options=PROPERTY_TYPES,
            index=0,
        )

        st.divider()
        st.subheader("פרטים נוספים (אופציונלי)")
        st.caption("ככל שתמלא יותר, הניתוח יהיה מדויק יותר")

        col1, col2 = st.columns(2)
        with col1:
            rooms = st.number_input("חדרים", min_value=0.0, max_value=20.0, step=0.5, value=0.0)
            floor = st.number_input("קומה", min_value=-1, max_value=50, step=1, value=0)
        with col2:
            size_sqm = st.number_input("שטח (מ\"ר)", min_value=0.0, max_value=2000.0, step=5.0, value=0.0)
            building_year = st.number_input("שנת בנייה", min_value=1900, max_value=2030, step=1, value=0)

        price = st.number_input(
            "מחיר ידוע/מבוקש (ש\"ח)",
            min_value=0, max_value=100_000_000, step=50000, value=0,
        )

        st.divider()

        include_ai = st.checkbox("כלול סיכום AI", value=True)

        st.divider()

        analyze_btn = st.button(
            "🔍 הפק דו\"ח ניתוח",
            type="primary",
            use_container_width=True,
            disabled=not address.strip(),
        )

    # --- Main Content ---
    if not address.strip():
        st.info("👈 הכנס כתובת נכס בסרגל הצד והקש על 'הפק דו\"ח ניתוח'")
        _show_instructions()
        return

    if analyze_btn:
        _run_analysis(
            address=address.strip(),
            property_type=property_type,
            rooms=rooms if rooms > 0 else None,
            floor=floor if floor != 0 else None,
            size_sqm=size_sqm if size_sqm > 0 else None,
            building_year=building_year if building_year > 1900 else None,
            price=price if price > 0 else None,
            include_ai=include_ai,
        )
    elif "report" in st.session_state:
        _display_report(st.session_state["report"])


def _show_instructions():
    """Show usage instructions when no report exists."""
    st.markdown("### איך להשתמש?")
    st.markdown("""
    1. הכנס **כתובת מלאה** של הנכס (כולל עיר)
    2. בחר **סוג נכס**
    3. מלא פרטים נוספים לדיוק טוב יותר
    4. לחץ על **הפק דו\"ח ניתוח**
    """)

    st.markdown("### מה הדו\"ח כולל?")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**📈 עסקאות**")
        st.caption("עסקאות שנסגרו מ-nadlan.gov.il")
    with cols[1]:
        st.markdown("**🏘️ נכסים מפורסמים**")
        st.caption("נכסים דומים כרגע ביד2")
    with cols[2]:
        st.markdown("**🤖 סיכום AI**")
        st.caption("ניתוח מקצועי של Claude")


def _run_analysis(
    address: str,
    property_type: str,
    rooms: float | None,
    floor: int | None,
    size_sqm: float | None,
    building_year: int | None,
    price: float | None,
    include_ai: bool,
):
    """Execute the market analysis with progress tracking."""
    progress_bar = st.progress(0, text="מתחיל ניתוח שוק...")
    status_text = st.empty()

    def progress_callback(message: str, pct: float):
        progress_bar.progress(pct, text=message)
        status_text.info(message)

    try:
        report = asyncio.run(
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

        # Store report in session state
        st.session_state["report"] = report

        # Show errors if any
        if report.errors:
            with st.expander("⚠️ שגיאות שנתקלנו בהן", expanded=False):
                for err in report.errors:
                    st.warning(err)

        _display_report(report)

    except Exception as e:
        st.error(f"שגיאה בהרצת הניתוח: {e}")
        progress_bar.empty()
        status_text.empty()


def _display_report(report: MarketAnalysisReport):
    """Display the full market analysis report."""

    # --- Header Metrics ---
    st.markdown("---")
    st.subheader(f"📊 דו\"ח ניתוח שוק: {report.subject_address}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("עסקאות שנמצאו", report.total_transactions)
    with col2:
        st.metric("נכסים מפורסמים", report.total_listings)
    with col3:
        avg_sqm = report.avg_price_per_sqm_street
        st.metric("ממוצע למ\"ר", f"{avg_sqm:,.0f} ש\"ח" if avg_sqm else "N/A")
    with col4:
        if report.value_estimation:
            st.metric("הערכת שווי", report.value_estimation.formatted_range)
        else:
            st.metric("הערכת שווי", "N/A")

    st.markdown("---")

    # --- PDF Download ---
    col_pdf, col_info = st.columns([1, 3])
    with col_pdf:
        try:
            pdf_buffer = generate_pdf(report)
            safe_addr = report.subject_address.replace(" ", "_").replace(",", "")
            st.download_button(
                label="📄 הורד דו\"ח PDF",
                data=pdf_buffer,
                file_name=f"market_analysis_{safe_addr}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"שגיאה ביצירת PDF: {e}")
    with col_info:
        st.caption(
            f"סוג נכס: {report.subject_property_type} | "
            f"עיר: {report.subject_city} | "
            f"מקורות: {', '.join(report.data_sources_used)}"
        )

    # --- Tabs ---
    tabs = st.tabs([
        "📋 עסקאות",
        "🏢 קומה vs מחיר",
        "🏗️ ישן vs חדש",
        "📈 מגמות",
        "🏘️ מפורסמים",
        "💰 הערכת שווי",
        "🤖 סיכום AI",
    ])

    # --- Tab 1: Transactions ---
    with tabs[0]:
        _render_transactions_tab(report)

    # --- Tab 2: Floor Analysis ---
    with tabs[1]:
        _render_floor_tab(report)

    # --- Tab 3: Building Age ---
    with tabs[2]:
        _render_age_tab(report)

    # --- Tab 4: Price Trends ---
    with tabs[3]:
        _render_trends_tab(report)

    # --- Tab 5: Current Listings ---
    with tabs[4]:
        _render_listings_tab(report)

    # --- Tab 6: Value Estimation ---
    with tabs[5]:
        _render_value_tab(report)

    # --- Tab 7: AI Summary ---
    with tabs[6]:
        _render_ai_tab(report)


def _render_transactions_tab(report: MarketAnalysisReport):
    """Render the transactions data tab."""
    st.subheader("עסקאות דומות שנמצאו")

    if not report.transactions:
        st.info("לא נמצאו עסקאות")
        return

    # Convert to DataFrame
    data = []
    for tx in report.transactions:
        data.append({
            "כתובת": tx.address,
            "מחיר (ש\"ח)": int(tx.deal_amount),
            "חדרים": tx.rooms or "",
            "קומה": tx.floor if tx.floor is not None else "",
            "מ\"ר": int(tx.size_sqm) if tx.size_sqm else "",
            "מחיר/מ\"ר": int(tx.price_per_sqm) if tx.price_per_sqm else "",
            "שנת בנייה": tx.building_year or "",
            "תאריך": tx.formatted_date,
        })

    df = pd.DataFrame(data)

    # Display statistics
    col1, col2, col3 = st.columns(3)
    with col1:
        prices = [tx.deal_amount for tx in report.transactions if tx.deal_amount > 0]
        if prices:
            st.metric("מחיר ממוצע", f"{int(sum(prices)/len(prices)):,} ש\"ח")
    with col2:
        sqm = [tx.price_per_sqm for tx in report.transactions if tx.price_per_sqm]
        if sqm:
            st.metric("ממוצע למ\"ר", f"{int(sum(sqm)/len(sqm)):,} ש\"ח")
    with col3:
        if prices:
            st.metric("טווח", f"{int(min(prices)):,} - {int(max(prices)):,}")

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Price distribution chart
    if len(report.transactions) >= 3:
        sqm_prices = [tx.price_per_sqm for tx in report.transactions if tx.price_per_sqm]
        if sqm_prices:
            fig = px.histogram(
                x=sqm_prices,
                nbins=15,
                labels={"x": "מחיר למ\"ר (ש\"ח)", "y": "מספר עסקאות"},
                title="התפלגות מחיר למ\"ר",
                color_discrete_sequence=["#667eea"],
            )
            fig.update_layout(
                font=dict(family="Arial, sans-serif"),
                xaxis_title="מחיר למ\"ר (ש\"ח)",
                yaxis_title="מספר עסקאות",
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_floor_tab(report: MarketAnalysisReport):
    """Render floor price analysis tab."""
    st.subheader("ניתוח מחיר לפי קומה")

    if not report.floor_analysis:
        st.info("אין מספיק נתונים לניתוח לפי קומה")
        return

    # Bar chart
    floors = [f"קומה {fa.floor}" for fa in report.floor_analysis]
    avg_prices = [fa.avg_price_per_sqm for fa in report.floor_analysis]
    counts = [fa.transaction_count for fa in report.floor_analysis]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=floors,
        y=avg_prices,
        text=[f"{p:,.0f}" for p in avg_prices],
        textposition="auto",
        marker_color="#2ecc71",
        hovertemplate="<b>%{x}</b><br>ממוצע למ\"ר: %{y:,.0f} ש\"ח<extra></extra>",
    ))
    fig.update_layout(
        title="ממוצע מחיר למ\"ר לפי קומה",
        xaxis_title="קומה",
        yaxis_title="מחיר ממוצע למ\"ר (ש\"ח)",
        font=dict(family="Arial, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Data table
    floor_data = []
    for fa in report.floor_analysis:
        floor_data.append({
            "קומה": fa.floor,
            "ממוצע למ\"ר (ש\"ח)": f"{int(fa.avg_price_per_sqm):,}",
            "ממוצע סה\"כ (ש\"ח)": fa.formatted_avg_price,
            "מספר עסקאות": fa.transaction_count,
        })
    st.dataframe(pd.DataFrame(floor_data), use_container_width=True, hide_index=True)


def _render_age_tab(report: MarketAnalysisReport):
    """Render building age analysis tab."""
    st.subheader("השוואת ישן מול חדש")

    if not report.building_age_analysis:
        st.info("אין מספיק נתונים לניתוח לפי גיל בניין")
        return

    # Bar chart with premium annotation
    categories = [ba.category for ba in report.building_age_analysis]
    avg_prices = [ba.avg_price_per_sqm for ba in report.building_age_analysis]
    premiums = [ba.price_premium_pct for ba in report.building_age_analysis]

    colors = []
    for p in premiums:
        if p is None:
            colors.append("#95a5a6")
        elif p > 0:
            colors.append("#2ecc71")
        else:
            colors.append("#e74c3c")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=avg_prices,
        text=[f"{p:,.0f}\n({pr:+.1f}%)" if pr is not None else f"{p:,.0f}" for p, pr in zip(avg_prices, premiums)],
        textposition="auto",
        marker_color=colors,
    ))
    fig.update_layout(
        title="ממוצע מחיר למ\"ר לפי גיל בניין",
        xaxis_title="קטגוריית גיל",
        yaxis_title="מחיר ממוצע למ\"ר (ש\"ח)",
        font=dict(family="Arial, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary cards
    cols = st.columns(len(report.building_age_analysis))
    for i, ba in enumerate(report.building_age_analysis):
        with cols[i]:
            premium_text = ""
            if ba.price_premium_pct is not None:
                emoji = "📈" if ba.price_premium_pct > 0 else "📉"
                premium_text = f"{emoji} {ba.price_premium_pct:+.1f}%"
            st.metric(
                ba.category,
                f"{int(ba.avg_price_per_sqm):,} ש\"ח/מ\"ר",
                premium_text,
            )
            st.caption(f"{ba.transaction_count} עסקאות")


def _render_trends_tab(report: MarketAnalysisReport):
    """Render price trends tab."""
    st.subheader("מגמות מחיר לאורך זמן")

    if not report.price_trends:
        st.info("אין מספיק נתונים למגמות מחיר")
        return

    # Line chart
    periods = [pt.period for pt in report.price_trends]
    prices = [pt.avg_price_per_sqm for pt in report.price_trends]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=periods,
        y=prices,
        mode="lines+markers",
        line=dict(color="#e67e22", width=3),
        marker=dict(size=8),
        hovertemplate="<b>%{x}</b><br>ממוצע למ\"ר: %{y:,.0f} ש\"ח<extra></extra>",
    ))
    fig.update_layout(
        title="מגמת מחיר למ\"ר לפי רבעון",
        xaxis_title="תקופה",
        yaxis_title="מחיר ממוצע למ\"ר (ש\"ח)",
        font=dict(family="Arial, sans-serif"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary metrics
    if len(report.price_trends) >= 2:
        first = report.price_trends[0]
        last = report.price_trends[-1]
        total_change = ((last.avg_price_per_sqm - first.avg_price_per_sqm) / first.avg_price_per_sqm) * 100

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                f"מחיר {first.period}",
                f"{int(first.avg_price_per_sqm):,} ש\"ח/מ\"ר",
            )
        with col2:
            st.metric(
                f"מחיר {last.period}",
                f"{int(last.avg_price_per_sqm):,} ש\"ח/מ\"ר",
            )
        with col3:
            st.metric(
                "שינוי מצטבר",
                f"{total_change:+.1f}%",
            )


def _render_listings_tab(report: MarketAnalysisReport):
    """Render current Yad2 listings tab."""
    st.subheader("נכסים מפורסמים כרגע (יד2)")

    if not report.current_listings:
        st.info("לא נמצאו נכסים מפורסמים דומים")
        return

    data = []
    for l in report.current_listings:
        data.append({
            "כתובת": l.address,
            "מחיר (ש\"ח)": int(l.price) if l.price > 0 else "",
            "חדרים": l.rooms or "",
            "קומה": l.floor if l.floor is not None else "",
            "מ\"ר": int(l.size_sqm) if l.size_sqm else "",
            "מחיר/מ\"ר": int(l.price_per_sqm) if l.price_per_sqm else "",
            "סוג": l.property_type,
        })

    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)

    # Comparison chart: listings vs transactions
    if report.transactions:
        tx_sqm = [tx.price_per_sqm for tx in report.transactions if tx.price_per_sqm]
        list_sqm = [l.price_per_sqm for l in report.current_listings if l.price_per_sqm]

        if tx_sqm and list_sqm:
            fig = go.Figure()
            fig.add_trace(go.Box(
                y=tx_sqm,
                name="עסקאות (נסגרו)",
                marker_color="#3498db",
            ))
            fig.add_trace(go.Box(
                y=list_sqm,
                name="מפורסמים (יד2)",
                marker_color="#e74c3c",
            ))
            fig.update_layout(
                title="השוואת מחיר למ\"ר: עסקאות vs מפורסמים",
                yaxis_title="מחיר למ\"ר (ש\"ח)",
                font=dict(family="Arial, sans-serif"),
            )
            st.plotly_chart(fig, use_container_width=True)


def _render_value_tab(report: MarketAnalysisReport):
    """Render value estimation tab."""
    st.subheader("הערכת שווי")

    if not report.value_estimation:
        st.warning("אין מספיק נתונים להערכת שווי (נדרשות לפחות 3 עסקאות דומות)")
        return

    ve = report.value_estimation

    # Big value display
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("מחיר מינימלי", f"{int(ve.estimated_price_low):,} ש\"ח")
    with col2:
        st.metric("מחיר מוערך", f"{int(ve.estimated_price_mid):,} ש\"ח")
    with col3:
        st.metric("מחיר מקסימלי", f"{int(ve.estimated_price_high):,} ש\"ח")

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.metric("מחיר ממוצע למ\"ר", f"{int(ve.estimated_price_per_sqm):,} ש\"ח")
    with col2:
        confidence_emoji = {"גבוה": "🟢", "בינוני": "🟡", "נמוך": "🔴"}.get(ve.confidence, "⚪")
        st.metric("רמת ביטחון", f"{confidence_emoji} {ve.confidence}")

    st.caption(f"מבוסס על {ve.comparable_count} נכסים | {ve.methodology}")

    # Gauge chart
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=ve.estimated_price_mid,
        number={"suffix": " ש\"ח", "valueformat": ",.0f"},
        gauge={
            "axis": {"range": [ve.estimated_price_low * 0.8, ve.estimated_price_high * 1.2]},
            "bar": {"color": "#667eea"},
            "steps": [
                {"range": [ve.estimated_price_low * 0.8, ve.estimated_price_low], "color": "#fadbd8"},
                {"range": [ve.estimated_price_low, ve.estimated_price_high], "color": "#d5f5e3"},
                {"range": [ve.estimated_price_high, ve.estimated_price_high * 1.2], "color": "#fadbd8"},
            ],
            "threshold": {
                "line": {"color": "red", "width": 4},
                "thickness": 0.75,
                "value": ve.estimated_price_mid,
            },
        },
        title={"text": "הערכת שווי הנכס"},
    ))
    fig.update_layout(height=350, font=dict(family="Arial, sans-serif"))
    st.plotly_chart(fig, use_container_width=True)


def _render_ai_tab(report: MarketAnalysisReport):
    """Render AI summary tab."""
    st.subheader("🤖 ניתוח AI")

    if not report.ai_summary:
        st.info("סיכום AI לא נוצר. סמן 'כלול סיכום AI' בהגדרות.")
        return

    st.markdown(report.ai_summary)


if __name__ == "__main__":
    main()
