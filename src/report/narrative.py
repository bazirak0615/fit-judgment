"""평가 결과를 사람이 읽기 좋은 형태의 문장·면접 질문으로 변환."""
from __future__ import annotations


REC_RATIONALE_TEMPLATES = {
    "면접 강력 추천": "JD가 요구하는 핵심 영역에서 압도적인 매칭이 확인됐습니다. 강점 검증 위주의 면접을 권장합니다.",
    "면접 추천": "주요 필수 요건을 충족하며 정량 성과가 명확합니다. 검증 포인트 중심으로 면접을 진행하세요.",
    "보류": "필수 요건 일부에서 갭이 있고, 일부 영역의 정보가 부족합니다. 전화/숏폼 인터뷰로 보완 검증 후 본면접 판단을 권장합니다.",
    "부적합": "JD가 명시한 필수 자격 또는 회피 신호에서 명확한 미스매치가 확인됐습니다. 본면접 진행은 권장되지 않습니다.",
}


def build_recommendation_narrative(result: dict) -> str:
    """추천 등급 결정 사유를 3~5줄 narrative로 생성."""
    rec = result.get("recommendation", "보류")
    overall = result.get("overall_score", 0)
    base = REC_RATIONALE_TEMPLATES.get(rec, REC_RATIONALE_TEMPLATES["보류"])

    dims = result.get("dimensions", [])
    must_dims = [d for d in dims if d.get("category") in ("필수", "must")]
    nice_dims = [d for d in dims if d.get("category") in ("우대", "nice")]

    must_avg = sum(d.get("score", 0) for d in must_dims) / max(len(must_dims), 1)
    nice_avg = sum(d.get("score", 0) for d in nice_dims) / max(len(nice_dims), 1)

    weak_dims = [d for d in dims if d.get("fit") in ("✗", "△") and d.get("category") in ("필수", "must")]
    strong_dims = [d for d in dims if d.get("fit") == "○"]

    parts = [
        f"**종합 점수 {overall}점 — '{rec}'**",
        f"필수 평균 {must_avg:.0f}점 / 우대 평균 {nice_avg:.0f}점.",
        base,
    ]

    if weak_dims:
        names = ", ".join(f"`{d['name']}`" for d in weak_dims[:3])
        parts.append(f"필수 영역 중 {names}에서 갭이 확인됩니다 — 면접에서 우선 검증 권장.")
    if strong_dims:
        names = ", ".join(f"`{d['name']}`" for d in strong_dims[:3])
        parts.append(f"강점 영역: {names}")

    if result.get("hard_gate_triggered"):
        parts.append(f"⚠ 하드 게이트 발동: {', '.join(result['hard_gate_triggered'])}")

    return "\n\n".join(parts)


# ============================================================
#  면접 질문 자동 생성 — 차원별 매칭/부족 항목과 검증 포인트를 결합
# ============================================================

QUESTION_TEMPLATES = {
    "matched": [
        "이력서에 기재된 '{item}' 경험에 대해 — 본인의 직접 기여 영역과 팀 기여 영역을 구분해 설명해주세요.",
        "'{item}'의 결과(수치/임팩트)는 어떤 의사결정과 액션이 핵심이었나요?",
    ],
    "missing": [
        "'{item}' 경험이 이력서에 없는데 — 유사한 경험이나 학습 계획이 있다면 알려주세요.",
        "'{item}'을 빠르게 익혀야 한다면 어떤 접근으로 시작하시겠어요?",
    ],
    "verification": [
        "{point}",
    ],
    "general": [
        "이전 회사에서 가장 큰 실패 경험과 거기서 배운 점은?",
        "팀과 의견 충돌이 생겼을 때 어떻게 해결하시는지 사례로 설명해주세요.",
    ],
}


def build_interview_questions(result: dict, max_per_dimension: int = 2, max_total: int = 10) -> list[dict]:
    """차원별로 면접 질문 자동 생성. dim_name별 그룹핑."""
    out: list[dict] = []
    for d in result.get("dimensions", []):
        dim_name = d.get("name", "차원")
        questions = []

        # 강점 검증 (matched 항목 중 1개)
        for item in d.get("matched", [])[:1]:
            tmpl = QUESTION_TEMPLATES["matched"][0]
            questions.append({"type": "강점 검증", "text": tmpl.format(item=item)})

        # 갭 확인 (missing 항목 중 1개)
        for item in d.get("missing", [])[:1]:
            tmpl = QUESTION_TEMPLATES["missing"][0]
            questions.append({"type": "갭 확인", "text": tmpl.format(item=item)})

        if questions:
            out.append({"dimension": dim_name, "questions": questions[:max_per_dimension]})

    # 검증 포인트 별도 그룹
    vp = result.get("verification_points") or []
    if vp:
        vp_questions = []
        for v in vp[:3]:
            if isinstance(v, dict):
                vp_questions.append({"type": "검증 포인트", "text": v.get("point", ""), "reason": v.get("reason", "")})
            else:
                vp_questions.append({"type": "검증 포인트", "text": str(v), "reason": ""})
        if vp_questions:
            out.append({"dimension": "검증 포인트 (Cross-cutting)", "questions": vp_questions})

    # 공통 질문 (always 추가)
    out.append({"dimension": "공통 컬처/협업 질문", "questions": [
        {"type": "공통", "text": q} for q in QUESTION_TEMPLATES["general"]
    ]})

    # 총 max_total 제한
    total = 0
    truncated = []
    for grp in out:
        remaining = max_total - total
        if remaining <= 0:
            break
        truncated.append({**grp, "questions": grp["questions"][:remaining]})
        total += len(grp["questions"][:remaining])
    return truncated


# ============================================================
#  비교 narrative — 후보자 간 차이를 텍스트로 요약
# ============================================================

def build_comparison_summary(results: list[dict]) -> str:
    """여러 후보자 결과를 비교해 narrative로 요약. results: [{"label": ..., "result": ...}]"""
    if len(results) < 2:
        return ""
    valid = [r for r in results if "error" not in (r.get("result") or {})]
    if len(valid) < 2:
        return ""

    sorted_r = sorted(valid, key=lambda r: r["result"].get("overall_score", 0), reverse=True)
    top = sorted_r[0]
    second = sorted_r[1] if len(sorted_r) > 1 else None
    last = sorted_r[-1]

    top_score = top["result"].get("overall_score", 0)
    last_score = last["result"].get("overall_score", 0)

    parts = [
        f"### 비교 요약 (총 {len(valid)}명)",
        f"- **1위**: `{top['label']}` ({top_score}점, {top['result'].get('recommendation','')})",
    ]
    if second:
        gap = top_score - second["result"].get("overall_score", 0)
        parts.append(f"- **2위와의 격차**: {gap}점")
    parts.append(f"- **점수 분포**: {last_score} ~ {top_score} (격차 {top_score - last_score}점)")

    # 추천 분포
    rec_counts: dict[str, int] = {}
    for r in valid:
        rec = r["result"].get("recommendation", "—")
        rec_counts[rec] = rec_counts.get(rec, 0) + 1
    rec_str = ", ".join(f"{k} {v}명" for k, v in rec_counts.items())
    parts.append(f"- **추천 분포**: {rec_str}")

    # 하드 게이트 발동자
    gate_triggered = [r["label"] for r in valid if r["result"].get("hard_gate_triggered")]
    if gate_triggered:
        parts.append(f"- **⚠ 하드 게이트 발동**: {', '.join(gate_triggered)}")

    return "\n".join(parts)
