from dataclasses import dataclass, field


@dataclass(slots=True)
class Analysis:
    external_id: str
    score: int
    summary: str
    risks: list[str]
    score_breakdown: dict[str, int] = field(default_factory=dict)
