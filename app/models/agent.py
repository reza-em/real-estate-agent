from __future__ import annotations

from dataclasses import dataclass

from app.models.search import RankedListing, SearchCriteria, SearchResult


@dataclass(frozen=True, slots=True)
class ParsedAgentQuery:
    criteria: SearchCriteria
    parser: str


@dataclass(slots=True)
class AgentResponse:
    query: ParsedAgentQuery
    search_result: SearchResult
    recommendations: list[RankedListing]
