"""Real Capital – כלי פרסום אוטומטי לפייסבוק."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st

st.set_page_config(
    page_title="פרסום לפייסבוק | Real Capital",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    font-family: 'Heebo', sans-serif;
    background-color: #F5F7FA;
    direction: rtl;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ─── Navbar ─── */
.nav-bar {
    background: #0B1F3B;
    padding: 0 3rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    box-shadow: 0 2px 20px rgba(0,0,0,0.3);
}
.nav-logo { display: flex; align-items: center; gap: 0.75rem; }
.nav-logo-mark {
    width: 38px; height: 38px;
    background: #1C3F94;
    border-radius: 8px;
    border: 1.5px solid #C9A84C;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 900; color: #FFFFFF;
    font-family: Georgia, serif;
}
.nav-logo-text .logo-real  { color: #FFF;    font-size: 1rem;   font-weight: 800; display: block; line-height: 1; }
.nav-logo-text .logo-cap   { color: #C9A84C; font-size: 0.72rem; font-weight: 400; letter-spacing: 2px; text-transform: uppercase; display: block; }
.nav-badge { background: rgba(201,168,76,0.15); color: #C9A84C; border: 1px solid rgba(201,168,76,0.4); padding: 0.3rem 1rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.back-link { color: rgba(255,255,255,0.6); font-size: 0.85rem; text-decoration: none; }
.back-link:hover { color: #FFF; }

/* ─── Hero banner ─── */
.fb-hero {
    background: linear-gradient(135deg, #0B1F3B 0%, #1a3a6e 60%, #0B1F3B 100%);
    padding: 4rem 3rem 3rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.fb-hero::before {
    content: '';
    position: absolute;
    inset: 0;
    background: repeating-linear-gradient(
        45deg,
        transparent,
        transparent 40px,
        rgba(255,255,255,0.015) 40px,
        rgba(255,255,255,0.015) 80px
    );
}
.fb-hero-icon {
    width: 80px; height: 80px;
    background: linear-gradient(135deg, #1877F2, #0d5dbf);
    border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: 2.5rem;
    margin: 0 auto 1.5rem;
    box-shadow: 0 8px 32px rgba(24,119,242,0.4);
    position: relative;
}
.fb-hero h1 { color: #FFFFFF; font-size: 2.6rem; font-weight: 900; line-height: 1.2; margin-bottom: 0.75rem; position: relative; }
.fb-hero p { color: rgba(255,255,255,0.65); font-size: 1.05rem; max-width: 560px; margin: 0 auto; font-weight: 300; line-height: 1.7; position: relative; }
.status-badge {
    display: inline-flex; align-items: center; gap: 0.5rem;
    background: rgba(255,193,7,0.15);
    color: #FFC107;
    border: 1px solid rgba(255,193,7,0.4);
    padding: 0.4rem 1.2rem;
    border-radius: 20px;
    font-size: 0.85rem; font-weight: 600;
    margin-bottom: 1.5rem;
    position: relative;
}
.status-dot {
    width: 8px; height: 8px;
    background: #FFC107;
    border-radius: 50%;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* ─── Content area ─── */
.content-wrap { max-width: 900px; margin: 0 auto; padding: 3rem 2rem; }

/* ─── Info card ─── */
.info-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    border: 1px solid #E8ECF0;
    box-shadow: 0 4px 24px rgba(11,31,59,0.06);
    margin-bottom: 1.5rem;
    direction: rtl;
    position: relative;
    overflow: hidden;
}
.info-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 4px; height: 100%;
}
.info-card.blue::before  { background: #1877F2; }
.info-card.navy::before  { background: #1C3F94; }
.info-card.gold::before  { background: #C9A84C; }
.info-card.green::before { background: #27AE60; }
.info-card h3 { color: #0B1F3B; font-size: 1.15rem; font-weight: 700; margin-bottom: 1rem; }
.info-card p  { color: #4A5568; font-size: 0.9rem; line-height: 1.7; }

/* ─── Why local section ─── */
.why-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin: 1rem 0; }
.why-item {
    background: #F8FAFC;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    display: flex; align-items: flex-start; gap: 0.75rem;
    direction: rtl;
    border: 1px solid #E8ECF0;
}
.why-icon { font-size: 1.5rem; flex-shrink: 0; margin-top: 0.1rem; }
.why-item h4 { color: #0B1F3B; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.25rem; }
.why-item p  { color: #6B7A8D; font-size: 0.82rem; line-height: 1.5; }

/* ─── Steps ─── */
.steps-wrap { margin: 1.25rem 0 0.5rem; }
.step-row {
    display: flex; align-items: flex-start; gap: 1.25rem;
    padding: 1rem 0;
    border-bottom: 1px solid #F0F2F7;
    direction: rtl;
}
.step-row:last-child { border-bottom: none; }
.step-num {
    width: 36px; height: 36px; flex-shrink: 0;
    background: #0B1F3B;
    color: #C9A84C;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 800; font-size: 0.9rem;
    font-family: Georgia, serif;
}
.step-content h4 { color: #0B1F3B; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.25rem; }
.step-content p  { color: #6B7A8D; font-size: 0.82rem; line-height: 1.5; }
.step-content code {
    background: #F0F2F7;
    color: #1C3F94;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-family: 'Courier New', monospace;
    display: inline-block;
    margin-top: 0.35rem;
}

/* ─── Feature list ─── */
.feat-list { list-style: none; }
.feat-list li {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.5rem 0;
    color: #4A5568; font-size: 0.9rem;
    border-bottom: 1px solid #F5F7FA;
    direction: rtl;
}
.feat-list li:last-child { border-bottom: none; }
.feat-list li .check { color: #1C3F94; font-weight: 700; font-size: 1rem; }

/* ─── Callout ─── */
.callout {
    background: linear-gradient(135deg, #EBF3FF, #F5F7FA);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    border: 1px solid rgba(28,63,148,0.15);
    display: flex; align-items: center; gap: 1rem;
    direction: rtl;
    margin-top: 1.5rem;
}
.callout-icon { font-size: 2rem; flex-shrink: 0; }
.callout-text h4 { color: #1C3F94; font-size: 0.95rem; font-weight: 700; margin-bottom: 0.25rem; }
.callout-text p  { color: #4A5568; font-size: 0.85rem; line-height: 1.6; }

/* ─── Section header ─── */
.section-header { margin: 0 0 1.5rem; direction: rtl; }
.section-header h2 { color: #0B1F3B; font-size: 1.5rem; font-weight: 800; margin-bottom: 0.25rem; }
.section-header p  { color: #6B7A8D; font-size: 0.9rem; }

/* ─── Footer ─── */
.footer { background: #0B1F3B; padding: 2rem 3rem; text-align: center; margin-top: 3rem; }
.footer p { color: rgba(255,255,255,0.4); font-size: 0.8rem; }
.footer strong { color: #C9A84C; }
</style>
""", unsafe_allow_html=True)

