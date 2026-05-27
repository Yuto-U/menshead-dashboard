"""ヘッダー、KPIカード、サイドバー、ページ共通レイアウト。"""
from __future__ import annotations

import base64
from datetime import datetime
from pathlib import Path

import streamlit as st

from components.auth import is_auth_enabled
from components.icons import svg

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

_favicon = None
_logo_cache: dict[str, str] = {}


def _logo_data_uri(name: str = "logo_icon.png") -> str:
    """ロゴをbase64でメモ化（毎ページ再エンコードを避ける）。"""
    if name in _logo_cache:
        return _logo_cache[name]
    path = ASSETS_DIR / name
    if not path.exists():
        _logo_cache[name] = ""
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    uri = f"data:image/png;base64,{data}"
    _logo_cache[name] = uri
    return uri


def favicon():
    """ロゴアイコンを PIL.Image で返す（st.set_page_config の page_icon 用）。"""
    global _favicon
    if _favicon is None:
        try:
            from PIL import Image
            _favicon = Image.open(ASSETS_DIR / "logo_icon.png")
        except Exception:
            _favicon = "🌿"
    return _favicon


NAV_ITEMS = [
    {"key": "home", "icon": "home", "label": "ホーム", "url": "/"},
    {"key": "store", "icon": "store", "label": "店舗別", "url": "/店舗別"},
    {"key": "cast", "icon": "user", "label": "キャスト別", "url": "/キャスト別"},
    {"key": "course", "icon": "target", "label": "コース別", "url": "/コース別"},
    {"key": "recruit", "icon": "book", "label": "採用・在籍", "url": "/採用研修"},
    {"key": "trend", "icon": "trend", "label": "トレンド分析", "url": "/トレンド分析"},
    {"key": "meeting", "icon": "presentation", "label": "会議モード", "url": "/会議モード"},
]
ADMIN_ITEMS = [
    {"key": "data", "icon": "database", "label": "データ管理", "url": "/データ管理"},
    {"key": "admin", "icon": "settings", "label": "管理", "url": "/管理"},
]


