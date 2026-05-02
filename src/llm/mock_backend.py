"""Mock LLM 백엔드 — LLM 호출 없이 동작하는 데모 모드.

LLM 호출 없이 사전 정의된 시나리오 응답을 반환합니다.
- jd_extract: JD 텍스트 키워드로 시나리오 매칭
- candidate_extract: 이력서 텍스트 키워드로 후보자 매칭
- dimension_eval: (jd, candidate) 페어로 평가 결과 매칭
- weight_recommend: JD 시나리오별 추천

매칭 실패 시 휴리스틱으로 그럴듯한 응답을 동적 생성합니다.
"""
from __future__ import annotations

import json
import os
import time
import hashlib
import random
import re
from typing import Any

from mocks import (
    JD_SCENARIOS,
    CANDIDATE_FIXTURES,
    EVALUATION_FIXTURES,
    WEIGHT_RECOMMENDATIONS,
)


# ============================================================
#  Helpers
# ============================================================

def _maybe_sleep() -> None:
    """실제 추론처럼 보이도록 약간의 지연 (환경변수로 끌 수 있음)."""
    if os.getenv("MOCK_NO_DELAY"):
        return
    time.sleep(random.uniform(0.4, 1.2))


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower())


def _score_keyword_match(text: str, keywords: list[str]) -> int:
    """텍스트 안에 키워드가 몇 개 들어있는지."""
    norm = _normalize(text)
    return sum(1 for kw in keywords if kw.lower() in norm)


def _match_jd(jd_text: str) -> dict[str, Any] | None:
    """JD 텍스트에서 가장 잘 매칭되는 시나리오 찾기."""
    best = None
    best_score = 0
    for scenario in JD_SCENARIOS.values():
        score = _score_keyword_match(jd_text, scenario["match_keywords"])
        if score > best_score:
            best = scenario
            best_score = score
    return best if best_score >= 2 else None


def _match_candidate(resume_text: str) -> dict[str, Any] | None:
    """이력서 텍스트에서 가장 잘 매칭되는 후보자 찾기."""
    best = None
    best_score = 0
    for cand in CANDIDATE_FIXTURES.values():
        score = _score_keyword_match(resume_text, cand["match_keywords"])
        if score > best_score:
            best = cand
            best_score = score
    return best if best_score >= 1 else None


def _stable_hash_int(text: str, modulo: int = 100) -> int:
    """텍스트 기반 결정적 정수 (fallback에서 일관된 점수 생성용)."""
    h = hashlib.md5(text.encode("utf-8")).hexdigest()
    return int(h, 16) % modulo


# ============================================================
#  jd_extract
# ============================================================

def _mock_jd_extract(variables: dict) -> dict:
    jd_text = variables.get("jd_text", "")
    matched = _match_jd(jd_text)
    if matched:
        return matched["structured"]

    # Fallback — JD 첫 줄에서 직책명 추출
    first_line = jd_text.strip().split("\n")[0][:80] if jd_text else ""
    title = re.sub(r"^[#\s]+", "", first_line) or "포지션"

    # 키워드 빈도 단순 추출
    words = re.findall(r"[가-힣A-Za-z]{3,}", jd_text or "")
    word_freq: dict[str, int] = {}
    for w in words:
        word_freq[w] = word_freq.get(w, 0) + 1
    top_keywords = sorted(word_freq.items(), key=lambda x: -x[1])[:5]

    return {
        "position_title": title,
        "company": "",
        "domain": [],
        "seniority_level": "Mid",
        "must_have": [
            "관련 분야 경력 5년 이상",
            "팀 협업 경험",
        ],
        "nice_to_have": ["관련 도메인 경험"],
        "key_responsibilities": ["JD에 명시된 핵심 업무 (Mock fallback)"],
        "hidden_criteria": [],
        "avoidance_signals": [],
        "emphasis_keywords": [
            {"keyword": kw, "frequency": freq, "context": "자동 추출"}
            for kw, freq in top_keywords
        ],
    }


# ============================================================
#  candidate_extract
# ============================================================

