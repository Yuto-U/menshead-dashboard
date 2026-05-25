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
from etl.pipeline import backfill_derived_fields, ingest_file

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

render_header(
    "管理",
    "毎月の日報・勤怠ファイルをアップロードしてダッシュボードへ反映",
    kicker="管理",
)

conn = get_conn()
init_schema(conn)


# ---------- DBステータスカード ----------
section_title("データ取込状況", sub="取り込み済みデータの行数")
summary = table_summary(conn)

cols = st.columns(4)
key_tables = [
    ("fact_daily_sales", "日次売上", "店舗×日別の売上集計"),
    ("fact_course_daily", "コース別", "日×コース×新規/リピート"),
    ("fact_cast_monthly", "キャスト×月", "月次のキャスト別集計"),
    ("fact_attendance", "勤怠", "キャスト×日の出勤記録"),
]
for col, (table, label, sub) in zip(cols, key_tables):
    with col:
        kpi_card(label, f"{summary.get(table, 0):,} 行", sub=sub)

with st.expander("全テーブルの行数を見る", expanded=False):
    df_summary = pd.DataFrame(
        [(k, v) for k, v in summary.items() if not k.startswith("information_")],
        columns=["テーブル", "行数"],
    ).sort_values("テーブル").reset_index(drop=True)
    st.dataframe(df_summary, use_container_width=True, hide_index=True)


# ---------- アップロード ----------
section_title("Excelをアップロードして取り込む", sub="ファイル名で自動判定／複数まとめてアップロードOK")

# 対応ファイル一覧を Streamlit native のテーブルで表示（HTMLレンダリング問題回避）
files_md = """
| ファイル名 | 用途 |
|:--|:--|
| `ao合計日報YYMM.xlsx` | CSスタッフの日報。売上・コース別・キャスト×月集計のメインデータ |
| `ヘッドホワイトボードYYMM.xlsx` | キャストの勤怠ステータス（出勤・欠勤・早退など） |
| `ヘッドスパニスト一覧管理表.xlsx` | キャストマスタ（源氏名・派遣名・優先度・在籍ステータス） |
| `ヘッド研修日程表.xlsx` | 研修進捗（OP・フット・オイル等の完了状況） |
"""
st.markdown(files_md)
st.caption("💡 ファイル名は変更しないでください（自動判定に使います）。同名ファイルを再アップすると上書き更新されます。")

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

        with st.spinner("派生データを補完中..."):
            backfill_derived_fields(conn)
        st.success(f"✅ {len(results)} ファイルを取り込みました。")
        for r in results:
            with st.expander(f"📄 {r['file']} — {r.get('status', '?')}", expanded=False):
                st.json(r)
        st.balloons()
        if st.button("🔄 ページを再読み込み", type="primary"):
            st.rerun()


# ---------- リセット ----------
section_title("DBリセット", sub="取り込み済みデータを全削除")
st.warning("⚠️ 取り込み済みの全データを削除します。再度Excelをアップロードする必要があります。")
confirm = st.checkbox("削除に同意する")
if st.button("全データを削除", disabled=not confirm):
    conn.close()
    reset_db()
    st.success("DBをリセットしました。ページを再読み込みします。")
    st.rerun()
