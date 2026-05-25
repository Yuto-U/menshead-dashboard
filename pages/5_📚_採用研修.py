"""採用・研修画面。研修進捗ヒートマップ、完了率、在籍ステータス分布など。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.auth import require_password
from components.charts import bar_horizontal, donut_share
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
from utils.format import yen
from components.style import apply_global_style
from components.theme import BORDER, BRONZE, TEXT_PRIMARY, TEXT_SECONDARY, install_plotly_theme
from db.warehouse import get_conn, init_schema, table_summary
from utils.format import percent


st.set_page_config(page_title="採用・研修 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="recruit")

conn = get_conn()
init_schema(conn)

summary = table_summary(conn)
has_cast = summary.get("dim_cast", 0) > 0
has_training = summary.get("fact_training", 0) > 0


# ---------------- ヘッダ ----------------
render_header(
    "採用・研修",
    "キャスト在籍ステータスと採用ファネル / 研修進捗の見える化",
    kicker="採用研修",
)

# ---------------- 在籍ステータス（7カード） ----------------
status_order = ["稼働中", "研修中", "休業中", "研修前離脱", "研修中離脱", "研修後離脱", "デビュー後離脱"]
status_rows = {r[0]: r[1] for r in conn.execute("SELECT status, COUNT(*) FROM dim_cast GROUP BY status").fetchall()}

section_title("在籍ステータス", granularity="現時点・全キャスト", sub="ヘッドスパニスト一覧管理表より")
status_cols = st.columns(len(status_order))
for col, status in zip(status_cols, status_order):
    with col:
        n = status_rows.get(status, 0)
        kpi_card(status, f"{n} 名", sub="")

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
    with chart_card(kicker="採用→デビュー→退店", title=f"{int(df_recruit['採用数'].sum() or 0)} 名採用", sub="ヘッドスパニスト一覧管理表 KPIシートより", granularity="月次"):
        st.dataframe(
            df_recruit.style.format({
                "採用数": "{:.0f}", "研修前離脱数": "{:.0f}", "デビュー数": "{:.0f}",
                "在籍退店数": "{:.0f}", "稼働在籍数": "{:.0f}",
                "デビュー率": "{:.1%}", "研修前離脱率": "{:.1%}",
            }, na_rep="-"),
            use_container_width=True, hide_index=True,
        )

if not has_cast:
    st.info("キャストデータがまだ取り込まれていません。管理ページからExcelをアップロードしてください。")
    st.stop()


# ---------------- KPIストリップ ----------------
status_rows = conn.execute(
    "SELECT COALESCE(status, '未設定') AS status, COUNT(*) FROM dim_cast GROUP BY 1"
).fetchall()
status_map = {r[0]: r[1] for r in status_rows}
total_cast = sum(status_map.values())
in_training = status_map.get("研修中", 0)

# 研修完了率（「済」ステータスの全レコード比率）
training_total = summary.get("fact_training", 0) or 0
training_done = 0
not_started = 0
if has_training:
    training_done = conn.execute(
        "SELECT COUNT(*) FROM fact_training WHERE status='済'"
    ).fetchone()[0] or 0
    not_started = conn.execute(
        "SELECT COUNT(DISTINCT cast_id) FROM fact_training WHERE status='未着手'"
    ).fetchone()[0] or 0

done_rate = (training_done / training_total) if training_total else 0

kpi_strip([
    {"label": "在籍キャスト数", "value": f"{total_cast:,} 名", "featured": True},
    {"label": "研修中", "value": f"{in_training:,} 名", "sub": "ステータス=研修中"},
    {"label": "研修完了率", "value": percent(done_rate), "sub": "全レコード中『済』比率"},
    {"label": "未着手あり", "value": f"{not_started:,} 名", "sub": "1件以上『未着手』あり"},
])


# ---------------- 研修進捗ヒートマップ ----------------
section_title("研修進捗ヒートマップ", granularity="キャスト×研修種別")

if not has_training:
    empty_state(message="研修データが取り込まれていません", icon="📚")
else:
    df_t = conn.execute(
        """
        SELECT c.cast_name AS キャスト, t.training_type AS 研修, t.status AS ステータス
        FROM fact_training t
        JOIN dim_cast c USING (cast_id)
        ORDER BY c.cast_name, t.training_type
        """
    ).fetchdf()

    # ステータスを数値スコアに変換（濃淡で可視化）
    status_score = {
        "済": 1.0,
        "研修中": 0.6,
        "1回目": 0.4,
        "日程調整中": 0.3,
        "休業中": 0.2,
        "未着手": 0.0,
    }
    df_t["スコア"] = df_t["ステータス"].map(status_score).fillna(0.1)

    with chart_card(
        kicker="研修進捗",
        title=f"{df_t['キャスト'].nunique():,} 名 × {df_t['研修'].nunique():,} 種別",
        sub="濃い=完了、薄い=未着手。ホバーで詳細表示",
        granularity="全期間",
    ):
        pivot = df_t.pivot_table(
            index="キャスト", columns="研修", values="スコア", aggfunc="max"
        ).fillna(-0.1)
        # ホバー用のステータステキスト
        status_pivot = df_t.pivot_table(
            index="キャスト", columns="研修", values="ステータス", aggfunc="first"
        ).fillna("（未登録）")

        height = max(320, min(1200, 18 * len(pivot.index) + 80))
        fig = go.Figure(go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            text=status_pivot.values,
            hovertemplate="%{y} / %{x}<br>ステータス: %{text}<extra></extra>",
            colorscale=[
                [0.0, "#F7F8FA"],
                [0.3, "#EADFD0"],
                [0.6, "#C8A464"],
                [1.0, "#7A5A36"],
            ],
            zmin=-0.1, zmax=1.0,
            showscale=False,
        ))
        fig.update_layout(
            height=height,
            margin=dict(l=120, r=20, t=10, b=40),
            xaxis=dict(side="top"),
            yaxis=dict(autorange="reversed"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------- 研修種別別 完了率 & 在籍ステータス分布 ----------------
col_left, col_right = st.columns([5, 4])

with col_left:
    section_title("研修種別別 完了率", granularity="種別ごとの『済』比率")
    if not has_training:
        empty_state(message="研修データがありません", icon="📊")
    else:
        df_rate = conn.execute(
            """
            SELECT training_type AS 研修種別,
                   COUNT(*) AS 全数,
                   SUM(CASE WHEN status='済' THEN 1 ELSE 0 END) AS 済数,
                   ROUND(SUM(CASE WHEN status='済' THEN 1 ELSE 0 END)*100.0/COUNT(*), 1) AS 完了率
            FROM fact_training
            GROUP BY training_type
            ORDER BY 完了率 DESC
            """
        ).fetchdf()

        if df_rate.empty:
            empty_state(message="研修種別データがありません", icon="📊")
        else:
            with chart_card(
                kicker="完了率ランキング",
                title=f"全{int(df_rate['全数'].sum()):,} 件",
                sub="種別別の『済』達成率",
                granularity="全期間",
            ):
                fig = bar_horizontal(df_rate, x="完了率", y="研修種別", height=320)
                fig.update_traces(
                    marker_color=BRONZE,
                    texttemplate="%{x:.1f}%",
                    textposition="outside",
                )
                fig.update_layout(
                    xaxis=dict(title=None, range=[0, max(105, df_rate["完了率"].max() * 1.15)]),
                    showlegend=False,
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with col_right:
    section_title("在籍ステータス分布", granularity="dim_cast.status")
    df_status = pd.DataFrame(
        [(k, v) for k, v in status_map.items()], columns=["ステータス", "人数"]
    ).sort_values("人数", ascending=False)
    if df_status.empty:
        empty_state(message="ステータスデータがありません", icon="👥")
    else:
        with chart_card(
            kicker="在籍構成",
            title=f"{total_cast:,} 名",
            sub="ステータス別の人数構成",
            granularity="現在",
        ):
            fig = donut_share(
                df_status, names="ステータス", values="人数",
                center_label=f"在籍<br><b>{total_cast:,} 名</b>",
                height=320,
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------- 未着手キャスト一覧 ----------------
section_title("未着手キャスト一覧", granularity="1件以上『未着手』")

if not has_training:
    empty_state(message="研修データがありません", icon="📋")
else:
    df_not_started = conn.execute(
        """
        SELECT c.cast_name AS キャスト,
               c.status AS 在籍,
               c.hire_date AS 入店日,
               COUNT(*) AS 未着手件数,
               STRING_AGG(t.training_type, ', ') AS 未着手研修
        FROM fact_training t
        JOIN dim_cast c USING (cast_id)
        WHERE t.status = '未着手'
        GROUP BY c.cast_name, c.status, c.hire_date
        ORDER BY 未着手件数 DESC, c.hire_date DESC
        """
    ).fetchdf()

    if df_not_started.empty:
        empty_state(message="未着手の研修はありません", icon="✅")
    else:
        with chart_card(
            kicker="未着手リスト",
            title=f"{len(df_not_started):,} 名",
            sub="入店日が新しい順 / 未着手件数の多い順",
            granularity="全期間",
        ):
            st.dataframe(
                df_not_started,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "入店日": st.column_config.DateColumn("入店日", format="YYYY/MM/DD"),
                    "未着手件数": st.column_config.NumberColumn("未着手件数", format="%d 件"),
                },
            )
