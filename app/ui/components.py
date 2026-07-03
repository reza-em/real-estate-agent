from __future__ import annotations

from html import escape

import pandas as pd
import streamlit as st

from app.core.formatting import format_toman
from app.models.category import CATEGORIES, CATEGORY_LABELS, PROPERTY, category_label
from app.models.memory import UserProfile
from app.models.search import RankedListing, SearchCriteria, SearchResult
from app.services.location_catalog import LocationCatalogService


def render_header() -> None:
    st.markdown(
        """
        <section class="hero">
            <div class="hero-kicker">دستیار هوشمند جست‌وجوی آگهی</div>
            <h1>ملک یا وسیله نقلیه مناسب را سریع‌تر پیدا کنید</h1>
            <p>آگهی‌های چند منبع را یک‌جا بررسی، بر اساس بودجه فیلتر و با معیارهای شما رتبه‌بندی می‌کنیم.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_section_title(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="section-title"><h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div>',
        unsafe_allow_html=True,
    )


def render_search_form(
    ai_available: bool,
    locations: LocationCatalogService,
    profile: UserProfile,
) -> SearchCriteria | None:
    render_section_title("فیلترهای جست‌وجو", "محدوده و اولویت‌های خرید خود را مشخص کنید.")
    grouped = locations.by_province()
    provinces = list(grouped)
    preferred_city = (
        profile.preferred_cities[-1] if profile.preferred_cities else "تهران"
    )
    preferred_province = locations.province_for_city(preferred_city) or "تهران"
    category = st.radio(
        "دسته‌بندی",
        CATEGORIES,
        format_func=lambda value: CATEGORY_LABELS[value],
        horizontal=True,
        key="listing_category",
    )
    with st.form("search_filters"):
        first, second, third, fourth, fifth = st.columns([1, 1, 1.3, 1, .9])
        with first:
            province = st.selectbox(
                "استان",
                provinces,
                index=provinces.index(preferred_province),
            )
        with second:
            cities = grouped[province]
            city_index = cities.index(preferred_city) if preferred_city in cities else 0
            city = st.selectbox("شهر", cities, index=city_index)
        with third:
            max_price_billion = st.number_input(
                "حداکثر بودجه (میلیارد تومان)",
                min_value=0.1,
                max_value=1_000.0,
                value=10.0,
                step=0.1,
            )
        with fourth:
            min_area = st.number_input(
                "حداقل متراژ" if category == PROPERTY else "متراژ (ویژه ملک)",
                min_value=0,
                max_value=10_000,
                value=0,
                step=5,
                disabled=category != PROPERTY,
            )
        with fifth:
            pages = st.slider("صفحه از هر دسته", 1, 5, 1)

        preferences = st.text_area(
            "اولویت‌ها و توضیحات",
            placeholder=(
                "مثلاً دو خواب، پارکینگ، آسانسور و سن بنا کمتر از ۱۰ سال"
                if category == PROPERTY
                else "مثلاً مدل، سال ساخت، کارکرد، گیربکس و وضعیت بدنه"
            ),
            height=88,
        )
        option_col, hint_col, button_col = st.columns([1.1, 2, 1.1])
        with option_col:
            use_ai = st.checkbox("رتبه‌بندی هوشمند", value=ai_available)
        with hint_col:
            if not ai_available:
                st.caption("کلید OpenAI تنظیم نشده؛ رتبه‌بندی قیمتی فعال است.")
            else:
                st.caption("تحلیل هوشمند حداکثر ۲۰ گزینه برتر را بررسی می‌کند.")
        with button_col:
            submitted = st.form_submit_button(
                "جست‌وجوی آگهی‌ها", type="primary", width="stretch"
            )

    if not submitted:
        return None
    city_option = locations.city_option(city, province)
    return SearchCriteria(
        city=city,
        max_price=int(max_price_billion * 1_000_000_000),
        min_area=int(min_area) if category == PROPERTY else 0,
        pages=pages,
        preferences=preferences.strip(),
        use_ai=use_ai,
        province=province,
        city_id=city_option.id if city_option else "",
        category=category,
    )


def render_summary(result: SearchResult) -> None:
    prices = [item.listing.price for item in result.items if item.listing.price]
    average_price = int(sum(prices) / len(prices)) if prices else None
    best_score = result.best.analysis.score if result.best else 0
    columns = st.columns(4)
    columns[0].metric("نتایج منطبق", f"{len(result.items):,}")
    columns[1].metric("آگهی‌های بررسی‌شده", f"{result.fetched_count:,}")
    columns[2].metric("میانگین قیمت", format_toman(average_price))
    columns[3].metric("بالاترین امتیاز", f"{best_score} از ۱۰۰")


def render_best_deals(items: list[RankedListing]) -> None:
    render_section_title("پیشنهادهای برتر", "گزینه‌هایی که بالاترین امتیاز مقایسه را گرفته‌اند.")
    columns = st.columns(3)
    labels = ("پیشنهاد اول", "پیشنهاد دوم", "پیشنهاد سوم")
    for index, item in enumerate(items[:3]):
        listing = item.listing
        analysis = item.analysis
        css_class = "deal-card best" if index == 0 else "deal-card"
        detail = f"{listing.area} متر" if listing.area else category_label(listing.category)
        card = f"""
        <article class="{css_class}">
            <div class="deal-rank">{labels[index]}</div>
            <div class="deal-title">{escape(listing.title)}</div>
            <div class="deal-meta">{escape(listing.location or 'موقعیت نامشخص')} · {detail} · {escape(listing.source)}</div>
            <div class="deal-price">{format_toman(listing.price)}</div>
            <div class="score-row">
                <span class="score-pill">{analysis.score}</span>
                <div class="score-track"><div class="score-fill" style="width:{analysis.score}%"></div></div>
            </div>
            <a class="deal-link" href="{escape(listing.url, quote=True)}" target="_blank" rel="noopener noreferrer">مشاهده آگهی در {escape(listing.source)}</a>
        </article>
        """
        columns[index].markdown(card, unsafe_allow_html=True)


def result_frame(items: list[RankedListing]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "امتیاز": item.analysis.score,
                "عنوان": item.listing.title,
                "منبع": item.listing.source,
                "دسته": category_label(item.listing.category),
                "قیمت (تومان)": item.listing.price,
                "متراژ": item.listing.area,
                "موقعیت": item.listing.location,
                "تحلیل": item.analysis.summary,
                "لینک": item.listing.url,
            }
            for item in items
        ]
    )


def render_results_table(items: list[RankedListing]) -> pd.DataFrame:
    render_section_title("جدول نتایج", "تمام گزینه‌ها به ترتیب امتیاز نمایش داده شده‌اند.")
    frame = result_frame(items)
    st.dataframe(
        frame,
        width="stretch",
        hide_index=True,
        height=min(680, 86 + len(frame) * 36),
        column_config={
            "امتیاز": st.column_config.ProgressColumn(
                min_value=0, max_value=100, format="%d"
            ),
            "قیمت (تومان)": st.column_config.NumberColumn(format="%d"),
            "متراژ": st.column_config.NumberColumn(format="%d متر"),
            "لینک": st.column_config.LinkColumn(display_text="مشاهده"),
        },
    )
    return frame


def render_listing_details(items: list[RankedListing]) -> None:
    with st.expander("جزئیات تحلیل و ریسک‌ها"):
        for item in items[:12]:
            listing = item.listing
            analysis = item.analysis
            risks = "، ".join(analysis.risks) or "موردی ثبت نشده است"
            st.markdown(
                f"""
                <article class="listing-card">
                    <h3>{escape(listing.title)} · امتیاز {analysis.score}</h3>
                    <p><strong>{format_toman(listing.price)}</strong> · {escape(listing.location or 'موقعیت نامشخص')}</p>
                    <p>{escape(analysis.summary)}</p>
                    <p><strong>موارد نیازمند بررسی:</strong> {escape(risks)}</p>
                </article>
                """,
                unsafe_allow_html=True,
            )
