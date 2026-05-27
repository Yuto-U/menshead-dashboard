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

# ============== 4. 成功（緑）/ Apple System Green ==============
SUCCESS_700 = "#248A3D"
SUCCESS = "#34C759"
SUCCESS_300 = "#A1E5B0"

# ============== 5. 警告（赤）/ Apple System Red ==============
DANGER_700 = "#C9342B"
DANGER = "#FF3B30"
DANGER_300 = "#FFA09B"

# ============== 6. 情報（青）/ Apple System Blue ==============
INFO_700 = "#0051D5"
INFO_500 = "#007AFF"
INFO_300 = "#80BDFF"

# ============== Apple/Google風 システムカラー ==============
# データ可視化用のカラー。意味的に使い分ける。
SYS_BLUE = "#007AFF"     # iOS Blue（情報・主軸データ）
SYS_GREEN = "#34C759"    # iOS Green（成功・好調・成長）
SYS_RED = "#FF3B30"      # iOS Red（警告・減少）
SYS_ORANGE = "#FF9500"   # iOS Orange（注意・特別）
SYS_YELLOW = "#FFCC00"   # iOS Yellow（強調）
SYS_PURPLE = "#AF52DE"   # iOS Purple（プレミアム・人）
SYS_PINK = "#FF2D55"     # iOS Pink
SYS_TEAL = "#5AC8FA"     # iOS Light Blue
SYS_INDIGO = "#5856D6"   # iOS Indigo

# ============== 店舗カラー（システムカラー） ==============
# 新宿=Blue(主力)、銀座=Orange(高単価)、上野=Green(成長)
STORE_COLORS = {
    "新宿": SYS_BLUE,
    "銀座": SYS_ORANGE,
    "上野": SYS_GREEN,
}

STORE_GRADIENTS = {
    "新宿": ("#0051D5", SYS_BLUE),
    "銀座": ("#C76A00", SYS_ORANGE),
    "上野": ("#248A3D", SYS_GREEN),
}

# ============== 区分（新規/リピート） ==============
SEGMENT_COLORS = {
    "new": SYS_BLUE,
    "repeat": SYS_ORANGE,
    "新規": SYS_BLUE,
    "リピート": SYS_ORANGE,
}

# ============== Plotly Colorway（多色） ==============
PLOT_COLORWAY = [
    SYS_BLUE,
    SYS_ORANGE,
    SYS_GREEN,
    SYS_PURPLE,
    SYS_PINK,
    SYS_TEAL,
    SYS_YELLOW,
    SYS_INDIGO,
]

# ============== 互換エイリアス（既存コード対応） ==============
BRONZE = BRONZE_500
BRONZE_LIGHT = BRONZE_400
BRONZE_DARK = BRONZE_700
GOLD = BRONZE_300
WARNING = SYS_ORANGE
INFO = INFO_500
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
