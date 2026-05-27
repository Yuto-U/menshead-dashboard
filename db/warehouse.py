"""DuckDB ウェアハウスの初期化と接続管理。"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import duckdb

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "warehouse.duckdb"

SCHEMA_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS dim_store (
        store_id INTEGER PRIMARY KEY,
        store_name TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_course (
        course_id INTEGER PRIMARY KEY,
        duration_min INTEGER,
        course_type TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS dim_cast (
        cast_id INTEGER PRIMARY KEY,
        cast_name TEXT UNIQUE NOT NULL,
        haken_name TEXT,
        hire_date DATE,
        fixed_area TEXT,
        status TEXT,
        agency TEXT,
        priority INTEGER,
        priority_raw TEXT,
        min_hours TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_daily_sales (
        date DATE,
        store_id INTEGER,
        sales BIGINT,
        case_count INTEGER,
        unit_price BIGINT,
        gross_profit BIGINT,
        cost BIGINT,
        new_count INTEGER,
        repeat_count INTEGER,
        repeat_rate DOUBLE,
        source_file TEXT,
        PRIMARY KEY (date, store_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_cast_monthly (
        year_month TEXT,
        cast_id INTEGER,
        sales BIGINT,
        reward BIGINT,
        gross_profit BIGINT,
        case_count INTEGER,
        work_hours DOUBLE,
        haken_nomination_rate DOUBLE,
        haken_main_nomination_rate DOUBLE,
        store_nomination_rate DOUBLE,
        store_main_nomination_rate DOUBLE,
        survey_score DOUBLE,
        source_file TEXT,
        PRIMARY KEY (year_month, cast_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_sale_item (
        sale_id BIGINT PRIMARY KEY,
        date DATE,
        store_id INTEGER,
        cast_id INTEGER,
        course_id INTEGER,
        customer_hash TEXT,
        amount BIGINT,
        new_or_repeat TEXT,
        time_slot TIME,
        source_file TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_course_daily (
        date DATE,
        store_id INTEGER,
        course_id INTEGER,
        new_or_repeat TEXT,
        case_count INTEGER,
        sales BIGINT,
        source_file TEXT,
        PRIMARY KEY (date, store_id, course_id, new_or_repeat)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_attendance (
        date DATE,
        cast_id INTEGER,
        status TEXT,
        work_hours DOUBLE,
        source_file TEXT,
        PRIMARY KEY (date, cast_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_training (
        cast_id INTEGER,
        training_type TEXT,
        status TEXT,
        completed_date DATE,
        source_file TEXT,
        PRIMARY KEY (cast_id, training_type)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_recruiting_monthly (
        year_month TEXT PRIMARY KEY,
        hired_count INTEGER,
        joined_count INTEGER,
        left_count INTEGER,
        debut_count INTEGER,
        active_count INTEGER,
        leave_rate DOUBLE,
        debut_rate DOUBLE,
        source_file TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_ban_customer (
        customer_hash TEXT,
        ng_cast_id INTEGER,
        ng_scope TEXT,
        store_or_haken TEXT,
        unpaid_amount BIGINT,
        recorded_at TIMESTAMP,
        source_file TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS fact_customer_nomination (
        visit_id BIGINT,
        visit_date DATE,
        customer_hash TEXT,
        customer_name TEXT,
        nomination_type TEXT,
        cast_name TEXT,
        store_or_haken TEXT,
        source_type TEXT,
        source_file TEXT,
        PRIMARY KEY (source_type, visit_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS etl_runs (
        run_id BIGINT PRIMARY KEY,
        run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        file_name TEXT,
        loader TEXT,
        row_count INTEGER,
        status TEXT,
        message TEXT
    )
    """,
]

SEED_STORE = [
    (1, "新宿"),
    (2, "銀座"),
    (3, "上野"),
    (0, "兼任"),
]

SEED_COURSE = [
    (1, 60, "通常"),
    (2, 90, "通常"),
    (3, 120, "通常"),
    (4, 90, "オイル"),
    (5, 120, "オイル"),
    (6, None, "クリーム"),
]


def get_conn(db_path: Optional[Path] = None) -> duckdb.DuckDBPyConnection:
    path = db_path or DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(str(path))
    return conn


_streamlit_conn = None


def get_conn_cached() -> duckdb.DuckDBPyConnection:
    """Streamlit用：プロセス内でDuckDB接続を1つ再利用。"""
    global _streamlit_conn
    if _streamlit_conn is None:
        _streamlit_conn = get_conn()
        init_schema(_streamlit_conn)
    return _streamlit_conn


ALTER_DDL = [
    # 既存DBへの追記用（カラムが既にあればDuckDBは無視する）
    "ALTER TABLE dim_cast ADD COLUMN IF NOT EXISTS priority INTEGER",
    "ALTER TABLE dim_cast ADD COLUMN IF NOT EXISTS priority_raw TEXT",
    "ALTER TABLE dim_cast ADD COLUMN IF NOT EXISTS min_hours TEXT",
    # fact_cast_monthly に全項目分の列を追加
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS work_days INTEGER",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS contract_hours TEXT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS priority_raw TEXT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS sales_store BIGINT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS reward_store BIGINT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS gross_profit_store BIGINT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS case_count_store INTEGER",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS nomination_store INTEGER",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS main_nomination_store INTEGER",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS nomination_rate_store2 DOUBLE",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS main_nomination_total INTEGER",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS total_sales BIGINT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS total_reward BIGINT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS total_gross_profit BIGINT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS total_case_count INTEGER",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS guarantee_amount BIGINT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS staff_name TEXT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS survey_text TEXT",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS survey_score INTEGER",
    "ALTER TABLE fact_cast_monthly ADD COLUMN IF NOT EXISTS note TEXT",
]


def init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    for ddl in SCHEMA_DDL:
        conn.execute(ddl)
    for ddl in ALTER_DDL:
        try:
            conn.execute(ddl)
        except Exception:
            pass
    conn.executemany(
        "INSERT OR REPLACE INTO dim_store (store_id, store_name) VALUES (?, ?)",
        SEED_STORE,
    )
    conn.executemany(
        "INSERT OR REPLACE INTO dim_course (course_id, duration_min, course_type) VALUES (?, ?, ?)",
        SEED_COURSE,
    )


def reset_db(db_path: Optional[Path] = None) -> None:
    """DuckDB ファイルを削除してまっさらにする（管理画面の Reset 用）。"""
    path = db_path or DEFAULT_DB_PATH
    if path.exists():
        path.unlink()
    wal = path.with_suffix(path.suffix + ".wal")
    if wal.exists():
        wal.unlink()


def table_summary(conn: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """各テーブルの行数を返す（管理画面の状態確認用）。"""
    result: dict[str, int] = {}
    tables = conn.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema='main' ORDER BY table_name"
    ).fetchall()
    for (tname,) in tables:
        count = conn.execute(f'SELECT COUNT(*) FROM "{tname}"').fetchone()[0]
        result[tname] = count
    return result
