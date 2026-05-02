"""Mock 모드용 더미 데이터.

실제 LLM 호출 없이 시스템 전체 흐름을 시연할 수 있도록
사전 정의된 JD/후보자/평가 결과를 제공합니다.

실제 운영 시에는 LLM_BACKEND=ollama 또는 LLM_BACKEND=anthropic으로 실 호출 가능.
"""
from .fixtures import (
    JD_SCENARIOS,
    CANDIDATE_FIXTURES,
    EVALUATION_FIXTURES,
    WEIGHT_RECOMMENDATIONS,
    list_demo_candidates,
)

__all__ = [
    "JD_SCENARIOS",
    "CANDIDATE_FIXTURES",
    "EVALUATION_FIXTURES",
    "WEIGHT_RECOMMENDATIONS",
    "list_demo_candidates",
]