def _mock_candidate_extract(variables: dict) -> dict:
    resume_text = variables.get("resume_text", "")
    matched = _match_candidate(resume_text)
    if matched:
        return matched["structured"]

    # Fallback — 이름·연차 추출 시도
    name_match = re.search(r"^([가-힣]{2,4})", resume_text.strip())
    name = name_match.group(1) if name_match else "익명 후보자"

    years_match = re.search(r"(\d+)년차", resume_text)
    years = int(years_match.group(1)) if years_match else _stable_hash_int(resume_text, 12) + 3

    return {
        "candidate_name": name,
        "total_experience_years": years,
        "current_title": "직책 미기재",
        "career_history": [],
        "skills": {"technical": [], "domain": [], "language": [{"name": "영어", "level": "미기재"}]},
        "leadership_signals": [],
        "stability_signals": {"shortest_tenure_months": 12, "longest_tenure_months": years * 12, "recent_3_avg_months": years * 4},
    }


# ============================================================
#  dimension_eval
# ============================================================

def _resolve_jd_id(jd_structured: dict | str) -> str | None:
    """jd_structured에서 시나리오 id 추정."""
    if isinstance(jd_structured, str):
        try:
            jd_structured = json.loads(jd_structured)
        except Exception:
            return None
    title = (jd_structured.get("position_title") or "").lower()
    company = (jd_structured.get("company") or "").lower()
    for sid, s in JD_SCENARIOS.items():
        st = s["structured"]
        if title and title == (st.get("position_title") or "").lower():
            return sid
        if company and company == (st.get("company") or "").lower():
            return sid
    return None


def _resolve_candidate_id(candidate_structured: dict | str) -> str | None:
    if isinstance(candidate_structured, str):
        try:
            candidate_structured = json.loads(candidate_structured)
        except Exception:
            return None
    name = (candidate_structured.get("candidate_name") or "").lower()
    title = (candidate_structured.get("current_title") or "").lower()
    for cid, c in CANDIDATE_FIXTURES.items():
        cs = c["structured"]
        if name and name == (cs.get("candidate_name") or "").lower():
            return cid
        if title and title == (cs.get("current_title") or "").lower():
            return cid
    return None


def _parse_dimensions_str(dim_str: str) -> list[dict]:
    """'- [필수] Hard Skills (가중치 30%): 필수 스킬·도구 매칭' 형식 파싱."""
    out = []
    for line in dim_str.split("\n"):
        m = re.match(r"-\s*\[(필수|우대)\]\s*(.+?)\s*\(가중치\s*(\d+)%\)\s*:\s*(.+)", line.strip())
        if m:
            out.append({
                "category": m.group(1),
                "name": m.group(2).strip(),
                "weight": int(m.group(3)) / 100,
                "description": m.group(4).strip(),
            })
    return out


