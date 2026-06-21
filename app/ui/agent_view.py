from __future__ import annotations

import streamlit as st

from app.core.formatting import format_toman
from app.memory.service import UserMemoryService
from app.models.auth import AuthUser
from app.models.agent import AgentResponse
from app.models.memory import UserProfile
from app.models.search import RankedListing
from app.ui.components import render_section_title
from app.ui.auth_view import logout


def render_user_bar(memory: UserMemoryService, user: AuthUser) -> UserProfile:
    identity_col, memory_col, action_col = st.columns([1, 3.4, .7])
    with identity_col:
        st.markdown(
            f"<div class='user-identity'><strong>{user.display_name}</strong><small>@{user.username}</small></div>",
            unsafe_allow_html=True,
        )
    profile = memory.profile(user.id)
    with memory_col:
        budget = format_toman(profile.budget) if profile.budget else "ثبت نشده"
        cities = "، ".join(profile.preferred_cities) or "ثبت نشده"
        st.markdown(
            f"""
            <div class="memory-bar">
                <span><strong>بودجه به‌یادمانده:</strong> {budget}</span>
                <span><strong>شهرها:</strong> {cities}</span>
                <span><strong>حداقل متراژ:</strong> {profile.min_area or 'ثبت نشده'}</span>
                <span><strong>پسند / رد:</strong> {len(profile.liked_properties)} / {len(profile.rejected_properties)}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with action_col:
        st.button("خروج", on_click=logout, width="stretch")
    return profile


def render_agent_form(
    ai_available: bool, profile: UserProfile
) -> tuple[str, int] | None:
    render_section_title(
        "از دستیار ملک بپرسید",
        "نیازتان را معمولی بنویسید؛ بودجه، شهر و متراژ به‌طور خودکار استخراج می‌شوند.",
    )
    placeholder = (
        "مثلاً یک آپارتمان ارزان در تهران تا ۵ میلیارد و حداقل ۸۰ متر می‌خواهم"
    )
    with st.form("agent_query_form"):
        query = st.text_area(
            "درخواست شما",
            placeholder=placeholder,
            height=110,
        )
        info_col, pages_col, button_col = st.columns([2.2, 1, 1.2])
        with info_col:
            parser = "OpenAI با fallback قانون‌محور" if ai_available else "پردازش قانون‌محور"
            memory_hint = (
                f"حافظه فعال است؛ {profile.interaction_count} تعامل قبلی برای شخصی‌سازی در دسترس است."
            )
            st.caption(f"{parser} · {memory_hint}")
        with pages_col:
            pages = st.slider("صفحه از هر دسته", 1, 5, 1, key="agent_pages")
        with button_col:
            submitted = st.form_submit_button(
                "از عامل بپرس", type="primary", width="stretch"
            )
    if not submitted:
        return None
    if not query.strip():
        st.warning("لطفاً نیاز ملکی خود را بنویسید.")
        return None
    return query.strip(), pages


def render_agent_recommendations(
    response: AgentResponse,
    user_id: str,
    memory: UserMemoryService,
) -> None:
    criteria = response.query.criteria
    parser_label = "OpenAI" if response.query.parser == "openai" else "قواعد محلی"
    st.markdown(
        f"""
        <div class="agent-query-summary">
            <strong>برداشت عامل از درخواست:</strong>
            شهر {criteria.city} · بودجه {format_toman(criteria.max_price)} ·
            حداقل {criteria.min_area or 'بدون محدودیت'} متر · پردازش با {parser_label}
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_section_title(
        "سه پیشنهاد عامل",
        "امتیاز هر پیشنهاد از تطابق بودجه، متراژ، موقعیت و حافظه شما ساخته شده است.",
    )
    columns = st.columns(3)
    profile = memory.profile(user_id)
    for index, item in enumerate(response.recommendations):
        with columns[index]:
            _render_recommendation_card(item, index, user_id, profile, memory)


def _render_recommendation_card(
    item: RankedListing,
    index: int,
    user_id: str,
    profile: UserProfile,
    memory: UserMemoryService,
) -> None:
    listing = item.listing
    analysis = item.analysis
    with st.container(border=True):
        st.markdown(f"**پیشنهاد {index + 1} · امتیاز {analysis.score}**")
        st.markdown(f"### {listing.title}")
        st.markdown(
            f"**{format_toman(listing.price)}**  \n"
            f"{listing.area or 'نامشخص'} متر · {listing.location or 'موقعیت نامشخص'}"
        )
        st.progress(analysis.score, text="امتیاز نهایی")
        st.markdown(f"<div class='agent-reason'>{analysis.summary}</div>", unsafe_allow_html=True)
        for label, score in analysis.score_breakdown.items():
            st.caption(f"{label}: {score}")
        st.link_button("مشاهده آگهی", listing.url, width="stretch")
        liked = listing.external_id in profile.liked_properties
        rejected = listing.external_id in profile.rejected_properties
        like_col, reject_col = st.columns(2)
        if like_col.button(
            "پسندیده‌ام" if liked else "پسندیدن",
            key=f"like_{listing.source}_{listing.external_id}",
            width="stretch",
            type="primary" if liked else "secondary",
        ):
            memory.record_feedback(user_id, listing, "liked")
            st.rerun()
        if reject_col.button(
            "رد شده" if rejected else "رد کردن",
            key=f"reject_{listing.source}_{listing.external_id}",
            width="stretch",
        ):
            memory.record_feedback(user_id, listing, "rejected")
            st.rerun()
