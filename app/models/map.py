from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MapPoint:
    listing_id: str
    latitude: float
    longitude: float
    title: str
    price: str
    area: str
    score: int
    address: str
    precision: str
    color: list[int]
    radius: int


@dataclass(slots=True)
class MapPresentation:
    points: list[MapPoint] = field(default_factory=list)
    center_latitude: float = 35.6892
    center_longitude: float = 51.3890
    zoom: float = 10.5
