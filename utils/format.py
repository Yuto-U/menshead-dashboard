"""表示用のフォーマッタ。"""
from __future__ import annotations


def yen(value: object, default: str = "-") -> str:
    if value is None:
        return default
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if v != v:  # NaN
        return default
    return f"¥{v:,.0f}"


def percent(value: object, default: str = "-") -> str:
    if value is None:
        return default
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    if v != v:
        return default
    # 0-1 のレンジ想定。1超なら既に %値とみなす
    if abs(v) <= 1.0:
        v *= 100
    return f"{v:.1f}%"


def int_or_dash(value: object, default: str = "-") -> str:
    if value is None:
        return default
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return default
