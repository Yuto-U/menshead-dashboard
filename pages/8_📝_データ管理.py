"""データ管理画面：Excel取込済データを直接編集（CRUD）。

ヘッドスパニスト一覧管理表「ヘッド」シート相当のキャストマスタ、
評価シートのキャスト×月データ、ヘッド店舗KPI、顧客リピートを
st.data_editor で編集→保存できる。
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from components.auth import require_password
from components.layout import (
    chart_card,
    empty_state,
    favicon,
    render_header,
    render_sidebar,
    section_title,
)
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import get_conn, init_schema

st.set_page_config(page_title="データ管理 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="data")

conn = get_conn()
init_schema(conn)

render_header(
    "データ管理",
    "Excelから取り込んだデータを直接編集・追加・削除",
    kicker="データ管理",
)

st.info(
    "💡 各タブで編集して「保存」を押すと DuckDB に反映されます。"
    "Excel原本は更新されません（次回Excelアップロード時に上書きされる可能性があります）。"
)

tab_cast, tab_eval, tab_customer, tab_kpi = st.tabs([
    "👥 キャストマスタ",
    "📊 キャスト×月 評価",
    "🧾 顧客リピート",
    "🏪 店舗月次KPI",
])


# ===================================================================
# Tab 1: キャストマスタ（dim_cast）
# ===================================================================
with tab_cast:
    section_title("キャストマスタ", granularity="ヘッドスパニスト一覧管理表「ヘッド」相当", sub="編集後「保存」ボタンで反映")

    df_cast = conn.execute(
        """
        SELECT cast_id, cast_name AS 源氏名, haken_name AS 派遣名,
               priority AS 優先度, priority_raw AS 優先度詳細,
               fixed_area AS 固定エリア, status AS 在籍ステータス,
               min_hours AS 契約最低時間, agency AS 派遣会社, hire_date AS 採用日
        FROM dim_cast
        ORDER BY cast_id
        """
    ).fetchdf()

    if df_cast.empty:
        empty_state("キャストマスタが未登録です。管理ページからExcelをアップロード、または下の行追加で新規登録してください。", icon="👥")

    edited = st.data_editor(
        df_cast,
        use_container_width=True,
        num_rows="dynamic",
        hide_index=True,
        column_config={
            "cast_id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "源氏名": st.column_config.TextColumn("源氏名", required=True),
            "派遣名": st.column_config.TextColumn("派遣名"),
            "優先度": st.column_config.SelectboxColumn("優先度", options=[None, 1, 2, 3]),
            "優先度詳細": st.column_config.TextColumn("優先度詳細(O③等)", width="small"),
            "固定エリア": st.column_config.TextColumn("固定エリア"),
            "在籍ステータス": st.column_config.SelectboxColumn(
                "在籍ステータス",
                options=["稼働中", "研修中", "休業中", "退店", "離脱", "研修前離脱", "研修中離脱", "研修後離脱", "デビュー後離脱"],
            ),
            "契約最低時間": st.column_config.TextColumn("契約最低時間", width="small"),
            "派遣会社": st.column_config.TextColumn("派遣会社"),
            "採用日": st.column_config.DateColumn("採用日", format="YYYY/MM/DD"),
        },
        key="cast_editor",
    )

    if st.button("💾 キャストマスタを保存", type="primary", key="save_cast"):
        try:
            existing_ids = set(df_cast["cast_id"].dropna().astype(int).tolist())
            edited_ids = set(edited["cast_id"].dropna().astype(int).tolist())
            deleted = existing_ids - edited_ids
            updates = 0
            inserts = 0

            # 削除
            for cid in deleted:
                conn.execute("DELETE FROM dim_cast WHERE cast_id = ?", [int(cid)])

            # 既存ID最大値
            max_id_row = conn.execute("SELECT COALESCE(MAX(cast_id), 0) FROM dim_cast").fetchone()
            max_id = max_id_row[0] if max_id_row else 0

            for _, row in edited.iterrows():
                name = row["源氏名"]
                if not name or (isinstance(name, float) and pd.isna(name)):
                    continue
                cid = row.get("cast_id")
                cid = int(cid) if cid is not None and not pd.isna(cid) else None

                vals = {
                    "haken_name": _val(row.get("派遣名")),
                    "priority": _val(row.get("優先度"), int),
                    "priority_raw": _val(row.get("優先度詳細")),
                    "fixed_area": _val(row.get("固定エリア")),
                    "status": _val(row.get("在籍ステータス")),
                    "min_hours": _val(row.get("契約最低時間")),
                    "agency": _val(row.get("派遣会社")),
                    "hire_date": _to_date(row.get("採用日")),
                }

                if cid is None:
                    max_id += 1
                    conn.execute(
                        "INSERT INTO dim_cast (cast_id, cast_name, haken_name, priority, priority_raw, fixed_area, status, min_hours, agency, hire_date) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        [max_id, name, vals["haken_name"], vals["priority"], vals["priority_raw"],
                         vals["fixed_area"], vals["status"], vals["min_hours"], vals["agency"], vals["hire_date"]],
                    )
                    inserts += 1
                else:
                    conn.execute(
                        "UPDATE dim_cast SET cast_name=?, haken_name=?, priority=?, priority_raw=?, "
                        "fixed_area=?, status=?, min_hours=?, agency=?, hire_date=? WHERE cast_id=?",
                        [name, vals["haken_name"], vals["priority"], vals["priority_raw"],
                         vals["fixed_area"], vals["status"], vals["min_hours"], vals["agency"], vals["hire_date"], cid],
                    )
                    updates += 1

            st.success(f"✅ 保存しました（追加 {inserts} 件 / 更新 {updates} 件 / 削除 {len(deleted)} 件）")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"保存に失敗しました: {e}")


# ===================================================================
# Tab 2: キャスト×月 評価データ（fact_cast_monthly）
# ===================================================================
def _val(v, cast_fn=None):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if cast_fn is None:
        return v
    try:
        return cast_fn(v)
    except (TypeError, ValueError):
        return None


def _to_date(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    if isinstance(v, date):
        return v
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None


with tab_eval:
    section_title("キャスト×月 評価", granularity="評価シート S〜X / AH〜AP列相当")

    # 月選択
    months = [r[0] for r in conn.execute("SELECT DISTINCT year_month FROM fact_cast_monthly ORDER BY year_month DESC").fetchall()]
    if not months:
        empty_state("評価データがまだありません。Excelをアップロードしてください。", icon="📊")
    else:
        sel_month = st.selectbox("対象月", months, key="eval_month")

        df_eval = conn.execute(
            """
            SELECT f.year_month, c.cast_id, c.cast_name AS 源氏名,
                   f.work_days AS 稼働日数, f.contract_hours AS 契約時間, f.work_hours AS 稼働時間,
                   f.priority_raw AS 優先度,
                   f.case_count_store AS 案件数, f.store_main_nomination_rate AS 本指名率,
                   f.main_nomination_store AS 本指名数,
                   f.sales_store AS 店舗売上, f.reward_store AS 店舗報酬, f.gross_profit_store AS 店舗粗利,
                   f.nomination_store AS 指名数, f.store_nomination_rate AS 指名率
            FROM fact_cast_monthly f
            JOIN dim_cast c USING (cast_id)
            WHERE f.year_month = ?
            ORDER BY c.cast_id
            """,
            [sel_month],
        ).fetchdf()

        edited_eval = st.data_editor(
            df_eval,
            use_container_width=True,
            num_rows="fixed",
            hide_index=True,
            column_config={
                "year_month": st.column_config.TextColumn("月", disabled=True, width="small"),
                "cast_id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
                "源氏名": st.column_config.TextColumn("源氏名", disabled=True),
                "稼働日数": st.column_config.NumberColumn("稼働日数", format="%d"),
                "契約時間": st.column_config.TextColumn("契約時間", width="small"),
                "稼働時間": st.column_config.NumberColumn("稼働時間", format="%.1f"),
                "優先度": st.column_config.TextColumn("優先度", width="small"),
                "案件数": st.column_config.NumberColumn("案件数", format="%d"),
                "本指名率": st.column_config.NumberColumn("本指名率", format="%.1f%%"),
                "本指名数": st.column_config.NumberColumn("本指名数", format="%d"),
                "店舗売上": st.column_config.NumberColumn("店舗売上", format="¥%d"),
                "店舗報酬": st.column_config.NumberColumn("店舗報酬", format="¥%d"),
                "店舗粗利": st.column_config.NumberColumn("店舗粗利", format="¥%d"),
                "指名数": st.column_config.NumberColumn("指名数", format="%d"),
                "指名率": st.column_config.NumberColumn("指名率", format="%.1f%%"),
            },
            key=f"eval_editor_{sel_month}",
        )

        if st.button("💾 評価データを保存", type="primary", key="save_eval"):
            try:
                updates = 0
                for _, row in edited_eval.iterrows():
                    cid = int(row["cast_id"])
                    conn.execute(
                        """UPDATE fact_cast_monthly SET
                           work_days=?, contract_hours=?, work_hours=?, priority_raw=?,
                           case_count_store=?, store_main_nomination_rate=?, main_nomination_store=?,
                           sales_store=?, reward_store=?, gross_profit_store=?,
                           nomination_store=?, store_nomination_rate=?
                           WHERE year_month=? AND cast_id=?""",
                        [
                            _val(row.get("稼働日数"), int), _val(row.get("契約時間")),
                            _val(row.get("稼働時間"), float), _val(row.get("優先度")),
                            _val(row.get("案件数"), int), _val(row.get("本指名率"), float),
                            _val(row.get("本指名数"), int),
                            _val(row.get("店舗売上"), int), _val(row.get("店舗報酬"), int),
                            _val(row.get("店舗粗利"), int),
                            _val(row.get("指名数"), int), _val(row.get("指名率"), float),
                            sel_month, cid,
                        ],
                    )
                    updates += 1
                st.success(f"✅ {updates} 件 更新しました")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"保存に失敗しました: {e}")


# ===================================================================
# Tab 3: 顧客リピート（fact_customer_visit）— Phase B-3 で実装
# ===================================================================
with tab_customer:
    section_title("顧客リピート", granularity="派遣本指名・店舗本指名 統合", sub="電話番号で顧客識別（ハッシュ化）／月別の来店回数集計")

    src = st.selectbox("ソース", ["all", "store", "haken"], format_func=lambda x: {"all": "すべて", "store": "店舗", "haken": "派遣"}[x], key="cust_src")
    src_filter = "" if src == "all" else f" AND source_type='{src}'"

    df_visit_summary = conn.execute(
        f"""
        SELECT customer_hash, MIN(customer_name) AS 顧客カナ,
               COUNT(*) AS 来店回数,
               SUM(CASE WHEN nomination_type='指名' OR nomination_type='本指名' THEN 1 ELSE 0 END) AS 指名回数,
               SUM(CASE WHEN nomination_type='フリー' THEN 1 ELSE 0 END) AS フリー回数,
               MIN(visit_date) AS 初回来店,
               MAX(visit_date) AS 最終来店
        FROM fact_customer_nomination
        WHERE 1=1{src_filter}
        GROUP BY customer_hash
        ORDER BY 来店回数 DESC
        """
    ).fetchdf()

    if df_visit_summary.empty:
        empty_state("顧客リピートデータがありません。aoスパニスト評価シートをアップロードしてください。", icon="🧾")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("ユニーク顧客数", f"{len(df_visit_summary):,} 名")
        with c2: st.metric("総来店回数", f"{int(df_visit_summary['来店回数'].sum()):,} 回")
        with c3:
            riipeat_count = (df_visit_summary["来店回数"] >= 2).sum()
            st.metric("リピート顧客数", f"{riipeat_count:,} 名", help="2回以上の来店")
        with c4:
            rate = riipeat_count / len(df_visit_summary) if len(df_visit_summary) else 0
            st.metric("リピート率", f"{rate*100:.1f}%")

        st.dataframe(
            df_visit_summary.drop(columns=["customer_hash"]),
            use_container_width=True, hide_index=True, height=500,
        )


# ===================================================================
# Tab 4: 店舗月次KPI（fact_daily_sales を月集計）— Phase B-4 で拡張
# ===================================================================
with tab_kpi:
    section_title("店舗月次KPI", granularity="ヘッド店舗KPI シート相当", sub="月×店舗の集計（現状は閲覧のみ）")

    df_kpi = conn.execute(
        """
        SELECT strftime(f.date, '%Y-%m') AS 月,
               s.store_name AS 店舗,
               SUM(f.sales) AS 売上,
               SUM(f.case_count) AS 案件数,
               CASE WHEN SUM(f.case_count) > 0 THEN SUM(f.sales)/SUM(f.case_count) ELSE 0 END AS 客単価,
               SUM(f.new_count) AS 新規件数,
               SUM(f.repeat_count) AS リピート件数,
               AVG(f.repeat_rate) AS リピート率
        FROM fact_daily_sales f
        JOIN dim_store s USING (store_id)
        WHERE s.store_id IN (1,2,3)
        GROUP BY 1, 2
        ORDER BY 1 DESC, 2
        """
    ).fetchdf()

    if df_kpi.empty:
        empty_state("店舗KPIデータがありません。日報をアップロードしてください。", icon="🏪")
    else:
        st.dataframe(
            df_kpi.style.format({
                "売上": "¥{:,.0f}", "案件数": "{:.0f}", "客単価": "¥{:,.0f}",
                "新規件数": "{:.0f}", "リピート件数": "{:.0f}", "リピート率": "{:.1%}",
            }, na_rep="-"),
            use_container_width=True,
            hide_index=True,
            height=500,
        )
        st.caption("Phase B-4 で編集機能を追加予定")
