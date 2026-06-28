from __future__ import annotations
import streamlit.components.v1 as components
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from analyzer import analyze
from db import save_listings
from scraper import CITY_IDS, DivarProvider


load_dotenv()

st.set_page_config(
    page_title="AI Real Estate Agent",
    page_icon="🏡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>

            
            /* ---------- Sidebar ---------- */

div[data-testid="stSidebar"]{
    background:#ffffff;
    border-right:1px solid #ececec;
}

div[data-testid="stSidebar"] h1,
div[data-testid="stSidebar"] h2,
div[data-testid="stSidebar"] h3{
    color:#2563eb;
}

div[data-testid="stSidebar"] label{
    font-weight:600;
    color:#333;
}

div[data-baseweb="select"]{
    border-radius:10px;
}

input{
    border-radius:10px !important;
}

textarea{
    border-radius:10px !important;
}

section[data-testid="stSidebar"]{
    padding-top:10px;
}
            

.stApp{
    background:#f6f8fc;
}

.main .block-container{
    padding-top:1rem;
    padding-bottom:2rem;
    max-width:1400px;
}

.hero{
    background:linear-gradient(135deg,#2563eb,#0ea5e9);
    color:white;
    padding:35px;
    border-radius:18px;
    margin-bottom:25px;
    box-shadow:0 10px 30px rgba(0,0,0,.15);
}

.hero h1{
    margin:0;
    font-size:40px;
    font-weight:700;
}

.hero p{
    margin-top:10px;
    font-size:18px;
}

div[data-testid="stSidebar"]{
    background:#ffffff;
    border-right:1px solid #ececec;
}

.stButton>button{
    width:100%;
    height:48px;
    border-radius:10px;
    font-size:17px;
    font-weight:bold;
}

.stDownloadButton>button{
    width:100%;
    border-radius:10px;
}

</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="hero">

<h1>🏡 AI Real Estate Agent</h1>

<p>
هوشمندانه بهترین خانه را پیدا کن، آگهی‌ها را مقایسه کن و با کمک هوش مصنوعی تصمیم بگیر.
</p>

</div>
""", unsafe_allow_html=True)


with st.sidebar:

    st.markdown("## 🔎 فیلترهای جستجو")

    st.markdown("---")

    city = st.selectbox(
        "📍 شهر",
        list(CITY_IDS)
    )

    max_price_billion = st.number_input(
        "💰 حداکثر بودجه (میلیارد تومان)",
        min_value=0.1,
        max_value=1000.0,
        value=10.0,
        step=0.5
    )

    pages = st.slider(
        "📄 تعداد صفحات بررسی",
        1,
        10,
        2
    )

    preferences = st.text_area(
        "✨ ویژگی‌های دلخواه",
        height=120,
        placeholder="""مثال:
✅ حداقل ۱۰۰ متر
✅ پارکینگ
✅ آسانسور
✅ انباری
✅ منطقه ۵
"""
    )

    st.markdown("---")

    use_ai = st.toggle(
        "🤖 تحلیل هوش مصنوعی",
        value=bool(os.getenv("OPENAI_API_KEY"))
    )

    st.markdown("")

    run = st.button(
        "🚀 شروع جستجو",
        type="primary",
        use_container_width=True
    )


if not os.getenv("OPENAI_API_KEY"):
    st.info("کلید OpenAI تنظیم نشده است؛ برنامه با امتیازدهی پایه اجرا می‌شود.")

if run:
    max_price = int(max_price_billion * 1_000_000_000)
    try:
        with st.spinner("در حال دریافت آگهی‌ها..."):
            listings = DivarProvider().search(city, max_price, pages)
            save_listings(listings)
        if not listings:
            st.warning("آگهی دارای قیمت در محدوده بودجه پیدا نشد.")
            st.stop()
        with st.spinner("در حال رتبه‌بندی..."):
            if not use_ai:
                old_key = os.environ.pop("OPENAI_API_KEY", None)
                try:
                    analyses = analyze(listings, max_price, preferences)
                finally:
                    if old_key:
                        os.environ["OPENAI_API_KEY"] = old_key
            else:
                analyses = analyze(listings, max_price, preferences)
        by_id = {item.external_id: item for item in analyses}
        rows = [
            {
                "امتیاز": by_id[item.external_id].score,
                "عنوان": item.title,
                "قیمت (تومان)": item.price,
                "موقعیت": item.location,
                "تحلیل": by_id[item.external_id].summary,
                "ریسک‌ها": "؛ ".join(by_id[item.external_id].risks),
                "لینک": item.url,
            }
            for item in listings
        ]
        
        frame = pd.DataFrame(rows).sort_values("امتیاز", ascending=False)

        st.success(f"✅ {len(frame)} آگهی پیدا شد")

        st.download_button(
            "⬇ دانلود CSV",
            frame.to_csv(index=False).encode("utf-8-sig"),
            "listings.csv",
            "text/csv",
        )

        st.markdown("---")

        for _, row in frame.iterrows():

            score = row["امتیاز"]

            if score >= 9:
                color = "#16a34a"
            elif score >= 7:
                color = "#2563eb"
            elif score >= 5:
                color = "#f59e0b"
            else:
                color = "#dc2626"

            st.markdown(
                f"""
        <div style="background:white;
        padding:20px;
        border-radius:18px;
        margin-bottom:18px;
        box-shadow:0 8px 20px rgba(0,0,0,.08);
        border-left:8px solid {color};">

        <h3 style="margin-bottom:8px;">
        🏠 {row["عنوان"]}
        </h3>

        <p style="font-size:18px;">
        💰 <b>{row["قیمت (تومان)"]:,}</b> تومان
        </p>

        <p>
        📍 {row["موقعیت"]}
        </p>

        <p>
        ⭐ <span style="font-size:22px;color:{color};"><b>{score}</b></span>
        </p>

        <p>
        🧠 {row["تحلیل"]}
        </p>

        <p>
        ⚠ {row["ریسک‌ها"]}
        </p>

        <a href="{row["لینک"]}" target="_blank">
        🔗 مشاهده آگهی
        </a>

        </div>
        """,
                unsafe_allow_html=True,
            )

    except Exception as exc:
        st.error(f"اجرای جست‌وجو ناموفق بود: {exc}")
        st.caption("ممکن است ساختار یا دسترسی سرویس منبع تغییر کرده باشد.")
