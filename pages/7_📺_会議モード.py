"""会議モード。定例で投影できる1画面サマリー。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from components.auth import require_password
from components.charts import bar_vertical, donut_share, line_trend
from components.layout import (
    chart_card,
    chart_card_sub_with_delta,
    empty_state,
    favicon,
    kpi_card,
    rank_list,
    render_header,
    render_sidebar,
    section_title,
)
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import get_conn, init_schema, table_summary
from utils.format import yen
from utils.kpi import compute_store_sales, latest_complete_month, projection_for_current_month


st.set_page_config(page_title="会議モード - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="meeting")

conn = get_conn()
init_schema(conn)

if table_summary(conn).get("fact_daily_sales", 0) == 0:
    render_header("今月の経営報告", kicker="会議モード")
    st.info("データがまだ取り込まれていません。管理ページからExcelをアップロードしてください。")
    st.stop()


# ---------------- ヘッダ ----------------
target_month = latest_complete_month(conn)
year, month = target_month.split("-")
render_header(
    "今月の経営報告",
    f"対象月 {int(year)}年{int(month)}月 — 定例会議用 1画面サマリー",
    kicker="会議モード",
)


# ---------------- 今月着地予想（大きく1枠） ----------------
proj = projection_for_current_month(conn, target_month)
ss = compute_store_sales(conn, target_month)

if proj:
    main_col, sub_col = st.columns([3, 2])
    with main_col:
        with chart_card(
            kicker="今月着地予想",
            title=yen(proj["projected_sales"]),
            sub=chart_card_sub_with_delta(proj["vs_last_month"], "前月比"),
            granularity="当月",
        ):
            st.markdown(
                f"""
                <div style="display:flex; gap:24px; padding-top:8px;">
                    <div>
                        <div style="font-size:12px; color:#6B7280;">本日までの実績</div>
                        <div style="font-size:20px; font-weight:600; color:#1F2937;">{yen(proj['actual_sales'])}</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:#6B7280;">残{proj['remaining_days']}日の予測</div>
                        <div style="font-size:20px; font-weight:600; color:#1F2937;">{yen(proj['remaining_estimate'])}</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:#6B7280;">平均日商（直近{proj['avg_window_days']}日）</div>
                        <div style="font-size:20px; font-weight:600; color:#1F2937;">{yen(proj['avg_daily'])}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with sub_col:
        with chart_card(
            kicker="前月実績",
            title=yen(ss["total"]["previous"]),
            sub="3店舗合計（前月）",
            granularity="月次",
        ):
            st.markdown(
                f"""
                <div style="padding-top:8px;">
                    <div style="font-size:12px; color:#6B7280;">当月（本日まで）</div>
                    <div style="font-size:22px; font-weight:600; color:#1F2937;">{yen(ss['total']['current'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------- 店舗別 売上 3カード ----------------
section_title("店舗別 当月売上", granularity="月次")

c1, c2, c3 = st.columns(3)
store_names = {1: "新宿店", 2: "銀座店", 3: "上野店"}
for col, sid in zip([c1, c2, c3], [1, 2, 3]):
    with col:
        kpi_card(
            store_names[sid],
            yen(ss[sid]["current"]),
            trend=ss[sid]["delta"],
            trend_suffix="前月比",
            sub=f"前月 {yen(ss[sid]['previous'])}",
            highlight=(sid == 1),
        )


# ---------------- TOP5 キャスト ----------------
section_title("当月 TOP5 キャスト", granularity="月次・売上順")

df_top = conn.execute(
    """
    SELECT c.cast_name AS キャスト,
           f.sales AS 売上,
           f.case_count AS 案件数
    FROM fact_cast_monthly f
    JOIN dim_cast c USING (cast_id)
    WHERE f.year_month = ?
    ORDER BY f.sales DESC
    LIMIT 5
    """,
    [target_month],
).fetchdf()

if df_top.empty:
    empty_state(message="当月のキャスト売上データがありません", icon="🏆")
else:
    with chart_card(
        kicker="売上ランキング",
        title=yen(df_top["売上"].sum()),
        sub="TOP5合計",
        granularity="月次",
    ):
        items = []
        for _, row in df_top.iterrows():
            items.append({
                "label": row["キャスト"],
                "value": yen(row["売上"]),
                "sub": f"{int(row['案件数'] or 0):,} 件",
            })
        rank_list(items)


# ---------------- 月次推移 / コース別構成（横並び） ----------------
left, right = st.columns(2)

with left:
    section_title("月次推移", granularity="月次・全社")
    df_monthly = conn.execute(
        """
        SELECT strftime(date,'%Y-%m') AS 年月, SUM(sales) AS 売上
        FROM fact_daily_sales
        WHERE store_id IN (1,2,3)
        GROUP BY 1
        ORDER BY 1
        """
    ).fetchdf()
    if df_monthly.empty:
        empty_state(message="月次データがありません", icon="📈")
    else:
        with chart_card(
            kicker="売上推移",
            title=yen(df_monthly["売上"].sum()),
            sub="全店舗合計",
            granularity="月次",
        ):
            fig = line_trend(df_monthly, x="年月", y="売上", area=True, height=240)
            fig.update_layout(margin=dict(l=50, r=10, t=10, b=30))
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with right:
    section_title("当月コース別構成", granularity="月次・コース別")
    df_course = conn.execute(
        """
        SELECT c.duration_min || '分 ' || c.course_type AS コース,
               SUM(f.sales) AS 売上
        FROM fact_course_daily f
        JOIN dim_course c USING (course_id)
        WHERE strftime(f.date,'%Y-%m') = ?
        GROUP BY コース
        ORDER BY 売上 DESC
        """,
        [target_month],
    ).fetchdf()
    if df_course.empty:
        empty_state(message="当月コース別データがありません", icon="🌿")
    else:
        with chart_card(
            kicker="コース構成",
            title=yen(df_course["売上"].sum()),
            sub="当月のコース別売上",
            granularity="月次",
        ):
            fig = donut_share(
                df_course, names="コース", values="売上",
                center_label=f"合計<br><b>{yen(df_course['売上'].sum())}</b>",
                height=240,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
