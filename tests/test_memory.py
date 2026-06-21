from pathlib import Path

from app.memory.repository import MemoryRepository
from app.memory.service import UserMemoryService
from app.models.listing import Listing
from app.models.search import SearchCriteria


def make_listing() -> Listing:
    return Listing(
        "test",
        "property-1",
        "آپارتمان ۸۰ متری",
        4_500_000_000,
        "تهران، پونک",
        "https://example.com",
        area=80,
        city="تهران",
    )


def test_memory_persists_profile_feedback_and_history(tmp_path: Path):
    path = tmp_path / "memory.db"
    memory = UserMemoryService(MemoryRepository(path))
    criteria = SearchCriteria("تهران", 5_000_000_000, min_area=80)
    memory.remember_search("user-1", criteria, mode="agent", raw_query="خانه تهران")
    memory.record_feedback("user-1", make_listing(), "liked")

    reloaded = UserMemoryService(MemoryRepository(path)).profile("user-1")
    assert reloaded.budget == 5_000_000_000
    assert reloaded.preferred_cities == ["تهران"]
    assert reloaded.min_area == 80
    assert "property-1" in reloaded.liked_properties
    assert reloaded.interaction_count == 2


def test_feedback_can_change_from_liked_to_rejected(tmp_path: Path):
    memory = UserMemoryService(MemoryRepository(tmp_path / "feedback.db"))
    listing = make_listing()
    memory.record_feedback("default", listing, "liked")
    memory.record_feedback("default", listing, "rejected")
    profile = memory.profile("default")
    assert listing.external_id not in profile.liked_properties
    assert listing.external_id in profile.rejected_properties
