"""ReportLab 기반 PDF 보고서 생성. 한글 폰트 자동 탐색."""
from __future__ import annotations

from io import BytesIO
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ============================================================
#  한글 폰트 — 시스템에서 사용 가능한 첫 폰트 등록
# ============================================================

KOREAN_FONT_CANDIDATES = [
    ("MalgunGothic", "C:/Windows/Fonts/malgun.ttf"),
    ("MalgunGothic", "C:/Windows/Fonts/malgunbd.ttf"),
    ("NanumGothic", "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"),
    ("AppleSDGothic", "/System/Library/Fonts/Supplemental/AppleSDGothicNeo.ttc"),
]

_FONT_NAME = "Helvetica"  # fallback


def _register_korean_font() -> str:
    global _FONT_NAME
    for name, path in KOREAN_FONT_CANDIDATES:
        if Path(path).exists():
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                _FONT_NAME = name
                return name
            except Exception:
                continue
    return _FONT_NAME


_register_korean_font()


# ============================================================
#  스타일
# ============================================================

def _styles():
    base = getSampleStyleSheet()
    fn = _FONT_NAME
    return {
        "title": ParagraphStyle("title", parent=base["Heading1"], fontName=fn, fontSize=18, leading=22, spaceAfter=10, textColor=HexColor("#1F2937")),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], fontName=fn, fontSize=13, leading=18, spaceBefore=10, spaceAfter=6, textColor=HexColor("#0061F2")),
        "h3": ParagraphStyle("h3", parent=base["Heading3"], fontName=fn, fontSize=11, leading=15, spaceBefore=6, spaceAfter=3, textColor=HexColor("#374151")),
        "body": ParagraphStyle("body", parent=base["BodyText"], fontName=fn, fontSize=9.5, leading=13, textColor=HexColor("#1F2937")),
        "caption": ParagraphStyle("caption", parent=base["BodyText"], fontName=fn, fontSize=8.5, leading=11, textColor=HexColor("#6B7280")),
        "metric": ParagraphStyle("metric", parent=base["BodyText"], fontName=fn, fontSize=11, leading=14, textColor=HexColor("#111827")),
    }


# ============================================================
#  Builder
# ============================================================

def _esc(s) -> str:
    """ReportLab Paragraph 안전한 문자열 변환."""
    if s is None:
        return ""
    s = str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


def _section_header(text: str, styles) -> Paragraph:
    return Paragraph(_esc(text), styles["h2"])


