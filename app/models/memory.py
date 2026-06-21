from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class UserProfile:
    user_id: str
    budget: int | None = None
    preferred_cities: list[str] = field(default_factory=list)
    min_area: int = 0
    preferences: str = ""
    liked_properties: set[str] = field(default_factory=set)
    rejected_properties: set[str] = field(default_factory=set)
    interaction_count: int = 0


@dataclass(frozen=True, slots=True)
class Interaction:
    event_type: str
    payload: dict[str, object]
    created_at: str
