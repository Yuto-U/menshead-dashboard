"""店舗名・キャスト名・コース名などの正規化ヘルパ。"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Optional

STORE_MAP: dict[str, str] = {
    "新宿": "新宿",
    "三丁目": "新宿",
    "新宿三丁目": "新宿",
    "３丁目": "新宿",
    "3丁目": "新宿",
    "銀座": "銀座",
    "上野": "上野",
    "上野銀座": "兼任",
    "銀座上野": "兼任",
    "銀座・上野": "兼任",
    "新宿・銀座": "兼任",
    "御苑": "新宿",
}

STORE_ID = {"新宿": 1, "銀座": 2, "上野": 3, "兼任": 0}

COURSE_PATTERNS: list[tuple[str, dict]] = [
    (r"オイル\s*120", {"course_id": 5, "時間": 120, "タイプ": "オイル"}),
    (r"オイル\s*90", {"course_id": 4, "時間": 90, "タイプ": "オイル"}),
    (r"クリーム", {"course_id": 6, "時間": None, "タイプ": "クリーム"}),
    (r"120", {"course_id": 3, "時間": 120, "タイプ": "通常"}),
    (r"90", {"course_id": 2, "時間": 90, "タイプ": "通常"}),
    (r"60", {"course_id": 1, "時間": 60, "タイプ": "通常"}),
]


def normalize_text(s: object) -> str:
    """全角→半角、前後空白除去、改行除去。"""
    if s is None:
        return ""
    text = str(s)
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("　", " ").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def normalize_store(raw: object) -> Optional[str]:
    """店舗名のゆれを「新宿」「銀座」「上野」「兼任」に正規化。"""
    text = normalize_text(raw)
    if not text:
        return None
    if text in STORE_MAP:
        return STORE_MAP[text]
    for key, value in STORE_MAP.items():
        if key in text:
            return value
    return None


def store_id_of(raw: object) -> Optional[int]:
    name = normalize_store(raw)
    if name is None:
        return None
    return STORE_ID.get(name)


def normalize_cast_name(raw: object) -> str:
    """キャスト源氏名のゆれを正規化（trim + NFKC）。"""
    return normalize_text(raw)


def classify_course(raw: object) -> Optional[dict]:
    """コース名文字列を course_id / 時間 / タイプ に分解。"""
    text = normalize_text(raw)
    if not text:
        return None
    for pattern, mapping in COURSE_PATTERNS:
        if re.search(pattern, text):
            return mapping
    return None


def hash_phone(phone: object) -> Optional[str]:
    """電話番号を SHA-256 でハッシュ化（個人情報保護）。"""
    if phone is None or str(phone).strip() == "":
        return None
    text = re.sub(r"[^\d]", "", str(phone))
    if not text:
        return None
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def parse_priority(s: object) -> Optional[int]:
    """優先度文字列から数値（1〜3）を抽出。

    NFKC正規化後の文字列で「指名料」「割引」など副次的な数字を含むパートを除外し、
    最初に現れる 1/2/3 を優先度とする。

    例: "③"→3, "O②"→2, "出①"→1, "O2"→2, "出3"→3, "出O1"→1, "出OJ2"→2,
        "出3指名料1万"→3, "店舗のみ"→None
    """
    text = normalize_text(s)
    if not text:
        return None
    # 副次的な数字を除外（指名料・割引・万円など）
    main = text.split("指名料")[0].split("指名")[0].split("割引")[0].split("万")[0]
    m = re.search(r"[123]", main)
    if m:
        return int(m.group(0))
    return None


def parse_yymm(s: object) -> Optional[tuple[int, int]]:
    """'2605' → (2026, 5)。"""
    text = normalize_text(s)
    m = re.search(r"(\d{2})(\d{2})", text)
    if not m:
        return None
    yy, mm = int(m.group(1)), int(m.group(2))
    if not (1 <= mm <= 12):
        return None
    return 2000 + yy, mm


def yymm_to_year_month(yymm: str) -> Optional[str]:
    """'2605' → '2026-05'。"""
    parsed = parse_yymm(yymm)
    if parsed is None:
        return None
    year, month = parsed
    return f"{year:04d}-{month:02d}"


def safe_int(v: object) -> Optional[int]:
    """カンマ・¥記号・空文字を許容して int 化。"""
    if v is None:
        return None
    if isinstance(v, (int,)):
        return v
    if isinstance(v, float):
        if v != v:  # NaN
            return None
        return int(v)
    text = str(v).strip()
    if text == "" or text.startswith("#"):
        return None
    text = text.replace(",", "").replace("¥", "").replace("円", "")
    try:
        return int(float(text))
    except ValueError:
        return None


def safe_float(v: object) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        if isinstance(v, float) and v != v:
            return None
        return float(v)
    text = str(v).strip()
    if text == "" or text.startswith("#"):
        return None
    text = text.replace(",", "").replace("%", "")
    try:
        return float(text)
    except ValueError:
        return None
