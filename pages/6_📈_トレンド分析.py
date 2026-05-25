"""トレンド分析画面。月次推移・前月比/前年同月比・コース別・曜日別ヒートマップ。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.auth import require_password
from components.charts import bar_vertical, line_trend
from components.layout import (
    chart_card,
    chart_card_sub_with_delta,
    empty_state,
    favicon,
    kpi_strip,
    render_header,
    render_sidebar,
    section_title,
)
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import get_conn, init_schema, table_summary
from utils.format import yen
from utils.kpi import latest_complete_month


st.set_page_config(page_title="トレンド分析 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="trend")

conn = get_conn()
init_schema(conn)

if table_summary(conn).get("fact_daily_sales", 0) == 0:
    render_header("トレンド分析", kicker="トレンド分析")
    st.info("データがまだ取り込まれていません。管理ページからExcelをアップロードしてください。")
    st.stop()


# ---------------- ヘッダ ----------------
target_month = latest_complete_month(conn)
render_header(
    "トレンド分析",
    "月次推移・前月比/前年同月比・曜日別パターンの把握",
    kicker="トレンド分析",
)


# ---------------- 月次集計 ----------------
df_monthly_total = conn.execute(
    """
    SELECT strftime(date,'%Y-%m') AS 年月,
           SUM(sales) AS 売上,
           SUM(case_count) AS 案件数
    FROM fact_daily_sales
    WHERE store_id IN (1,2,3)
    GROUP BY 1
    ORDER BY 1
    """
).fetchdf()


# ---------------- KPIストリップ ----------------
latest_sales = 0
latest_delta = None
avg3 = 0
best_label = "-"

if not df_monthly_total.empty:
    last_row = df_monthly_total.iloc[-1]
    latest_sales = float(last_row["売上"] or 0)
    if len(df_monthly_total) >= 2:
        prev = float(df_monthly_total.iloc[-2]["売上"] or 0)
        latest_delta = (latest_sales - prev) / prev if prev else None
    avg3 = float(df_monthly_total.tail(3)["売上"].mean() or 0)
    best_idx = df_monthly_total["売上"].idxmax()
    best_row = df_monthly_total.loc[best_idx]
    best_label = f"{best_row['年月']} ({yen(best_row['売上'])})"

kpi_strip([
    {
        "label": f"直近月売上（{target_month}）", "value": yen(latest_sales),
        "delta": latest_delta, "delta_suffix": "前月比", "featured": True,
    },
    {
        "label": "直近月 前月比",
        "value": f"{latest_delta*100:+.1f}%" if latest_delta is not None else "-",
        "sub": "前月との売上差",
    },
    {"label": "直近3ヶ月平均", "value": yen(avg3), "sub": "売上のローリング平均"},
    {"label": "過去最高月", "value": best_label, "sub": "売上ピーク月"},
])


# ---------------- 全社売上の月次推移 ----------------
section_title("全社売上の月次推移", granularity="月次")

if df_monthly_total.empty:
    empty_state(message="月次データがありません", icon="📈")
else:
    with chart_card(
        kicker="売上トレンド",
        title=yen(df_monthly_total["売上"].sum()),
        sub="全店舗合計 / エリア表示",
        granularity="月次",
    ):
        fig = line_trend(df_monthly_total, x="年月", y="売上", area=True, height=300)
        fig.update_layout(margin=dict(l=50, r=20, t=10, b=40))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------- 店舗別売上の月次推移 ----------------
section_title("店舗別売上の月次推移", granularity="月次・店舗別")

df_monthly_store = conn.execute(
    """
    SELECT strftime(f.date,'%Y-%m') AS 年月,
           s.store_name AS 店舗,
           SUM(f.sales) AS 売上
    FROM fact_daily_sales f
    JOIN dim_store s USING (store_id)
    WHERE s.store_id IN (1,2,3)
    GROUP BY 1, 2
    ORDER BY 1, 2
    """
).fetchdf()

if df_monthly_store.empty:
    empty_state(message="店舗別データがありません", icon="🏪")
else:
    with chart_card(
        kicker="店舗別推移",
        title="3店舗の月次売上",
        sub="新宿・銀座・上野の並走比較",
        granularity="月次",
    ):
        fig = line_trend(df_monthly_store, x="年月", y="売上", color="店舗", height=320)
        fig.update_layout(margin=dict(l=50, r=20, t=10, b=40))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------- 前月比/前年同月比テーブル ----------------
section_title("前月比 / 前年同月比", granularity="月次")

if df_monthly_total.empty:
    empty_state(message="比較データがありません", icon="📊")
else:
    df_cmp = df_monthly_total.copy().sort_values("年月").reset_index(drop=True)
    df_cmp["前月売上"] = df_cmp["売上"].shift(1)
    df_cmp["前月比"] = (df_cmp["売上"] - df_cmp["前月売上"]) / df_cmp["前月売上"]

    # 前年同月比（12ヶ月前）
    df_cmp["前年売上"] = df_cmp["売上"].shift(12)
    df_cmp["前年同月比"] = (df_cmp["売上"] - df_cmp["前年売上"]) / df_cmp["前年売上"]

    df_show = df_cmp[["年月", "売上", "前月売上", "前月比", "前年売上", "前年同月比"]].sort_values(
        "年月", ascending=False
    )

    with chart_card(
        kicker="比較サマリー",
        title="前月比・前年同月比",
        sub="新しい順に表示",
        granularity="月次",
    ):
        st.dataframe(
            df_show,
            use_container_width=True,
            hide_index=True,
            column_config={
                "売上": st.column_config.NumberColumn("売上", format="¥%d"),
                "前月売上": st.column_config.NumberColumn("前月売上", format="¥%d"),
                "前月比": st.column_config.NumberColumn("前月比", format="%.1f%%"),
                "前年売上": st.column_config.NumberColumn("前年売上", format="¥%d"),
                "前年同月比": st.column_config.NumberColumn("前年同月比", format="%.1f%%"),
            },
        )


# ---------------- コース別トレンド：月×コース 積み上げ ----------------
section_title("コース別トレンド", granularity="月次・コース別")

df_course = conn.execute(
    """
    SELECT strftime(f.date,'%Y-%m') AS 年月,
           c.duration_min || '分 ' || c.course_type AS コース,
           SUM(f.sales) AS 売上
    FROM fact_course_daily f
    JOIN dim_course c USING (course_id)
    GROUP BY 1, 2
    ORDER BY 1, 2
    """
).fetchdf()

if df_course.empty:
    empty_state(message="コース別データがありません", icon="🌿")
else:
    with chart_card(
        kicker="コース別 積み上げ",
        title=yen(df_course["売上"].sum()),
        sub="月ごとのコース構成変化",
        granularity="月次",
    ):
        fig = bar_vertical(
            df_course, x="年月", y="売上", color="コース",
            barmode="stack", text_auto=False, height=340,
        )
        fig.update_layout(margin=dict(l=50, r=20, t=10, b=40))
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ---------------- 曜日別売上ヒートマップ ----------------
section_title("曜日別売上ヒートマップ", granularity="日次・曜日×店舗")

df_dow = conn.execute(
    """
    SELECT s.store_name AS 店舗,
           dayofweek(f.date) AS dow_num,
           AVG(f.sales) AS 平均売上
    FROM fact_daily_sales f
    JOIN dim_store s USING (store_id)
    WHERE s.store_id IN (1,2,3)
    GROUP BY 1, 2
    ORDER BY 1, 2
    """
).fetchdf()

if df_dow.empty:
    empty_state(message="曜日別データがありません", icon="📅")
else:
    # DuckDB の dayofweek は 0=日, 1=月 ... 6=土
    dow_labels = ["日", "月", "火", "水", "木", "金", "土"]
    df_dow["曜日"] = df_dow["dow_num"].astype(int).map(lambda i: dow_labels[i])

    pivot = df_dow.pivot_table(index="店舗", columns="曜日", values="平均売上", aggfunc="mean")
    # 月→日の順に並べる（営業視点）
    order = ["月", "火", "水", "木", "金", "土", "日"]
    pivot = pivot.reindex(columns=[c for c in order if c in pivot.columns])

    with chart_card(
        kicker="曜日パターン",
        title="店舗×曜日 平均日商",
        sub="濃い=平均日商が高い曜日",
        granularity="日次平均",
    ):
        fig = go.Figure(go.Heatmap(
            z=pivot.values,
            x=pivot.columns, y=pivot.index,
            colorscale=[[0, "#F7F8FA"], [0.5, "#C8A464"], [1, "#7A5A36"]],
            colorbar=dict(title="¥"),
            hovertemplate="%{y} / %{x}曜日<br>平均 ¥%{z:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            height=280,
            margin=dict(l=80, r=20, t=10, b=40),
            xaxis=dict(side="top"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
