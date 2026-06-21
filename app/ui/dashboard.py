from __future__ import annotations

import streamlit as st
from dotenv import load_dotenv

from app.agents.real_estate_agent import AgentQueryParser, RealEstateAgent
from app.auth.service import AuthService
from app.db.repository import ListingRepository
from app.memory.service import UserMemoryService
from app.models.agent import AgentResponse
from app.models.search import SearchCriteria, SearchResult
from app.providers.divar import DivarProvider
from app.services.decision_engine import DecisionEngine
from app.services.geocoder import GeocoderService
from app.services.location_catalog import LocationCatalogService
from app.services.ranking import RankingService
from app.services.search import SearchService
from app.ui.agent_view import (
    render_agent_form,
    render_agent_recommendations,
    render_user_bar,
)
from app.ui.auth_view import render_auth_gate
from app.ui.components import (
    render_best_deals,
    render_header,
    render_listing_details,
    render_results_table,
    result_frame,
    render_search_form,
    render_section_title,
    render_summary,
)
from app.ui.map_view import render_map_view, render_selected_listing
from app.ui.styles import APP_CSS


def run_dashboard() -> None:
    load_dotenv()
    st.set_page_config(
        page_title="خانه‌یاب | دستیار خرید ملک",
        page_icon=":material/home:",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown(APP_CSS, unsafe_allow_html=True)
    user = render_auth_gate(AuthService())
    if user is None:
        return
    render_header()

    ranking = RankingService()
    memory = UserMemoryService()
    locations = _location_catalog()
    profile = render_user_bar(memory, user)
    user_id = user.id
    mode = st.radio(
        "حالت جست‌وجو",
        ("فیلتر دستی", "عامل هوشمند"),
        horizontal=True,
        key="search_mode",
    )
    if mode == "عامل هوشمند":
        request = render_agent_form(ranking.ai_available, profile)
        if request:
            _execute_agent(request[0], request[1], user_id, memory, locations)
    else:
        criteria = render_search_form(ranking.ai_available, locations, profile)
        if criteria:
            _execute_search(criteria, ranking, user_id, memory, locations)

    result = st.session_state.get("search_result")
    if result is not None:
        if not result.items:
            st.warning("آگهی منطبق با بودجه و متراژ انتخاب‌شده پیدا نشد.")
            return
        render_section_title("نمای کلی", "خلاصه‌ای از نتیجه آخرین جست‌وجو.")
        render_summary(result)
        agent_response = st.session_state.get("agent_response")
        if isinstance(agent_response, AgentResponse):
            refreshed_profile = memory.profile(user_id)
            result.items = DecisionEngine().rank(
                result.items, agent_response.query.criteria, refreshed_profile
            )
            agent_response.recommendations = result.items[:3]
            render_agent_recommendations(agent_response, user_id, memory)
        else:
            render_best_deals(result.items)
        if "selected_listing_id" not in st.session_state:
            st.session_state["selected_listing_id"] = result.items[0].listing.external_id

        view = st.radio(
            "نوع نمایش نتایج",
            ("نمای فهرست", "نمای نقشه"),
            horizontal=True,
            label_visibility="collapsed",
        )
        if view == "نمای نقشه":
            render_section_title(
                "نمایش روی نقشه",
                "برای مشاهده جزئیات روی نشانگر کلیک کنید؛ موقعیت‌های تقریبی با فاصله محدود نمایش داده می‌شوند.",
            )
            st.markdown(
                """
                <div class="map-legend">
                    <span><i class="dot selected"></i>ملک منتخب</span>
                    <span><i class="dot best"></i>بهترین رتبه</span>
                    <span><i class="dot normal"></i>سایر آگهی‌ها</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            previous_id = st.session_state["selected_listing_id"]
            selected_id = render_map_view(result.items, previous_id, result.city)
            if selected_id and selected_id != previous_id:
                st.session_state["selected_listing_id"] = selected_id
                st.rerun()
            render_selected_listing(
                result.items, st.session_state["selected_listing_id"]
            )
        else:
            _render_list_view(result)

        frame = result_frame(result.items)
        action_col, note_col = st.columns([1, 3])
        with action_col:
            st.download_button(
                "دانلود خروجی CSV",
                frame.to_csv(index=False).encode("utf-8-sig"),
                "listings.csv",
                "text/csv",
                width="stretch",
            )
        with note_col:
            st.caption(
                "این نتایج برای بررسی اولیه‌اند؛ سند، مالکیت، قیمت و وضعیت فنی ملک باید مستقل راستی‌آزمایی شوند."
            )
        if view == "نمای نقشه":
            render_listing_details(result.items)


def _execute_search(
    criteria: SearchCriteria,
    ranking: RankingService,
    user_id: str,
    memory: UserMemoryService,
    locations: LocationCatalogService,
) -> None:
    city_ids = locations.city_ids
    if criteria.city_id:
        city_ids[criteria.city] = criteria.city_id
    provider = DivarProvider(city_ids=city_ids)
    repository = ListingRepository()
    geocoder = GeocoderService(repository, city_centers=locations.city_centers)
    service = SearchService(provider, repository, ranking, geocoder)
    try:
        memory.remember_search(user_id, criteria, mode="filter")
        with st.spinner("در حال دریافت، فیلتر و رتبه‌بندی آگهی‌ها..."):
            st.session_state["search_result"] = service.search(criteria)
        st.session_state.pop("agent_response", None)
        result = st.session_state["search_result"]
        if result.items:
            st.session_state["selected_listing_id"] = result.items[0].listing.external_id
        st.success(f"{len(result.items)} آگهی منطبق پیدا شد.")
        if criteria.use_ai and not result.ai_available:
            st.info("رتبه‌بندی پایه استفاده شد؛ کلید OpenAI در دسترس نیست.")
    except Exception as exc:
        st.error(f"اجرای جست‌وجو ناموفق بود: {exc}")
        st.caption("ممکن است دسترسی یا ساختار سرویس منبع موقتاً تغییر کرده باشد.")
    finally:
        geocoder.close()
        provider.close()


def _execute_agent(
    query: str,
    pages: int,
    user_id: str,
    memory: UserMemoryService,
    locations: LocationCatalogService,
) -> None:
    provider = DivarProvider(city_ids=locations.city_ids)
    repository = ListingRepository()
    geocoder = GeocoderService(repository, city_centers=locations.city_centers)
    search_service = SearchService(
        provider, repository, RankingService(api_key=""), geocoder
    )
    agent = RealEstateAgent(
        search_service,
        memory,
        parser=AgentQueryParser(city_names=locations.city_ids),
    )
    try:
        with st.spinner("عامل در حال فهم درخواست و بررسی آگهی‌هاست..."):
            response = agent.ask(user_id, query, pages)
        st.session_state["agent_response"] = response
        st.session_state["search_result"] = response.search_result
        if response.search_result.items:
            st.session_state["selected_listing_id"] = response.search_result.items[0].listing.external_id
        st.success(f"عامل {len(response.search_result.items)} گزینه منطبق پیدا کرد.")
    except Exception as exc:
        st.error(f"اجرای عامل ناموفق بود: {exc}")
        st.caption("در صورت خطای OpenAI، parser قانون‌محور به‌صورت خودکار استفاده می‌شود.")
    finally:
        geocoder.close()
        provider.close()


def _render_list_view(result: SearchResult) -> None:
    options = [item.listing.external_id for item in result.items]
    by_id = {item.listing.external_id: item for item in result.items}
    current_id = st.session_state.get("selected_listing_id", options[0])
    index = options.index(current_id) if current_id in options else 0
    selected_id = st.selectbox(
        "ملک منتخب برای بررسی",
        options,
        index=index,
        format_func=lambda listing_id: by_id[listing_id].listing.title,
    )
    st.session_state["selected_listing_id"] = selected_id
    render_selected_listing(result.items, selected_id)
    render_results_table(result.items)
    render_listing_details(result.items)


@st.cache_resource(show_spinner=False)
def _location_catalog() -> LocationCatalogService:
    return LocationCatalogService()
