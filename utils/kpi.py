"""ダッシュボード共通の KPI 計算ロジック。"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

import duckdb


def latest_complete_month(conn: duckdb.DuckDBPyConnection) -> str:
    """fact_daily_sales に存在する最新の年月 'YYYY-MM' を返す。"""
    row = conn.execute(
        "SELECT strftime(MAX(date), '%Y-%m') FROM fact_daily_sales WHERE store_id IN (1,2,3)"
    ).fetchone()
    return row[0] if row and row[0] else date.today().strftime("%Y-%m")


def _prev_year_month(year_month: str) -> str:
    year, month = map(int, year_month.split("-"))
    if month > 1:
        return f"{year:04d}-{month - 1:02d}"
    return f"{year - 1:04d}-12"


def _delta(current: float | None, previous: float | None) -> float | None:
    if not previous:
        return None
    if current is None:
        return None
    return (current - previous) / previous


def compute_store_sales(conn: duckdb.DuckDBPyConnection, year_month: str) -> dict:
    """全社+店舗別の当月売上と前月比をまとめて返す。

    返り値: {
        "total": {"current": ..., "previous": ..., "delta": ...},
        1: ..., 2: ..., 3: ...  # store_id
    }
    """
    sql = (
        "SELECT store_id, COALESCE(SUM(sales), 0) AS s "
        "FROM fact_daily_sales "
        "WHERE strftime(date,'%Y-%m') = ? AND store_id IN (1,2,3) "
        "GROUP BY store_id"
    )
    cur = {row[0]: row[1] for row in conn.execute(sql, [year_month]).fetchall()}
    prev_ym = _prev_year_month(year_month)
    prev = {row[0]: row[1] for row in conn.execute(sql, [prev_ym]).fetchall()}

    result: dict = {}
    for sid in (1, 2, 3):
        c = cur.get(sid, 0) or 0
        p = prev.get(sid, 0) or 0
        result[sid] = {"current": c, "previous": p, "delta": _delta(c, p)}

    total_c = sum(cur.values())
    total_p = sum(prev.values())
    result["total"] = {
        "current": total_c,
        "previous": total_p,
        "delta": _delta(total_c, total_p),
    }
    return result


def compute_home_kpi(conn: duckdb.DuckDBPyConnection, year_month: str) -> dict:
    """ホーム画面の主要KPI（当月実績 + 前月比）。"""
    sql = """
        SELECT
            COALESCE(SUM(sales), 0) AS sales_actual,
            COALESCE(SUM(case_count), 0) AS case_count,
            CASE WHEN SUM(case_count) > 0 THEN SUM(sales)*1.0/SUM(case_count) ELSE 0 END AS unit_price,
            COALESCE(AVG(repeat_rate), 0) AS repeat_rate
        FROM fact_daily_sales
        WHERE strftime(date, '%Y-%m') = ?
          AND store_id IN (1,2,3)
    """
    cur = conn.execute(sql, [year_month]).fetchone()
    prev = conn.execute(sql, [_prev_year_month(year_month)]).fetchone()
    return {
        "sales_actual": cur[0] or 0,
        "case_count": cur[1] or 0,
        "unit_price": cur[2] or 0,
        "repeat_rate": cur[3] or 0,
        "delta_sales": _delta(cur[0], prev[0]),
        "delta_cases": _delta(cur[1], prev[1]),
        "delta_unit": _delta(cur[2], prev[2]),
        "delta_repeat": _delta(cur[3], prev[3]),
    }


def projection_for_current_month(
    conn: duckdb.DuckDBPyConnection,
    year_month: str,
    avg_window_days: int = 7,
) -> Optional[dict]:
    """
    当月着地見込みを計算する。
    - 当月の実績売上を集計
    - 直近 avg_window_days 日の平均日商を算出
    - 残営業日数 × 平均日商 = 残期間予測
    - 実績 + 予測 = 月末着地予想
    """
    # 対象月の最大日付
    max_row = conn.execute(
        "SELECT MAX(date) FROM fact_daily_sales "
        "WHERE strftime(date, '%Y-%m') = ? AND store_id IN (1,2,3)",
        [year_month],
    ).fetchone()
    if not max_row or max_row[0] is None:
        return None
    latest_date: date = max_row[0]

    # 月初〜最新日付までの実績
    actual_row = conn.execute(
        "SELECT SUM(sales) FROM fact_daily_sales "
        "WHERE strftime(date, '%Y-%m') = ? AND store_id IN (1,2,3) AND date <= ?",
        [year_month, latest_date],
    ).fetchone()
    actual_sales = actual_row[0] or 0

    # 直近 N 日の平均日商
    avg_row = conn.execute(
        """
        SELECT AVG(daily_sales) FROM (
            SELECT date, SUM(sales) AS daily_sales
            FROM fact_daily_sales
            WHERE store_id IN (1,2,3) AND date <= ?
            GROUP BY date
            ORDER BY date DESC
            LIMIT ?
        )
        """,
        [latest_date, avg_window_days],
    ).fetchone()
    avg_daily = avg_row[0] or 0

    # 月末日と残営業日数
    year, month = map(int, year_month.split("-"))
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    month_end = next_month_first - timedelta(days=1)
    remaining_days = (month_end - latest_date).days

    remaining_estimate = int(avg_daily * remaining_days) if remaining_days > 0 else 0
    projected_sales = actual_sales + remaining_estimate

    # 前月比
    prev_year, prev_month = (year, month - 1) if month > 1 else (year - 1, 12)
    prev_year_month = f"{prev_year:04d}-{prev_month:02d}"
    prev_row = conn.execute(
        "SELECT SUM(sales) FROM fact_daily_sales WHERE strftime(date, '%Y-%m') = ? AND store_id IN (1,2,3)",
        [prev_year_month],
    ).fetchone()
    prev_sales = prev_row[0] or 0
    vs_last_month = ((projected_sales - prev_sales) / prev_sales) if prev_sales else 0

    return {
        "actual_sales": actual_sales,
        "avg_daily": avg_daily,
        "avg_window_days": avg_window_days,
        "remaining_days": remaining_days,
        "remaining_estimate": remaining_estimate,
        "projected_sales": projected_sales,
        "latest_date": latest_date,
        "vs_last_month": vs_last_month,
    }
