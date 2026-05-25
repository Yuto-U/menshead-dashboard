"""グローバル CSS（CSS変数によるデザイントークン化／8つのデザイン原則準拠）。

設計原則：
1. レイアウト：サイドバー + max-w 1400px、余白統一
2. カード：rounded-lg(16px)、影なし、薄ボーダー1pxのみ（フラット）
3. セクションヘッダー：kicker + title の2行構成
4. 数値：英字フォント(Inter)、太字、上下ラベル
5. グリッド：情報優先度で4/3/2カラム
6. デザイントークン化：色・余白・角丸・フォントはCSS変数
7. Empty State：データ0件時の点線プレースホルダー
8. NG禁止：カード毎に影/角丸変えない、余白バラバラ禁止、派手装飾禁止
"""
from __future__ import annotations

import streamlit as st

SIDEBAR_WIDTH = 232  # px

_GLOBAL_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Inter:wght@400;700;800&display=swap');

/* ===== デザイントークン（CSS変数） ===== */
:root {{
    /* 色 - 5色ベース */
    --color-bg: #FAFAFB;
    --color-surface: #FFFFFF;
    --color-surface-2: #F7F8FA;
    --color-border: #E5E7EB;
    --color-border-soft: #F0F1F4;
    --color-text: #111827;
    --color-text-muted: #6B7280;
    --color-text-dim: #9CA3AF;

    /* アクセント（ブロンズ系） */
    --color-accent: #A88564;
    --color-accent-light: #C8A464;
    --color-accent-soft: #E8C77A;
    --color-accent-dark: #7A6552;
    --color-accent-bg: #FAF3E6;

    /* セマンティック */
    --color-success: #16A34A;
    --color-success-bg: #DCFCE7;
    --color-danger: #DC2626;
    --color-danger-bg: #FEE2E2;

    /* 角丸 */
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 14px;
    --radius-xl: 16px;
    --radius-pill: 999px;

    /* 余白 */
    --space-1: 4px;
    --space-2: 8px;
    --space-3: 12px;
    --space-4: 16px;
    --space-5: 20px;
    --space-6: 24px;
    --space-7: 28px;
    --space-8: 32px;
    --space-10: 40px;

    /* フォント */
    --font-jp: "Noto Sans JP", "Hiragino Sans", sans-serif;
    --font-en: "Inter", -apple-system, sans-serif;
    --font-display: "Noto Sans JP", "Hiragino Sans", sans-serif;

    /* レイアウト */
    --container-max: 1400px;
    --sidebar-w: {SIDEBAR_WIDTH}px;
}}

/* ===== フォント／ベース ===== */
.stApp, body, .main,
section[data-testid="stSidebar"], .stMarkdown, .stText, input, textarea, button {{
    font-family: var(--font-jp) !important;
}}
.stApp, body {{
    font-weight: 400;
    background: var(--color-bg) !important;
    color: var(--color-text);
}}
header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
#MainMenu, footer {{ visibility: hidden; }}

.block-container {{
    padding: var(--space-7) var(--space-8) var(--space-10) var(--space-8) !important;
    max-width: var(--container-max) !important;
}}

h1, h2, h3, h4 {{
    color: var(--color-text) !important;
    font-weight: 700;
    letter-spacing: -0.01em;
    margin: 0 !important;
    font-family: var(--font-display);
}}

