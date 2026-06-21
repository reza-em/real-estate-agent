from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CityOption:
    id: str
    name: str
    province: str
    latitude: float | None = None
    longitude: float | None = None