def _heuristic_evaluation(jd_structured: dict | str, candidate_structured: dict | str, dim_str: str) -> dict:
    """매칭 실패 시 휴리스틱으로 그럴듯한 평가 생성."""
    if isinstance(jd_structured, str):
        try:
            jd_structured = json.loads(jd_structured)
        except Exception:
            jd_structured = {}
    if isinstance(candidate_structured, str):
        try:
            candidate_structured = json.loads(candidate_structured)
        except Exception:
            candidate_structured = {}

    cand_name = candidate_structured.get("candidate_name", "후보자")
    dims_meta = _parse_dimensions_str(dim_str) or [
        {"name": "Hard Skills", "category": "필수", "weight": 0.3, "description": "필수 스킬"},
        {"name": "Experience", "category": "필수", "weight": 0.3, "description": "경험"},
        {"name": "Achievements", "category": "필수", "weight": 0.2, "description": "성과"},
        {"name": "Domain Fit", "category": "우대", "weight": 0.15, "description": "도메인"},
        {"name": "Seniority", "category": "우대", "weight": 0.05, "description": "레벨"},
    ]

    # 기본 점수: 후보자 텍스트와 JD must_have 매칭 키워드 수로 결정
    cand_text_dump = json.dumps(candidate_structured, ensure_ascii=False)
    must_have = jd_structured.get("must_have", [])
    nice_have = jd_structured.get("nice_to_have", [])
    must_match = sum(1 for m in must_have if any(kw in cand_text_dump for kw in re.findall(r"[가-힣A-Za-z]{3,}", m)[:2]))
    nice_match = sum(1 for m in nice_have if any(kw in cand_text_dump for kw in re.findall(r"[가-힣A-Za-z]{3,}", m)[:2]))

    base_score = 40 + min(must_match * 8, 35) + min(nice_match * 4, 15)
    base_score = max(20, min(base_score, 90))

    dimensions = []
    for i, d in enumerate(dims_meta):
        # 차원별 약간의 변동
        delta = _stable_hash_int(f"{cand_name}_{d['name']}", 21) - 10
        score = max(15, min(base_score + delta, 95))
        fit = "○" if score >= 75 else ("△" if score >= 50 else "✗")
        dimensions.append({
            "name": d["name"],
            "category": d["category"],
            "score": score,
            "weight": d["weight"],
            "fit": fit,
            "summary": f"{d['name']} 영역에서 {fit} 수준의 매칭 (휴리스틱 평가)",
            "matched": [must_have[0]] if must_have and i == 0 else [],
            "missing": [must_have[1]] if len(must_have) > 1 and score < 60 else [],
            "evidence": "Mock 백엔드의 휴리스틱 평가입니다. 실제 LLM 연동 시 후보자 이력서에서 직접 인용된 근거가 표시됩니다.",
            "info_status": "충분" if score >= 60 else "부족",
        })

    weighted = sum(d["score"] * d["weight"] for d in dimensions)
    overall = int(round(weighted))

    if overall >= 75:
        rec = "면접 추천"
    elif overall >= 55:
        rec = "보류"
    else:
        rec = "부적합"

    return {
        "overall_score": overall,
        "weighted_score": round(weighted, 1),
        "recommendation": rec,
        "hard_gate_triggered": [],
        "dimensions": dimensions,
        "verification_points": [
            {"point": f"{cand_name}의 핵심 경력 정량 임팩트", "reason": "휴리스틱 평가의 보완 필요"},
        ],
        "risks": ["Mock 평가 — 실제 LLM 연동 시 더 정확한 리스크 분석 가능"],
        "strengths": [f"{cand_name}: 휴리스틱 점수 {overall}"],
        "one_line_summary": f"Mock 평가 — 종합 {overall}점, {rec}",
    }


def _mock_dimension_eval(variables: dict) -> dict:
    jd_id = _resolve_jd_id(variables.get("jd_structured", {}))
    cand_id = _resolve_candidate_id(variables.get("candidate_structured", {}))

    if jd_id and cand_id and (jd_id, cand_id) in EVALUATION_FIXTURES:
        return EVALUATION_FIXTURES[(jd_id, cand_id)]

    return _heuristic_evaluation(
        variables.get("jd_structured", {}),
        variables.get("candidate_structured", {}),
        variables.get("dimensions_with_weights", ""),
    )


# ============================================================
#  weight_recommend
# ============================================================

def _mock_weight_recommend(variables: dict) -> dict:
    jd_id = _resolve_jd_id(variables.get("jd_structured", {}))
    if jd_id and jd_id in WEIGHT_RECOMMENDATIONS:
        return WEIGHT_RECOMMENDATIONS[jd_id]

    # Fallback — 기본 추천
    default = json.loads(variables.get("default_weights", "{}")) if isinstance(variables.get("default_weights"), str) else variables.get("default_weights", {})
    return {
        "adjustments": [
            {"dimension": name, "default": w, "recommended": w, "delta": 0.0,
             "reason": "Mock 백엔드 — 기본값 유지 (실제 LLM 연동 시 JD 분석 기반 추천)"}
            for name, w in default.items()
        ],
        "final_weights": default,
        "warnings": ["Mock 백엔드 — JD 매칭 실패로 기본값 사용"],
    }


# ============================================================
#  Public API
# ============================================================

PROMPT_HANDLERS = {
    "jd_extract": _mock_jd_extract,
    "candidate_extract": _mock_candidate_extract,
    "dimension_eval": _mock_dimension_eval,
    "weight_recommend": _mock_weight_recommend,
}


def mock_generate_json(prompt_name: str, variables: dict, model: str | None = None, temperature: float = 0.2) -> dict:
    """generate_json의 mock 버전. 백엔드 분기에서 호출됨."""
    handler = PROMPT_HANDLERS.get(prompt_name)
    if not handler:
        raise ValueError(f"Mock backend: unknown prompt '{prompt_name}'")
    _maybe_sleep()
    return handler(variables)


def is_mock_backend() -> bool:
    return os.getenv("LLM_BACKEND", "ollama").lower() == "mock"
