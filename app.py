"""Real Capital - דף בית ראשי."""
import streamlit as st

st.set_page_config(
    page_title="Real Capital | רוי עידו",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS גלובלי ─────────────────────────────────────────────────────────────
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

.nav-bar {
    background: #0B1F3B;
    padding: 0 3rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
    position: sticky;
    top: 0;
    z-index: 999;
    box-shadow: 0 2px 20px rgba(0,0,0,0.3);
}
.nav-logo { display: flex; align-items: center; gap: 0.75rem; text-decoration: none; }
.nav-logo-mark {
    width: 38px; height: 38px;
    background: #1C3F94;
    border-radius: 8px;
    border: 1.5px solid #C9A84C;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; font-weight: 900; color: #FFFFFF;
    font-family: Georgia, serif;
    flex-shrink: 0;
}
.nav-logo-text { line-height: 1; }
.nav-logo-text .logo-real { color: #FFFFFF; font-size: 1rem; font-weight: 800; display: block; }
.nav-logo-text .logo-capital { color: #C9A84C; font-size: 0.75rem; font-weight: 400; letter-spacing: 2px; display: block; text-transform: uppercase; }
.nav-links { display: flex; gap: 2rem; list-style: none; direction: rtl; }
.nav-links a { color: rgba(255,255,255,0.75); text-decoration: none; font-size: 0.9rem; font-weight: 500; }
.nav-links a:hover { color: #FFFFFF; }
.nav-badge { background: rgba(201,168,76,0.15); color: #C9A84C; border: 1px solid rgba(201,168,76,0.4); padding: 0.3rem 1rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }

.hero {
    background: linear-gradient(135deg, #0B1F3B 0%, #1C3F94 60%, #0B1F3B 100%);
    padding: 5rem 3rem 4rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.hero-tag {
    display: inline-block;
    background: rgba(74,144,217,0.2);
    color: #4A90D9;
    border: 1px solid rgba(74,144,217,0.4);
    padding: 0.3rem 1.2rem;
    border-radius: 20px;
    font-size: 0.85rem;
    font-weight: 600;
    margin-bottom: 1.5rem;
    letter-spacing: 1px;
}
.hero h1 { color: #FFFFFF; font-size: 3.2rem; font-weight: 900; line-height: 1.2; margin-bottom: 1rem; }
.hero h1 span { color: #4A90D9; }
.hero p { color: rgba(255,255,255,0.7); font-size: 1.1rem; max-width: 600px; margin: 0 auto 2.5rem; font-weight: 300; line-height: 1.7; }
.hero-stats {
    display: flex;
    justify-content: center;
    gap: 3rem;
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid rgba(255,255,255,0.1);
}
.hero-stat-num { color: #FFFFFF; font-size: 1.4rem; font-weight: 800; }
.hero-stat-label { color: rgba(255,255,255,0.5); font-size: 0.8rem; }

.section { padding: 4rem 3rem; max-width: 1200px; margin: 0 auto; }
.section-title { color: #0B1F3B; font-size: 1.8rem; font-weight: 800; margin-bottom: 0.5rem; text-align: right; }
.section-sub { color: #6B7A8D; font-size: 0.95rem; margin-bottom: 2.5rem; text-align: right; }

.tool-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }
.tool-card {
    background: #FFFFFF;
    border-radius: 16px;
    padding: 2.5rem;
    border: 1px solid #E8ECF0;
    box-shadow: 0 4px 24px rgba(11,31,59,0.06);
    transition: transform 0.2s, box-shadow 0.2s;
    direction: rtl;
    position: relative;
    overflow: hidden;
}
.tool-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 4px; height: 100%;
    background: #1C3F94;
}
.tool-card:hover { transform: translateY(-4px); box-shadow: 0 8px 40px rgba(11,31,59,0.12); }
.tool-card.secondary::before { background: #4A90D9; }
.tool-icon { font-size: 2.5rem; margin-bottom: 1rem; display: block; }
.tool-card h3 { color: #0B1F3B; font-size: 1.4rem; font-weight: 700; margin-bottom: 0.5rem; }
.tool-card p { color: #6B7A8D; font-size: 0.9rem; line-height: 1.7; margin-bottom: 1.5rem; }
.tool-features { list-style: none; margin-bottom: 2rem; }
.tool-features li { color: #4A5568; font-size: 0.85rem; padding: 0.35rem 0; display: flex; align-items: center; gap: 0.5rem; }
.tool-features li::before { content: '✓'; color: #1C3F94; font-weight: 700; }

.btn-primary {
    display: inline-block;
    background: #0B1F3B;
    color: #FFFFFF;
    padding: 0.75rem 1.75rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    text-decoration: none;
}
.btn-secondary {
    display: inline-block;
    background: transparent;
    color: #1C3F94;
    padding: 0.75rem 1.75rem;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 600;
    text-decoration: none;
    border: 2px solid #1C3F94;
}

.features-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
.feature-item {
    background: #FFFFFF;
    border-radius: 12px;
    padding: 1.5rem;
    text-align: center;
    border: 1px solid #E8ECF0;
}
.feature-item .icon { font-size: 1.8rem; margin-bottom: 0.75rem; }
.feature-item h4 { color: #0B1F3B; font-size: 0.9rem; font-weight: 700; margin-bottom: 0.3rem; }
.feature-item p { color: #6B7A8D; font-size: 0.78rem; line-height: 1.5; }

.footer { background: #0B1F3B; padding: 2rem 3rem; text-align: center; margin-top: 4rem; border-top: 1px solid rgba(201,168,76,0.2); }
.footer p { color: rgba(255,255,255,0.4); font-size: 0.8rem; }
.footer strong { color: #C9A84C; }
</style>
""", unsafe_allow_html=True)

# ─── Navigation ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="nav-bar">
    <div class="nav-logo">
        <div class="nav-logo-mark">R</div>
        <div class="nav-logo-text">
            <span class="logo-real">Real</span>
            <span class="logo-capital">Capital</span>
        </div>
    </div>
    <ul class="nav-links">
        <li><a href="#">דשבורד</a></li>
        <li><a href="/market_analysis">ניתוח שוק</a></li>
        <li><a href="#">נכסים</a></li>
        <li><a href="#">לקוחות</a></li>
    </ul>
    <span class="nav-badge">רוי עידו | מתווך</span>
</div>
""", unsafe_allow_html=True)

# ─── Hero ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div style="display:flex;align-items:center;justify-content:center;gap:1rem;margin-bottom:1.5rem;">
        <div style="width:56px;height:56px;background:#1C3F94;border-radius:12px;border:2px solid #C9A84C;display:flex;align-items:center;justify-content:center;font-family:Georgia,serif;font-size:1.8rem;font-weight:700;color:#fff;">R</div>
        <div style="text-align:right;">
            <div style="color:#fff;font-size:1.4rem;font-weight:800;line-height:1;">Real Capital</div>
            <div style="color:#C9A84C;font-size:0.7rem;letter-spacing:3px;text-transform:uppercase;">Professional Real Estate</div>
        </div>
    </div>
    <div class="hero-tag">⚡ כלי נדל"ן חכמים</div>
    <h1>פלטפורמת <span>ניהול נדל"ן</span><br/>מקצועית</h1>
    <p>כל הכלים שמתווך מוביל צריך — ניתוח שוק מעמיק, נתוני עסקאות אמיתיים, וסיכום AI חכם — במקום אחד.</p>
    <div class="hero-stats">
        <div>
            <div class="hero-stat-num">nadlan.gov.il</div>
            <div class="hero-stat-label">מקור נתוני עסקאות</div>
        </div>
        <div>
            <div class="hero-stat-num">יד2</div>
            <div class="hero-stat-label">נכסים מפורסמים</div>
        </div>
        <div>
            <div class="hero-stat-num">Claude AI</div>
            <div class="hero-stat-label">סיכום אינטליגנטי</div>
        </div>
        <div>
            <div class="hero-stat-num">PDF</div>
            <div class="hero-stat-label">דו"ח מקצועי</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Tools ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section">
    <div class="section-title">🛠️ הכלים שלנו</div>
    <div class="section-sub">בחר את הכלי המתאים לצרכי העבודה שלך</div>
    <div class="tool-grid">
        <div class="tool-card">
            <span class="tool-icon">📊</span>
            <h3>ניתוח שוק השוואתי (CMA)</h3>
            <p>הפק דו"ח ניתוח שוק מקיף לכל נכס — עסקאות אמיתיות, ניתוח קומות, השוואת ישן/חדש, מגמות שוק והערכת שווי.</p>
            <ul class="tool-features">
                <li>עסקאות מ-nadlan.gov.il</li>
                <li>נכסים מפורסמים מיד2</li>
                <li>ניתוח מחיר לפי קומה וגיל בניין</li>
                <li>מגמות שוק — עיר, שכונה, רחוב</li>
                <li>הערכת שווי + סיכום Claude AI</li>
                <li>ייצוא PDF מקצועי</li>
            </ul>
            <a href="/market_analysis" class="btn-primary">פתח ניתוח שוק ←</a>
        </div>
        <div class="tool-card secondary">
            <span class="tool-icon">📱</span>
            <h3>פרסום אוטומטי לפייסבוק</h3>
            <p>פרסם נכסים אוטומטית לקבוצות פייסבוק ישירות מ-Notion — עם תמונות, תיאור מעוצב וחתימה אישית.</p>
            <ul class="tool-features">
                <li>חיבור ל-Notion Database</li>
                <li>פרסום לקבוצות מרובות</li>
                <li>תבניות תוכן חכמות</li>
                <li>עיכובים אנושיים בין פרסומים</li>
                <li>דיווח מקיף על תוצאות</li>
                <li>זמין בהרצה מקומית בלבד</li>
            </ul>
            <a href="/facebook_poster" class="btn-secondary">הסבר על הכלי ←</a>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Features ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="section" style="padding-top:0">
    <div class="section-title">✨ יכולות מרכזיות</div>
    <div class="section-sub">מה הופך את הפלטפורמה לכלי העבודה האידיאלי של מתווך מוביל</div>
    <div class="features-grid">
        <div class="feature-item">
            <div class="icon">🔍</div>
            <h4>נתוני שוק אמיתיים</h4>
            <p>עסקאות ממשלתיות מאומתות מנדל"ן.gov.il</p>
        </div>
        <div class="feature-item">
            <div class="icon">📈</div>
            <h4>ניתוח מעמיק</h4>
            <p>קומה, גיל בניין, מגמות מחיר לאורך זמן</p>
        </div>
        <div class="feature-item">
            <div class="icon">🤖</div>
            <h4>סיכום Claude AI</h4>
            <p>ניתוח מקצועי חכם בעברית</p>
        </div>
        <div class="feature-item">
            <div class="icon">📄</div>
            <h4>דו"ח PDF</h4>
            <p>דו"ח מקצועי מלא להורדה ושיתוף</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Footer ──────────────────────────────────────────────────────────────────
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