def render_sidebar(active_key: str = "home") -> None:
    """ロゴ + ナビゲーション。ダーク背景。"""
    logo_uri = _logo_data_uri("logo_icon.png")

    with st.sidebar:
        st.markdown(
            f"""
            <div class="sidebar-logo-wrap">
                <img src="{logo_uri}" />
                <div class="sidebar-brand-block">
                    <div class="sidebar-brand-name">MEN'S HEAD SPA</div>
                    <div class="sidebar-brand-sub">経営ダッシュボード</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="sidebar-section">メイン</div>', unsafe_allow_html=True)
        for item in NAV_ITEMS:
            cls = "sidebar-nav-link" + (" active" if item["key"] == active_key else "")
            st.markdown(
                f'<a class="{cls}" href="{item["url"]}" target="_self">'
                f'{svg(item["icon"], size=18)}<span>{item["label"]}</span></a>',
                unsafe_allow_html=True,
            )

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section">設定</div>', unsafe_allow_html=True)
        for item in ADMIN_ITEMS:
            cls = "sidebar-nav-link" + (" active" if item["key"] == active_key else "")
            st.markdown(
                f'<a class="{cls}" href="{item["url"]}" target="_self">'
                f'{svg(item["icon"], size=18)}<span>{item["label"]}</span></a>',
                unsafe_allow_html=True,
            )

        if is_auth_enabled():
            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
            if st.button("ログアウト", use_container_width=True, key="sidebar_logout"):
                st.session_state["authenticated"] = False
                st.rerun()


def render_header(
    title: str,
    subtitle: str | None = None,
    kicker: str = "DASHBOARD",
    meta_label: str | None = None,
) -> None:
    """ページヘッダ。`kicker` で上部の小ラベル、`title` で大見出し。"""
    if meta_label is None:
        now = datetime.now().strftime("%Y/%m/%d %H:%M")
        meta_label = f"最終更新 <b>{now}</b>"

    sub_html = f'<div class="page-subtitle">{subtitle}</div>' if subtitle else ""

    st.markdown(
        f"""
        <div class="page-header">
            <div style="min-width:0;">
                <div class="page-kicker">{kicker}</div>
                <div class="page-title">{title}</div>
                {sub_html}
            </div>
            <div class="page-meta">{meta_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def kpi_card(
    label: str,
    value: str,
    sub: str | None = None,
    trend: float | None = None,
    trend_suffix: str = "前月比",
    highlight: bool = False,
) -> None:
    """KPIカード。レイアウトは label→value→(trend|sub) の3階層、高さ揃え。"""
    trend_html = ""
    if trend is not None:
        cls = "up" if trend > 0 else ("down" if trend < 0 else "flat")
        arrow = "↑" if trend > 0 else ("↓" if trend < 0 else "—")
        trend_html = (
            f'<div class="kpi-trend {cls}">{arrow} {abs(trend)*100:.1f}% '
            f'<span class="trend-suffix">{trend_suffix}</span></div>'
        )

    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    bottom = trend_html or sub_html
    extra_cls = " highlight" if highlight else ""

    st.markdown(
        f"""
        <div class="kpi-card{extra_cls}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div>{bottom}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str, sub: str | None = None, granularity: str | None = None) -> None:
    g_html = f'<span class="granularity">{granularity}</span>' if granularity else ""
    st.markdown(f'<div class="section-title">{text}{g_html}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def _delta_html(delta: float | None, suffix: str = "") -> str:
    if delta is None:
        return ""
    cls = "up" if delta > 0 else ("down" if delta < 0 else "flat")
    arrow = "↗" if delta > 0 else ("↘" if delta < 0 else "—")
    sfx = f'<span class="trend-suffix">{suffix}</span>' if suffix else ""
    return f'<span class="kpi-strip-delta {cls}">{arrow} {delta*100:+.1f}%{sfx}</span>'


def kpi_strip(items: list[dict]) -> None:
    """4枚のKPIを縦線区切りで1つのカードにまとめる。

    各item: {"label": str, "value": str, "delta": float|None,
             "delta_suffix": str, "sub": str|None, "featured": bool}
    """
    cells = []
    for i, item in enumerate(items):
        cls_parts = ["kpi-strip-cell"]
        if i == 0:
            cls_parts.append("first")
        if item.get("featured"):
            cls_parts.append("featured")
        cls = " ".join(cls_parts)
        delta_html = _delta_html(item.get("delta"), item.get("delta_suffix", ""))
        bottom = delta_html or (
            f'<div class="kpi-strip-sub">{item["sub"]}</div>' if item.get("sub") else ""
        )
        cells.append(
            f'<div class="{cls}">'
            f'<div class="kpi-strip-label">{item["label"]}</div>'
            f'<div class="kpi-strip-value">{item["value"]}</div>'
            f'{bottom}'
            f'</div>'
        )
    st.markdown(f'<div class="kpi-strip">{"".join(cells)}</div>', unsafe_allow_html=True)


import contextlib


@contextlib.contextmanager
def chart_card(
    kicker: str | None = None,
    title: str | None = None,
    sub: str | None = None,
    granularity: str | None = None,
):
    """枠付きカード（st.container(border=True) ベース）。

    granularity: 「月次」「日次」「店舗別」等の粒度バッジ。kickerの隣に表示。

    使い方:
        with chart_card(kicker="ラベル", title="¥1,234", sub="..."):
            st.plotly_chart(fig, ...)
    """
    container = st.container(border=True)
    with container:
        if kicker:
            g_html = f'<span class="granularity">{granularity}</span>' if granularity else ""
            st.markdown(f'<div class="chart-kicker"><span>{kicker}</span>{g_html}</div>', unsafe_allow_html=True)
        if title:
            st.markdown(f'<div class="chart-title">{title}</div>', unsafe_allow_html=True)
        if sub:
            st.markdown(f'<div class="chart-sub">{sub}</div>', unsafe_allow_html=True)
        yield container


def rank_list(items: list[dict]) -> None:
    """順位バッジ付きランキングリスト。

    各item: {"label": str, "value": str, "sub": str|None, "delta": float|None}
    """
    rows = []
    badges = ["gold", "silver", "bronze"]
    for i, item in enumerate(items):
        badge_cls = badges[i] if i < 3 else "plain"
        sub_html = f'<div class="rank-sub">{item["sub"]}</div>' if item.get("sub") else ""
        delta = item.get("delta")
        delta_html = ""
        if delta is not None:
            cls = "up" if delta > 0 else ("down" if delta < 0 else "")
            arrow = "↑" if delta > 0 else ("↓" if delta < 0 else "—")
            delta_html = f'<div class="rank-delta {cls}">{arrow} {abs(delta)*100:.1f}%</div>'
        rows.append(
            f'<div class="rank-row">'
            f'<div class="rank-badge {badge_cls}">{i+1}</div>'
            f'<div><div class="rank-label">{item["label"]}</div>{sub_html}</div>'
            f'<div><div class="rank-value">{item["value"]}</div>{delta_html}</div>'
            f'</div>'
        )
    st.markdown(f'<div class="rank-list">{"".join(rows)}</div>', unsafe_allow_html=True)


def record_pill(text: str) -> str:
    """ベスト記録バッジのHTML文字列を返す（kickerやtitleに埋め込み可）。"""
    return f'<span class="record-pill">{text}</span>'


def priority_table_full(items: list[dict], priority_groups: bool = True) -> None:
    """優先度バッジ付き・13列フル版（横幅コンパクト）。

    各item:
    {
        "priority": int|None, "name": str,
        "work_days": str, "contract_h": str, "work_h": str,
        "case_count": str, "main_rate": str, "main_nom": str,
        "sales": str, "reward": str, "gp": str,
        "nom": str, "nom_rate": str,
    }
    """
    if not items:
        empty_state("対象データがありません", icon="🎯")
        return

    rows = []
    last_prio = object()
    cols = 13  # 優先度バッジ + 12項目

    for item in items:
        prio = item.get("priority")
        prio_label = (["", "①", "②", "③"][prio] if prio in (1, 2, 3) else "-")
        prio_cls = f"p{prio}" if prio in (1, 2, 3) else "none"

        if priority_groups and prio != last_prio:
            count = sum(1 for x in items if x.get("priority") == prio)
            label_text = f"優先度 {prio_label}" if prio in (1, 2, 3) else "優先度 未設定"
            rows.append(
                f'<tr class="priority-group-row"><td colspan="{cols}">'
                f'<span class="priority-group-label">{label_text} '
                f'<span class="count">{count}名</span></span></td></tr>'
            )
            last_prio = prio

        rows.append(
            "<tr>"
            f'<td><span class="priority-badge {prio_cls}">{prio_label}</span></td>'
            f'<td class="cast-name-cell">{item.get("name","")}</td>'
            f'<td class="num">{item.get("work_days","-")}</td>'
            f'<td class="text-mini">{item.get("contract_h","-")}</td>'
            f'<td class="num">{item.get("work_h","-")}</td>'
            f'<td class="num">{item.get("case_count","-")}</td>'
            f'<td class="num">{item.get("main_rate","-")}</td>'
            f'<td class="num">{item.get("main_nom","-")}</td>'
            f'<td class="num">{item.get("sales","-")}</td>'
            f'<td class="num">{item.get("reward","-")}</td>'
            f'<td class="num">{item.get("gp","-")}</td>'
            f'<td class="num">{item.get("nom","-")}</td>'
            f'<td class="num">{item.get("nom_rate","-")}</td>'
            "</tr>"
        )

    html = (
        '<div class="priority-table-wrap"><table class="priority-table compact">'
        "<thead><tr>"
        '<th style="width:36px;">優先度</th>'
        "<th>店舗名</th>"
        '<th class="right">稼働日数</th>'
        "<th>契約時間</th>"
        '<th class="right">稼働時間</th>'
        '<th class="right">案件数</th>'
        '<th class="right">本指名率</th>'
        '<th class="right">本指名数</th>'
        '<th class="right">売上</th>'
        '<th class="right">報酬</th>'
        '<th class="right">粗利</th>'
        '<th class="right">指名数</th>'
        '<th class="right">指名率</th>'
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def priority_table(items: list[dict], priority_groups: bool = True) -> None:
    """優先度バッジ付きのキャスト一覧テーブル（優先度降順）。

    items の各dict:
    {
        "priority": int|None,  # 1,2,3
        "priority_label": str, # "①" 等の表示用ラベル
        "name": str,
        "haken_name": str|None,
        "area": str|None,
        "status": str|None,
        "sales": str,          # 整形済み
        "cases": str,
        "hours": str,
        "nom_rate": str,
    }
    """
    if not items:
        empty_state("優先度データが取得できませんでした", icon="🎯")
        return

    rows = []
    last_prio = object()
    for item in items:
        prio = item.get("priority")
        prio_label = item.get("priority_label") or (
            ["", "①", "②", "③"][prio] if prio in (1, 2, 3) else "-"
        )
        prio_cls = f"p{prio}" if prio in (1, 2, 3) else "none"

        if priority_groups and prio != last_prio:
            count = sum(1 for x in items if x.get("priority") == prio)
            label_text = f"優先度 {prio_label}" if prio in (1, 2, 3) else "優先度 未設定"
            rows.append(
                f'<tr class="priority-group-row"><td colspan="7">'
                f'<span class="priority-group-label">{label_text} '
                f'<span class="count">{count}名</span></span></td></tr>'
            )
            last_prio = prio

        meta_bits = []
        if item.get("haken_name"):
            meta_bits.append(item["haken_name"])
        if item.get("status"):
            meta_bits.append(item["status"])
        meta = " · ".join(meta_bits) if meta_bits else ""

        rows.append(
            f"<tr>"
            f'<td><span class="priority-badge {prio_cls}">{prio_label}</span></td>'
            f'<td><div class="priority-cast-name">{item.get("name","")}</div>'
            f'{f"<div class=\"priority-cast-meta\">{meta}</div>" if meta else ""}</td>'
            f'<td><span class="priority-cell-area">{item.get("area") or "-"}</span></td>'
            f'<td class="num">{item.get("sales","-")}</td>'
            f'<td class="num">{item.get("cases","-")}</td>'
            f'<td class="num">{item.get("hours","-")}</td>'
            f'<td class="num">{item.get("nom_rate","-")}</td>'
            f"</tr>"
        )

    html = (
        '<div class="priority-table-wrap"><table class="priority-table">'
        "<thead><tr>"
        '<th style="width:48px;">優先度</th>'
        "<th>キャスト</th>"
        "<th>固定エリア</th>"
        '<th class="right">当月売上</th>'
        '<th class="right">案件数</th>'
        '<th class="right">稼働時間</th>'
        '<th class="right">本指名率</th>'
        "</tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table></div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def empty_state(message: str = "データが入るとここに表示されます", cta: str | None = None, icon: str = "📊", height: int | None = None) -> None:
    """データ0件のとき表示する点線プレースホルダ。"""
    h_style = f"min-height:{height}px;" if height else ""
    cta_html = f'<div class="empty-cta">{cta}</div>' if cta else ""
    st.markdown(
        f"""
        <div class="empty-state" style="{h_style}">
            <div class="empty-icon">{icon}</div>
            <div class="empty-message">{message}</div>
            {cta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def chart_card_sub_with_delta(delta: float, suffix: str) -> str:
    """chart_card の sub 引数に渡すための整形済みHTMLを返す。"""
    cls = "delta-up" if delta > 0 else ("delta-down" if delta < 0 else "")
    arrow = "↗" if delta > 0 else ("↘" if delta < 0 else "—")
    return f'<span class="{cls}">{arrow} {delta*100:+.1f}%</span> <span>{suffix}</span>'
