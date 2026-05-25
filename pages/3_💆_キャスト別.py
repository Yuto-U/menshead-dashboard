"""キャスト別画面。個別キャストのパフォーマンス + 全キャストランキング。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from components.auth import require_password
from components.charts import bar_horizontal, bar_vertical, donut_share, line_trend
from components.layout import (
    chart_card,
    empty_state,
    favicon,
    kpi_card,
    kpi_strip,
    priority_table,
    priority_table_full,
    rank_list,
    render_header,
    render_sidebar,
    section_title,
)
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import get_conn, init_schema, table_summary
from utils.format import percent, yen
from utils.kpi import latest_complete_month


st.set_page_config(page_title="キャスト別 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="cast")

conn = get_conn()
init_schema(conn)

render_header("キャスト別", "個別キャストのパフォーマンスと全体ランキング（稼働中キャストのみ）", kicker="キャスト別")

if table_summary(conn).get("fact_cast_monthly", 0) == 0:
    empty_state("キャスト評価データが取り込まれていません。管理ページから aoスパニスト評価シート.xlsx をアップロードしてください。", icon="💆")
    st.stop()

# 稼働中フィルタ（退店・離脱・研修中等を除外）
ACTIVE_FILTER = "c.status = '稼働中'"

# ---- 利用可能な対象月の取得 ----
months = [
    r[0]
    for r in conn.execute(
        "SELECT DISTINCT year_month FROM fact_cast_monthly ORDER BY year_month DESC"
    ).fetchall()
]
fcol1, fcol2 = st.columns([1, 5])
with fcol1:
    selected_month = st.selectbox("対象月", months, index=0)

target_month = selected_month

# ============= 全体サマリー =============
total = conn.execute(
    """
    SELECT COUNT(DISTINCT cast_id) AS active_n,
           SUM(sales) AS sales,
           SUM(case_count) AS cases,
           AVG(work_hours) AS avg_work_h
    FROM fact_cast_monthly
    WHERE year_month = ?
    """,
    [target_month],
).fetchone()

prev_ym = (
    f"{int(target_month[:4]):04d}-{int(target_month[5:7])-1:02d}"
    if int(target_month[5:7]) > 1
    else f"{int(target_month[:4])-1:04d}-12"
)
prev_total = conn.execute(
    "SELECT COUNT(DISTINCT cast_id), SUM(sales), SUM(case_count), AVG(work_hours) "
    "FROM fact_cast_monthly WHERE year_month = ?",
    [prev_ym],
).fetchone()


def _delta(c, p):
    if p in (None, 0):
        return None
    return ((c or 0) - p) / p


kpi_strip([
    {"label": "稼働キャスト数", "value": f"{int(total[0] or 0):,} 名",
     "delta": _delta(total[0], prev_total[0]), "delta_suffix": "前月比", "featured": True},
    {"label": "合計売上", "value": yen(total[1] or 0),
     "delta": _delta(total[1], prev_total[1]), "delta_suffix": "前月比"},
    {"label": "合計案件数", "value": f"{int(total[2] or 0):,} 件",
     "delta": _delta(total[2], prev_total[2]), "delta_suffix": "前月比"},
    {"label": "平均稼働時間", "value": f"{(total[3] or 0):.1f} h",
     "delta": _delta(total[3], prev_total[3]), "delta_suffix": "前月比"},
])


# ============= TOP10ランキング + ステータス分布 =============
section_title("TOP10 キャスト", granularity="月次・売上順")

df_top = conn.execute(
    """
    SELECT c.cast_id, c.cast_name AS キャスト, c.fixed_area AS エリア,
           f.sales AS 売上, f.case_count AS 案件数, f.work_hours AS 稼働時間,
           f.store_main_nomination_rate AS 本指名率
    FROM fact_cast_monthly f JOIN dim_cast c USING (cast_id)
    WHERE f.year_month = ? AND f.sales > 0 AND c.status = '稼働中'
    ORDER BY f.sales DESC
    LIMIT 10
    """,
    [target_month],
).fetchdf()

prev_sales_map = {
    r[0]: r[1]
    for r in conn.execute(
        "SELECT cast_id, sales FROM fact_cast_monthly WHERE year_month = ?",
        [prev_ym],
    ).fetchall()
}

col1, col2 = st.columns([5, 4])
with col1:
    with chart_card(kicker="売上TOP10", title=yen(df_top["売上"].sum() if not df_top.empty else 0), sub="個別貢献", granularity="月次"):
        if df_top.empty:
            empty_state("売上データがありません", icon="💆")
        else:
            items = []
            for _, row in df_top.iterrows():
                prev = prev_sales_map.get(row["cast_id"], 0) or 0
                delta = (row["売上"] - prev) / prev if prev else None
                items.append({
                    "label": row["キャスト"],
                    "value": yen(row["売上"]),
                    "sub": f"{int(row['案件数'] or 0):,} 件 / 本指名 {percent(row['本指名率'])}",
                    "delta": delta,
                })
            rank_list(items)

with col2:
    with chart_card(kicker="在籍状況", title="ステータス分布", sub="dim_cast 全体", granularity="現時点"):
        df_status = conn.execute(
            "SELECT COALESCE(status, '未分類') AS ステータス, COUNT(*) AS 人数 FROM dim_cast GROUP BY 1 ORDER BY 2 DESC"
        ).fetchdf()
        if df_status.empty:
            empty_state("ステータス情報が不足しています", icon="📋")
        else:
            fig = donut_share(df_status, names="ステータス", values="人数",
                              center_label=f"<b>{int(df_status['人数'].sum()):,}名</b>",
                              height=240)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ============= 個別キャスト詳細 =============
section_title("個別キャスト詳細", granularity="月次推移")

all_casts = [
    r[1] for r in conn.execute(
        "SELECT cast_id, cast_name FROM dim_cast WHERE status = '稼働中' "
        "AND cast_id IN (SELECT DISTINCT cast_id FROM fact_cast_monthly) "
        "ORDER BY cast_name"
    ).fetchall()
]

if all_casts:
    sel_cast = st.selectbox("キャスト", all_casts, index=0)
    cast_row = conn.execute(
        "SELECT cast_id, haken_name, fixed_area, status FROM dim_cast WHERE cast_name = ?",
        [sel_cast],
    ).fetchone()
    cast_id, haken_name, area, status = cast_row

    # 当月実績
    cur = conn.execute(
        "SELECT sales, case_count, work_hours, store_main_nomination_rate, reward, gross_profit "
        "FROM fact_cast_monthly WHERE cast_id = ? AND year_month = ?",
        [cast_id, target_month],
    ).fetchone()
    prev = conn.execute(
        "SELECT sales, case_count, work_hours, store_main_nomination_rate "
        "FROM fact_cast_monthly WHERE cast_id = ? AND year_month = ?",
        [cast_id, prev_ym],
    ).fetchone()

    info = f"派遣名: {haken_name or '-'}　/　エリア: {area or '-'}　/　ステータス: {status or '-'}"
    st.caption(info)

    if cur is None:
        empty_state(f"{sel_cast} の当月データはありません", icon="💆")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1: kpi_card("売上", yen(cur[0]), trend=_delta(cur[0], prev[0] if prev else None), trend_suffix="前月比", sub="当月")
        with c2: kpi_card("案件数", f"{int(cur[1] or 0):,} 件", trend=_delta(cur[1], prev[1] if prev else None), trend_suffix="前月比")
        with c3: kpi_card("稼働時間", f"{(cur[2] or 0):.1f} h", trend=_delta(cur[2], prev[2] if prev else None), trend_suffix="前月比")
        with c4: kpi_card("本指名率", percent(cur[3]), trend=_delta(cur[3], prev[3] if prev else None), trend_suffix="前月比")

        c5, c6 = st.columns(2)
        with c5: kpi_card("報酬", yen(cur[4]), sub="当月")
        with c6: kpi_card("粗利貢献", yen(cur[5]), sub="店舗+派遣")

    # 月次推移
    df_trend = conn.execute(
        """
        SELECT year_month AS 年月, sales AS 売上, case_count AS 案件数, work_hours AS 稼働時間
        FROM fact_cast_monthly WHERE cast_id = ? ORDER BY year_month
        """,
        [cast_id],
    ).fetchdf()

    if not df_trend.empty:
        col1, col2 = st.columns(2)
        with col1:
            with chart_card(kicker="売上推移", title=yen(df_trend["売上"].sum()), sub="個人累計", granularity="月次"):
                fig = line_trend(df_trend, x="年月", y="売上", area=True, height=260)
                fig.update_layout(margin=dict(l=50, r=10, t=10, b=30))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        with col2:
            with chart_card(kicker="案件数推移", title=f"{int(df_trend['案件数'].sum()):,} 件", sub="個人累計", granularity="月次"):
                fig2 = bar_vertical(df_trend, x="年月", y="案件数", text_auto=".0f", height=260)
                fig2.update_traces(marker_color="#A88564")
                fig2.update_layout(margin=dict(l=50, r=10, t=10, b=30))
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ============= 優先度順 全キャスト一覧 =============
section_title("優先度順 キャスト一覧", granularity="月次・優先度降順", sub="フリー客の割り振り順（③最高→①最低）")

df_pri = conn.execute(
    """
    SELECT c.cast_id, c.cast_name AS name, c.priority,
           c.min_hours AS contract_h,
           COALESCE(f.case_count_store, 0) AS case_count_store,
           f.store_main_nomination_rate AS store_main_rate,
           COALESCE(f.main_nomination_store, 0) AS store_main_nom,
           COALESCE(f.sales_store, 0) AS store_sales,
           COALESCE(f.reward_store, 0) AS store_reward,
           COALESCE(f.gross_profit_store, 0) AS store_gp,
           COALESCE(f.nomination_store, 0) AS store_nom,
           f.store_nomination_rate AS store_nom_rate,
           COALESCE(f.main_nomination_total, 0) AS total_main_nom,
           att.work_days AS work_days,
           att.work_h AS work_h
    FROM dim_cast c
    LEFT JOIN fact_cast_monthly f ON f.cast_id = c.cast_id AND f.year_month = ?
    LEFT JOIN (
        SELECT cast_id,
               COUNT(DISTINCT date) AS work_days,
               SUM(work_hours) AS work_h
        FROM fact_attendance
        WHERE strftime(date, '%Y-%m') = ?
          AND COALESCE(work_hours, 0) > 0
        GROUP BY cast_id
    ) att ON att.cast_id = c.cast_id
    WHERE c.priority IS NOT NULL AND c.status = '稼働中'
    ORDER BY c.priority DESC NULLS LAST, COALESCE(f.sales_store, 0) DESC
    """,
    [target_month, target_month],
).fetchdf()

if df_pri.empty:
    empty_state("優先度が設定されたキャストがいません。ヘッドスパニスト一覧管理表をアップロードしてください。", icon="🎯")
else:
    items = []
    for _, r in df_pri.iterrows():
        prio = int(r["priority"]) if r["priority"] is not None and not pd.isna(r["priority"]) else None
        items.append({
            "priority": prio,
            "name": r["name"],
            "work_days": f"{int(r['work_days'])}" if pd.notna(r["work_days"]) else "-",
            "contract_h": r["contract_h"] if pd.notna(r["contract_h"]) else "-",
            "work_h": f"{r['work_h']:.1f}" if pd.notna(r["work_h"]) else "-",
            "case_count": f"{int(r['case_count_store']):,}" if r["case_count_store"] else "-",
            "main_rate": percent(r["store_main_rate"]) if pd.notna(r["store_main_rate"]) else "-",
            "main_nom": f"{int(r['store_main_nom'])}" if r["store_main_nom"] else "-",
            "sales": yen(r["store_sales"]) if r["store_sales"] else "-",
            "reward": yen(r["store_reward"]) if r["store_reward"] else "-",
            "gp": yen(r["store_gp"]) if r["store_gp"] else "-",
            "nom": f"{int(r['store_nom'])}" if r["store_nom"] else "-",
            "nom_rate": percent(r["store_nom_rate"]) if pd.notna(r["store_nom_rate"]) else "-",
        })
    with chart_card(kicker="優先度順", title=f"{len(items)} 名", sub="ヘッドスパニスト一覧管理表 C列より（稼働中のみ）", granularity="月次"):
        priority_table_full(items, priority_groups=True)


# ============= 優先度未設定のキャスト一覧（参考） =============
df_none = conn.execute(
    """
    SELECT c.cast_name AS name, c.haken_name, c.fixed_area AS area, c.status,
           COALESCE(f.sales, 0) AS sales,
           COALESCE(f.case_count, 0) AS cases,
           f.work_hours AS hours,
           f.store_main_nomination_rate AS nom_rate
    FROM dim_cast c
    LEFT JOIN fact_cast_monthly f ON f.cast_id = c.cast_id AND f.year_month = ?
    WHERE c.priority IS NULL AND c.status = '稼働中'
    ORDER BY COALESCE(f.sales, 0) DESC
    """,
    [target_month],
).fetchdf()

if not df_none.empty:
    with st.expander(f"優先度未設定のキャスト（{len(df_none)}名・参考）", expanded=False):
        items = []
        for _, r in df_none.iterrows():
            items.append({
                "priority": None,
                "name": r["name"],
                "haken_name": r["haken_name"] if pd.notna(r["haken_name"]) else None,
                "area": r["area"] if pd.notna(r["area"]) else None,
                "status": r["status"] if pd.notna(r["status"]) else None,
                "sales": yen(r["sales"]) if r["sales"] else "-",
                "cases": f"{int(r['cases']):,}" if r["cases"] else "-",
                "hours": f"{r['hours']:.1f}h" if pd.notna(r["hours"]) else "-",
                "nom_rate": percent(r["nom_rate"]) if pd.notna(r["nom_rate"]) else "-",
            })
        priority_table(items, priority_groups=False)


# ============= 評価シート全項目（2605シート相当） =============
section_title("評価シート全項目", granularity="月次・全列", sub="aoスパニスト評価シート 2605シートの全項目を表示")

df_full = conn.execute(
    """
    SELECT
        c.priority AS 優先度,
        c.haken_name AS 派遣名,
        c.cast_name AS 源氏名,
        f.work_days AS 稼働日数,
        f.contract_hours AS 契約時間,
        f.work_hours AS 稼働時間,
        f.priority_raw AS 優先度詳細,
        f.case_count_store AS 店舗案件数,
        f.store_main_nomination_rate AS 店舗本指名率,
        f.main_nomination_store AS 店舗本指名,
        f.sales_store AS 店舗売上,
        f.reward_store AS 店舗報酬,
        f.gross_profit_store AS 店舗粗利,
        f.nomination_store AS 店舗指名,
        f.store_nomination_rate AS 店舗指名率,
        f.main_nomination_total AS 合計本指名数,
        f.total_sales AS total売上,
        f.total_reward AS total報酬,
        f.total_gross_profit AS total粗利,
        f.total_case_count AS total案件数,
        f.guarantee_amount AS 保証額,
        f.survey_text AS アンケート,
        f.survey_score AS 評価点,
        f.staff_name AS 担当スタッフ,
        f.note AS 備考
    FROM dim_cast c
    LEFT JOIN fact_cast_monthly f ON f.cast_id = c.cast_id AND f.year_month = ?
    WHERE f.year_month = ? AND c.status = '稼働中'
    ORDER BY c.priority DESC NULLS LAST, f.total_sales DESC NULLS LAST
    """,
    [target_month, target_month],
).fetchdf()

if df_full.empty:
    empty_state("対象月の評価データがありません", icon="💆")
else:
    with chart_card(
        kicker="全項目テーブル",
        title=f"{len(df_full)} 名",
        sub=f"対象月 {target_month}・優先度降順 → 売上降順",
        granularity="月次",
    ):
        st.dataframe(
            df_full.style.format({
                "優先度": "{:.0f}",
                "稼働日数": "{:.0f}",
                "稼働時間": "{:.1f}",
                "店舗案件数": "{:.0f}",
                "店舗本指名率": "{:.1%}",
                "店舗本指名": "{:.0f}",
                "店舗売上": "¥{:,.0f}",
                "店舗報酬": "¥{:,.0f}",
                "店舗粗利": "¥{:,.0f}",
                "店舗指名": "{:.0f}",
                "店舗指名率": "{:.1%}",
                "合計本指名数": "{:.0f}",
                "total売上": "¥{:,.0f}",
                "total報酬": "¥{:,.0f}",
                "total粗利": "¥{:,.0f}",
                "total案件数": "{:.0f}",
                "保証額": "¥{:,.0f}",
                "評価点": "{:.0f}",
            }, na_rep="-"),
            use_container_width=True,
            hide_index=True,
            height=500,
        )
