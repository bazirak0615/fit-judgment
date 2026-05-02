"""Plotly 기반 평가 결과 차트."""
from __future__ import annotations

import plotly.graph_objects as go


PALETTE = {
    "must": "#2C7BE5",
    "nice": "#39AFD1",
    "ranking": "#0061F2",
    "axis": "rgba(0,0,0,0.2)",
}


def dimension_radar(dimensions: list[dict], candidate_label: str = "") -> go.Figure:
    """차원별 점수 레이더 차트."""
    names = [d["name"] for d in dimensions]
    scores = [d.get("score") or 0 for d in dimensions]
    # 닫힌 polygon
    names_closed = names + [names[0]]
    scores_closed = scores + [scores[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores_closed,
        theta=names_closed,
        fill="toself",
        name=candidate_label or "후보자",
        line=dict(color=PALETTE["ranking"], width=2),
        fillcolor="rgba(0,97,242,0.25)",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], tickvals=[20, 40, 60, 80, 100]),
            angularaxis=dict(tickfont=dict(size=12)),
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=20, b=20),
        height=320,
    )
    return fig


def dimension_bar(dimensions: list[dict]) -> go.Figure:
    """차원별 점수 + 가중치 가로 막대."""
    names = [d["name"] for d in dimensions]
    scores = [d.get("score") or 0 for d in dimensions]
    weights = [(d.get("weight") or 0) * 100 for d in dimensions]
    cats = [d.get("category", "must") for d in dimensions]
    colors = [PALETTE["must"] if c in ("must", "필수") else PALETTE["nice"] for c in cats]
    labels = [f"{s} (가중치 {w:.0f}%)" for s, w in zip(scores, weights)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scores,
        y=names,
        orientation="h",
        marker_color=colors,
        text=labels,
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="점수 (0~100)", showgrid=True, gridcolor=PALETTE["axis"]),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=80, t=20, b=40),
        height=max(180, 50 * len(names)),
        showlegend=False,
    )
    return fig


def ranking_bar(rows: list[dict]) -> go.Figure:
    """후보자 랭킹 막대 차트.
    rows: [{"label": str, "score": int, "recommendation": str}]
    """
    rows_sorted = sorted(rows, key=lambda r: r.get("score") or 0, reverse=True)
    names = [r["label"] for r in rows_sorted]
    scores = [r.get("score") or 0 for r in rows_sorted]
    recs = [r.get("recommendation", "") for r in rows_sorted]

    color_by_rec = {
        "면접 강력 추천": "#2BC076",
        "면접 추천": "#2C7BE5",
        "보류": "#F6C343",
        "부적합": "#E63757",
    }
    colors = [color_by_rec.get(r, "#95AAC9") for r in recs]
    text = [f"{s} · {r}" for s, r in zip(scores, recs)]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=scores,
        y=names,
        orientation="h",
        marker_color=colors,
        text=text,
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        xaxis=dict(range=[0, 110], title="종합 점수", showgrid=True, gridcolor=PALETTE["axis"]),
        yaxis=dict(autorange="reversed"),
        margin=dict(l=20, r=140, t=20, b=40),
        height=max(220, 40 * len(names) + 80),
        showlegend=False,
    )
    return fig
