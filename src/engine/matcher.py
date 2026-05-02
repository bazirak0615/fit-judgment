import json
from src.llm import generate_json
from .schema import Weights, HardGates
from .hard_gates import apply_hard_gates


def _format_dimensions(weights: Weights) -> str:
    lines = []
    for d in weights.dimensions:
        cat = "필수" if d.category == "must" else "우대"
        lines.append(f"- [{cat}] {d.name} (가중치 {d.weight*100:.0f}%): {d.description}")
    return "\n".join(lines)


def _format_hard_gates(gates: HardGates) -> str:
    parts = [
        f"- 필수 항목 최저 점수: {gates.min_score_per_must}점 미만 시 부적합",
        f"- 정보 미기재 시 등급 1단계 하향: {'예' if gates.info_missing_downgrade else '아니오'}",
    ]
    if gates.avoidance_keywords:
        parts.append(f"- 회피 키워드: {', '.join(gates.avoidance_keywords)}")
    return "\n".join(parts)


def evaluate_candidate(
    jd_structured: dict,
    candidate_structured: dict,
    weights: Weights,
    hard_gates: HardGates,
    model: str = "qwen2.5:14b",
    candidate_text: str = "",
) -> dict:
    """LLM 평가 + 코드 레벨 하드 게이트 후처리.

    candidate_text: 회피 키워드 검색용 원본 이력서 텍스트 (옵션). 비어있으면
                    candidate_structured를 직렬화한 텍스트에서 검색.
    """
    result = generate_json(
        "dimension_eval",
        {
            "jd_structured": json.dumps(jd_structured, ensure_ascii=False, indent=2),
            "candidate_structured": json.dumps(candidate_structured, ensure_ascii=False, indent=2),
            "dimensions_with_weights": _format_dimensions(weights),
            "hard_gates": _format_hard_gates(hard_gates),
        },
        model=model,
        temperature=0.1,
    )

    # 코드 레벨 하드 게이트 강제 (LLM 자유재량 보완)
    text_for_search = candidate_text or json.dumps(candidate_structured, ensure_ascii=False)
    return apply_hard_gates(result, hard_gates, candidate_text=text_for_search)
