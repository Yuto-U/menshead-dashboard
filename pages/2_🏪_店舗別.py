"""店舗別の詳細画面。新宿/銀座/上野の比較＋月次推移＋当月着地見込み。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components.auth import require_password
from components.charts import (
    bar_horizontal,
    bar_vertical,
    donut_share,
    line_trend,
)
from components.layout import (
    chart_card,
    favicon,
    kpi_card,
    kpi_strip,
    rank_list,
    render_header,
    render_sidebar,
    section_title,
)
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import get_conn, init_schema, table_summary
from utils.format import percent, yen
from utils.kpi import (
    compute_store_sales,
    latest_complete_month,
    projection_for_current_month,
)


st.set_page_config(page_title="店舗別 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="store")

conn = get_conn()
init_schema(conn)

if table_summary(conn).get("fact_daily_sales", 0) == 0:
    render_header("店舗別", kicker="店舗別")
    st.info("データがまだ取り込まれていません。管理ページからExcelをアップロードしてください。")
    st.stop()

# ---------------- フィルタ + ヘッダ ----------------
target_month_default = latest_complete_month(conn)
months = [
    r[0]
    for r in conn.execute(
        "SELECT DISTINCT strftime(date,'%Y-%m') ym FROM fact_daily_sales ORDER BY ym DESC"
    ).fetchall()
]
stores = conn.execute(
    "SELECT store_id, store_name FROM dim_store WHERE store_id IN (1,2,3) ORDER BY store_id"
).fetchall()

render_header("店舗別", "新宿 / 銀座 / 上野 のパフォーマンス比較", kicker="店舗別")

fcol1, fcol2, _ = st.columns([1, 1, 4])
with fcol1:
    selected_month = st.selectbox("対象月", months, index=0)
with fcol2:
    store_names = ["（全店）"] + [s[1] for s in stores]
    selected_store = st.selectbox("店舗", store_names, index=0)

store_filter_sql = ""
store_params: list = []
if selected_store != "（全店）":
    store_id = [s[0] for s in stores if s[1] == selected_store][0]
    store_filter_sql = " AND store_id = ?"
    store_params = [store_id]


# ---------------- 上部KPIストリップ：全社+3店舗 ----------------
ss = compute_store_sales(conn, selected_month)
kpi_strip([
    {"label": "全社合計", "value": yen(ss["total"]["current"]),
     "delta": ss["total"]["delta"], "delta_suffix": "前月比", "featured": True},
    {"label": "新宿店", "value": yen(ss[1]["current"]), "delta": ss[1]["delta"], "delta_suffix": "前月比"},
    {"label": "銀座店", "value": yen(ss[2]["current"]), "delta": ss[2]["delta"], "delta_suffix": "前月比"},
    {"label": "上野店", "value": yen(ss[3]["current"]), "delta": ss[3]["delta"], "delta_suffix": "前月比"},
])


# ---------------- フィルタ後の実績KPI 4枚 ----------------
actual = conn.execute(
    f"""
    SELECT SUM(sales), SUM(case_count),
           CASE WHEN SUM(case_count)>0 THEN SUM(sales)/SUM(case_count) ELSE 0 END,
           AVG(repeat_rate)
    FROM fact_daily_sales
    WHERE strftime(date,'%Y-%m')=?{store_filter_sql} AND store_id IN (1,2,3)
    """,
    [selected_month] + store_params,
).fetchone()

section_title(f"{selected_month} 実績 — {selected_store}", granularity="月次")
c1, c2, c3, c4 = st.columns(4)
with c1: kpi_card("売上", yen(actual[0]), sub="期間内合計")
with c2: kpi_card("案件数", f"{int(actual[1] or 0):,} 件", sub="期間内合計")
with c3: kpi_card("客単価", yen(actual[2]), sub="売上÷件数")
with c4: kpi_card("リピート率", percent(actual[3]), sub="平均")


# ---------------- 着地見込み（当月＆全店のときだけ） ----------------
if selected_month == target_month_default and selected_store == "（全店）":
    proj = projection_for_current_month(conn, selected_month)
    if proj:
        section_title("当月着地見込み", granularity="日次")
        cc1, cc2, cc3 = st.columns(3)
        with cc1:
            kpi_card("月末着地予想", yen(proj["projected_sales"]),
                     trend=proj["vs_last_month"], trend_suffix="前月比", highlight=True)
        with cc2:
            kpi_card("実績（本日まで）", yen(proj["actual_sales"]))
        with cc3:
            kpi_card("残期間予測", yen(proj["remaining_estimate"]),
                     sub=f"平均日商 ¥{proj['avg_daily']:,.0f}")


# ---------------- 店舗別比較 ----------------
section_title("店舗別比較（当月）", granularity="月次・店舗別")

df_store = conn.execute(
    """
    SELECT s.store_name AS 店舗, SUM(f.sales) AS 売上, SUM(f.case_count) AS 案件数,
           CASE WHEN SUM(f.case_count)>0 THEN SUM(f.sales)/SUM(f.case_count) ELSE 0 END AS 客単価,
           AVG(f.repeat_rate) AS リピート率
    FROM fact_daily_sales f JOIN dim_store s USING (store_id)
    WHERE strftime(f.date, '%Y-%m')=? AND s.store_id IN (1,2,3)
    GROUP BY s.store_name ORDER BY 売上 DESC
    """,
    [selected_month],
).fetchdf()

prev_ym = (
    f"{int(selected_month[:4]):04d}-{int(selected_month[5:7])-1:02d}"
    if int(selected_month[5:7]) > 1
    else f"{int(selected_month[:4])-1:04d}-12"
)
prev_map = {
    r[0]: r[1]
    for r in conn.execute(
        "SELECT s.store_name, SUM(f.sales) FROM fact_daily_sales f JOIN dim_store s USING (store_id) "
        "WHERE strftime(f.date,'%Y-%m')=? AND s.store_id IN (1,2,3) GROUP BY s.store_name",
        [prev_ym],
    ).fetchall()
}

if not df_store.empty:
    col1, col2 = st.columns([5, 4])
    with col1:
        with chart_card(kicker="店舗別ランキング", title=yen(df_store["売上"].sum()), sub="3店舗合計", granularity="月次"):
            items = []
            for _, row in df_store.iterrows():
                prev = prev_map.get(row["店舗"], 0) or 0
                delta = (row["売上"] - prev) / prev if prev else None
                items.append({
                    "label": row["店舗"],
                    "value": yen(row["売上"]),
                    "sub": f"{int(row['案件数']):,} 件 / 客単価 {yen(row['客単価'])}",
                    "delta": delta,
                })
            rank_list(items)
    with col2:
        with chart_card(kicker="店舗別シェア", title="構成比", sub="売上比率", granularity="月次"):
            total = df_store["売上"].sum()
            fig_donut = donut_share(
                df_store, names="店舗", values="売上",
                center_label=f"全店<br><b>{yen(total)}</b>",
                height=240,
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})


# ---------------- 月次推移 ----------------
section_title("月次推移", granularity="月次")

df_monthly = conn.execute(
    f"""
    SELECT strftime(f.date,'%Y-%m') AS 年月, s.store_name AS 店舗,
           SUM(f.sales) AS 売上, SUM(f.case_count) AS 案件数
    FROM fact_daily_sales f JOIN dim_store s USING (store_id)
    WHERE s.store_id IN (1,2,3){store_filter_sql.replace('store_id', 'f.store_id')}
    GROUP BY 1, 2 ORDER BY 1, 2
    """,
    store_params,
).fetchdf()

if not df_monthly.empty:
    col1, col2 = st.columns(2)
    with col1:
        with chart_card(kicker="売上推移", title=yen(df_monthly["売上"].sum()), sub="累計", granularity="月次"):
            fig_line = line_trend(df_monthly, x="年月", y="売上", color="店舗", height=280)
            fig_line.update_layout(margin=dict(l=50, r=10, t=10, b=30))
            st.plotly_chart(fig_line, use_container_width=True, config={"displayModeBar": False})
    with col2:
        with chart_card(kicker="案件数推移", title=f"{int(df_monthly['案件数'].sum()):,} 件", sub="累計", granularity="月次"):
            fig_case = bar_vertical(df_monthly, x="年月", y="案件数", color="店舗", barmode="group", text_auto=False, height=280)
            fig_case.update_layout(margin=dict(l=50, r=10, t=10, b=30))
            st.plotly_chart(fig_case, use_container_width=True, config={"displayModeBar": False})


# ---------------- 当月コース別 ----------------
section_title("当月のコース別構成", granularity="月次・コース別")

df_course = conn.execute(
    f"""
    SELECT c.duration_min || '分 ' || c.course_type AS コース,
           f.new_or_repeat AS 区分,
           SUM(f.case_count) AS 件数, SUM(f.sales) AS 売上
    FROM fact_course_daily f JOIN dim_course c USING (course_id)
    WHERE strftime(f.date,'%Y-%m')=?{store_filter_sql}
    GROUP BY コース, 区分 ORDER BY 売上 DESC
    """,
    [selected_month] + store_params,
).fetchdf()

if not df_course.empty:
    col1, col2 = st.columns([4, 5])
    with col1:
        df_total = df_course.groupby("コース", as_index=False)["売上"].sum().sort_values("売上", ascending=False)
        with chart_card(kicker="コース別シェア", title=yen(df_total["売上"].sum()), sub="合計", granularity="月次"):
            fig_pie = donut_share(
                df_total, names="コース", values="売上",
                center_label=f"合計<br><b>{yen(df_total['売上'].sum())}</b>",
                height=300,
            )
            st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})
    with col2:
        with chart_card(kicker="新規 vs リピート", title="積み上げ", sub="区分別構成", granularity="月次"):
            fig_stack = bar_vertical(df_course, x="コース", y="売上", color="区分", barmode="stack", text_auto=False, height=300)
            fig_stack.update_layout(margin=dict(l=50, r=10, t=10, b=40))
            st.plotly_chart(fig_stack, use_container_width=True, config={"displayModeBar": False})
