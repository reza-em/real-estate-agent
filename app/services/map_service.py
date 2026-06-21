from __future__ import annotations

import hashlib
from collections import Counter

from app.core.formatting import format_toman
from app.models.map import MapPoint, MapPresentation
from app.models.search import RankedListing
from app.services.geocoder import CITY_CENTERS


class MapService:
    def build(
        self,
        items: list[RankedListing],
        selected_id: str | None = None,
        city: str = "",
    ) -> MapPresentation:
        located = [item for item in items if item.listing.has_coordinates]
        if not located:
            center = CITY_CENTERS.get(city, CITY_CENTERS["تهران"])
            return MapPresentation(center_latitude=center[0], center_longitude=center[1])

        coordinate_counts = Counter(
            (item.listing.latitude, item.listing.longitude) for item in located
        )
        best_id = items[0].listing.external_id if items else None
        points = []
        for item in located:
            listing = item.listing
            latitude, longitude = self._display_coordinates(
                listing.latitude,
                listing.longitude,
                listing.external_id,
                coordinate_counts[(listing.latitude, listing.longitude)] > 1,
            )
            is_selected = listing.external_id == selected_id
            is_best = listing.external_id == best_id
            color = (
                [245, 158, 11, 235]
                if is_selected
                else [220, 38, 38, 230]
                if is_best
                else [15, 118, 110, 210]
            )
            points.append(
                MapPoint(
                    listing_id=listing.external_id,
                    latitude=latitude,
                    longitude=longitude,
                    title=listing.title,
                    price=format_toman(listing.price),
                    area=f"{listing.area} متر" if listing.area else "نامشخص",
                    score=item.analysis.score,
                    address=listing.address or listing.location or "موقعیت نامشخص",
                    precision=(
                        "تقریبی"
                        if listing.location_precision == "approximate"
                        else "مکان‌یابی‌شده"
                    ),
                    color=color,
                    radius=310 if is_selected else 260 if is_best else 190,
                )
            )

        center_latitude = sum(point.latitude for point in points) / len(points)
        center_longitude = sum(point.longitude for point in points) / len(points)
        return MapPresentation(
            points=points,
            center_latitude=center_latitude,
            center_longitude=center_longitude,
            zoom=10.5 if len(points) > 1 else 13.0,
        )

    @staticmethod
    def _display_coordinates(
        latitude: float | None,
        longitude: float | None,
        listing_id: str,
        needs_offset: bool,
    ) -> tuple[float, float]:
        if latitude is None or longitude is None:
            raise ValueError("Map point is missing coordinates")
        if not needs_offset:
            return latitude, longitude
        digest = hashlib.sha256(listing_id.encode("utf-8")).digest()
        lat_offset = (digest[0] / 255 - 0.5) * 0.004
        lon_offset = (digest[1] / 255 - 0.5) * 0.004
        return latitude + lat_offset, longitude + lon_offset
