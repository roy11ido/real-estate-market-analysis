"""
Real Estate Tools - Main Entry Point
=====================================
Streamlit multipage app for real estate agents.
Serves as the home/landing page.
"""

import streamlit as st

# --- Page Configuration ---
st.set_page_config(
    page_title="Real Capital - כלי נדל\"ן",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Heebo', sans-serif;
    }

    .main-title {
        text-align: center;
        padding: 2rem 0 1rem;
    }
    .main-title h1 {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .main-title p {
        font-size: 1.2rem;
        color: #666;
    }

    .tool-card {
        background: white;
        border-radius: 16px;
        padding: 2rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s, box-shadow 0.2s;
        direction: rtl;
        height: 100%;
    }
    .tool-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
    }
    .tool-card h3 {
        font-size: 1.4rem;
        margin: 1rem 0 0.5rem;
        color: #1a1a2e;
    }
    .tool-card p {
        color: #666;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .tool-icon {
        font-size: 3rem;
    }

    .footer {
        text-align: center;
        padding: 2rem 0;
        color: #999;
        font-size: 0.85rem;
        border-top: 1px solid #eee;
        margin-top: 3rem;
    }

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def main():
    # --- Header ---
    st.markdown(
        """
        <div class="main-title">
            <h1>🏠 Real Capital</h1>
            <p>כלי נדל"ן חכמים למתווכים | רוי עידו</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()

    # --- Tool Cards ---
    col1, col2 = st.columns(2, gap="large")

    with col1:
        st.markdown(
            """
            <div class="tool-card">
                <div class="tool-icon">📊</div>
                <h3>ניתוח שוק השוואתי</h3>
                <p>
                    הפק דו"ח ניתוח שוק מקיף לכל נכס.<br>
                    כולל עסקאות מ-nadlan.gov.il, נכסים מפורסמים מיד2,
                    ניתוח מחיר לפי קומה וגיל בניין, מגמות שוק,
                    הערכת שווי, וסיכום AI מקצועי.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link("pages/1_📊_market_analysis.py", label="פתח ניתוח שוק →", use_container_width=True)

    with col2:
        st.markdown(
            """
            <div class="tool-card">
                <div class="tool-icon">📱</div>
                <h3>פרסום לפייסבוק</h3>
                <p>
                    פרסם נכסים אוטומטית לקבוצות פייסבוק.<br>
                    בחר נכסים מ-Notion, צפה בתצוגה מקדימה,
                    ופרסם בלחיצה אחת עם תמונות ותיאור מעוצב.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.page_link("pages/2_📱_facebook_poster.py", label="פתח מפרסם FB →", use_container_width=True)

    # --- Features Overview ---
    st.divider()
    st.markdown("### ✨ מה הכלים מציעים?")

    features = st.columns(4)

    with features[0]:
        st.markdown("**🔍 נתוני שוק אמיתיים**")
        st.caption("עסקאות ממשלתיות מ-nadlan.gov.il + נכסים מפורסמים מיד2")

    with features[1]:
        st.markdown("**📈 ניתוח מעמיק**")
        st.caption("השוואת מחירים לפי קומה, גיל בניין, מגמות שוק")

    with features[2]:
        st.markdown("**🤖 סיכום AI**")
        st.caption("ניתוח מקצועי אוטומטי עם Claude AI")

    with features[3]:
        st.markdown("**📄 דו\"ח PDF**")
        st.caption("הורדת דו\"ח מעוצב לשליחה ללקוחות")

    # --- Footer ---
    st.markdown(
        """
        <div class="footer">
            Real Capital | רוי עידו | 050-592-2642 | roy11ido@gmail.com
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
