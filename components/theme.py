"""ブランドカラーパレットとPlotlyテーマの定義（ベース5色／グラデーション主体）。

色数を5色以内に絞り、明度差で強調と調和を作る設計。
- ブロンズ系（プライマリ）
- テキストグレー
- 背景白系
- 成功緑
- 警告赤
店舗の区別はブロンズ明度違い（補色不使用）。
"""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

# ============== 1. ブロンズ系（プライマリ） ==============
BRONZE_900 = "#5C4530"
BRONZE_700 = "#7A6552"
BRONZE_500 = "#A88564"   # ブランドメイン
BRONZE_400 = "#C8A464"
BRONZE_300 = "#E8C77A"
BRONZE_100 = "#F5E1B5"
BRONZE_50  = "#FAF3E6"

# ============== 2. テキストグレー ==============
TEXT_900 = "#111827"
TEXT_700 = "#4B5563"
TEXT_500 = "#6B7280"
TEXT_300 = "#9CA3AF"

# ============== 3. 背景・ボーダー ==============
BG_PRIMARY = "#FFFFFF"
BG_SECONDARY = "#FAFAFB"
BG_TERTIARY = "#F7F8FA"
BORDER = "#E5E7EB"
BORDER_STRONG = "#D1D5DB"

# ============== 4. 成功（緑） ==============
SUCCESS_700 = "#15803D"
SUCCESS = "#16A34A"
SUCCESS_300 = "#4ADE80"

# ============== 5. 警告（赤） ==============
DANGER_700 = "#991B1B"
DANGER = "#DC2626"
DANGER_300 = "#F87171"

# ============== 店舗カラー（ブロンズ明度違い） ==============
STORE_COLORS = {
    "新宿": BRONZE_700,   # 濃
    "銀座": BRONZE_500,   # 中
    "上野": BRONZE_300,   # 薄
}

# グラデーション用（CSSで使う場合）
STORE_GRADIENTS = {
    "新宿": (BRONZE_900, BRONZE_700),
    "銀座": (BRONZE_700, BRONZE_500),
    "上野": (BRONZE_400, BRONZE_300),
}

# ============== 区分（新規/リピート） ==============
# 明度差で対比、補色は使わない
SEGMENT_COLORS = {
    "new": BRONZE_700,
    "repeat": BRONZE_300,
    "新規": BRONZE_700,
    "リピート": BRONZE_300,
}

# ============== Plotly Colorway（ブロンズ階調） ==============
PLOT_COLORWAY = [
    BRONZE_500,
    BRONZE_700,
    BRONZE_300,
    BRONZE_900,
    BRONZE_400,
    BRONZE_100,
]

# ============== 互換エイリアス（既存コード対応） ==============
BRONZE = BRONZE_500
BRONZE_LIGHT = BRONZE_400
BRONZE_DARK = BRONZE_700
GOLD = BRONZE_300
WARNING = "#F59E0B"   # ※ Plotlyテンプレート以外ではほぼ未使用
INFO = TEXT_700
TEXT_PRIMARY = TEXT_900
TEXT_SECONDARY = TEXT_500
TEXT_MUTED = TEXT_300


# ============== Plotly テーマ ==============
def _build_template() -> go.layout.Template:
    return go.layout.Template(
        layout=dict(
            plot_bgcolor=BG_PRIMARY,
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(
                family='"Noto Sans JP","Hiragino Sans","Roboto",sans-serif',
                color=TEXT_900,
                size=12,
            ),
            colorway=PLOT_COLORWAY,
            xaxis=dict(
                gridcolor="#F0F1F4",
                linecolor=BORDER,
                zerolinecolor=BORDER,
                tickfont=dict(color=TEXT_500, size=11),
                title=dict(font=dict(color=TEXT_500, size=12)),
            ),
            yaxis=dict(
                gridcolor="#F0F1F4",
                linecolor=BORDER,
                zerolinecolor=BORDER,
                tickfont=dict(color=TEXT_500, size=11),
                title=dict(font=dict(color=TEXT_500, size=12)),
            ),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color=TEXT_500, size=11),
            ),
            margin=dict(l=50, r=20, t=40, b=40),
            hoverlabel=dict(
                bgcolor=BG_PRIMARY,
                bordercolor=BORDER,
                font=dict(color=TEXT_900, size=12, family='"Noto Sans JP",sans-serif'),
            ),
            title=dict(text="", font=dict(color=TEXT_900, size=15)),
        )
    )


def install_plotly_theme() -> None:
    pio.templates["esthi"] = _build_template()
    pio.templates.default = "esthi"