# ─── Navbar ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="nav-bar">
    <div class="nav-logo">
        <div class="nav-logo-mark">R</div>
        <div class="nav-logo-text">
            <span class="logo-real">Real Capital</span>
            <span class="logo-cap">Professional Real Estate</span>
        </div>
    </div>
    <a class="back-link" href="/">← חזרה לדשבורד</a>
    <span class="nav-badge">רוי עידו | מתווך</span>
</div>
""", unsafe_allow_html=True)

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="fb-hero">
    <div class="fb-hero-icon">📱</div>
    <div class="status-badge">
        <span class="status-dot"></span>
        זמין בהרצה מקומית בלבד
    </div>
    <h1>פרסום אוטומטי לפייסבוק</h1>
    <p>פרסם נכסים אוטומטית לקבוצות פייסבוק ישירות מ-Notion — עם תמונות, תיאור מעוצב וחתימה אישית.</p>
</div>
""", unsafe_allow_html=True)

# ─── Main content ─────────────────────────────────────────────────────────────
st.markdown('<div class="content-wrap">', unsafe_allow_html=True)

# Why local only
st.markdown("""
<div class="section-header">
    <h2>🔒 למה רק מקומית?</h2>
    <p>פרסום לפייסבוק דורש גישה ישירה לדפדפן שלך — זה לא אפשרי דרך שרת ענן</p>
</div>
<div class="why-grid">
    <div class="why-item">
        <span class="why-icon">🍪</span>
        <div>
            <h4>Session Cookies של פייסבוק</h4>
            <p>הכניסה לפייסבוק מצריכה cookies אישיים שקיימים רק בדפדפן שלך — לא ניתן להעביר אותם לשרת ענן.</p>
        </div>
    </div>
    <div class="why-item">
        <span class="why-icon">🤖</span>
        <div>
            <h4>Playwright – אוטומציה של דפדפן</h4>
            <p>הכלי מפעיל דפדפן Chrome מקומי דרך Playwright שמנהל אוטומטית את הפרסום לקבוצות.</p>
        </div>
    </div>
    <div class="why-item">
        <span class="why-icon">🛡️</span>
        <div>
            <h4>אבטחת חשבון</h4>
            <p>פייסבוק חוסמת כניסות מ-IP של שרתים. הפרסום ממחשבך האישי נראה לגמרי רגיל.</p>
        </div>
    </div>
    <div class="why-item">
        <span class="why-icon">📂</span>
        <div>
            <h4>גישה לתמונות מקומיות</h4>
            <p>התמונות נשמרות ב-Notion ומורדות ישירות למחשב לפני הפרסום — דורש דיסק מקומי.</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Features
st.markdown("""
<div class="info-card blue" style="margin-top:1.5rem">
    <h3>✨ מה הכלי עושה</h3>
    <ul class="feat-list">
        <li><span class="check">✓</span> מתחבר ל-Notion Database שלך ומושך נכסים חדשים לפרסום</li>
        <li><span class="check">✓</span> מייצר תיאור נכס מעוצב עם כל הפרטים — חדרים, שטח, קומה, מחיר</li>
        <li><span class="check">✓</span> מוסיף חתימה אישית ומספר טלפון בכל פוסט</li>
        <li><span class="check">✓</span> מעלה תמונות בצורה אוטומטית לפייסבוק</li>
        <li><span class="check">✓</span> מפרסם לרשימת קבוצות פייסבוק מוגדרת מראש</li>
        <li><span class="check">✓</span> שומר עיכובים אנושיים בין פרסומים כדי למנוע חסימה</li>
        <li><span class="check">✓</span> מדווח על הצלחה/כישלון לכל קבוצה</li>
    </ul>
</div>
""", unsafe_allow_html=True)

# Setup steps
st.markdown("""
<div class="info-card navy">
    <h3>🚀 איך להפעיל מקומית</h3>
    <div class="steps-wrap">
        <div class="step-row">
            <div class="step-num">1</div>
            <div class="step-content">
                <h4>שכפל את הפרויקט</h4>
                <p>פתח Terminal והרץ:</p>
                <code>git clone https://github.com/roy11ido/real-estate-market-analysis.git</code>
            </div>
        </div>
        <div class="step-row">
            <div class="step-num">2</div>
            <div class="step-content">
                <h4>התקן תלויות</h4>
                <code>pip install -r requirements.txt && playwright install chromium</code>
            </div>
        </div>
        <div class="step-row">
            <div class="step-num">3</div>
            <div class="step-content">
                <h4>הגדר משתני סביבה</h4>
                <p>צור קובץ <code>.env</code> עם:</p>
                <code>NOTION_TOKEN=secret_xxx<br/>NOTION_DB_ID=xxx<br/>ANTHROPIC_API_KEY=sk-ant-xxx</code>
            </div>
        </div>
        <div class="step-row">
            <div class="step-num">4</div>
            <div class="step-content">
                <h4>הרץ את האפליקציה</h4>
                <code>streamlit run app.py</code>
            </div>
        </div>
        <div class="step-row">
            <div class="step-num">5</div>
            <div class="step-content">
                <h4>כנס לפייסבוק ופרסם</h4>
                <p>פתח את עמוד "פרסום לפייסבוק", בחר נכסים מ-Notion ולחץ פרסם — הכלי יעשה הכל אוטומטית.</p>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Callout to CMA
st.markdown("""
<div class="callout">
    <span class="callout-icon">📊</span>
    <div class="callout-text">
        <h4>בינתיים — נסה ניתוח שוק השוואתי</h4>
        <p>כלי ניתוח השוק (CMA) פועל כאן ב-Cloud ומוכן לשימוש עכשיו. הפק דו"ח מקצועי לכל נכס תוך דקות.</p>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <div style="display:flex;align-items:center;justify-content:center;gap:0.75rem;margin-bottom:0.75rem;">
        <div style="width:32px;height:32px;background:#1C3F94;border-radius:6px;border:1px solid #C9A84C;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-size:1rem;font-weight:700;color:#fff;">R</div>
        <span style="color:#C9A84C;font-weight:700;font-size:1rem;">Real Capital</span>
    </div>
    <p>רוי עידו | 050-592-2642 | roy11ido@gmail.com</p>
    <p style="margin-top:0.5rem">© 2025 כל הזכויות שמורות</p>
</div>
""", unsafe_allow_html=True)
