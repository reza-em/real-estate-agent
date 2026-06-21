from app.models.analysis import Analysis
from app.models.listing import Listing
from app.models.search import RankedListing
from app.services.map_service import MapService


def ranked(external_id: str, score: int) -> RankedListing:
    listing = Listing(
        source="test",
        external_id=external_id,
        title=f"خانه {external_id}",
        price=8_000_000_000,
        location="تهران، پونک",
        url="https://example.com",
        area=80,
        latitude=35.7,
        longitude=51.3,
        address="تهران، پونک",
        city="تهران",
        location_precision="geocoded",
    )
    return RankedListing(listing, Analysis(external_id, score, "خلاصه", []))


def test_map_service_highlights_selected_and_best():
    presentation = MapService().build(
        [ranked("best", 95), ranked("selected", 80)],
        selected_id="selected",
        city="تهران",
    )
    points = {point.listing_id: point for point in presentation.points}
    assert points["best"].color[:3] == [220, 38, 38]
    assert points["selected"].color[:3] == [245, 158, 11]
    assert (points["best"].latitude, points["best"].longitude) != (
        points["selected"].latitude,
        points["selected"].longitude,
    )