/* ===== サイドバー ===== */
section[data-testid="stSidebar"] {{
    width: var(--sidebar-w) !important;
    min-width: var(--sidebar-w) !important;
    max-width: var(--sidebar-w) !important;
    background: var(--color-surface) !important;
    border-right: 1px solid var(--color-border) !important;
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] > div:first-child {{
    background: var(--color-surface) !important;
    width: var(--sidebar-w) !important;
    padding-top: 0 !important;
}}
section[data-testid="stSidebar"] .block-container,
[data-testid="stSidebarUserContent"] {{
    padding: 0 !important;
    margin-top: 0 !important;
    background: var(--color-surface) !important;
}}
[data-testid="stSidebarHeader"] {{ padding: 0 !important; height: 0 !important; min-height: 0 !important; }}
[data-testid="stSidebarCollapseButton"] {{ position: absolute; top: 8px; right: 8px; }}

.sidebar-logo-wrap {{
    padding: var(--space-4) var(--space-4) var(--space-4) var(--space-4);
    display: flex; align-items: center; gap: var(--space-3);
    border-bottom: 1px solid var(--color-border-soft);
    white-space: nowrap; overflow: hidden;
}}
.sidebar-logo-wrap img {{
    width: 34px; height: 34px; border-radius: var(--radius-sm);
    background: var(--color-bg); padding: 4px;
    border: 1px solid var(--color-border); flex-shrink: 0;
}}
.sidebar-brand-block {{ line-height: 1.2; min-width: 0; }}
.sidebar-brand-name {{
    font-size: 12px; font-weight: 700; color: var(--color-text);
    letter-spacing: 0.04em;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.sidebar-brand-sub {{
    font-size: 10px; color: var(--color-text-dim); font-weight: 400;
    letter-spacing: 0.04em; margin-top: 3px;
}}
.sidebar-section {{
    color: var(--color-text-dim);
    font-size: 11px;
    letter-spacing: 0.3em;  /* tracking-[0.3em] */
    text-transform: uppercase;
    margin: var(--space-5) var(--space-4) var(--space-2) var(--space-4);
    font-weight: 700;
}}
.sidebar-nav-link {{
    display: flex; align-items: center; gap: var(--space-3);
    padding: var(--space-2) var(--space-3); margin: 2px var(--space-2);
    color: var(--color-text-muted) !important; text-decoration: none !important;
    font-size: 13px; font-weight: 400;
    border-radius: var(--radius-sm);
    transition: background 0.15s, color 0.15s;
    white-space: nowrap; overflow: hidden;
}}
.sidebar-nav-link:hover {{
    background: #F3F4F6; color: var(--color-text) !important;
}}
.sidebar-nav-link.active {{
    background: linear-gradient(90deg, #F2E6CC 0%, var(--color-accent-bg) 100%);
    color: var(--color-accent-dark) !important;
    font-weight: 700;
}}
.sidebar-nav-link svg {{ flex-shrink: 0; color: var(--color-text-muted); }}
.sidebar-nav-link.active svg {{ color: var(--color-accent); }}
.sidebar-nav-link:hover svg {{ color: var(--color-text); }}

.sidebar-divider {{ height: 1px; background: var(--color-border-soft); margin: var(--space-3) var(--space-4); }}

section[data-testid="stSidebar"] .stButton > button {{
    background: var(--color-surface) !important;
    color: var(--color-text-muted) !important;
    border: 1px solid var(--color-border) !important;
    box-shadow: none !important;
    font-weight: 400; font-size: 13px !important;
    margin: 4px var(--space-3); padding: 7px var(--space-3) !important;
    min-height: 34px !important; border-radius: var(--radius-sm) !important;
}}
section[data-testid="stSidebar"] .stButton > button:hover {{
    background: #F3F4F6 !important; color: var(--color-text) !important;
}}

/* ===== ページヘッダ（セクションヘッダー定型：kicker + title） ===== */
.page-header {{
    display: flex; justify-content: space-between; align-items: flex-start;
    gap: var(--space-4);
    padding: 0 4px var(--space-5) 4px;
    margin-bottom: var(--space-7);
    border-bottom: 1px solid var(--color-border);
}}
.page-kicker {{
    color: var(--color-accent);
    font-size: 12px;
    letter-spacing: 0.3em;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 6px;
    display: inline-block;
    font-family: var(--font-en);
}}
.page-title {{
    font-size: 30px; font-weight: 700; color: var(--color-text);
    letter-spacing: -0.02em; line-height: 1.2;
    font-family: var(--font-display);
}}
.page-subtitle {{ color: var(--color-text-muted); font-size: 12px; font-weight: 400; margin-top: 6px; }}
.page-meta {{
    color: var(--color-text-dim); font-size: 11px; text-align: right;
    white-space: nowrap; padding-top: 10px; font-weight: 400;
    font-family: var(--font-en);
}}
.page-meta b {{ color: var(--color-text-muted); font-weight: 700; }}

/* ===== KPIストリップ（フラット・ボーダー1pxのみ） ===== */
.kpi-strip {{
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-xl);
    padding: 0;
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0;
    overflow: hidden;
    margin-bottom: var(--space-4);
}}
.kpi-strip-cell {{
    padding: var(--space-6) var(--space-7);
    border-left: 1px solid var(--color-border-soft);
    min-width: 0;
    position: relative;
}}
.kpi-strip-cell.first {{ border-left: none; }}
.kpi-strip-cell.featured {{
    background: linear-gradient(135deg, rgba(168,133,100,0.10) 0%, rgba(232,199,122,0.05) 50%, rgba(255,255,255,0) 100%);
}}
/* KPIカードのコーナーマーク（コーナーロゴ装飾・薄い透過） */
.kpi-strip-cell.featured::after {{
    content: "";
    position: absolute;
    top: 50%; right: -10px;
    width: 80px; height: 80px;
    transform: translateY(-50%);
    background-image: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="%23A88564"><path d="M12 2L1 22h22L12 2zm0 4l8 14H4l8-14z"/></svg>');
    background-repeat: no-repeat;
    background-size: contain;
    opacity: 0.04;
    pointer-events: none;
}}
.kpi-strip-label {{
    color: var(--color-text-muted); font-size: 13px; font-weight: 400;
    margin-bottom: var(--space-3);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}}
.kpi-strip-value {{
    color: var(--color-text); font-size: 32px; font-weight: 800;
    line-height: 1.1; letter-spacing: -0.02em;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-family: var(--font-en);
}}
.kpi-strip-cell.featured .kpi-strip-value {{
    background: linear-gradient(135deg, var(--color-accent-dark), var(--color-accent-light));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.kpi-strip-delta {{
    font-size: 13px; font-weight: 700; margin-top: var(--space-3);
    display: inline-flex; align-items: center; gap: 4px;
    font-family: var(--font-en);
    letter-spacing: 0.02em;
}}
.kpi-strip-delta.up {{ color: var(--color-success); }}
.kpi-strip-delta.down {{ color: var(--color-danger); }}
.kpi-strip-delta.flat {{ color: var(--color-text-dim); }}
.kpi-strip-delta .trend-suffix {{
    color: var(--color-text-dim); font-weight: 400; margin-left: 4px;
    letter-spacing: 0.18em; text-transform: uppercase; font-size: 10px;
}}
.kpi-strip-sub {{
    color: var(--color-text-dim); font-size: 10px; margin-top: var(--space-2);
    letter-spacing: 0.18em; text-transform: uppercase;
}}

/* ===== KPIカード（単独） ===== */
.kpi-card {{
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-5) var(--space-6);
    min-height: 140px;
    display: flex; flex-direction: column; justify-content: space-between;
    transition: border-color 0.18s;
    overflow: hidden;
}}
.kpi-card:hover {{ border-color: #D1D5DB; }}
.kpi-label {{ color: var(--color-text-muted); font-size: 13px; font-weight: 400; }}
.kpi-value {{
    color: var(--color-text); font-size: 32px; font-weight: 800;
    line-height: 1.15; letter-spacing: -0.02em;
    margin: var(--space-2) 0;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-family: var(--font-en);
}}
.kpi-sub {{
    color: var(--color-text-dim); font-size: 10px; font-weight: 400; line-height: 1.4;
    letter-spacing: 0.18em; text-transform: uppercase;
}}
.kpi-trend {{
    display: inline-flex; gap: 4px; align-items: center;
    font-size: 13px; font-weight: 700;
    font-family: var(--font-en);
}}
.kpi-trend.up {{ color: var(--color-success); }}
.kpi-trend.down {{ color: var(--color-danger); }}
.kpi-trend.flat {{ color: var(--color-text-dim); }}
.kpi-trend .trend-suffix {{
    color: var(--color-text-dim); font-weight: 400;
    letter-spacing: 0.18em; text-transform: uppercase; font-size: 10px;
}}

/* ハイライトKPI */
.kpi-card.highlight {{
    background: linear-gradient(135deg, #FFF6E0 0%, #FFFCF4 60%, var(--color-surface) 100%);
    border: 1px solid var(--color-accent-soft);
}}
.kpi-card.highlight .kpi-label {{ color: var(--color-accent-dark); font-weight: 700; }}

/* ===== セクション ===== */
.section-title {{
    color: var(--color-text);
    font-size: 20px;
    font-weight: 700;
    margin: var(--space-5) 0 var(--space-3) 0;
    letter-spacing: -0.01em;
    display: flex; align-items: center; gap: var(--space-3);
    font-family: var(--font-display);
}}
.section-title .granularity {{
    color: var(--color-text-dim);
    font-size: 12px;
    font-weight: 400;
    background: var(--color-surface-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 3px 10px;
    letter-spacing: 0.04em;
}}
.section-sub {{ color: var(--color-text-muted); font-size: 12px; margin: -8px 0 var(--space-3) 0; font-weight: 400; }}

/* ===== チャートカード（フラット・ボーダー1pxのみ・内側30%余白） ===== */
[data-testid="stLayoutWrapper"] {{
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    border-radius: var(--radius-xl) !important;
    padding: var(--space-7) !important;  /* 全方位28px */
    box-shadow: none !important;
    margin-bottom: 8px;
    box-sizing: border-box !important;
}}
/* st.columns()を内包する外側ラッパーは枠を消す（二重枠回避） */
[data-testid="stLayoutWrapper"]:has(> div > [data-testid="stHorizontalBlock"]),
[data-testid="stLayoutWrapper"]:has(> [data-testid="stHorizontalBlock"]) {{
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin-bottom: 0 !important;
}}
/* 内側のVerticalBlock：Streamlitのデフォルトborderを消して二重枠を防ぐ */
[data-testid="stLayoutWrapper"] [data-testid="stVerticalBlock"] {{
    border: none !important;
    background: transparent !important;
    border-radius: 0 !important;
    padding: 0 !important;
    box-shadow: none !important;
}}
[data-testid="stLayoutWrapper"] > div > [data-testid="stVerticalBlock"] {{
    gap: 0.7rem !important;
}}
[data-testid="stLayoutWrapper"] [data-testid="element-container"] {{
    margin: 0 !important;
}}
.chart-kicker {{
    color: var(--color-text-muted);
    font-size: 14px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    display: flex; align-items: center; gap: var(--space-2);
    font-family: var(--font-en);
}}
.chart-kicker > span:first-child {{ color: var(--color-text-muted); }}
.chart-kicker .granularity {{
    color: var(--color-text-dim);
    font-size: 11px;
    font-weight: 400;
    background: var(--color-surface-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    padding: 2px 6px;
    letter-spacing: 0.04em;
    text-transform: none;
    font-family: var(--font-jp);
}}
.chart-title {{
    font-size: 30px; font-weight: 800; color: var(--color-text);
    margin-top: 6px; margin-bottom: 4px;
    letter-spacing: -0.02em; line-height: 1.2;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-family: var(--font-en);
}}
.chart-sub {{
    font-size: 14px; color: var(--color-text-muted);
    margin-bottom: var(--space-3); font-weight: 400;
}}
.chart-sub .delta-up {{ color: var(--color-success); font-weight: 700; font-family: var(--font-en); }}
.chart-sub .delta-down {{ color: var(--color-danger); font-weight: 700; font-family: var(--font-en); }}

/* ===== ランキングリスト ===== */
.rank-list {{
    display: flex; flex-direction: column; gap: var(--space-2);
    margin-top: var(--space-2);
}}
.rank-row {{
    display: grid;
    grid-template-columns: 32px 1fr auto;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-2) var(--space-3);
    background: var(--color-bg);
    border: 1px solid var(--color-border-soft);
    border-radius: var(--radius-sm);
}}
.rank-badge {{
    width: 28px; height: 28px;
    border-radius: var(--radius-sm);
    display: inline-flex; align-items: center; justify-content: center;
    font-size: 13px; font-weight: 700;
    color: var(--color-surface);
    font-family: var(--font-en);
}}
.rank-badge.gold {{ background: linear-gradient(135deg, var(--color-accent-light), var(--color-accent-soft)); }}
.rank-badge.silver {{ background: linear-gradient(135deg, #94A3B8, #CBD5E1); }}
.rank-badge.bronze {{ background: linear-gradient(135deg, var(--color-accent-dark), var(--color-accent)); }}
.rank-badge.plain {{ background: var(--color-border); color: var(--color-text-muted); }}
.rank-label {{ font-size: 15px; font-weight: 700; color: var(--color-text); }}
.rank-sub {{ font-size: 12px; color: var(--color-text-dim); font-weight: 400; margin-top: 3px; }}
.rank-value {{ font-size: 16px; font-weight: 800; color: var(--color-text); text-align: right; font-family: var(--font-en); }}
.rank-delta {{ font-size: 12px; font-weight: 700; text-align: right; margin-top: 3px; font-family: var(--font-en); }}
.rank-delta.up {{ color: var(--color-success); }}
.rank-delta.down {{ color: var(--color-danger); }}

/* ベスト記録バッジ */
.record-pill {{
    display: inline-flex; align-items: center; gap: 4px;
    padding: 2px 8px; border-radius: var(--radius-pill);
    background: linear-gradient(135deg, #FFF6E0, var(--color-accent-bg));
    border: 1px solid var(--color-accent-soft);
    color: var(--color-accent-dark);
    font-size: 11px; font-weight: 700;
    margin-left: 8px;
    font-family: var(--font-en);
}}

/* ===== 優先度テーブル ===== */
.priority-table-wrap {{
    overflow-x: auto;
    margin-top: var(--space-2);
}}
.priority-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 13px;
}}
.priority-table thead th {{
    padding: 10px 12px;
    text-align: left;
    color: var(--color-text-dim);
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-surface);
    position: sticky; top: 0;
    white-space: nowrap;
    font-family: var(--font-en);
}}
.priority-table thead th.right {{ text-align: right; }}
.priority-table tbody td {{
    padding: 12px;
    border-bottom: 1px solid var(--color-border-soft);
    color: var(--color-text);
    vertical-align: middle;
}}
.priority-table tbody td.num {{
    text-align: right;
    font-family: var(--font-en);
    font-weight: 700;
}}
.priority-table tbody tr:last-child td {{ border-bottom: none; }}
.priority-table tbody tr:hover td {{ background: #FAFAFB; }}

.priority-group-row td {{
    padding: 14px 12px 8px 12px !important;
    border-bottom: none !important;
    background: transparent !important;
}}
.priority-group-label {{
    display: inline-flex; align-items: center; gap: 8px;
    color: var(--color-text-muted);
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.2em; text-transform: uppercase;
    font-family: var(--font-en);
}}
.priority-group-label .count {{
    color: var(--color-text-dim); font-weight: 400; letter-spacing: 0.04em;
}}

.priority-badge {{
    display: inline-flex;
    align-items: center; justify-content: center;
    width: 32px; height: 32px;
    border-radius: var(--radius-sm);
    font-size: 14px; font-weight: 700;
    color: var(--color-surface);
    font-family: var(--font-en);
}}
.priority-badge.p3 {{ background: linear-gradient(135deg, var(--color-accent-light), var(--color-accent-soft)); }}
.priority-badge.p2 {{ background: linear-gradient(135deg, var(--color-accent), var(--color-accent-light)); }}
.priority-badge.p1 {{ background: linear-gradient(135deg, var(--color-accent-dark), var(--color-accent)); }}
.priority-badge.none {{ background: var(--color-border); color: var(--color-text-muted); }}

.priority-cast-name {{
    font-weight: 700; color: var(--color-text); font-size: 14px;
}}
.priority-cast-meta {{
    font-size: 11px; color: var(--color-text-dim);
    margin-top: 2px;
}}
.priority-cell-area {{
    display: inline-block;
    padding: 2px 8px;
    background: var(--color-surface-2);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: 11px;
    color: var(--color-text-muted);
    font-weight: 400;
}}

/* コンパクト版（13列の優先度全項目テーブル用・読みやすさ重視） */
.priority-table.compact thead th {{
    padding: 10px 10px;
    font-size: 13px;
    letter-spacing: 0.04em;
    text-transform: none;
    color: var(--color-text-muted);
    font-weight: 700;
}}
.priority-table.compact tbody td {{
    padding: 12px 10px;
    font-size: 14px;
}}
.priority-table.compact tbody td.num {{
    font-size: 15px;
}}
.priority-table.compact .priority-badge {{
    width: 30px; height: 30px;
    font-size: 14px;
    border-radius: 7px;
}}
.priority-table.compact .cast-name-cell {{
    font-weight: 700;
    color: var(--color-text);
    font-size: 15px;
}}
.priority-table.compact .text-mini {{
    font-size: 13px;
    color: var(--color-text-muted);
    text-align: center;
}}
.priority-table.compact .priority-group-row td {{
    padding: 14px 10px 8px 10px !important;
}}
.priority-table.compact .priority-group-label {{
    font-size: 12px;
}}

/* ===== Empty State ===== */
.empty-state {{
    border: 1.5px dashed var(--color-border);
    border-radius: var(--radius-xl);
    background: var(--color-surface-2);
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center;
    padding: var(--space-6);
    min-height: 180px;
}}
.empty-state .empty-icon {{
    font-size: 22px; opacity: 0.4; margin-bottom: var(--space-2);
}}
.empty-state .empty-message {{
    color: var(--color-text-dim); font-size: 12px; line-height: 1.5;
}}
.empty-state .empty-cta {{
    color: var(--color-accent); font-size: 11px; margin-top: var(--space-2);
    letter-spacing: 0.18em; text-transform: uppercase; font-weight: 700;
}}

/* ===== グリッド余白（カード間隔を詰める） ===== */
[data-testid="stHorizontalBlock"] {{
    display: flex !important;
    align-items: stretch !important;
    gap: 0.75rem !important;
    margin-bottom: 0.6rem;
}}
.main [data-testid="stVerticalBlock"] {{ gap: 0.6rem !important; }}

/* ===== 横並びカードの高さ揃え（多階層flex stretch） ===== */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
    padding: 0 4px !important;
    display: flex !important;
    flex-direction: column !important;
    align-self: stretch !important;
}}
/* column の直下のすべての層を flex で伸ばす */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > div,
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] > div > div {{
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 auto !important;
}}
/* BorderWrapper を column 全高に伸ばす */
[data-testid="stHorizontalBlock"] > [data-testid="stColumn"] [data-testid="stLayoutWrapper"] {{
    flex: 1 1 auto !important;
    height: auto !important;
    min-height: 100% !important;
    box-sizing: border-box !important;
}}

/* ===== データフレーム ===== */
[data-testid="stDataFrame"] {{
    background: var(--color-surface);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border);
}}

/* ===== Selectbox / Input ===== */
div[data-baseweb="select"] > div {{
    background: var(--color-surface) !important;
    border: 1px solid #D1D5DB !important;
    border-radius: var(--radius-sm) !important;
    min-height: 36px !important;
}}
input, textarea {{
    background: var(--color-surface) !important;
    color: #1F2937 !important;
    border: 1px solid #D1D5DB !important;
    border-radius: var(--radius-sm) !important;
    font-weight: 400;
}}
[data-testid="stWidgetLabel"] {{
    font-size: 12px !important;
    color: var(--color-text-muted) !important;
    margin-bottom: 4px !important;
    font-weight: 400 !important;
}}

/* ===== メインボタン ===== */
.main .stButton > button,
div[data-testid="stForm"] .stButton > button {{
    background: linear-gradient(135deg, var(--color-accent) 0%, var(--color-accent-light) 100%) !important;
    color: var(--color-surface) !important;
    border: none !important;
    border-radius: var(--radius-sm);
    font-weight: 700;
    padding: 10px 20px;
    box-shadow: none;
    transition: background 0.18s, transform 0.06s;
}}
.main .stButton > button:hover,
div[data-testid="stForm"] .stButton > button:hover {{
    background: linear-gradient(135deg, #927055 0%, #B89554 100%) !important;
    transform: translateY(-1px);
}}

/* ===== ログイン ===== */
.login-wrap {{ max-width: 380px; margin: 64px auto 0; text-align: center; }}
.login-logo {{
    width: 72px; height: 72px; border-radius: var(--radius-xl);
    background: var(--color-surface); border: 1px solid var(--color-border);
    display: inline-flex; align-items: center; justify-content: center;
    margin-bottom: var(--space-3);
}}
.login-title {{ font-size: 18px; font-weight: 700; color: var(--color-text); letter-spacing: 0.04em; }}
.login-sub {{ color: var(--color-text-muted); font-size: 12px; margin-top: 4px; margin-bottom: var(--space-4); font-weight: 400; }}

/* ===== バッジ ===== */
.badge {{ display: inline-block; padding: 2px 8px; border-radius: var(--radius-sm); font-size: 11px; font-weight: 700; }}
.badge.bronze {{ background: linear-gradient(135deg, #F2E6CC, #FFF8E7); color: var(--color-accent-dark); }}
.badge.success {{ background: linear-gradient(135deg, #BBF7D0, var(--color-success-bg)); color: #166534; }}
.badge.danger {{ background: linear-gradient(135deg, #FECACA, var(--color-danger-bg)); color: #991B1B; }}

/* スクロールバー */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: var(--color-surface-2); }}
::-webkit-scrollbar-thumb {{ background: #D1D5DB; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--color-text-dim); }}

/* Plotly */
[data-testid="stPlotlyChart"] {{ margin-top: 0 !important; }}

[data-testid="stAlert"] {{
    padding: 12px 16px !important;
    border-radius: var(--radius-md) !important;
    font-size: 13px !important;
    background: var(--color-surface) !important;
    border: 1px solid var(--color-border) !important;
    color: var(--color-text) !important;
    font-weight: 400;
}}

/* expander */
.streamlit-expanderHeader, [data-testid="stExpander"] details summary {{
    font-size: 13px !important;
    padding: 10px 14px !important;
    background: var(--color-surface) !important;
    border-radius: var(--radius-md) !important;
    border: 1px solid var(--color-border) !important;
    font-weight: 700;
}}

/* ===== レスポンシブ ===== */
@media (max-width: 1280px) {{
    .kpi-strip-value {{ font-size: 24px; }}
    .kpi-strip-cell {{ padding: var(--space-5) var(--space-5); }}
    [data-testid="stLayoutWrapper"] {{ padding: var(--space-5) var(--space-5) !important; }}
}}
@media (max-width: 1024px) {{
    .block-container {{ padding: var(--space-5) var(--space-5) var(--space-8) var(--space-5) !important; }}
    .page-title {{ font-size: 24px; }}
    .kpi-value {{ font-size: 24px; }}
    .kpi-strip-value {{ font-size: 22px; }}
    .kpi-strip-cell {{ padding: var(--space-4) var(--space-5); }}
    .kpi-card {{ min-height: 124px; padding: var(--space-4) var(--space-5); }}
    .chart-title {{ font-size: 20px; }}
}}
@media (max-width: 768px) {{
    section[data-testid="stSidebar"],
    section[data-testid="stSidebar"] > div:first-child {{
        width: 210px !important; min-width: 210px !important;
    }}
    .block-container {{ padding: var(--space-4) var(--space-4) var(--space-8) var(--space-4) !important; }}
    .page-header {{
        flex-direction: column; align-items: flex-start;
        padding-bottom: var(--space-4); margin-bottom: var(--space-5);
    }}
    .page-title {{ font-size: 22px; }}
    .page-meta {{ text-align: left; padding-top: 4px; }}
    .kpi-card {{ min-height: 116px; padding: var(--space-4); }}
    .kpi-value {{ font-size: 22px; }}
    .section-title {{ font-size: 14px; }}
    [data-testid="stColumn"] {{ padding: 0 4px !important; min-width: 100% !important; }}
    .kpi-strip {{ grid-template-columns: repeat(2, 1fr); padding: 0; }}
    .kpi-strip-cell:nth-child(3), .kpi-strip-cell:nth-child(4) {{ border-top: 1px solid var(--color-border-soft); }}
    .kpi-strip-cell:nth-child(3) {{ border-left: none; }}
    [data-testid="stLayoutWrapper"] {{ padding: var(--space-5) !important; }}
    .chart-title {{ font-size: 20px; }}
}}
@media (max-width: 480px) {{
    .block-container {{ padding: var(--space-3) var(--space-3) var(--space-7) var(--space-3) !important; }}
    .page-title {{ font-size: 20px; }}
    .page-kicker {{ font-size: 10px; }}
    .kpi-card {{ min-height: 106px; padding: var(--space-3) var(--space-4); }}
    .kpi-value {{ font-size: 20px; }}
    .kpi-label {{ font-size: 11px; }}
    [data-testid="stLayoutWrapper"] {{ padding: var(--space-4) !important; }}
    .kpi-strip {{ grid-template-columns: 1fr; padding: 0; }}
    .kpi-strip-cell {{
        padding: var(--space-4) !important; border-left: none !important;
        border-top: 1px solid var(--color-border-soft);
    }}
    .kpi-strip-cell.first {{ border-top: none; }}
}}
</style>
"""


def apply_global_style() -> None:
    st.markdown(_GLOBAL_CSS, unsafe_allow_html=True)
