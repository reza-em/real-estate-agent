from base64 import b64encode
from pathlib import Path


def _font_data(filename: str) -> str:
    path = Path(__file__).with_name("assets") / filename
    return b64encode(path.read_bytes()).decode("ascii")


FONT_CSS = f"""
<style>
@font-face {{
    font-family: "Yekan";
    src: url("data:font/woff2;base64,{_font_data('Yekan-Regular.woff2')}") format("woff2");
    font-weight: 400 600;
    font-style: normal;
    font-display: swap;
}}
@font-face {{
    font-family: "Yekan";
    src: url("data:font/woff2;base64,{_font_data('Yekan-Bold.woff2')}") format("woff2");
    font-weight: 700 900;
    font-style: normal;
    font-display: swap;
}}
</style>
"""


APP_CSS = FONT_CSS + """
<style>
@import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;500;600;700;800&display=swap');

:root {
    --brand: #0f766e;
    --brand-dark: #115e59;
    --brand-soft: #ecfdf5;
    --ink: #17202a;
    --muted: #64748b;
    --line: #e2e8f0;
    --surface: #ffffff;
    --canvas: #f8fafc;
}

html, body, [class*="css"], .stApp, input, textarea, button {
    font-family: "Yekan", "Vazirmatn", Tahoma, sans-serif !important;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    direction: rtl;
}

.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stMarkdownContainer"] p,
.stApp [data-testid="stMarkdownContainer"] h1,
.stApp [data-testid="stMarkdownContainer"] h2,
.stApp [data-testid="stMarkdownContainer"] h3,
.stApp [data-testid="stMarkdownContainer"] h4,
.stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stAlertContent"] {
    direction: rtl;
    text-align: right !important;
}

.stApp { background: var(--canvas); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { max-width: 1320px; padding-top: 2rem; }
[data-testid="stWidgetLabel"] p { font-weight: 600; color: #334155; }

.hero {
    direction: rtl;
    text-align: right;
    background: linear-gradient(135deg, #0f766e 0%, #115e59 55%, #134e4a 100%);
    border-radius: 24px;
    padding: 2.2rem 2.4rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 20px 45px rgba(15, 118, 110, .16);
}
.hero-kicker { font-size: .82rem; opacity: .78; font-weight: 700; letter-spacing: .04em; }
.hero h1 { font-size: 2rem; line-height: 1.5; margin: .35rem 0 .45rem; color: white; }
.hero p { max-width: 760px; margin: 0 0 0 auto; opacity: .86; line-height: 2; text-align: right; }

.section-title { direction: rtl; text-align: right; margin: 1.8rem 0 .8rem; }
.section-title h2 { font-size: 1.22rem; margin: 0; color: var(--ink); }
.section-title p { color: var(--muted); margin: .2rem 0 0; font-size: .88rem; }

[data-testid="stForm"] {
    direction: rtl;
    text-align: right;
    background: var(--surface);
    border: 1px solid var(--line) !important;
    border-radius: 20px !important;
    padding: 1.2rem 1.35rem .7rem;
    box-shadow: 0 8px 24px rgba(15, 23, 42, .04);
}

.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {
    border-radius: 12px !important;
    min-height: 45px;
    font-weight: 700 !important;
}
.stFormSubmitButton > button[kind="primary"], .stButton > button[kind="primary"] {
    background: var(--brand) !important;
    border-color: var(--brand) !important;
}
.stFormSubmitButton > button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {
    background: var(--brand-dark) !important;
    border-color: var(--brand-dark) !important;
}

[data-testid="stMetric"] {
    direction: rtl;
    text-align: right;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 1rem 1.1rem;
    box-shadow: 0 6px 18px rgba(15, 23, 42, .035);
}
[data-testid="stMetricLabel"] { color: var(--muted); }
[data-testid="stMetricValue"] { color: var(--ink); font-weight: 800; }
[data-testid="stMetricLabel"],
[data-testid="stMetricValue"],
[data-testid="stMetricDelta"] { justify-content: flex-start; text-align: right; }

.stApp input,
.stApp textarea,
.stApp [data-baseweb="select"] {
    direction: rtl;
    text-align: right;
}

.deal-card {
    position: relative;
    min-height: 270px;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 18px;
    padding: 1.2rem;
    box-shadow: 0 9px 25px rgba(15, 23, 42, .05);
    overflow: hidden;
}
.deal-card.best { border: 2px solid #14b8a6; background: linear-gradient(180deg, #f0fdfa 0%, #fff 45%); }
.deal-rank { color: var(--brand); font-size: .76rem; font-weight: 800; margin-bottom: .65rem; }
.deal-title { color: var(--ink); font-size: 1rem; font-weight: 800; line-height: 1.75; min-height: 3.5rem; }
.deal-meta { color: var(--muted); font-size: .82rem; margin-top: .45rem; }
.deal-price { color: var(--brand-dark); font-size: 1.05rem; font-weight: 800; margin-top: .8rem; }
.score-row { display: flex; align-items: center; gap: .65rem; margin-top: 1rem; }
.score-pill { background: var(--brand); color: white; border-radius: 999px; padding: .3rem .7rem; font-weight: 800; }
.score-track { height: 7px; flex: 1; background: #dbeafe; border-radius: 99px; overflow: hidden; }
.score-fill { height: 100%; background: linear-gradient(90deg, #14b8a6, #0f766e); border-radius: 99px; }
.deal-link { display: inline-block; margin-top: 1rem; color: var(--brand-dark) !important; font-weight: 700; text-decoration: none; }

.listing-card {
    background: white;
    border: 1px solid var(--line);
    border-right: 4px solid var(--brand);
    border-radius: 14px;
    padding: 1rem 1.1rem;
    margin: .65rem 0;
}
.listing-card h3 { font-size: .98rem; margin: 0 0 .35rem; color: var(--ink); }
.listing-card p { color: var(--muted); font-size: .84rem; line-height: 1.8; margin: .25rem 0; }
.listing-card strong { color: var(--brand-dark); }

.selected-property {
    background: linear-gradient(135deg, #fffbeb 0%, #ffffff 75%);
    border: 2px solid #f59e0b;
    border-radius: 18px;
    padding: 1.2rem 1.35rem;
    margin: 1rem 0;
    box-shadow: 0 10px 25px rgba(245, 158, 11, .1);
}
.selected-property h3 { margin: .35rem 0 .7rem; color: var(--ink); }
.selected-property p { color: var(--muted); line-height: 1.9; margin: .4rem 0; }
.selected-property a { color: var(--brand-dark) !important; font-weight: 800; }
.selected-label { color: #b45309; font-size: .8rem; font-weight: 800; }
.selected-grid { display: flex; flex-wrap: wrap; gap: .5rem 1.4rem; color: #475569; }

.map-legend {
    display: flex;
    gap: 1.2rem;
    flex-wrap: wrap;
    color: var(--muted);
    font-size: .82rem;
    margin: -.25rem 0 .75rem;
}
.map-legend span { display: inline-flex; align-items: center; gap: .4rem; }
.map-legend .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.map-legend .selected { background: #f59e0b; }
.map-legend .best { background: #dc2626; }
.map-legend .normal { background: #0f766e; }

.st-key-property_map { border-radius: 18px; overflow: hidden; border: 1px solid var(--line); }

.memory-bar {
    direction: rtl;
    display: flex;
    justify-content: flex-start;
    flex-wrap: wrap;
    gap: .55rem 1.4rem;
    background: #f0fdfa;
    border: 1px solid #ccfbf1;
    border-radius: 14px;
    padding: .78rem 1rem;
    margin-top: 1.75rem;
    color: #475569;
    font-size: .82rem;
}
.memory-bar strong { color: var(--brand-dark); }
.agent-query-summary {
    direction: rtl;
    text-align: right;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-right: 4px solid #2563eb;
    border-radius: 14px;
    padding: .9rem 1.1rem;
    margin: 1rem 0;
    color: #334155;
}
.agent-reason {
    direction: rtl;
    text-align: right;
    min-height: 74px;
    color: #475569;
    line-height: 1.85;
    margin: .6rem 0;
}

.auth-hero {
    direction: rtl;
    text-align: center;
    max-width: 760px;
    margin: 3rem auto 1.5rem;
    padding: 2.4rem;
    color: white;
    border-radius: 24px;
    background: linear-gradient(135deg, #0f766e, #134e4a);
    box-shadow: 0 20px 45px rgba(15, 118, 110, .18);
}
.auth-hero h1 { color: white; margin: .5rem 0; }
.auth-hero p { opacity: .85; margin: 0; }
.auth-brand { font-size: .86rem; font-weight: 800; opacity: .75; }
[data-testid="stTabs"] { max-width: 760px; margin: 0 auto; }
[data-testid="stTabs"] [data-baseweb="tab-list"] { justify-content: center; }
.user-identity {
    direction: rtl;
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 72px;
    text-align: right;
}
.user-identity strong { color: var(--ink); font-size: 1rem; }
.user-identity small { color: var(--muted); direction: ltr; text-align: right; }

[data-testid="stDataFrame"] { direction: rtl; border: 1px solid var(--line); border-radius: 16px; overflow: hidden; }
[data-testid="stAlert"] { direction: rtl; border-radius: 14px; }

@media (max-width: 700px) {
    [data-testid="stMainBlockContainer"] { padding: 1rem; }
    .hero { padding: 1.5rem; border-radius: 18px; }
    .hero h1 { font-size: 1.55rem; }
}
</style>
"""
