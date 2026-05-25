"""管理ページ：Excel アップロードと ETL 実行、DB状態確認、リセット。"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from components.auth import require_password
from components.layout import favicon, kpi_card, render_header, render_sidebar, section_title
from components.style import apply_global_style
from components.theme import install_plotly_theme
from db.warehouse import DEFAULT_DB_PATH, get_conn, init_schema, reset_db, table_summary
from etl.pipeline import ingest_file

st.set_page_config(page_title="管理 - ダッシュボード", page_icon=favicon(), layout="wide")
apply_global_style()
install_plotly_theme()
require_password()
render_sidebar(active_key="admin")

st.markdown(
    """
    <style>
    .upload-zone {
        background: linear-gradient(160deg, #161D2D 0%, #11161F 100%);
        border: 2px dashed #3A4256;
        border-radius: 14px;
        padding: 28px;
        text-align: center;
        transition: border-color 0.2s;
    }
    .upload-zone:hover { border-color: #C8A464; }
    </style>
    """,
    unsafe_allow_html=True,
)

render_header("管理", "Excelをアップロードしてダッシュボードへ反映", kicker="管理")

conn = get_conn()
init_schema(conn)


# ---------- DBステータスカード ----------
section_title("📊 データ取込状況")
summary = table_summary(conn)
fact_tables = {k: v for k, v in summary.items() if k.startswith("fact_")}
dim_tables = {k: v for k, v in summary.items() if k.startswith("dim_")}

cols = st.columns(4)
key_tables = ["fact_daily_sales", "fact_course_daily", "fact_cast_monthly", "fact_attendance"]
labels = ["日次×店舗売上", "コース別×日", "キャスト×月", "勤怠"]
for col, table, label in zip(cols, key_tables, labels):
    with col:
        kpi_card(label, f"{summary.get(table, 0):,} 行", sub=table)


# 詳細テーブル
with st.expander("📋 全テーブルの行数", expanded=False):
    df_summary = pd.DataFrame(
        [(k, v) for k, v in summary.items() if not k.startswith("information_")],
        columns=["テーブル", "行数"],
    ).sort_values("テーブル").reset_index(drop=True)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)


# ---------- アップロード ----------
st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)
section_title("📤 Excelをアップロードして取り込む")
st.markdown(
    """
    <div style="color:#94A3B8;font-size:13px;line-height:1.7;">
    対応ファイル（ファイル名で自動判定 / 複数同時OK）：<br>
    ✅ <b style="color:#E8C77A;">ヘッド店舗KPI.xlsx</b> — 日次×店舗の売上、コース別件数（実装済）<br>
    🔜 aoスパニスト評価シート.xlsx — キャスト×月の指名率・売上（Phase2）<br>
    🔜 ao合計日報{YYMM}.xlsx — 案件単位の生データ（Phase2）<br>
    🔜 ヘッドホワイトボード{YYMM}.xlsx — 勤怠・出禁リスト（Phase2）<br>
    🔜 ヘッドスパニスト一覧管理表.xlsx — キャストマスタ・採用ファネル（Phase2）<br>
    🔜 ヘッド研修日程表.xlsx — 研修進捗（Phase2）
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    " ", type=["xlsx"], accept_multiple_files=True, label_visibility="collapsed"
)

if uploaded:
    if st.button("🚀 取り込み実行", type="primary", use_container_width=True):
        results = []
        progress = st.progress(0.0)
        for i, file in enumerate(uploaded):
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(file.getvalue())
                tmp_path = Path(tmp.name)
            renamed = tmp_path.with_name(file.name)
            tmp_path.rename(renamed)
            with st.spinner(f"取り込み中：{file.name}"):
                result = ingest_file(renamed, conn=conn)
            results.append(result)
            progress.progress((i + 1) / len(uploaded))
            renamed.unlink(missing_ok=True)

        st.success(f"✅ {len(results)} ファイルを取り込みました。")
        for r in results:
            with st.expander(f"📄 {r['file']} — {r.get('status', '?')}", expanded=False):
                st.json(r)
        st.balloons()
        if st.button("🔄 ページを再読み込み", type="primary"):
            st.rerun()


# ---------- リセット ----------
st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
section_title("🗑 DBリセット（危険）")
st.warning("全データを削除して空の状態に戻します。再度Excelをアップロードする必要があります。")
confirm = st.checkbox("削除に同意する")
if st.button("🗑 全データを削除", disabled=not confirm):
    conn.close()
    reset_db()
    st.success("DBをリセットしました。ページを再読み込みします。")
    st.rerun()

st.markdown(f'<div style="color:#64748B;font-size:11px;margin-top:24px;">DB: <code>{DEFAULT_DB_PATH}</code></div>', unsafe_allow_html=True)
