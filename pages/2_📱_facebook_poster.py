"""Streamlit page for Facebook posting - wrapper around existing app.py."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700&display=swap');
    html, body, [class*="css"] { font-family: 'Heebo', sans-serif; }
    .rtl-text { direction: rtl; text-align: right; }
    .stButton > button { width: 100%; border-radius: 10px; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📱 מפרסם נכסים לפייסבוק")
st.markdown("**Real Capital** | רוי עידו")
st.divider()

st.warning(
    "⚠️ כלי זה דורש חיבור מקומי לפייסבוק דרך Playwright.\n\n"
    "לשימוש בפרסום, הרץ מקומית:\n"
    "```\nstreamlit run src/app.py\n```"
)

st.info(
    "הכלי הזה זמין רק בהרצה מקומית כי הוא דורש:\n"
    "- חיבור לפייסבוק עם דפדפן (Playwright)\n"
    "- session cookies מקומיים\n"
    "- גישה ל-Notion API\n\n"
    "**ניתוח שוק** ← פתוח לכולם באינטרנט\n"
    "**פרסום לפייסבוק** ← רק מקומי"
)
