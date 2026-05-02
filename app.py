import json
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.parsers import parse_file, load_json_candidates, MAX_CANDIDATES_PER_JSON
from src.engine import (
    DEFAULT_DIMENSIONS,
    DEFAULT_HARD_GATES,
    Dimension,
    HardGates,
    Weights,
    extract_jd,
    extract_candidate,
    evaluate_candidate,
)
from src.weights import recommend_weights, rebalance
from src.db import (
    init_db,
    save_evaluation,
    list_evaluations,
    list_evaluations_grouped,
    get_evaluation_detail,
    delete_evaluation,
    save_preset,
    list_presets,
    delete_preset,
    bump_preset_usage,
)
from src.llm import check_status, get_backend
from src.report import (
    dimension_radar,
    dimension_bar,
    ranking_bar,
    build_recommendation_narrative,
    build_interview_questions,
    build_comparison_summary,
)


st.set_page_config(page_title="적합인재 판단기", layout="wide")
init_db()


SESSION_FILE = Path(__file__).resolve().parent / "data" / "last_session.json"
SESSION_BACKUP = Path(__file__).resolve().parent / "data" / "last_session.json.bak"


def _load_session() -> dict:
    """디스크에 저장된 직전 세션을 불러옴. 손상됐으면 백업 시도. 없으면 빈 dict."""
    for path in (SESSION_FILE, SESSION_BACKUP):
        try:
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
    return {}


def _save_session() -> None:
    """현재 session_state의 핵심 작업 상태를 디스크에 영속화. 빈 값 덮어쓰기 가드 + 백업."""
    try:
        ss = st.session_state
        hg = ss.get("hard_gates")
        new_data = {
            "step": ss.get("step", 1),
            "jd_text": ss.get("jd_text", "") or "",
            "jd_structured": ss.get("jd_structured"),
            "dimensions": [
                {"name": d.name, "category": d.category, "weight": d.weight, "description": d.description}
                for d in ss.get("dimensions", [])
            ],
            "hard_gates": {
                "min_score_per_must": hg.min_score_per_must,
                "info_missing_downgrade": hg.info_missing_downgrade,
                "avoidance_keywords": list(hg.avoidance_keywords),
            } if hg else None,
            "model_name": ss.get("model_name"),
        }

        # 가드: 디스크에 유효한 JD가 있는데 메모리는 비어있으면 — 덮어쓰기 거부
        if SESSION_FILE.exists():
            try:
                existing = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
            disk_has_jd = bool(existing.get("jd_structured")) or bool(existing.get("jd_text", "").strip())
            mem_has_jd = bool(new_data.get("jd_structured")) or bool(new_data.get("jd_text", "").strip())
            if disk_has_jd and not mem_has_jd:
                return  # 빈 메모리로 유효한 디스크 데이터를 파괴하지 않음

            # 백업: 기존 파일을 .bak으로 옮김
            try:
                SESSION_BACKUP.write_text(SESSION_FILE.read_text(encoding="utf-8"), encoding="utf-8")
            except Exception:
                pass

        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(json.dumps(new_data, ensure_ascii=False, indent=2), encoding="utf-8")
        st.session_state["_last_save_ts"] = pd.Timestamp.now().strftime("%H:%M:%S")
    except Exception as e:
        st.session_state["_last_save_error"] = str(e)


def _clear_session_file() -> None:
    try:
        SESSION_FILE.unlink(missing_ok=True)
        SESSION_BACKUP.unlink(missing_ok=True)
    except Exception:
        pass


# ---------- Session state ----------
def _init_state():
    ss = st.session_state
    saved = _load_session() if not ss.get("_session_loaded") else {}
    ss["_session_loaded"] = True

    ss.setdefault("step", saved.get("step", 1))
    ss.setdefault("jd_text", saved.get("jd_text", ""))
    ss.setdefault("jd_structured", saved.get("jd_structured"))

    if saved.get("dimensions"):
        ss.setdefault("dimensions", [
            Dimension(
                name=d["name"],
                category=d.get("category", "must"),
                weight=float(d.get("weight", 0.0)),
                description=d.get("description", ""),
            ) for d in saved["dimensions"]
        ])
    else:
        ss.setdefault("dimensions", [Dimension(d.name, d.category, d.weight, d.description) for d in DEFAULT_DIMENSIONS])

    if saved.get("hard_gates"):
        hg = saved["hard_gates"]
        ss.setdefault("hard_gates", HardGates(
            min_score_per_must=int(hg.get("min_score_per_must", DEFAULT_HARD_GATES.min_score_per_must)),
            info_missing_downgrade=bool(hg.get("info_missing_downgrade", DEFAULT_HARD_GATES.info_missing_downgrade)),
            avoidance_keywords=list(hg.get("avoidance_keywords", [])),
        ))
    else:
        ss.setdefault("hard_gates", HardGates(
            min_score_per_must=DEFAULT_HARD_GATES.min_score_per_must,
            info_missing_downgrade=DEFAULT_HARD_GATES.info_missing_downgrade,
            avoidance_keywords=list(DEFAULT_HARD_GATES.avoidance_keywords),
        ))

    ss.setdefault("ai_recommendation", None)
    ss.setdefault("results", [])
    ss.setdefault("model_name", saved.get("model_name") or "qwen2.5:7b")


_init_state()


