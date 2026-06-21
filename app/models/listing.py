from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from typing import Any


@dataclass(slots=True)
class Listing:
    source: str
    external_id: str
    title: str
    price: int | None
    location: str
    url: str
    description: str = ""
    area: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)
    latitude: float | None = None
    longitude: float | None = None
    address: str | None = None
    city: str = ""
    location_precision: str = "unknown"

    @property
    def has_coordinates(self) -> bool:
        return (
            self.latitude is not None
            and self.longitude is not None
            and isfinite(self.latitude)
            and isfinite(self.longitude)
            and -90 <= self.latitude <= 90
            and -180 <= self.longitude <= 180
        )
