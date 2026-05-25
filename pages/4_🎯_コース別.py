"""コース別画面。コース別の件数・売上、新規/リピート構成、月次推移。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components.auth import require_password
from components.charts import bar_horizontal, bar_vertical, donut_share, line_trend
from components.layout import (
    chart_card,
    empty_state,
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
from utils.format import yen, percent
from utils.kpi import latest_complete_month


st.set_page_config(page_title="コース別 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="course")

conn = get_conn()
init_schema(conn)

render_header("コース別", "コース別の件数・売上・新規/リピート構成", kicker="コース別")

if table_summary(conn).get("fact_course_daily", 0) == 0:
    empty_state("コース別データが取り込まれていません。管理ページからExcelをアップロードしてください。", icon="🎯")
    st.stop()

# フィルタ
months = [
    r[0]
    for r in conn.execute(
        "SELECT DISTINCT strftime(date, '%Y-%m') ym FROM fact_course_daily ORDER BY ym DESC"
    ).fetchall()
]
stores = conn.execute(
    "SELECT store_id, store_name FROM dim_store WHERE store_id IN (1,2,3) ORDER BY store_id"
).fetchall()

fcol1, fcol2, _ = st.columns([1, 1, 4])
with fcol1:
    selected_month = st.selectbox("対象月", months, index=0)
with fcol2:
    store_names = ["（全店）"] + [s[1] for s in stores]
    selected_store = st.selectbox("店舗", store_names, index=0)

store_filter = ""
store_params: list = []
if selected_store != "（全店）":
    sid = [s[0] for s in stores if s[1] == selected_store][0]
    store_filter = " AND store_id = ?"
    store_params = [sid]


# ---- KPIストリップ ----
prev_ym = (
    f"{int(selected_month[:4]):04d}-{int(selected_month[5:7])-1:02d}"
    if int(selected_month[5:7]) > 1
    else f"{int(selected_month[:4])-1:04d}-12"
)

cur = conn.execute(
    f"""
    SELECT SUM(sales), SUM(case_count),
           SUM(CASE WHEN new_or_repeat='new' THEN sales END),
           SUM(CASE WHEN new_or_repeat='repeat' THEN sales END)
    FROM fact_course_daily
    WHERE strftime(date,'%Y-%m')=?{store_filter}
    """,
    [selected_month] + store_params,
).fetchone()
prev = conn.execute(
    f"""
    SELECT SUM(sales), SUM(case_count),
           SUM(CASE WHEN new_or_repeat='new' THEN sales END),
           SUM(CASE WHEN new_or_repeat='repeat' THEN sales END)
    FROM fact_course_daily
    WHERE strftime(date,'%Y-%m')=?{store_filter}
    """,
    [prev_ym] + store_params,
).fetchone()


def _delta(c, p):
    if not p:
        return None
    return ((c or 0) - p) / p


kpi_strip([
    {"label": "コース合計売上", "value": yen(cur[0] or 0),
     "delta": _delta(cur[0], prev[0]), "delta_suffix": "前月比", "featured": True},
    {"label": "合計件数", "value": f"{int(cur[1] or 0):,} 件",
     "delta": _delta(cur[1], prev[1]), "delta_suffix": "前月比"},
    {"label": "新規売上", "value": yen(cur[2] or 0),
     "delta": _delta(cur[2], prev[2]), "delta_suffix": "前月比"},
    {"label": "リピート売上", "value": yen(cur[3] or 0),
     "delta": _delta(cur[3], prev[3]), "delta_suffix": "前月比"},
])


# ---- ランキング + ドーナツ ----
section_title("コース別ランキング", granularity="月次")

df_course = conn.execute(
    f"""
    SELECT c.duration_min || '分 ' || c.course_type AS コース,
           SUM(f.case_count) AS 件数, SUM(f.sales) AS 売上,
           SUM(CASE WHEN f.new_or_repeat='new' THEN f.sales ELSE 0 END) AS 新規売上,
           SUM(CASE WHEN f.new_or_repeat='repeat' THEN f.sales ELSE 0 END) AS リピート売上,
           SUM(CASE WHEN f.new_or_repeat='new' THEN f.case_count ELSE 0 END) AS 新規件数,
           SUM(CASE WHEN f.new_or_repeat='repeat' THEN f.case_count ELSE 0 END) AS リピート件数,
           CASE WHEN SUM(f.case_count)>0 THEN SUM(f.sales)/SUM(f.case_count) ELSE 0 END AS 客単価
    FROM fact_course_daily f JOIN dim_course c USING (course_id)
    WHERE strftime(f.date, '%Y-%m')=?{store_filter}
    GROUP BY コース ORDER BY 売上 DESC
    """,
    [selected_month] + store_params,
).fetchdf()

prev_map_course = {
    r[0]: r[1]
    for r in conn.execute(
        f"""
        SELECT c.duration_min || '分 ' || c.course_type, SUM(f.sales)
        FROM fact_course_daily f JOIN dim_course c USING (course_id)
        WHERE strftime(f.date, '%Y-%m')=?{store_filter} GROUP BY 1
        """,
        [prev_ym] + store_params,
    ).fetchall()
}

if df_course.empty:
    empty_state("対象月のコース別データがありません", icon="🎯")
else:
    col1, col2 = st.columns([5, 4])
    with col1:
        with chart_card(kicker="売上順位", title=yen(df_course["売上"].sum()), sub="コース別合計（新規 / リピート 内訳付き）", granularity="月次"):
            items = []
            for _, row in df_course.iterrows():
                prev = prev_map_course.get(row["コース"], 0) or 0
                delta = (row["売上"] - prev) / prev if prev else None
                items.append({
                    "label": row["コース"],
                    "value": yen(row["売上"]),
                    "sub": (
                        f"{int(row['件数']):,} 件 / 客単価 {yen(row['客単価'])}　"
                        f"｜　新規 {yen(row['新規売上'])}（{int(row['新規件数'])}件）　"
                        f"／　リピート {yen(row['リピート売上'])}（{int(row['リピート件数'])}件）"
                    ),
                    "delta": delta,
                })
            rank_list(items)
    with col2:
        with chart_card(kicker="コース別シェア", title="構成比", sub="売上比率", granularity="月次"):
            fig = donut_share(
                df_course, names="コース", values="売上",
                center_label=f"<b>{yen(df_course['売上'].sum())}</b>",
                height=240,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---- 新規 vs リピート 構成 ----
section_title("新規 vs リピート 構成", granularity="月次・コース別")

df_seg = conn.execute(
    f"""
    SELECT c.duration_min || '分 ' || c.course_type AS コース,
           f.new_or_repeat AS 区分,
           SUM(f.sales) AS 売上, SUM(f.case_count) AS 件数
    FROM fact_course_daily f JOIN dim_course c USING (course_id)
    WHERE strftime(f.date, '%Y-%m')=?{store_filter}
    GROUP BY コース, 区分 ORDER BY 売上 DESC
    """,
    [selected_month] + store_params,
).fetchdf()

if not df_seg.empty:
    col1, col2 = st.columns(2)
    with col1:
        with chart_card(kicker="売上構成", title="積み上げ売上", sub="区分×コース", granularity="月次"):
            fig = bar_vertical(df_seg, x="コース", y="売上", color="区分", barmode="stack", text_auto=False, height=300)
            fig.update_layout(margin=dict(l=50, r=10, t=10, b=40))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        with chart_card(kicker="件数構成", title="積み上げ件数", sub="区分×コース", granularity="月次"):
            fig2 = bar_vertical(df_seg, x="コース", y="件数", color="区分", barmode="stack", text_auto=False, height=300)
            fig2.update_layout(margin=dict(l=50, r=10, t=10, b=40))
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})


# ---- 月次推移 ----
section_title("月次推移（コース別）", granularity="月次")

df_trend = conn.execute(
    f"""
    SELECT strftime(f.date, '%Y-%m') AS 年月,
           c.duration_min || '分 ' || c.course_type AS コース,
           SUM(f.sales) AS 売上
    FROM fact_course_daily f JOIN dim_course c USING (course_id)
    WHERE 1=1{store_filter}
    GROUP BY 1, 2 ORDER BY 1, 2
    """,
    store_params,
).fetchdf()

if not df_trend.empty:
    with chart_card(kicker="売上推移", title=yen(df_trend["売上"].sum()), sub="コース別の月推移", granularity="月次"):
        fig = bar_vertical(df_trend, x="年月", y="売上", color="コース", barmode="stack", text_auto=False, height=320)
        fig.update_layout(margin=dict(l=50, r=10, t=10, b=40))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