# ---------- Helpers ----------
def _read_uploaded(uploaded) -> str:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name
    try:
        return parse_file(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _expand_uploaded_to_candidates(uploaded) -> list[dict]:
    """
    업로드된 파일을 후보자 항목 리스트로 변환.
    - JSON: 1~100명 (배열/래핑 객체/단일 객체 자동 인식)
    - 기타: 파일 1개 = 후보자 1명
    """
    suffix = Path(uploaded.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = tmp.name
    try:
        if suffix == ".json":
            items = load_json_candidates(tmp_path)
            return [{"label": it["label"], "text": it["resume_text"]} for it in items]
        text = parse_file(tmp_path)
        return [{"label": uploaded.name, "text": text}]
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _current_weights() -> Weights:
    return Weights(dimensions=st.session_state.dimensions)


def _format_score(score) -> str:
    if score is None:
        return "—"
    return f"{score:.1f}"


DIMENSION_JD_FIELDS: dict[str, list[str]] = {
    "Hard Skills": ["must_have"],
    "Experience": ["key_responsibilities"],
    "Achievements": ["emphasis_keywords", "hidden_criteria"],
    "Domain Fit": ["domain", "nice_to_have"],
    "Seniority": ["seniority_level"],
    "전략 컨설팅·신사업 실행": ["must_have"],
    "Framework 사업성 판단": ["must_have"],
    "사업계획·P&L 수립": ["must_have"],
    "비즈니스 영어": ["must_have"],
    "재직 안정성": ["hidden_criteria", "avoidance_signals"],
    "헬스케어 산업 경험": ["domain"],
    "글로벌 사업 경험": ["nice_to_have"],
}

DIMENSION_PURPOSE: dict[str, str] = {
    "Hard Skills": "JD가 명시한 **필수 자격·스킬**을 후보자가 충족하는지 (이 항목 자체의 보유 여부)",
    "Experience": "JD가 요구하는 **수행 업무**를 후보자가 실제로 해본 적 있는지 (직무 유사도·연차)",
    "Achievements": "JD가 **강조한 키워드**나 **숨은 기준**(검토 노트)에 후보자가 부합하는 성과 신호를 가졌는지",
    "Domain Fit": "후보자의 **산업/도메인 배경**이 JD와 맞는지 (도메인 일치 + 우대 산업 경험)",
    "Seniority": "후보자의 **연차·역할 레벨**이 JD가 기대하는 시니어리티와 맞는지",
}

JD_FIELD_LABELS: dict[str, str] = {
    "must_have": "필수 요건",
    "nice_to_have": "우대 사항",
    "key_responsibilities": "주요 업무",
    "domain": "산업/도메인",
    "seniority_level": "시니어리티 레벨",
    "emphasis_keywords": "강조 키워드",
    "hidden_criteria": "숨은 기준",
    "avoidance_signals": "회피 신호",
}


def _render_jd_field(field: str, value) -> None:
    if not value:
        return
    label = JD_FIELD_LABELS.get(field, field)
    st.markdown(f"**{label}**")
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                kw = item.get("keyword") or item.get("name") or ""
                ctx = item.get("context")
                freq = item.get("frequency")
                meta = []
                if freq is not None:
                    meta.append(f"{freq}회")
                if ctx:
                    meta.append(ctx)
                meta_str = f" — _{', '.join(meta)}_" if meta else ""
                st.markdown(f"- {kw}{meta_str}")
            else:
                st.markdown(f"- {item}")
    elif isinstance(value, str):
        st.markdown(f"- {value}")
    else:
        st.markdown(f"- {value}")


def _render_dimension_evidence(dim_name: str, jd: dict) -> None:
    """차원별 JD 기준 표시. 매핑이 없으면 JD 전체로 폴백."""
    if not jd:
        st.caption("JD가 아직 구조화되지 않았습니다.")
        return

    purpose = DIMENSION_PURPOSE.get(dim_name)
    if purpose:
        st.info(f"**평가 기준**: {purpose}")

    fields = DIMENSION_JD_FIELDS.get(dim_name)
    if not fields:
        st.caption("이 차원은 JD 매핑이 정의되지 않아 전체 JD를 표시합니다.")
        st.json(jd)
        return
    rendered_any = False
    for f in fields:
        v = jd.get(f)
        if v:
            _render_jd_field(f, v)
            rendered_any = True
    if not rendered_any:
        st.caption("JD에서 이 차원에 해당하는 항목이 추출되지 않았습니다.")


def _apply_preset(preset: dict) -> None:
    """프리셋의 가중치/하드 게이트를 session_state에 반영. 콜백 안전."""
    weights_dict = preset.get("weights", {})
    new_dims = []
    for name, info in weights_dict.items():
        if isinstance(info, dict):
            new_dims.append(Dimension(
                name=name,
                category=info.get("category", "must"),
                weight=float(info.get("weight", 0.0)),
                description=info.get("description", ""),
            ))
    if new_dims:
        st.session_state.dimensions = new_dims
        # 슬라이더/숫자입력 위젯의 stored value도 함께 갱신해야 UI가 바뀜
        for d in new_dims:
            st.session_state[f"slider_{d.name}"] = float(d.weight)
            st.session_state[f"num_{d.name}"] = float(d.weight)

    hg = preset.get("hard_gates") or {}
    if hg:
        st.session_state.hard_gates = HardGates(
            min_score_per_must=int(hg.get("min_score_per_must", DEFAULT_HARD_GATES.min_score_per_must)),
            info_missing_downgrade=bool(hg.get("info_missing_downgrade", DEFAULT_HARD_GATES.info_missing_downgrade)),
            avoidance_keywords=list(hg.get("avoidance_keywords", [])),
        )

    bump_preset_usage(preset["id"])
    _save_session()


def _apply_preset_and_redirect(preset: dict) -> None:
    """프리셋 적용 + '새 평가' 페이지로 이동. on_click 콜백 전용."""
    _apply_preset(preset)
    st.session_state.page = "새 평가"
    if st.session_state.get("step", 1) < 2:
        st.session_state.step = 2
    st.session_state["_flash"] = f"'{preset['name']}' 프리셋 적용 완료 — 새 평가 화면입니다."


def _apply_preset_inplace(preset: dict) -> None:
    """프리셋 적용만 수행. on_click 콜백 전용."""
    _apply_preset(preset)
    st.session_state["_flash"] = f"'{preset['name']}' 프리셋 적용 완료"


def _delete_preset_callback(preset_id: int) -> None:
    delete_preset(preset_id)


# ---------- Sidebar ----------
with st.sidebar:
    st.title("적합인재 판단기")
    backend = get_backend()
    if backend == "mock":
        st.caption(":violet[**[DEMO]**] Mock 모드 — 사전 정의 응답 (LLM 호출 없음)")
    elif backend == "anthropic":
        st.caption(":blue[**[CLOUD]**] Anthropic Claude API")
    elif backend == "openai":
        st.caption(":blue[**[CLOUD]**] OpenAI GPT API")
    else:
        st.caption(":green[**[LOCAL]**] 로컬 LLM (Ollama)")

    status = check_status(st.session_state.model_name)
    if not status["ok"]:
        st.error("⚠ Ollama 서버에 연결할 수 없습니다.")
        with st.expander("해결 방법"):
            st.markdown(
                "**Windows**: Ollama 앱을 실행하거나, 터미널에서 다음 명령:\n\n"
                "```\nollama serve\n```\n\n"
                f"오류: `{status['error']}`"
            )
        st.session_state.model_name = st.text_input(
            "Ollama 모델",
            value=st.session_state.model_name,
            help="서버 연결 후 자동으로 목록이 표시됩니다.",
        )
    elif not status["models"]:
        st.warning("⚠ 설치된 모델이 없습니다.")
        st.markdown(
            "터미널에서 모델을 받으세요:\n\n"
            f"```\nollama pull {st.session_state.model_name}\n```"
        )
        st.session_state.model_name = st.text_input(
            "Ollama 모델",
            value=st.session_state.model_name,
        )
    else:
        options = status["models"]
        current = st.session_state.model_name
        # 저장된 모델이 더 이상 설치돼 있지 않으면 자동으로 첫 번째 사용 가능 모델로 전환
        if current not in options:
            new_model = options[0]
            st.info(
                f"저장된 모델 `{current}`이(가) 설치되어 있지 않아 "
                f"`{new_model}`(으)로 자동 전환됐습니다."
            )
            st.session_state.model_name = new_model
            current = new_model
            _save_session()
        st.session_state.model_name = st.selectbox(
            "Ollama 모델",
            options=options,
            index=options.index(current),
            help="설치된 모델 목록입니다. 추가 설치는 'ollama pull <모델명>'.",
        )
        st.success(f"✓ Ollama 연결됨 ({len(status['models'])}개 모델)")

    st.divider()
    page = st.radio("화면", ["새 평가", "이력", "프리셋"], key="page", label_visibility="collapsed")
    st.divider()

    progress_steps = ["JD 입력", "가중치 조정", "후보자 평가", "리포트"]
    for i, name in enumerate(progress_steps, 1):
        marker = "●" if st.session_state.step == i else ("✓" if st.session_state.step > i else "○")
        st.caption(f"{marker} Step {i}. {name}")

    st.divider()
    last_ts = st.session_state.get("_last_save_ts")
    if last_ts:
        st.caption(f"💾 자동 저장: {last_ts}")
    else:
        st.caption("💾 자동 저장 대기 중")
    if err := st.session_state.get("_last_save_error"):
        st.caption(f"⚠ 저장 오류: {err}")


# ---------- Page: 이력 ----------
if page == "이력":
    st.header("평가 이력")

    grouped_raw = list_evaluations_grouped(limit=500)
    if not grouped_raw:
        st.info("저장된 평가 이력이 없습니다.")
        st.stop()

    REC_BADGE = {
        "면접 강력 추천": ":green[●]",
        "면접 추천": ":blue[●]",
        "보류": ":orange[●]",
        "부적합": ":red[●]",
    }

    # ---------- 검색 + 필터 UI ----------
    with st.container(border=True):
        st.markdown("**🔍 검색 및 필터**")
        sc1, sc2 = st.columns([3, 2])
        with sc1:
            search_q = st.text_input(
                "검색어 (이름·후보자ID·현직·회사·도메인·스킬)",
                key="hist_search",
                placeholder="예: 정현우 / EduCore / Spark / 핀테크",
                help="평가 결과 안의 모든 텍스트(후보자 정보, 추천 사유, 강점, 차원 근거 등)에서 검색",
            )
        with sc2:
            jd_filter = st.multiselect(
                "JD 필터",
                options=sorted(grouped_raw.keys()),
                default=[],
                placeholder="전체 JD",
                key="hist_jd_filter",
            )

        sc3, sc4, sc5 = st.columns(3)
        with sc3:
            rec_filter = st.multiselect(
                "추천 등급 필터",
                options=["면접 강력 추천", "면접 추천", "보류", "부적합"],
                default=[],
                placeholder="전체 등급",
                key="hist_rec_filter",
            )
        with sc4:
            min_score = st.number_input("최소 점수", 0, 100, 0, 5, key="hist_min_score")
        with sc5:
            sort_mode = st.selectbox(
                "정렬",
                ["점수 ↓", "점수 ↑", "최근순", "오래된순"],
                index=0,
                key="hist_sort",
            )

    # ---------- 검색·필터 적용: 후보자 단위로 매칭 ----------
    def _matches(eval_summary: dict, jd_title: str) -> bool:
        # JD 필터
        if jd_filter and jd_title not in jd_filter:
            return False
        # 추천 필터
        if rec_filter and (eval_summary.get("recommendation") or "—") not in rec_filter:
            return False
        # 점수 필터
        sc = eval_summary.get("overall_score")
        if sc is not None and sc < min_score:
            return False
        if sc is None and min_score > 0:
            return False
        # 검색어
        if search_q.strip():
            q = search_q.strip().lower()
            # 1차: summary에서 빠르게 (label만)
            quick_hit = q in (eval_summary.get("candidate_label") or "").lower()
            if quick_hit:
                return True
            # 2차: detail 가져와서 전체 JSON 텍스트 검색
            detail = get_evaluation_detail(eval_summary["id"])
            if not detail:
                return False
            haystack = json.dumps(detail, ensure_ascii=False).lower()
            return q in haystack
        return True

    # 그룹별로 필터링
    filtered: dict[str, list[dict]] = {}
    for jd_title, evals in grouped_raw.items():
        matched_evals = [e for e in evals if _matches(e, jd_title)]
        if matched_evals:
            filtered[jd_title] = matched_evals

    total_count_all = sum(len(v) for v in grouped_raw.values())
    total_count_filt = sum(len(v) for v in filtered.values())
    if total_count_filt < total_count_all:
        st.caption(f"🎯 검색 결과: **{total_count_filt}건** / 전체 {total_count_all}건  ({len(filtered)}개 JD)")
    else:
        st.caption(f"총 **{total_count_all}건** 평가 ({len(grouped_raw)}개 JD)")

    if not filtered:
        st.warning("검색 조건에 일치하는 평가가 없습니다.")
        st.stop()

    grouped = filtered

    # 정렬 함수 — 후보자 단위
    def _sort_evals(evals: list[dict]) -> list[dict]:
        if sort_mode == "점수 ↓":
            return sorted(evals, key=lambda e: e.get("overall_score") or -1, reverse=True)
        if sort_mode == "점수 ↑":
            return sorted(evals, key=lambda e: e.get("overall_score") if e.get("overall_score") is not None else 999)
        if sort_mode == "최근순":
            return sorted(evals, key=lambda e: e.get("created_at") or "", reverse=True)
        return sorted(evals, key=lambda e: e.get("created_at") or "")

    # JD별 그룹: 평가 건수 많은 순으로 정렬
    sorted_titles = sorted(
        grouped.keys(),
        key=lambda t: (-len(grouped[t]), -max((r["created_at"] or "") for r in grouped[t]).count("")),
    )

    for jd_title in sorted_titles:
        evals = grouped[jd_title]
        scores = [e["overall_score"] for e in evals if e["overall_score"] is not None]
        avg_score = sum(scores) / len(scores) if scores else None
        max_score = max(scores) if scores else None
        latest = max((e["created_at"] or "") for e in evals)

        header_parts = [f"📁 **{jd_title}**", f"{len(evals)}명"]
        if avg_score is not None:
            header_parts.append(f"평균 {avg_score:.0f}점")
        if max_score is not None:
            header_parts.append(f"최고 {max_score:.0f}점")
        header_parts.append(f"최근 {latest[:10]}")
        header = "  ·  ".join(header_parts)

        # 검색어가 있으면 폴더 자동 펼침
        is_searching = bool(search_q.strip()) or bool(jd_filter) or bool(rec_filter) or min_score > 0
        with st.expander(header, expanded=is_searching):
            # 추천 등급 분포
            rec_counts: dict[str, int] = {}
            for e in evals:
                rec = e.get("recommendation") or "—"
                rec_counts[rec] = rec_counts.get(rec, 0) + 1
            rec_summary = " · ".join(f"{REC_BADGE.get(k, '⚪')} {k} {v}" for k, v in rec_counts.items())
            st.caption(rec_summary)
            st.divider()

            # 후보자별 토글
            evals_sorted = _sort_evals(evals)
            for e in evals_sorted:
                badge = REC_BADGE.get(e.get("recommendation"), "⚪")
                score_str = f"{e['overall_score']:.0f}" if e["overall_score"] is not None else "—"
                cand_header = f"{badge}  **{e['candidate_label']}**  ·  {score_str}점  ·  {e.get('recommendation', '—')}  ·  {(e.get('created_at') or '')[:16]}"

                # 검색어가 있고 결과가 적으면 자동 펼침
                auto_expand = bool(search_q.strip()) and len(evals_sorted) <= 3
                with st.expander(cand_header, expanded=auto_expand):
                    detail = get_evaluation_detail(e["id"])
                    if not detail:
                        st.warning("상세 데이터를 불러오지 못했습니다.")
                        continue

                    res = detail["result"]
                    cand = detail.get("candidate_structured") or {}

                    # 후보자 핵심 정보
                    cci1, cci2 = st.columns([1, 2])
                    with cci1:
                        st.markdown(f"**현직**: {cand.get('current_title', '—')}")
                        st.markdown(f"**경력**: {cand.get('total_experience_years', '?')}년")
                    with cci2:
                        if res.get("one_line_summary"):
                            st.markdown(f"**한줄 요약**: _{res['one_line_summary']}_")
                        if res.get("hard_gate_triggered"):
                            st.error("🚨 하드 게이트: " + ", ".join(res["hard_gate_triggered"]))

                    # 차원별 미니 표
                    if res.get("dimensions"):
                        dim_rows = [
                            {
                                "차원": d.get("name"),
                                "분류": d.get("category"),
                                "점수": d.get("score"),
                                "가중": f"{(d.get('weight', 0)) * 100:.0f}%",
                                "적합": d.get("fit"),
                            }
                            for d in res["dimensions"]
                        ]
                        st.dataframe(pd.DataFrame(dim_rows), use_container_width=True, hide_index=True)

                    # 강점/리스크
                    sr1, sr2 = st.columns(2)
                    with sr1:
                        st.markdown("**✅ 강점**")
                        for x in (res.get("strengths") or [])[:5]:
                            st.markdown(f"- {x}")
                    with sr2:
                        st.markdown("**⚠ 리스크**")
                        for x in (res.get("risks") or [])[:5]:
                            st.markdown(f"- {x}")

                    # 다운로드 + 삭제
                    bcol1, bcol2, bcol3 = st.columns([2, 2, 1])
                    with bcol1:
                        st.download_button(
                            "📄 JSON",
                            json.dumps(detail, ensure_ascii=False, indent=2),
                            f"eval_{e['id']}_{e['candidate_label']}.json",
                            "application/json",
                            key=f"hist_dl_json_{e['id']}",
                        )
                    with bcol2:
                        try:
                            from src.report.pdf_generator import build_pdf_report
                            pdf_bytes = build_pdf_report(
                                candidate_label=e["candidate_label"],
                                candidate=cand,
                                result=res,
                                jd_structured=detail.get("jd_structured"),
                            )
                            st.download_button(
                                "📑 PDF",
                                pdf_bytes,
                                f"eval_{e['id']}_{e['candidate_label']}.pdf",
                                "application/pdf",
                                key=f"hist_dl_pdf_{e['id']}",
                            )
                        except Exception as ex:
                            st.caption(f"PDF 생성 실패 ({ex})")
                    with bcol3:
                        if st.button("🗑 삭제", key=f"hist_del_{e['id']}", help="이 평가 이력 삭제 (되돌릴 수 없음)"):
                            delete_evaluation(e["id"])
                            st.rerun()

    st.stop()


# ---------- Page: 프리셋 ----------
if page == "프리셋":
    st.header("가중치 프리셋")
    presets = list_presets()
    if not presets:
        st.info("저장된 프리셋이 없습니다. 새 평가에서 가중치를 조정한 후 저장하세요.")
    else:
        st.caption("저장된 가중치/하드 게이트 설정을 새 평가에 바로 적용할 수 있습니다.")
        if msg := st.session_state.pop("_flash", None):
            st.success(msg)
        for p in presets:
            with st.expander(f"{p['name']}  ·  사용 {p['used_count']}회  ·  {p['created_at']}"):
                ca, cb, _ = st.columns([1, 1, 4])
                with ca:
                    st.button(
                        "이 프리셋 적용 →",
                        key=f"apply_{p['id']}",
                        type="primary",
                        on_click=_apply_preset_and_redirect,
                        args=(p,),
                    )
                with cb:
                    st.button(
                        "삭제",
                        key=f"del_{p['id']}",
                        on_click=_delete_preset_callback,
                        args=(p["id"],),
                    )
                st.markdown("**가중치**")
                st.json(p["weights"])
                st.markdown("**하드 게이트**")
                st.json(p["hard_gates"])
    st.stop()


# ============================================================
#  새 평가 — Step 1: JD 입력
# ============================================================
if st.session_state.step == 1:
    st.header("Step 1. JD 입력")

    tab_text, tab_file = st.tabs(["텍스트 붙여넣기", "파일 업로드"])

    with tab_text:
        prev_text = st.session_state.jd_text
        st.session_state.jd_text = st.text_area(
            "JD 본문",
            value=st.session_state.jd_text,
            height=300,
            placeholder="채용공고 텍스트를 붙여넣으세요.",
        )
        if st.session_state.jd_text and st.session_state.jd_text != prev_text:
            _save_session()

    with tab_file:
        jd_file = st.file_uploader(
            "JD 파일 (PDF / Word / Excel / JSON / 텍스트)",
            type=["pdf", "docx", "xlsx", "xls", "json", "txt", "md"],
            key="jd_file",
        )
        if jd_file is not None:
            try:
                st.session_state.jd_text = _read_uploaded(jd_file)
                _save_session()
                st.success(f"파일에서 {len(st.session_state.jd_text):,}자 추출 완료")
                with st.expander("추출된 텍스트 미리보기"):
                    st.text(st.session_state.jd_text[:2000])
            except Exception as e:
                st.error(f"파일 파싱 실패: {e}")

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("JD 구조화 →", type="primary"):
            if not st.session_state.jd_text.strip():
                st.warning("JD 텍스트를 입력하거나 파일을 업로드하세요.")
            else:
                # 분석 시작 직전 jd_text를 한 번 더 디스크에 보존 (LLM 도중 강제종료 대비)
                _save_session()
                with st.spinner("LLM이 JD를 분석 중입니다..."):
                    try:
                        st.session_state.jd_structured = extract_jd(
                            st.session_state.jd_text, model=st.session_state.model_name
                        )
                        st.session_state.step = 2
                        _save_session()
                        st.rerun()
                    except Exception as e:
                        st.error(f"JD 추출 실패: {e}")


# ============================================================
#  Step 2: 가중치 조정
# ============================================================
elif st.session_state.step == 2:
    st.header("Step 2. 평가 가중치 조정")

    jd = st.session_state.jd_structured or {}
    with st.expander("JD 구조화 결과", expanded=False):
        st.json(jd)

    # 프리셋 불러오기
    if msg := st.session_state.pop("_flash", None):
        st.success(msg)
    saved_presets = list_presets()
    if saved_presets:
        with st.expander("📂 저장된 프리셋에서 불러오기", expanded=False):
            preset_options = {f"{p['name']}  ·  사용 {p['used_count']}회": p for p in saved_presets}
            choice = st.selectbox(
                "프리셋 선택",
                options=list(preset_options.keys()),
                key="preset_picker",
            )
            st.button(
                "선택한 프리셋 적용",
                key="apply_preset_btn",
                on_click=_apply_preset_inplace,
                args=(preset_options[choice],),
            )

    # AI 추천
    st.subheader("AI 추천 가중치")
    rec_col1, rec_col2 = st.columns([1, 4])
    with rec_col1:
        if st.button("AI 추천 받기"):
            with st.spinner("LLM이 가중치를 추천 중입니다..."):
                try:
                    st.session_state.ai_recommendation = recommend_weights(
                        jd, _current_weights(), model=st.session_state.model_name
                    )
                except Exception as e:
                    st.error(f"추천 실패: {e}")

    if st.session_state.ai_recommendation:
        rec = st.session_state.ai_recommendation
        for adj in rec.get("adjustments", []):
            delta = adj.get("delta", 0)
            arrow = "⬆" if delta > 0 else ("⬇" if delta < 0 else "·")
            st.caption(f"{arrow} **{adj['dimension']}**: {adj['default']*100:.0f}% → {adj['recommended']*100:.0f}% ({adj['reason']})")
        if st.button("추천 적용"):
            final = rec.get("final_weights", {})
            for d in st.session_state.dimensions:
                if d.name in final:
                    d.weight = float(final[d.name])
            st.rerun()

    st.divider()

    # 차원별 가중치 입력
    st.subheader("차원별 가중치")
    must_dims = [d for d in st.session_state.dimensions if d.category == "must"]
    nice_dims = [d for d in st.session_state.dimensions if d.category == "nice"]

    def _delete_dimension_callback(dim_name: str):
        st.session_state.dimensions = [d for d in st.session_state.dimensions if d.name != dim_name]
        # 위젯 stored value 정리
        for prefix in ("slider_", "num_"):
            st.session_state.pop(f"{prefix}{dim_name}", None)
        _save_session()

    st.markdown(f"**필수 요건 ({sum(d.weight for d in must_dims)*100:.0f}%)**")
    for d in must_dims:
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            st.markdown(f"**{d.name}**")
            st.caption(d.description)
        with c2:
            new_val = st.slider(
                f"slider_{d.name}",
                min_value=0.0,
                max_value=0.5,
                value=float(d.weight),
                step=0.05,
                label_visibility="collapsed",
                key=f"slider_{d.name}",
            )
        with c3:
            new_num = st.number_input(
                f"num_{d.name}",
                min_value=0.0,
                max_value=0.5,
                value=float(new_val),
                step=0.05,
                format="%.2f",
                label_visibility="collapsed",
                key=f"num_{d.name}",
            )
        with c4:
            st.button(
                "🗑",
                key=f"del_dim_{d.name}",
                help=f"'{d.name}' 차원 삭제",
                on_click=_delete_dimension_callback,
                args=(d.name,),
            )
        with st.expander(f"📌 {d.name} — JD 기준 보기", expanded=False):
            _render_dimension_evidence(d.name, jd)
        if abs(new_num - d.weight) > 1e-6:
            rebalance(_current_weights(), d.name, new_num)
            _save_session()
            st.rerun()

    st.markdown(f"**우대 사항 ({sum(d.weight for d in nice_dims)*100:.0f}%)**")
    for d in nice_dims:
        c1, c2, c3, c4 = st.columns([3, 3, 2, 1])
        with c1:
            st.markdown(f"**{d.name}**")
            st.caption(d.description)
        with c2:
            new_val = st.slider(
                f"slider_{d.name}",
                min_value=0.0,
                max_value=0.5,
                value=float(d.weight),
                step=0.05,
                label_visibility="collapsed",
                key=f"slider_{d.name}",
            )
        with c3:
            new_num = st.number_input(
                f"num_{d.name}",
                min_value=0.0,
                max_value=0.5,
                value=float(new_val),
                step=0.05,
                format="%.2f",
                label_visibility="collapsed",
                key=f"num_{d.name}",
            )
        with c4:
            st.button(
                "🗑",
                key=f"del_dim_{d.name}",
                help=f"'{d.name}' 차원 삭제",
                on_click=_delete_dimension_callback,
                args=(d.name,),
            )
        with st.expander(f"📌 {d.name} — JD 기준 보기", expanded=False):
            _render_dimension_evidence(d.name, jd)
        if abs(new_num - d.weight) > 1e-6:
            rebalance(_current_weights(), d.name, new_num)
            _save_session()
            st.rerun()

    # 차원 추가
    with st.expander("차원 추가"):
        new_name = st.text_input("차원 이름", key="new_dim_name")
        new_cat = st.selectbox("분류", ["must", "nice"], key="new_dim_cat")
        new_weight = st.number_input("가중치", 0.0, 0.5, 0.10, 0.05, key="new_dim_weight")
        new_desc = st.text_input("설명", key="new_dim_desc")
        if st.button("추가") and new_name:
            st.session_state.dimensions.append(
                Dimension(new_name, new_cat, float(new_weight), new_desc)
            )
            st.rerun()

    st.divider()

    # 하드 게이트
    st.subheader("하드 게이트 룰")
    g = st.session_state.hard_gates
    g.min_score_per_must = st.slider("필수 항목 최저 점수", 0, 100, g.min_score_per_must, 5)
    g.info_missing_downgrade = st.checkbox("정보 미기재 시 등급 1단계 하향", value=g.info_missing_downgrade)
    keywords_text = st.text_input(
        "회피 키워드 (쉼표 구분)",
        value=", ".join(g.avoidance_keywords),
        placeholder="단기 이직, 6개월 이하",
    )
    g.avoidance_keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]

    st.divider()

    # 검증
    weights = _current_weights()
    valid, msg = weights.is_valid()
    total_pct = weights.total() * 100

    cstat1, cstat2 = st.columns(2)
    with cstat1:
        st.metric("합계", f"{total_pct:.1f}%", delta="✓" if valid else msg)
    with cstat2:
        st.metric("필수 / 우대", f"{weights.must_total()*100:.0f}% / {weights.nice_total()*100:.0f}%")

    if not valid:
        st.warning(msg)

    # 저장 / 다음
    cnav1, cnav2, cnav3 = st.columns([1, 1, 1])
    with cnav1:
        if st.button("← 이전"):
            st.session_state.step = 1
            st.rerun()
    with cnav2:
        preset_name = st.text_input("프리셋 저장 이름", key="preset_name", placeholder="예: 케어랩스 전략매니저")
        if st.button("프리셋 저장") and preset_name and valid:
            save_preset(
                preset_name,
                {d.name: {"category": d.category, "weight": d.weight, "description": d.description} for d in st.session_state.dimensions},
                {
                    "min_score_per_must": g.min_score_per_must,
                    "info_missing_downgrade": g.info_missing_downgrade,
                    "avoidance_keywords": g.avoidance_keywords,
                },
            )
            st.success("저장 완료")
    with cnav3:
        if st.button("후보자 평가로 →", type="primary", disabled=not valid):
            st.session_state.step = 3
            _save_session()
            st.rerun()


# ============================================================
#  Step 3: 후보자 평가
# ============================================================
elif st.session_state.step == 3:
    st.header("Step 3. 후보자 평가")

    mode = st.radio("입력 방식", ["단일 후보자", "일괄 후보자"], horizontal=True)

    if mode == "단일 후보자":
        candidate_file = st.file_uploader(
            "이력서 파일",
            type=["pdf", "docx", "xlsx", "xls", "json", "txt", "md"],
            key="single_candidate",
        )
        candidate_label = st.text_input("후보자 식별자(메모)", placeholder="예: 후보 A")

        if candidate_file and st.button("평가 시작", type="primary"):
            try:
                resume_text = _read_uploaded(candidate_file)
                with st.spinner("후보자 프로필 추출 중..."):
                    cand = extract_candidate(resume_text, model=st.session_state.model_name)
                with st.spinner("적합도 평가 중..."):
                    result = evaluate_candidate(
                        st.session_state.jd_structured,
                        cand,
                        _current_weights(),
                        st.session_state.hard_gates,
                        model=st.session_state.model_name,
                        candidate_text=resume_text,
                    )
                save_evaluation(
                    jd_title=st.session_state.jd_structured.get("position_title", "JD"),
                    candidate_label=candidate_label or candidate_file.name,
                    jd_structured=st.session_state.jd_structured,
                    candidate_structured=cand,
                    weights={d.name: d.weight for d in st.session_state.dimensions},
                    result=result,
                )
                st.session_state.results = [{"label": candidate_label or candidate_file.name, "result": result, "candidate": cand}]
                st.session_state.step = 4
                st.rerun()
            except Exception as e:
                st.error(f"평가 실패: {e}")

    else:
        candidate_files = st.file_uploader(
            "이력서 파일 (여러 개)",
            type=["pdf", "docx", "xlsx", "xls", "json", "txt", "md"],
            accept_multiple_files=True,
            key="batch_candidates",
        )

        st.caption(
            f"💡 JSON 파일 한 개에 최대 **{MAX_CANDIDATES_PER_JSON}명**까지 후보자 배열로 넣을 수 있습니다. "
            "지원 형식: `[{...}, {...}]` 또는 `{\"candidates\": [...]}` 또는 단일 객체. "
            "각 항목에 `name`/`label` + `resume`/`resume_text`/`text` 필드 권장."
        )

        candidates_to_evaluate = []
        if candidate_files:
            for f in candidate_files:
                try:
                    items = _expand_uploaded_to_candidates(f)
                    candidates_to_evaluate.extend(items)
                except Exception as e:
                    st.error(f"{f.name} 분해 실패: {e}")

            if candidates_to_evaluate:
                st.info(f"평가 대기: 총 **{len(candidates_to_evaluate)}명** "
                        f"(파일 {len(candidate_files)}개)")

        if candidates_to_evaluate and st.button("일괄 평가 시작", type="primary"):
            results = []
            total = len(candidates_to_evaluate)
            progress = st.progress(0, text="평가 중...")
            for i, item in enumerate(candidates_to_evaluate, 1):
                progress.progress(i / total, text=f"{i}/{total} — {item['label']}")
                try:
                    cand = extract_candidate(item["text"], model=st.session_state.model_name)
                    result = evaluate_candidate(
                        st.session_state.jd_structured,
                        cand,
                        _current_weights(),
                        st.session_state.hard_gates,
                        model=st.session_state.model_name,
                        candidate_text=item["text"],
                    )
                    save_evaluation(
                        jd_title=st.session_state.jd_structured.get("position_title", "JD"),
                        candidate_label=item["label"],
                        jd_structured=st.session_state.jd_structured,
                        candidate_structured=cand,
                        weights={d.name: d.weight for d in st.session_state.dimensions},
                        result=result,
                    )
                    results.append({"label": item["label"], "result": result, "candidate": cand})
                except Exception as e:
                    results.append({"label": item["label"], "result": {"error": str(e)}, "candidate": None})
            progress.empty()
            st.session_state.results = results
            st.session_state.step = 4
            st.rerun()

    if st.button("← 이전"):
        st.session_state.step = 2
        st.rerun()


# ============================================================
#  Step 4: 리포트 (보강판)
# ============================================================
elif st.session_state.step == 4:
    st.header("Step 4. 평가 리포트")

    results = st.session_state.results
    jd_struct = st.session_state.jd_structured or {}

    # 백엔드 출처 캡션 (시연 신뢰성)
    _backend = get_backend()
    if _backend == "mock":
        st.caption(":violet[**[DEMO]**] 본 결과는 **Mock 데모 모드**로 사전 정의된 응답입니다. 실제 LLM 평가가 아닙니다.")
    elif _backend in ("anthropic", "openai"):
        st.caption(f":blue[**[CLOUD]**] 본 결과는 클라우드 API ({_backend})로 평가됐습니다.")
    else:
        st.caption(f":green[**[LOCAL]**] 본 결과는 로컬 LLM ({st.session_state.model_name})으로 평가됐습니다.")

    # ---------- JD 요약 (항상 보임) ----------
    with st.expander(f"📋 JD 요약 — {jd_struct.get('position_title', '포지션')} @ {jd_struct.get('company', '')}", expanded=False):
        cjd1, cjd2 = st.columns(2)
        with cjd1:
            st.markdown("**필수 요건**")
            for x in jd_struct.get("must_have", []):
                st.markdown(f"- {x}")
        with cjd2:
            st.markdown("**우대 사항**")
            for x in jd_struct.get("nice_to_have", []):
                st.markdown(f"- {x}")
        if jd_struct.get("hidden_criteria"):
            st.markdown("**숨은 기준**")
            for x in jd_struct["hidden_criteria"]:
                st.markdown(f"- {x}")

    # ---------- 다인원: 비교 narrative + 랭킹 + 차트 ----------
    if len(results) > 1:
        valid_results = [r for r in results if "error" not in (r.get("result") or {})]
        st.subheader("종합 비교")

        # narrative 비교 요약
        comp = build_comparison_summary(results)
        if comp:
            st.markdown(comp)

        # 랭킹 차트
        if valid_results:
            ranking_rows = [
                {"label": r["label"], "score": r["result"].get("overall_score"), "recommendation": r["result"].get("recommendation", "")}
                for r in valid_results
            ]
            st.plotly_chart(ranking_bar(ranking_rows), use_container_width=True)

        # 랭킹 표
        rows = []
        for r in results:
            res = r["result"]
            if "error" in res:
                rows.append({"후보자": r["label"], "종합": None, "가중": None, "추천": "오류", "요약": res["error"]})
            else:
                rows.append({
                    "후보자": r["label"],
                    "종합": res.get("overall_score"),
                    "가중": res.get("weighted_score"),
                    "추천": res.get("recommendation"),
                    "요약": res.get("one_line_summary", ""),
                })
        df = pd.DataFrame(rows).sort_values("종합", ascending=False, na_position="last")
        with st.expander("🔢 랭킹 표 + Excel(CSV) 내보내기", expanded=False):
            st.dataframe(df, use_container_width=True, hide_index=True)
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Excel(CSV) 내보내기", csv, "ranking.csv", "text/csv")

        st.divider()
        st.subheader("개별 리포트")

    # ---------- 개별 리포트 ----------
    for r in results:
        res = r["result"]
        cand = r.get("candidate") or {}

        if "error" in res:
            st.error(f"{r['label']}: {res['error']}")
            continue

        cand_name = cand.get("candidate_name", r["label"]) if isinstance(cand, dict) else r["label"]
        title = cand.get("current_title", "—") if isinstance(cand, dict) else "—"
        years = cand.get("total_experience_years", "?") if isinstance(cand, dict) else "?"

        _badge_map = {"면접 강력 추천": "●●●", "면접 추천": "●●", "보류": "●", "부적합": "✗"}
        _badge = _badge_map.get(res.get("recommendation"), "·")
        header = f"[{_badge}] {cand_name} · {years}년차 · {_format_score(res.get('overall_score'))}점 · {res.get('recommendation', '—')}"
        with st.expander(header, expanded=(len(results) == 1)):

            # ----- 후보자 프로필 카드 -----
            if isinstance(cand, dict) and cand:
                ccc1, ccc2, ccc3 = st.columns([2, 2, 3])
                with ccc1:
                    st.markdown(f"### 👤 {cand_name}")
                    st.markdown(f"**현직**: {title}")
                    st.markdown(f"**경력**: {years}년")
                with ccc2:
                    st.markdown("**핵심 회사**")
                    for h in (cand.get("career_history") or [])[:3]:
                        st.markdown(f"- {h.get('company', '')} · {h.get('title','')}")
                with ccc3:
                    st.markdown("**핵심 스킬**")
                    skills = cand.get("skills", {})
                    tech = (skills.get("technical") or [])[:6]
                    domain = (skills.get("domain") or [])[:4]
                    if tech:
                        st.caption("기술 — " + ", ".join(tech))
                    if domain:
                        st.caption("도메인 — " + ", ".join(domain))
                    langs = skills.get("language") or []
                    for l in langs:
                        if isinstance(l, dict):
                            st.caption(f"{l.get('name','')}: {l.get('level','')}")
                st.divider()

            # ----- 메트릭 + 추천 사유 -----
            mcol1, mcol2, mcol3 = st.columns(3)
            with mcol1:
                st.metric("종합 점수", _format_score(res.get("overall_score")))
            with mcol2:
                st.metric("가중 점수", _format_score(res.get("weighted_score")))
            with mcol3:
                st.metric("추천", res.get("recommendation", "—"))

            if res.get("hard_gate_triggered"):
                st.error("🚨 하드 게이트 발동: " + ", ".join(res["hard_gate_triggered"]))

            st.markdown("#### 📝 추천 사유")
            st.markdown(build_recommendation_narrative(res))

            st.markdown("#### 📊 차원별 분석")
            chart_col1, chart_col2 = st.columns([1, 1])
            with chart_col1:
                st.plotly_chart(dimension_radar(res.get("dimensions", []), cand_name), use_container_width=True, key=f"radar_{r['label']}")
            with chart_col2:
                st.plotly_chart(dimension_bar(res.get("dimensions", [])), use_container_width=True, key=f"bar_{r['label']}")

            with st.expander("📌 차원별 상세 (매칭/부족/근거)", expanded=False):
                for d in res.get("dimensions", []):
                    st.markdown(f"**{d.get('name')}** ({d.get('category')}, 가중치 {d.get('weight', 0)*100:.0f}%) — 점수 **{d.get('score')}**, 적합 {d.get('fit')}")
                    st.caption(d.get("summary", ""))
                    if d.get("matched"):
                        st.markdown(f"  ✓ **매칭**: {', '.join(d['matched'])}")
                    if d.get("missing"):
                        st.markdown(f"  ✗ **부족**: {', '.join(d['missing'])}")
                    if d.get("evidence"):
                        st.markdown(f"  📎 **근거**: _{d['evidence']}_")
                    st.markdown(f"  📋 정보 상태: `{d.get('info_status', '—')}`")
                    st.markdown("---")

            # ----- 강점 / 리스크 -----
            sr1, sr2 = st.columns(2)
            with sr1:
                st.markdown("#### ✅ 강점")
                for x in res.get("strengths", []):
                    st.markdown(f"- {x}")
            with sr2:
                st.markdown("#### ⚠ 리스크")
                for x in res.get("risks", []):
                    st.markdown(f"- {x}")

            # ----- 면접 질문 가이드 -----
            st.markdown("#### 🎯 면접 질문 가이드 (자동 생성)")
            for grp in build_interview_questions(res, max_total=12):
                with st.expander(f"  {grp['dimension']} ({len(grp['questions'])}개)"):
                    for q in grp["questions"]:
                        st.markdown(f"- **[{q['type']}]** {q['text']}")
                        if q.get("reason"):
                            st.caption(f"  → 검증 사유: {q['reason']}")

            # ----- 다운로드 -----
            dlc1, dlc2 = st.columns(2)
            with dlc1:
                st.download_button(
                    f"JSON 내보내기",
                    json.dumps(res, ensure_ascii=False, indent=2),
                    f"report_{r['label']}.json",
                    "application/json",
                    key=f"dl_json_{r['label']}",
                )
            with dlc2:
                # PDF 내보내기는 src.report.pdf_generator가 있을 때만 활성화
                try:
                    from src.report.pdf_generator import build_pdf_report
                    pdf_bytes = build_pdf_report(
                        candidate_label=r["label"],
                        candidate=cand,
                        result=res,
                        jd_structured=jd_struct,
                    )
                    st.download_button(
                        "PDF 보고서 내보내기",
                        pdf_bytes,
                        f"report_{r['label']}.pdf",
                        "application/pdf",
                        key=f"dl_pdf_{r['label']}",
                    )
                except Exception as e:
                    st.caption(f"PDF 생성 비활성 ({e})")

    st.divider()
    cnav1, cnav2 = st.columns(2)
    with cnav1:
        if st.button("← 후보자 추가 평가"):
            st.session_state.step = 3
            st.rerun()
    with cnav2:
        if st.button("처음부터 새 평가"):
            _clear_session_file()
            for k in ["step", "jd_text", "jd_structured", "ai_recommendation", "results", "_session_loaded"]:
                st.session_state.pop(k, None)
            _init_state()
            st.rerun()
