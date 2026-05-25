"""共通グラフユーティリティ。視覚的に整ったPlotlyフィギュアを返す。"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from components.theme import (
    BORDER,
    BRONZE,
    BRONZE_LIGHT,
    GOLD,
    PLOT_COLORWAY,
    SEGMENT_COLORS,
    STORE_COLORS,
    SUCCESS,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


def _store_color_map(color_field: str | None) -> dict | None:
    if color_field == "店舗":
        return STORE_COLORS
    if color_field in ("区分", "new_or_repeat"):
        return SEGMENT_COLORS
    return None


def bar_horizontal(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str | None = None,
    color: str | None = None,
    height: int = 300,
) -> go.Figure:
    fig = px.bar(
        df, x=x, y=y, orientation="h",
        color=color or y,
        color_discrete_map=_store_color_map(color or y),
        color_discrete_sequence=PLOT_COLORWAY,
    )
    fig.update_traces(
        text=None,  # まずundefinedを消す
        texttemplate="%{x:,.0f}",
        textposition="outside",
        marker_line_width=0,
        textfont=dict(color=TEXT_PRIMARY, size=12),
    )
    fig.update_layout(
        title={"text": title or ""},
        height=height,
        showlegend=False,
        xaxis=dict(showgrid=True, title=None),
        yaxis=dict(showgrid=False, title=None, autorange="reversed"),
        margin=dict(l=70, r=60, t=40 if title else 16, b=20),
    )
    return fig


def bar_vertical(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str | None = None,
    text_auto: str | bool = ".2s",
    height: int = 320,
    barmode: str = "group",
) -> go.Figure:
    """棒グラフ。text_auto は文字列のときのみpx.barに渡し、Falseの場合は何も渡さない。

    text_auto=False を直接 px.bar に渡すと Plotly Express がデータラベルに
    "undefined" を描画する既知の挙動を回避するため、引数を条件付きで構築。
    """
    px_kwargs: dict = dict(
        x=x, y=y, color=color,
        color_discrete_map=_store_color_map(color),
        color_discrete_sequence=PLOT_COLORWAY,
        barmode=barmode,
    )
    if isinstance(text_auto, str) and text_auto:
        px_kwargs["text_auto"] = text_auto

    fig = px.bar(df, **px_kwargs)
    fig.update_traces(marker_line_width=0, textfont=dict(color=TEXT_PRIMARY, size=11))
    # text_autoが渡されてないときは、念のためtextを空にしてラベル領域を消す
    if "text_auto" not in px_kwargs:
        fig.update_traces(text=None, texttemplate="", textposition="none")

    fig.update_layout(
        title={"text": title or ""},
        height=height,
        showlegend=color is not None,
        margin=dict(l=50, r=20, t=40 if title else 16, b=40),
    )
    return fig


def line_trend(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: str | None = None,
    title: str | None = None,
    height: int = 360,
    markers: bool = True,
    area: bool = False,
) -> go.Figure:
    if area and color is None:
        fig = px.area(df, x=x, y=y, markers=markers)
        fig.update_traces(
            line=dict(color=BRONZE, width=2.5),
            fillcolor="rgba(168,133,100,0.12)",
        )
    else:
        fig = px.line(
            df, x=x, y=y, color=color, markers=markers,
            color_discrete_map=_store_color_map(color),
            color_discrete_sequence=PLOT_COLORWAY,
        )
        fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
    fig.update_traces(text=None, texttemplate="")
    fig.update_layout(
        title={"text": title or ""},
        height=height,
        hovermode="x unified",
        margin=dict(l=50, r=20, t=40 if title else 16, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


def donut_share(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str | None = None,
    height: int = 320,
    center_label: str | None = None,
) -> go.Figure:
    fig = px.pie(
        df, names=names, values=values, hole=0.62, color=names,
        color_discrete_sequence=PLOT_COLORWAY,
        color_discrete_map=_store_color_map(names),
    )
    fig.update_traces(
        textposition="outside",
        textinfo="label+percent",
        marker=dict(line=dict(color="#FFFFFF", width=2)),
        textfont=dict(color=TEXT_PRIMARY, size=12),
    )
    annotations = []
    if center_label:
        annotations.append(dict(
            text=center_label,
            x=0.5, y=0.5,
            font=dict(size=13, color=TEXT_PRIMARY, family='"Noto Sans JP",sans-serif'),
            showarrow=False,
            align="center",
        ))
    fig.update_layout(
        title={"text": title or ""},
        height=height,
        showlegend=False,
        annotations=annotations,
        margin=dict(l=20, r=20, t=30 if title else 8, b=20),
    )
    return fig


def pie_chart(
    df: pd.DataFrame,
    names: str,
    values: str,
    title: str | None = None,
    height: int = 320,
) -> go.Figure:
    fig = px.pie(
        df, names=names, values=values, color=names,
        color_discrete_sequence=PLOT_COLORWAY,
        color_discrete_map=_store_color_map(names),
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        marker=dict(line=dict(color="#FFFFFF", width=2)),
    )
    fig.update_layout(
        title={"text": title or ""},
        height=height,
        showlegend=False,
        margin=dict(l=20, r=20, t=40 if title else 16, b=20),
    )
    return fig


def projection_gauge(actual: float, projected: float, previous: float, height: int = 240) -> go.Figure:
    """着地見込みをゲージで表現（前月実績を閾値ラインで表示）。"""
    ref = max(previous, projected) * 1.15 if previous else projected * 1.2
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=projected,
        number={"prefix": "¥", "valueformat": ",.0f", "font": {"color": TEXT_PRIMARY, "size": 26}},
        delta={
            "reference": previous, "valueformat": ",.0f", "prefix": "前月比 ¥",
            "increasing": {"color": SUCCESS}, "decreasing": {"color": "#DC2626"},
            "font": {"color": TEXT_SECONDARY, "size": 13},
        },
        gauge={
            "axis": {"range": [0, ref], "tickfont": {"color": TEXT_SECONDARY, "size": 10},
                     "tickcolor": BORDER},
            "bar": {"color": BRONZE, "thickness": 0.75},
            "bgcolor": "#F7F8FA",
            "borderwidth": 0,
            "steps": [
                {"range": [0, actual], "color": "rgba(168,133,100,0.35)"},
            ],
            "threshold": {
                "line": {"color": GOLD, "width": 4},
                "thickness": 0.85,
                "value": previous,
            },
        },
    ))
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=20, b=20),
    )
    return fig


def heatmap(df: pd.DataFrame, x: str, y: str, z: str, title: str | None = None, height: int = 320) -> go.Figure:
    pivot = df.pivot(index=y, columns=x, values=z).fillna(0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns, y=pivot.index,
        colorscale=[[0, "#F7F8FA"], [0.5, "#C8A464"], [1, "#7A5A36"]],
        showscale=True,
    ))
    fig.update_layout(
        title={"text": title or ""}, height=height,
        margin=dict(l=80, r=20, t=40 if title else 16, b=40),
    )
    return fig
