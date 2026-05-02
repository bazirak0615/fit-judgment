"""하드 게이트 코드 강제 후처리.

LLM이 반환한 평가 결과(result)에 하드 게이트 룰을 코드 레벨로 적용:
1. 필수 차원 점수 < min_score_per_must → 발동 + 추천 등급 1단계 하향
2. info_status="미기재"이고 info_missing_downgrade=True → 등급 1단계 하향
3. 후보자 텍스트에 회피 키워드 매칭 → 발동 + risks 추가

이는 LLM의 자유 재량에 의한 누락을 방지하기 위한 결정적 안전장치다.
"""
from __future__ import annotations

from .schema import HardGates


REC_LEVELS = ["면접 강력 추천", "면접 추천", "보류", "부적합"]


def _downgrade(rec: str | None, steps: int = 1) -> str:
    """추천 등급을 N단계 하향."""
    if not rec:
        return "보류"
    try:
        idx = REC_LEVELS.index(rec)
    except ValueError:
        return rec
    new_idx = min(idx + steps, len(REC_LEVELS) - 1)
    return REC_LEVELS[new_idx]


def apply_hard_gates(
    result: dict,
    gates: HardGates,
    candidate_text: str = "",
) -> dict:
    """평가 결과에 하드 게이트를 코드 레벨로 강제 적용.

    Args:
        result: LLM이 반환한 평가 dict (mutated in-place + returned)
        gates: HardGates 설정 (min_score_per_must, info_missing_downgrade, avoidance_keywords)
        candidate_text: 후보자 원문 (회피 키워드 검색용, 비어있으면 result 안에서만 검색)

    Returns:
        result (수정된 dict — hard_gate_triggered 보강 + recommendation 하향 가능)
    """
    triggered: list[str] = list(result.get("hard_gate_triggered") or [])
    downgrade_steps = 0

    dimensions = result.get("dimensions") or []

    # Rule 1: 필수 차원 최저 점수 미달
    for d in dimensions:
        cat = d.get("category", "")
        if cat in ("필수", "must"):
            score = d.get("score")
            if score is None:
                continue
            try:
                score_val = float(score)
            except (ValueError, TypeError):
                continue
            if score_val < gates.min_score_per_must:
                msg = f"필수 차원 '{d.get('name', '?')}' 점수 {score_val:.0f} < 최저 {gates.min_score_per_must}"
                if msg not in triggered:
                    triggered.append(msg)
                downgrade_steps = max(downgrade_steps, 1)

    # Rule 2: 정보 미기재 시 등급 하향
    if gates.info_missing_downgrade:
        missing_count = sum(1 for d in dimensions if d.get("info_status") in ("미기재",))
        partial_count = sum(1 for d in dimensions if d.get("info_status") in ("부족",))
        if missing_count > 0:
            msg = f"정보 미기재 차원 {missing_count}개 — 등급 1단계 하향"
            if msg not in triggered:
                triggered.append(msg)
            downgrade_steps = max(downgrade_steps, 1)
        elif partial_count >= len(dimensions) // 2 and dimensions:
            # 절반 이상이 정보 부족이면 하향
            msg = f"정보 부족 차원 {partial_count}개 (전체 {len(dimensions)}) — 등급 1단계 하향"
            if msg not in triggered:
                triggered.append(msg)
            downgrade_steps = max(downgrade_steps, 1)

    # Rule 3: 회피 키워드 매칭
    if gates.avoidance_keywords:
        haystack = candidate_text.lower() if candidate_text else ""
        # result 안의 evidence·근거 텍스트도 함께 검색
        for d in dimensions:
            for fld in ("evidence", "summary"):
                v = d.get(fld) or ""
                if isinstance(v, str):
                    haystack += " " + v.lower()
        for kw in gates.avoidance_keywords:
            if kw.strip() and kw.lower() in haystack:
                msg = f"회피 키워드 '{kw}' 매칭"
                if msg not in triggered:
                    triggered.append(msg)
                # risks에도 추가
                risks = result.get("risks") or []
                risk_msg = f"하드 게이트 회피 키워드 매칭: '{kw}'"
                if risk_msg not in risks:
                    risks.append(risk_msg)
                result["risks"] = risks
                downgrade_steps = max(downgrade_steps, 1)

    # 최종 적용
    result["hard_gate_triggered"] = triggered
    if downgrade_steps > 0:
        original_rec = result.get("recommendation")
        new_rec = _downgrade(original_rec, downgrade_steps)
        if new_rec != original_rec:
            result["recommendation"] = new_rec
            # one_line_summary에도 가벼운 표시
            ols = result.get("one_line_summary") or ""
            if "하드 게이트" not in ols:
                result["one_line_summary"] = (ols + " | 하드 게이트 발동").strip(" |")

    return result
