"""採用・在籍画面。在籍ステータスと採用ファネルを表示（研修進捗は運用対象外）。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from components.auth import require_password
from components.charts import donut_share
from components.layout import (
    chart_card,
    empty_state,
    favicon,
    kpi_card,
    kpi_strip,
    render_header,
    render_sidebar,
    section_title,
)
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import get_conn, init_schema, table_summary

st.set_page_config(page_title="採用・在籍 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="recruit")

conn = get_conn()
init_schema(conn)

summary = table_summary(conn)
has_cast = summary.get("dim_cast", 0) > 0

render_header(
    "採用・在籍",
    "在籍ステータスと採用ファネルの推移",
    kicker="採用・在籍",
)

if not has_cast:
    empty_state("キャストデータがまだ取り込まれていません。管理ページからExcelをアップロードしてください。", icon="👥")
    st.stop()


# ---------------- 在籍ステータス（7カード横並び） ----------------
status_order = ["稼働中", "研修中", "休業中", "研修前離脱", "研修中離脱", "研修後離脱", "デビュー後離脱"]
status_rows = {r[0]: r[1] for r in conn.execute("SELECT status, COUNT(*) FROM dim_cast GROUP BY status").fetchall()}

section_title("在籍ステータス", granularity="現時点・全キャスト")
status_cols = st.columns(len(status_order))
for col, status in zip(status_cols, status_order):
    with col:
        n = status_rows.get(status, 0)
        kpi_card(status, f"{n} 名", sub="")


# ---------------- 在籍構成（ドーナツ） ----------------
section_title("在籍構成", granularity="ステータス別")
df_status = (
    pd.DataFrame([(k, v) for k, v in status_rows.items()], columns=["ステータス", "人数"])
    .sort_values("人数", ascending=False)
)
total_cast = int(df_status["人数"].sum())

col1, col2 = st.columns([3, 5])
with col1:
    with chart_card(kicker="在籍状況", title=f"{total_cast:,} 名", sub="全キャスト合計"):
        fig = donut_share(
            df_status, names="ステータス", values="人数",
            center_label=f"在籍<br><b>{total_cast:,} 名</b>",
            height=320,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col2:
    with chart_card(kicker="優先度別 (稼働中)", title="フリー客の割り振り順", sub="③最高 → ①最低"):
        df_pri = conn.execute(
            """
            SELECT
                COALESCE(CAST(priority AS VARCHAR), '未設定') AS 優先度,
                COUNT(*) AS 人数
            FROM dim_cast
            WHERE status='稼働中'
            GROUP BY 1
            ORDER BY 1 DESC NULLS LAST
            """
        ).fetchdf()
        if df_pri.empty:
            empty_state("優先度データなし", icon="🎯")
        else:
            st.dataframe(df_pri, use_container_width=True, hide_index=True)


# ---------------- 採用ファネル（月別） ----------------
df_recruit = conn.execute(
    """
    SELECT year_month AS 月,
           hired_count AS 採用数,
           joined_count AS 研修前離脱数,
           debut_count AS デビュー数,
           left_count AS 在籍退店数,
           active_count AS 稼働在籍数,
           debut_rate AS デビュー率,
           leave_rate AS 研修前離脱率
    FROM fact_recruiting_monthly
    ORDER BY year_month DESC
    """
).fetchdf()

section_title("採用ファネル", granularity="月別")
if df_recruit.empty:
    empty_state("採用ファネル（KPIシート）が取り込まれていません。ヘッドスパニスト一覧管理表をアップロードしてください。", icon="📋")
else:
    with chart_card(
        kicker="採用→デビュー→退店",
        title=f"{int(df_recruit['採用数'].sum() or 0)} 名採用",
        sub="ヘッドスパニスト一覧管理表 KPIシートより",
        granularity="月次",
    ):
        st.dataframe(
            df_recruit.style.format({
                "採用数": "{:.0f}", "研修前離脱数": "{:.0f}", "デビュー数": "{:.0f}",
                "在籍退店数": "{:.0f}", "稼働在籍数": "{:.0f}",
                "デビュー率": "{:.1%}", "研修前離脱率": "{:.1%}",
            }, na_rep="-"),
            use_container_width=True, hide_index=True,
        )
