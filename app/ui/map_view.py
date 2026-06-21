from __future__ import annotations

from html import escape

import pandas as pd
import pydeck as pdk
import streamlit as st

from app.core.formatting import format_toman
from app.models.search import RankedListing
from app.services.map_service import MapService


MAP_LAYER_ID = "property-listings"


def render_map_view(
    items: list[RankedListing], selected_id: str | None, city: str
) -> str | None:
    try:
        presentation = MapService().build(items, selected_id, city)
        if not presentation.points:
            st.warning("برای این نتایج مختصات قابل نمایش روی نقشه موجود نیست.")
            return selected_id

        data = pd.DataFrame(
            [
                {
                    "listing_id": point.listing_id,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "title": point.title,
                    "price": point.price,
                    "area": point.area,
                    "score": point.score,
                    "address": point.address,
                    "precision": point.precision,
                    "color": point.color,
                    "radius": point.radius,
                }
                for point in presentation.points
            ]
        )
        layer = pdk.Layer(
            "ScatterplotLayer",
            id=MAP_LAYER_ID,
            data=data,
            get_position="[longitude, latitude]",
            get_fill_color="color",
            get_line_color=[255, 255, 255, 240],
            get_radius="radius",
            radius_min_pixels=8,
            radius_max_pixels=22,
            line_width_min_pixels=2,
            stroked=True,
            filled=True,
            pickable=True,
            auto_highlight=True,
        )
        deck = pdk.Deck(
            map_style=None,
            initial_view_state=pdk.ViewState(
                latitude=presentation.center_latitude,
                longitude=presentation.center_longitude,
                zoom=presentation.zoom,
                pitch=0,
            ),
            layers=[layer],
            tooltip={
                "html": (
                    "<div style='direction:rtl;text-align:right;font-family:Tahoma'>"
                    "<b>{title}</b><br/>"
                    "{price} · {area}<br/>"
                    "امتیاز: <b>{score}</b><br/>"
                    "{address}<br/><small>{precision}</small></div>"
                ),
                "style": {"backgroundColor": "#17202a", "color": "white"},
            },
        )
        event = st.pydeck_chart(
            deck,
            height=560,
            width="stretch",
            on_select="rerun",
            selection_mode="single-object",
            key="property_map",
        )
        objects = event.selection.objects.get(MAP_LAYER_ID, [])
        if objects:
            return str(objects[0].get("listing_id") or selected_id)
        return selected_id
    except Exception as exc:
        st.warning(f"نمایش نقشه موقتاً در دسترس نیست: {exc}")
        return selected_id


def render_selected_listing(
    items: list[RankedListing], selected_id: str | None
) -> None:
    selected = next(
        (item for item in items if item.listing.external_id == selected_id), None
    )
    if selected is None:
        return
    listing = selected.listing
    analysis = selected.analysis
    precision = (
        "موقعیت تقریبی"
        if listing.location_precision == "approximate"
        else "موقعیت مکان‌یابی‌شده"
    )
    risks = "، ".join(analysis.risks) or "موردی ثبت نشده است"
    st.markdown(
        f"""
        <article class="selected-property">
            <div class="selected-label">ملک منتخب · امتیاز {analysis.score}</div>
            <h3>{escape(listing.title)}</h3>
            <div class="selected-grid">
                <span><strong>{format_toman(listing.price)}</strong></span>
                <span>{listing.area or 'نامشخص'} متر</span>
                <span>{escape(listing.address or listing.location or 'موقعیت نامشخص')}</span>
                <span>{precision}</span>
            </div>
            <p>{escape(analysis.summary)}</p>
            <p><strong>نیازمند بررسی:</strong> {escape(risks)}</p>
            <a href="{escape(listing.url, quote=True)}" target="_blank" rel="noopener noreferrer">مشاهده آگهی کامل</a>
        </article>
        """,
        unsafe_allow_html=True,
    )