def build_pdf_report(candidate_label: str, candidate: dict | None, result: dict, jd_structured: dict | None = None) -> bytes:
    """후보자 1명 평가 결과를 2~3페이지 PDF로 생성.
    반환: PDF 바이트.
    """
    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=f"적합도 평가 — {candidate_label}",
    )

    story = []
    candidate = candidate or {}
    jd_structured = jd_structured or {}

    cand_name = candidate.get("candidate_name", candidate_label)
    title = candidate.get("current_title", "—")
    years = candidate.get("total_experience_years", "?")

    # 헤더
    story.append(Paragraph(f"적합도 평가 보고서", styles["title"]))
    story.append(Paragraph(_esc(f"포지션: {jd_structured.get('position_title', '—')} @ {jd_structured.get('company', '—')}"), styles["caption"]))
    story.append(Spacer(1, 8))

    # 후보자 프로필
    story.append(_section_header("👤 후보자 프로필", styles))
    profile_rows = [
        ["이름", _esc(cand_name)],
        ["현직", _esc(title)],
        ["경력", _esc(f"{years}년")],
    ]
    skills = candidate.get("skills", {}) or {}
    if skills.get("technical"):
        profile_rows.append(["기술", _esc(", ".join(skills["technical"][:8]))])
    if skills.get("domain"):
        profile_rows.append(["도메인", _esc(", ".join(skills["domain"][:6]))])
    langs = skills.get("language") or []
    if langs:
        lang_str = ", ".join(f"{l.get('name','')}: {l.get('level','')}" for l in langs if isinstance(l, dict))
        if lang_str:
            profile_rows.append(["언어", _esc(lang_str)])
    profile_table = Table(profile_rows, colWidths=[25 * mm, 140 * mm])
    profile_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), _FONT_NAME, 9),
        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#6B7280")),
        ("BACKGROUND", (0, 0), (0, -1), HexColor("#F3F4F6")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BOX", (0, 0), (-1, -1), 0.3, HexColor("#E5E7EB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#E5E7EB")),
    ]))
    story.append(profile_table)
    story.append(Spacer(1, 10))

    # 종합 점수
    story.append(_section_header("📊 종합 평가", styles))
    rec = result.get("recommendation", "—")
    overall = result.get("overall_score", "—")
    weighted = result.get("weighted_score", "—")
    score_table = Table([
        ["종합 점수", "가중 점수", "추천 등급"],
        [str(overall), str(weighted), _esc(rec)],
    ], colWidths=[55 * mm, 55 * mm, 55 * mm])
    score_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), _FONT_NAME, 11),
        ("FONTSIZE", (0, 1), (-1, 1), 16),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#0061F2")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("BACKGROUND", (0, 1), (-1, 1), HexColor("#F9FAFB")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("BOX", (0, 0), (-1, -1), 0.3, HexColor("#E5E7EB")),
    ]))
    story.append(score_table)

    if result.get("hard_gate_triggered"):
        story.append(Spacer(1, 6))
        story.append(Paragraph(_esc("🚨 하드 게이트 발동: " + ", ".join(result["hard_gate_triggered"])),
                               ParagraphStyle("warn", parent=styles["body"], textColor=HexColor("#E63757"))))

    story.append(Spacer(1, 6))
    if result.get("one_line_summary"):
        story.append(Paragraph(_esc(f"한줄 요약: {result['one_line_summary']}"), styles["caption"]))
    story.append(Spacer(1, 10))

    # 차원별 평가
    story.append(_section_header("📐 차원별 분석", styles))
    dim_rows = [["차원", "분류", "점수", "가중치", "적합", "정보"]]
    for d in result.get("dimensions", []):
        dim_rows.append([
            _esc(d.get("name")),
            _esc(d.get("category")),
            str(d.get("score", "—")),
            f"{(d.get('weight') or 0) * 100:.0f}%",
            _esc(d.get("fit", "—")),
            _esc(d.get("info_status", "—")),
        ])
    dim_table = Table(dim_rows, colWidths=[40 * mm, 18 * mm, 18 * mm, 22 * mm, 18 * mm, 22 * mm])
    dim_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), _FONT_NAME, 9),
        ("BACKGROUND", (0, 0), (-1, 0), HexColor("#1F2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.3, HexColor("#E5E7EB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#FFFFFF"), HexColor("#F9FAFB")]),
    ]))
    story.append(dim_table)
    story.append(Spacer(1, 8))

    # 차원별 상세
    for d in result.get("dimensions", []):
        story.append(Paragraph(_esc(f"▸ {d.get('name')} — {d.get('summary', '')}"), styles["h3"]))
        if d.get("matched"):
            story.append(Paragraph(_esc(f"매칭: {', '.join(d['matched'])}"), styles["caption"]))
        if d.get("missing"):
            story.append(Paragraph(_esc(f"부족: {', '.join(d['missing'])}"), styles["caption"]))
        if d.get("evidence"):
            story.append(Paragraph(_esc(f"근거: {d['evidence']}"), styles["body"]))
        story.append(Spacer(1, 4))

    story.append(PageBreak())

    # 강점·리스크
    story.append(_section_header("✅ 강점 / ⚠ 리스크", styles))
    sr_data = [["강점", "리스크"]]
    strengths = result.get("strengths") or []
    risks = result.get("risks") or []
    rows = max(len(strengths), len(risks), 1)
    for i in range(rows):
        sr_data.append([
            _esc(f"• {strengths[i]}" if i < len(strengths) else ""),
            _esc(f"• {risks[i]}" if i < len(risks) else ""),
        ])
    sr_table = Table(sr_data, colWidths=[85 * mm, 85 * mm])
    sr_table.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, -1), _FONT_NAME, 9),
        ("BACKGROUND", (0, 0), (0, 0), HexColor("#10B981")),
        ("BACKGROUND", (1, 0), (1, 0), HexColor("#F59E0B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.3, HexColor("#E5E7EB")),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, HexColor("#E5E7EB")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(sr_table)
    story.append(Spacer(1, 10))

    # 면접 질문 가이드
    from .narrative import build_interview_questions
    story.append(_section_header("🎯 면접 질문 가이드", styles))
    for grp in build_interview_questions(result, max_total=10):
        story.append(Paragraph(_esc(f"▸ {grp['dimension']}"), styles["h3"]))
        for q in grp["questions"]:
            story.append(Paragraph(_esc(f"  Q. [{q['type']}] {q['text']}"), styles["body"]))
            if q.get("reason"):
                story.append(Paragraph(_esc(f"     → {q['reason']}"), styles["caption"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))
    story.append(Paragraph(_esc("이 보고서는 자동 생성됐습니다. 의사결정 시 면접·레퍼런스 체크를 병행하세요."), styles["caption"]))

    doc.build(story)
    return buffer.getvalue()
