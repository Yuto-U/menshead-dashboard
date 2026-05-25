"""メンズヘッドスパ 経営ダッシュボード - エントリポイント / ホーム画面。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st

from components.auth import require_password
from components.charts import (
    bar_horizontal,
    bar_vertical,
    donut_share,
    line_trend,
    projection_gauge,
)
from components.layout import (
    chart_card,
    chart_card_sub_with_delta,
    favicon,
    kpi_card,
    kpi_strip,
    rank_list,
    record_pill,
    render_header,
    render_sidebar,
    section_title,
)
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import get_conn, init_schema, table_summary
from utils.format import percent, yen
from utils.kpi import (
    compute_home_kpi,
    compute_store_sales,
    latest_complete_month,
    projection_for_current_month,
)


st.set_page_config(
    page_title="メンズヘッドスパ ダッシュボード",
    page_icon=favicon(),
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="home")

conn = get_conn()
init_schema(conn)
summary = table_summary(conn)
has_sales = summary.get("fact_daily_sales", 0) > 0

# ---------------- 空状態 ----------------
if not has_sales:
    render_header("ようこそ", "まずはExcelをアップロードしてください", kicker="ホーム")
    st.info("サイドバー → 管理 からExcelファイルをアップロードしてください。")
    section_title("データ取込状況")
    df_summary = pd.DataFrame([(k, v) for k, v in summary.items()], columns=["テーブル", "行数"])
    st.dataframe(df_summary, use_container_width=True, hide_index=True)
    st.stop()


# ---------------- ヘッダ ----------------
target_month = latest_complete_month(conn)
year, month = target_month.split("-")
render_header(
    "経営サマリー",
    f"対象月 {int(year)}年{int(month)}月（最新の取り込み済み月）",
    kicker="ホーム",
)

# ---------------- KPIストリップ：全社売上 + 3店舗売上（粒度: 月次・店舗別） ----------------
ss = compute_store_sales(conn, target_month)
kpi_strip([
    {
        "label": "当月総売上（全社）", "value": yen(ss["total"]["current"]),
        "delta": ss["total"]["delta"], "delta_suffix": "前月比", "featured": True,
    },
    {"label": "新宿店", "value": yen(ss[1]["current"]), "delta": ss[1]["delta"], "delta_suffix": "前月比"},
    {"label": "銀座店", "value": yen(ss[2]["current"]), "delta": ss[2]["delta"], "delta_suffix": "前月比"},
    {"label": "上野店", "value": yen(ss[3]["current"]), "delta": ss[3]["delta"], "delta_suffix": "前月比"},
])

# ---------------- サブKPI：案件数 / 客単価 / リピート率（粒度: 月次・全社平均） ----------------
section_title("補助KPI", granularity="月次・全社")
kpi = compute_home_kpi(conn, target_month)
c1, c2, c3 = st.columns(3)
with c1:
    kpi_card("案件数", f"{int(kpi['case_count']):,} 件",
             trend=kpi["delta_cases"], trend_suffix="前月比", sub="月次・全社累計")
with c2:
    kpi_card("客単価", yen(kpi["unit_price"]),
             trend=kpi["delta_unit"], trend_suffix="前月比", sub="月次・売上÷件数")
with c3:
    kpi_card("リピート率", percent(kpi["repeat_rate"]),
             trend=kpi["delta_repeat"], trend_suffix="前月比", sub="月次・全店平均")

# ---------------- 当月着地見込み（粒度: 当月日次推移） ----------------
proj = projection_for_current_month(conn, target_month)

if proj:
    section_title("当月着地見込み", granularity="当月の日次推移")
    df_daily = conn.execute(
        """
        SELECT date AS 日付, SUM(sales) AS 売上
        FROM fact_daily_sales
        WHERE strftime(date,'%Y-%m')=? AND store_id IN (1,2,3)
        GROUP BY date ORDER BY date
        """,
        [target_month],
    ).fetchdf()

    main, side = st.columns([3, 2])
    with main:
        with chart_card(
            kicker="月末着地予想",
            title=yen(proj["projected_sales"]),
            sub=chart_card_sub_with_delta(proj["vs_last_month"], "前月比"),
            granularity="日次",
        ):
            if not df_daily.empty:
                fig = bar_vertical(df_daily, x="日付", y="売上", text_auto=False, height=240)
                fig.update_traces(marker_color="#A88564", marker_line_width=0)
                fig.update_layout(margin=dict(l=50, r=10, t=10, b=30))
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    with side:
        prev_sales = ss["total"]["previous"]
        progress_pct = int(proj['actual_sales']/proj['projected_sales']*100) if proj['projected_sales'] else 0
        with chart_card(
            kicker="着地進捗ゲージ",
            title=f"進捗 {progress_pct}%",
            sub=f"実績 {yen(proj['actual_sales'])} / 残{proj['remaining_days']}日",
            granularity="当月",
        ):
            gauge = projection_gauge(proj["actual_sales"], proj["projected_sales"], prev_sales, height=200)
            st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})


# ---------------- 店舗別ランキング（粒度: 月次・店舗単位） ----------------
section_title("店舗別ランキング", granularity="月次・店舗別")

df_store = conn.execute(
    """
    SELECT s.store_name AS 店舗, SUM(f.sales) AS 売上, SUM(f.case_count) AS 案件数,
           CASE WHEN SUM(f.case_count)>0 THEN SUM(f.sales)/SUM(f.case_count) ELSE 0 END AS 客単価,
           AVG(f.repeat_rate) AS リピート率
    FROM fact_daily_sales f JOIN dim_store s USING (store_id)
    WHERE strftime(f.date, '%Y-%m')=? AND s.store_id IN (1,2,3)
    GROUP BY s.store_name ORDER BY 売上 DESC
    """,
    [target_month],
).fetchdf()

# 前月実績マップ
prev_ym = (
    f"{int(target_month[:4]):04d}-{int(target_month[5:7])-1:02d}"
    if int(target_month[5:7]) > 1
    else f"{int(target_month[:4])-1:04d}-12"
)
prev_map = {
    r[0]: r[1]
    for r in conn.execute(
        """
        SELECT s.store_name, SUM(f.sales)
        FROM fact_daily_sales f JOIN dim_store s USING (store_id)
        WHERE strftime(f.date,'%Y-%m')=? AND s.store_id IN (1,2,3)
        GROUP BY s.store_name
        """,
        [prev_ym],
    ).fetchall()
}

if not df_store.empty:
    col1, col2 = st.columns([5, 4])
    with col1:
        with chart_card(
            kicker="売上順位",
            title=yen(df_store["売上"].sum()),
            sub="3店舗合計",
            granularity="月次",
        ):
            items = []
            for _, row in df_store.iterrows():
                prev = prev_map.get(row["店舗"], 0) or 0
                delta = (row["売上"] - prev) / prev if prev else None
                cases = int(row["案件数"]) if pd.notna(row["案件数"]) else None
                up = row["客単価"] if pd.notna(row["客単価"]) else None
                sub_parts = []
                if cases:
                    sub_parts.append(f"{cases:,} 件")
                if up:
                    sub_parts.append(f"客単価 {yen(up)}")
                items.append({
                    "label": row["店舗"],
                    "value": yen(row["売上"]),
                    "sub": " / ".join(sub_parts) if sub_parts else "店舗売上",
                    "delta": delta,
                })
            rank_list(items)
    with col2:
        with chart_card(
            kicker="店舗別シェア",
            title="構成比",
            sub="店舗ごとの売上比率",
            granularity="月次",
        ):
            fig_donut = donut_share(
                df_store, names="店舗", values="売上",
                center_label=f"全店<br><b>{yen(df_store['売上'].sum())}</b>",
                height=240,
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})


# ---------------- 月次推移（粒度: 月次・全社） ----------------
section_title("月次推移", granularity="月次・全社")

df_monthly = conn.execute(
    """
    SELECT strftime(date,'%Y-%m') AS 年月, SUM(sales) AS 売上, SUM(case_count) AS 案件数
    FROM fact_daily_sales WHERE store_id IN (1,2,3) GROUP BY 1 ORDER BY 1
    """
).fetchdf()

if not df_monthly.empty:
    # 過去最高月をハイライト（継続利用工夫）
    best_idx = df_monthly["売上"].idxmax()
    best_month = df_monthly.loc[best_idx, "年月"]
    best_sales = df_monthly.loc[best_idx, "売上"]
    best_pill = record_pill(f"過去最高 {best_month} ¥{best_sales:,.0f}") if best_month != target_month else record_pill(f"今月が過去最高！ ¥{best_sales:,.0f}")

    col1, col2 = st.columns(2)
    with col1:
        with chart_card(
            kicker="売上推移",
            title=yen(df_monthly["売上"].sum()),
            sub=f"累計売上 {best_pill}",
            granularity="月次",
        ):
            fig_line = line_trend(df_monthly, x="年月", y="売上", area=True, height=240)
            fig_line.update_layout(margin=dict(l=50, r=10, t=10, b=30))
            st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    with col2:
        with chart_card(
            kicker="案件数推移",
            title=f"{int(df_monthly['案件数'].sum()):,} 件",
            sub="累計案件数",
            granularity="月次",
        ):
            fig_bar2 = bar_vertical(df_monthly, x="年月", y="案件数", text_auto=".0f", height=240)
            fig_bar2.update_traces(marker_color="#A88564")
            fig_bar2.update_layout(margin=dict(l=50, r=10, t=10, b=30))
            st.plotly_chart(fig_bar2, use_container_width=True, config={"displayModeBar": False})


# ---------------- コース別構成（粒度: 月次・コース別） ----------------
section_title("当月のコース別売上構成", granularity="月次・コース別")

df_course = conn.execute(
    """
    SELECT c.duration_min || '分 ' || c.course_type AS コース,
           f.new_or_repeat AS 区分, SUM(f.sales) AS 売上, SUM(f.case_count) AS 件数
    FROM fact_course_daily f JOIN dim_course c USING (course_id)
    WHERE strftime(f.date,'%Y-%m')=?
    GROUP BY コース, 区分 ORDER BY 売上 DESC
    """,
    [target_month],
).fetchdf()

if not df_course.empty:
    col1, col2 = st.columns(2)
    with col1:
        df_total = df_course.groupby("コース", as_index=False)["売上"].sum().sort_values("売上", ascending=False)
        with chart_card(
            kicker="コース別シェア",
            title=yen(df_total["売上"].sum()),
            sub="当月のコース別売上合計",
            granularity="月次",
        ):
            fig_pie = donut_share(
                df_total, names="コース", values="売上",
                center_label=f"合計<br><b>{yen(df_total['売上'].sum())}</b>",
                height=260,
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    with col2:
        with chart_card(
            kicker="新規 vs リピート",
            title="コース別 積み上げ",
            sub="区分別の売上構成",
            granularity="月次",
        ):
            fig_stack = bar_vertical(df_course, x="コース", y="売上", color="区分", barmode="stack", text_auto=False, height=260)
            fig_stack.update_layout(margin=dict(l=50, r=10, t=10, b=40))
            st.plotly_chart(fig_stack, use_container_width=True, config={"displayModeBar": False})
