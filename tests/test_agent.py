from pathlib import Path
from types import SimpleNamespace

from app.agents.real_estate_agent import AgentQueryParser, RealEstateAgent
from app.memory.repository import MemoryRepository
from app.memory.service import UserMemoryService
from app.models.analysis import Analysis
from app.models.listing import Listing
from app.models.memory import UserProfile
from app.models.search import RankedListing, SearchResult
from app.services.decision_engine import DecisionEngine


def make_ranked(external_id: str, price: int = 4_500_000_000) -> RankedListing:
    listing = Listing(
        "test",
        external_id,
        "آپارتمان ۹۰ متری",
        price,
        "تهران، پونک",
        "https://example.com",
        area=90,
        city="تهران",
    )
    return RankedListing(listing, Analysis(external_id, 50, "اولیه", []))


def test_rule_parser_understands_persian_and_english_query():
    parser = AgentQueryParser(api_key="")
    profile = UserProfile("default")
    persian = parser.parse(
        "آپارتمان در تهران زیر ۵ میلیارد با حداقل ۸۰ متر", profile
    )
    english = parser.parse(
        "cheap apartment in Tehran under 5 billion with at least 80m", profile
    )
    for result in (persian, english):
        assert result.criteria.city == "تهران"
        assert result.criteria.max_price == 5_000_000_000
        assert result.criteria.min_area == 80
        assert result.parser == "rules"


def test_openai_failure_falls_back_to_rules():
    class FailingResponses:
        def create(self, **kwargs):
            raise RuntimeError("offline")

    client = SimpleNamespace(responses=FailingResponses())
    parser = AgentQueryParser(api_key="test", client=client)
    result = parser.parse("خانه در شیراز تا ۶ میلیارد", UserProfile("u"))
    assert result.criteria.city == "شیراز"
    assert result.criteria.max_price == 6_000_000_000
    assert result.parser == "rules"


def test_rule_parser_supports_catalog_cities_beyond_legacy_list():
    parser = AgentQueryParser(api_key="", city_names=["تهران", "پردیس"])
    result = parser.parse("خانه در پردیس تا ۴ میلیارد", UserProfile("u"))
    assert result.criteria.city == "پردیس"


def test_decision_engine_uses_rejected_property_memory():
    profile = UserProfile(
        "u", preferred_cities=["تهران"], min_area=80, rejected_properties={"bad"}
    )
    criteria = AgentQueryParser(api_key="").parse(
        "تهران تا ۵ میلیارد حداقل ۸۰ متر", profile
    ).criteria
    ranked = DecisionEngine().rank(
        [make_ranked("bad", 4_000_000_000), make_ranked("good", 4_500_000_000)],
        criteria,
        profile,
    )
    assert ranked[0].listing.external_id == "good"
    assert ranked[0].analysis.score_breakdown["حافظه و سابقه"] > 0
    assert ranked[1].analysis.score_breakdown["حافظه و سابقه"] == -50


def test_agent_orchestrates_search_and_records_recommendations(tmp_path: Path):
    class FakeSearchService:
        def search(self, criteria):
            return SearchResult(
                items=[make_ranked("a"), make_ranked("b")],
                fetched_count=2,
                city=criteria.city,
            )

    memory = UserMemoryService(MemoryRepository(tmp_path / "agent.db"))
    agent = RealEstateAgent(
        FakeSearchService(), memory, parser=AgentQueryParser(api_key="")
    )
    response = agent.ask("u", "تهران تا ۵ میلیارد حداقل ۸۰ متر")
    assert len(response.recommendations) == 2
    assert response.recommendations[0].analysis.score_breakdown
    assert memory.profile("u").interaction_count == 2
