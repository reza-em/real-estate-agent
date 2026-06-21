from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.db.location_repository import LocationCatalogRepository
from app.models.location import CityOption


DIVAR_CITIES_URL = "https://api.divar.ir/v8/places/cities"
PROVINCE_BY_PARENT = {
    876: "خراسان جنوبی",
    877: "کرمان",
    878: "قزوین",
    879: "زنجان",
    880: "خراسان رضوی",
    881: "آذربایجان غربی",
    882: "سمنان",
    883: "سیستان و بلوچستان",
    884: "لرستان",
    885: "کردستان",
    886: "یزد",
    887: "کهگیلویه و بویراحمد",
    888: "ایلام",
    889: "گیلان",
    890: "اصفهان",
    891: "آذربایجان شرقی",
    892: "قم",
    893: "مازندران",
    894: "هرمزگان",
    895: "البرز",
    896: "خراسان شمالی",
    897: "گلستان",
    898: "فارس",
    899: "همدان",
    900: "بوشهر",
    901: "مرکزی",
    902: "خوزستان",
    903: "چهارمحال و بختیاری",
    904: "تهران",
    905: "کرمانشاه",
    906: "اردبیل",
}

FALLBACK_CAPITALS = (
    ("15", "اراک", 901, 34.0954, 49.7013),
    ("17", "اردبیل", 906, 38.2498, 48.2933),
    ("10", "ارومیه", 881, 37.5527, 45.0761),
    ("4", "اصفهان", 890, 32.6546, 51.6680),
    ("7", "اهواز", 902, 31.3183, 48.6706),
    ("32", "ایلام", 888, 33.6374, 46.4227),
    ("39", "بجنورد", 896, 37.4747, 57.3290),
    ("18", "بندرعباس", 894, 27.1832, 56.2666),
    ("25", "بوشهر", 900, 28.9234, 50.8203),
    ("34", "بیرجند", 876, 32.8649, 59.2262),
    ("5", "تبریز", 891, 38.0800, 46.2919),
    ("1", "تهران", 904, 35.6892, 51.3890),
    ("27", "خرم‌آباد", 884, 33.4878, 48.3558),
    ("12", "رشت", 889, 37.2808, 49.5832),
    ("11", "زاهدان", 883, 29.4963, 60.8629),
    ("20", "زنجان", 879, 36.6736, 48.4787),
    ("22", "ساری", 893, 36.5659, 53.0586),
    ("35", "سمنان", 882, 35.5769, 53.3921),
    ("28", "سنندج", 885, 35.3219, 46.9862),
    ("36", "شهرکرد", 903, 32.3256, 50.8644),
    ("6", "شیراز", 898, 29.5918, 52.5837),
    ("19", "قزوین", 878, 36.2797, 50.0049),
    ("8", "قم", 892, 34.6416, 50.8746),
    ("2", "کرج", 895, 35.8400, 50.9391),
    ("13", "کرمان", 877, 30.2839, 57.0834),
    ("9", "کرمانشاه", 905, 34.3142, 47.0650),
    ("21", "گرگان", 897, 36.8427, 54.4439),
    ("3", "مشهد", 880, 36.2605, 59.6168),
    ("14", "همدان", 899, 34.7989, 48.5150),
    ("38", "یاسوج", 887, 30.6682, 51.5870),
    ("16", "یزد", 886, 31.8974, 54.3569),
)


class LocationCatalogService:
    def __init__(
        self,
        repository: LocationCatalogRepository | None = None,
        client: Any | None = None,
        cache_ttl: timedelta = timedelta(days=7),
    ) -> None:
        self.repository = repository or LocationCatalogRepository()
        self.client = client or httpx.Client(
            timeout=20.0,
            headers={"User-Agent": "RealEstateResearch/0.4 (personal-use)"},
        )
        self._owns_client = client is None
        self.cache_ttl = cache_ttl
        self._cities: list[CityOption] | None = None

    @property
    def cities(self) -> list[CityOption]:
        if self._cities is None:
            self._cities = self._load()
        return self._cities

    @property
    def city_ids(self) -> dict[str, str]:
        return {city.name: city.id for city in self.cities}

    @property
    def city_centers(self) -> dict[str, tuple[float, float]]:
        return {
            city.name: (city.latitude, city.longitude)
            for city in self.cities
            if city.latitude is not None and city.longitude is not None
        }

    def by_province(self) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = defaultdict(list)
        for city in self.cities:
            grouped[city.province].append(city.name)
        return {
            province: sorted(names)
            for province, names in sorted(grouped.items())
        }

    def province_for_city(self, city_name: str) -> str | None:
        return next(
            (city.province for city in self.cities if city.name == city_name), None
        )

    def city_option(self, city_name: str, province: str = "") -> CityOption | None:
        return next(
            (
                city
                for city in self.cities
                if city.name == city_name
                and (not province or city.province == province)
            ),
            None,
        )

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def _load(self) -> list[CityOption]:
        cached = self.repository.load()
        if cached and datetime.now() - cached[1] < self.cache_ttl:
            return self._parse(cached[0])
        try:
            response = self.client.get(DIVAR_CITIES_URL)
            response.raise_for_status()
            payload = response.json()
            self.repository.save(payload)
            return self._parse(payload)
        except (httpx.HTTPError, ValueError, KeyError):
            if cached:
                return self._parse(cached[0])
            return self._fallback()

    @staticmethod
    def _parse(payload: dict[str, object]) -> list[CityOption]:
        results = []
        for item in payload.get("cities", []):
            if not isinstance(item, dict):
                continue
            province = PROVINCE_BY_PARENT.get(int(item.get("parent", 0)))
            if not province:
                continue
            center = item.get("centroid") or item.get("default_location") or {}
            results.append(
                CityOption(
                    id=str(item["id"]),
                    name=str(item["name"]),
                    province=province,
                    latitude=_float_or_none(center.get("latitude")),
                    longitude=_float_or_none(center.get("longitude")),
                )
            )
        return results or LocationCatalogService._fallback()

    @staticmethod
    def _fallback() -> list[CityOption]:
        return [
            CityOption(str(city_id), name, PROVINCE_BY_PARENT[parent], lat, lon)
            for city_id, name, parent, lat, lon in FALLBACK_CAPITALS
        ]


def _float_or_none(value: object) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None
