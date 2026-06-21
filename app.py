from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from analyzer import analyze
from db import save_listings
from scraper import CITY_IDS, DivarProvider


load_dotenv()
st.set_page_config(page_title="دستیار خرید خانه", page_icon="🏠", layout="wide")
st.markdown("<style>body, .stApp {direction: rtl;} table {direction: rtl;}</style>", unsafe_allow_html=True)
st.title("دستیار بررسی آگهی خرید خانه")
st.caption("جست‌وجوی اولیه و مقایسه آگهی‌ها؛ جایگزین بازدید، کارشناسی فنی و استعلام حقوقی نیست.")

with st.sidebar:
    st.header("فیلترها")
    city = st.selectbox("شهر", list(CITY_IDS))
    max_price_billion = st.number_input("حداکثر بودجه (میلیارد تومان)", 0.1, 1_000.0, 10.0, 0.1)
    pages = st.slider("تعداد صفحه بررسی", 1, 5, 1)
    preferences = st.text_area("ترجیحات", placeholder="مثلاً حداقل ۸۰ متر، پارکینگ، منطقه ۵")
    use_ai = st.checkbox("تحلیل با OpenAI", value=bool(os.getenv("OPENAI_API_KEY")))
    run = st.button("جست‌وجو و تحلیل", type="primary", use_container_width=True)

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
        st.success(f"{len(frame)} آگهی در محدوده بودجه پیدا شد.")
        st.dataframe(
            frame,
            use_container_width=True,
            hide_index=True,
            column_config={
                "قیمت (تومان)": st.column_config.NumberColumn(format="%d"),
                "لینک": st.column_config.LinkColumn(display_text="مشاهده آگهی"),
            },
        )
        st.download_button(
            "دانلود CSV",
            frame.to_csv(index=False).encode("utf-8-sig"),
            "listings.csv",
            "text/csv",
        )
    except Exception as exc:
        st.error(f"اجرای جست‌وجو ناموفق بود: {exc}")
        st.caption("ممکن است ساختار یا دسترسی سرویس منبع تغییر کرده باشد.")
