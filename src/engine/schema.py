from dataclasses import dataclass, field
from typing import Literal


Category = Literal["must", "nice"]


@dataclass
class Dimension:
    name: str
    category: Category
    weight: float
    description: str = ""


@dataclass
class Weights:
    dimensions: list[Dimension]

    def total(self) -> float:
        return sum(d.weight for d in self.dimensions)

    def must_total(self) -> float:
        return sum(d.weight for d in self.dimensions if d.category == "must")

    def nice_total(self) -> float:
        return sum(d.weight for d in self.dimensions if d.category == "nice")

    def is_valid(self) -> tuple[bool, str]:
        if abs(self.total() - 1.0) > 1e-6:
            return False, f"합계가 100%가 아닙니다 (현재 {self.total()*100:.1f}%)"
        if self.must_total() < 0.5:
            return False, f"필수 합계는 50% 이상이어야 합니다 (현재 {self.must_total()*100:.1f}%)"
        if self.nice_total() > 0.5:
            return False, f"우대 합계는 50% 이하여야 합니다 (현재 {self.nice_total()*100:.1f}%)"
        return True, ""


@dataclass
class HardGates:
    min_score_per_must: int = 50
    info_missing_downgrade: bool = True
    avoidance_keywords: list[str] = field(default_factory=list)


DEFAULT_DIMENSIONS = [
    Dimension("Hard Skills", "must", 0.30, "필수 스킬·도구 매칭"),
    Dimension("Experience", "must", 0.25, "직무 유사도·연차"),
    Dimension("Achievements", "must", 0.20, "성과·업무 매칭"),
    Dimension("Domain Fit", "nice", 0.15, "산업·도메인 일치"),
    Dimension("Seniority", "nice", 0.10, "레벨 갭"),
]


DEFAULT_HARD_GATES = HardGates(
    min_score_per_must=50,
    info_missing_downgrade=True,
    avoidance_keywords=[],
)
