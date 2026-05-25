"""Excelファイル → DuckDB への取り込みパイプライン。"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

import duckdb
import pandas as pd

from db.warehouse import get_conn, init_schema
from etl.loaders import dispatch


def ingest_file(file_path: Path, conn: duckdb.DuckDBPyConnection | None = None) -> dict:
    """1ファイルを取り込んで、各テーブルへ INSERT / REPLACE する。"""
    file_path = Path(file_path)
    loader = dispatch(file_path)
    if loader is None:
        return {"file": file_path.name, "status": "skipped", "reason": "no_loader"}

    own_conn = False
    if conn is None:
        conn = get_conn()
        init_schema(conn)
        own_conn = True

    started = time.time()
    try:
        dataframes = loader(file_path)
    except Exception as exc:  # noqa: BLE001
        return {"file": file_path.name, "status": "error", "error": str(exc)}

    counts: dict[str, int] = {}
    for table, df in dataframes.items():
        if df is None or df.empty:
            counts[table] = 0
            continue
        counts[table] = _upsert_dataframe(conn, table, df, file_path.name)

    if own_conn:
        # 単独取り込みでも補完を実行
        backfill_derived_fields(conn)
        conn.close()

    return {
        "file": file_path.name,
        "status": "ok",
        "counts": counts,
        "duration_sec": round(time.time() - started, 2),
    }


def ingest_files(files: Iterable[Path]) -> list[dict]:
    conn = get_conn()
    init_schema(conn)
    results = []
    for f in files:
        results.append(ingest_file(Path(f), conn=conn))
    backfill_derived_fields(conn)
    conn.close()
    return results


def backfill_derived_fields(conn: duckdb.DuckDBPyConnection) -> None:
    """ETL後の自動補完処理。

    1. fact_daily_sales の case_count / new_count / repeat_count / repeat_rate を
       fact_course_daily（全社）の合計と店舗別売上の比率で按分して補完。
    2. fact_daily_sales の unit_price を sales/case_count から算出。
    """
    # 案件数・新規/リピート件数・リピート率の補完
    conn.execute(
        """
        WITH course_total AS (
            SELECT date, SUM(case_count) AS total_cases,
                   SUM(CASE WHEN new_or_repeat='new' THEN case_count ELSE 0 END) AS new_cases,
                   SUM(CASE WHEN new_or_repeat='repeat' THEN case_count ELSE 0 END) AS repeat_cases
            FROM fact_course_daily WHERE store_id=0 GROUP BY date
        ),
        store_total AS (
            SELECT date, SUM(sales) AS day_sales FROM fact_daily_sales WHERE store_id IN (1,2,3) GROUP BY date
        )
        UPDATE fact_daily_sales f
        SET case_count = CAST(ct.total_cases * (f.sales*1.0 / NULLIF(st.day_sales, 0)) AS INTEGER),
            new_count = CAST(ct.new_cases * (f.sales*1.0 / NULLIF(st.day_sales, 0)) AS INTEGER),
            repeat_count = CAST(ct.repeat_cases * (f.sales*1.0 / NULLIF(st.day_sales, 0)) AS INTEGER),
            repeat_rate = ct.repeat_cases*1.0 / NULLIF(ct.total_cases, 0)
        FROM course_total ct, store_total st
        WHERE f.date = ct.date AND f.date = st.date AND f.case_count IS NULL
        """
    )
    # 客単価の補完
    conn.execute(
        """
        UPDATE fact_daily_sales
        SET unit_price = CAST(sales*1.0/case_count AS INTEGER)
        WHERE case_count > 0 AND unit_price IS NULL
        """
    )


def _ensure_cast_ids(conn: duckdb.DuckDBPyConnection, names: list[str]) -> dict[str, int]:
    """与えられた源氏名群について dim_cast にレコードがなければ新規追加し、{name: cast_id} を返す。"""
    if not names:
        return {}
    existing = {r[0]: r[1] for r in conn.execute("SELECT cast_name, cast_id FROM dim_cast").fetchall()}
    missing = [n for n in names if n not in existing]
    if missing:
        max_id = conn.execute("SELECT COALESCE(MAX(cast_id), 0) FROM dim_cast").fetchone()[0]
        rows = []
        for n in missing:
            max_id += 1
            rows.append((max_id, n))
        conn.executemany(
            "INSERT INTO dim_cast (cast_id, cast_name) VALUES (?, ?)",
            rows,
        )
        for n, _ in zip(missing, range(1)):
            pass
        for cid, name in rows:
            existing[name] = cid
    return existing


def _safe_value(v):
    """NaN / NaT → None。"""
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    return v


def _to_date(v):
    if v is None:
        return None
    if isinstance(v, float) and pd.isna(v):
        return None
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None


def _upsert_dim_cast(conn: duckdb.DuckDBPyConnection, df: pd.DataFrame) -> int:
    """dim_cast を upsert（新規はcast_id付番、既存は属性のみ更新）。"""
    names = df["cast_name"].dropna().astype(str).tolist()
    name_to_id = _ensure_cast_ids(conn, names)
    updated = 0
    for _, row in df.iterrows():
        cn = row.get("cast_name")
        if not cn or (isinstance(cn, float) and pd.isna(cn)):
            continue
        cid = name_to_id.get(cn)
        if cid is None:
            continue
        haken = _safe_value(row.get("haken_name"))
        area = _safe_value(row.get("fixed_area"))
        status = _safe_value(row.get("status"))
        hire = _to_date(row.get("hire_date"))
        prio = _safe_value(row.get("priority"))
        prio_raw = _safe_value(row.get("priority_raw"))
        min_h = _safe_value(row.get("min_hours"))
        if prio is not None:
            try:
                prio = int(prio)
            except (TypeError, ValueError):
                prio = None
        conn.execute(
            "UPDATE dim_cast SET "
            "haken_name = COALESCE(?, haken_name), "
            "fixed_area = COALESCE(?, fixed_area), "
            "status = COALESCE(?, status), "
            "hire_date = COALESCE(CAST(? AS DATE), hire_date), "
            "priority = COALESCE(?, priority), "
            "priority_raw = COALESCE(?, priority_raw), "
            "min_hours = COALESCE(?, min_hours) "
            "WHERE cast_id = ?",
            [haken, area, status, hire, prio, prio_raw, min_h, cid],
        )
        updated += 1
    return updated


def _upsert_fact_with_cast_name(
    conn: duckdb.DuckDBPyConnection,
    table: str,
    df: pd.DataFrame,
    source_file: str,
) -> int:
    """cast_name 列を cast_id に解決してから upsert。"""
    if "cast_name" not in df.columns:
        return _upsert_plain_dataframe(conn, table, df, source_file)
    names = df["cast_name"].dropna().astype(str).unique().tolist()
    name_to_id = _ensure_cast_ids(conn, names)
    df = df.copy()
    df["cast_id"] = df["cast_name"].map(name_to_id)
    df = df.drop(columns=["cast_name"])
    df = df.dropna(subset=["cast_id"])
    df["cast_id"] = df["cast_id"].astype("Int64")
    return _upsert_plain_dataframe(conn, table, df, source_file)


def _upsert_plain_dataframe(
    conn: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame, source_file: str
) -> int:
    """source_file をキーに既存行を削除してから INSERT する（冪等）。"""
    conn.execute(f'DELETE FROM "{table}" WHERE source_file = ?', [source_file])
    cols_in_db = [
        c[1] for c in conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    ]
    df_aligned = df[[c for c in df.columns if c in cols_in_db]].copy()
    for c in df_aligned.columns:
        if c in ("date", "completed_date"):
            df_aligned[c] = pd.to_datetime(df_aligned[c], errors="coerce").dt.date
        elif c == "recorded_at":
            df_aligned[c] = pd.to_datetime(df_aligned[c], errors="coerce")
            df_aligned[c] = df_aligned[c].where(df_aligned[c].notna(), None)
    conn.register("_df_tmp", df_aligned)
    col_list = ", ".join(f'"{c}"' for c in df_aligned.columns)
    conn.execute(f'INSERT INTO "{table}" ({col_list}) SELECT {col_list} FROM _df_tmp')
    conn.unregister("_df_tmp")
    return len(df_aligned)


def _upsert_dataframe(
    conn: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame, source_file: str
) -> int:
    """テーブル別に振り分け。"""
    if table == "dim_cast_seed":
        return _upsert_dim_cast(conn, df)
    # cast_name → cast_id 変換が必要なテーブル
    if table in {"fact_cast_monthly", "fact_attendance", "fact_training"}:
        return _upsert_fact_with_cast_name(conn, table, df, source_file)
    return _upsert_plain_dataframe(conn, table, df, source_file)
