"""Lucide風 SVGアイコン（インラインで使用）。currentColor 対応。"""
from __future__ import annotations

ICONS: dict[str, str] = {
    "home": (
        '<path d="M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z"/>'
    ),
    "store": (
        '<path d="M3 9 4.5 4h15L21 9"/>'
        '<path d="M4 9v11a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V9"/>'
        '<path d="M9 21v-6h6v6"/>'
    ),
    "user": (
        '<circle cx="12" cy="8" r="4"/>'
        '<path d="M4 21a8 8 0 0 1 16 0"/>'
    ),
    "target": (
        '<circle cx="12" cy="12" r="9"/>'
        '<circle cx="12" cy="12" r="5"/>'
        '<circle cx="12" cy="12" r="1.5"/>'
    ),
    "book": (
        '<path d="M4 4h13a3 3 0 0 1 3 3v13H7a3 3 0 0 1-3-3z"/>'
        '<path d="M4 17a3 3 0 0 1 3-3h13"/>'
    ),
    "trend": (
        '<polyline points="3 17 9 11 13 15 21 7"/>'
        '<polyline points="14 7 21 7 21 14"/>'
    ),
    "presentation": (
        '<path d="M3 4h18"/>'
        '<path d="M4 4v12a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1V4"/>'
        '<path d="M12 17v4"/>'
        '<path d="M8 21h8"/>'
    ),
    "settings": (
        '<circle cx="12" cy="12" r="3"/>'
        '<path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>'
    ),
    "logout": (
        '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>'
        '<polyline points="16 17 21 12 16 7"/>'
        '<line x1="21" y1="12" x2="9" y2="12"/>'
    ),
    "upload": (
        '<path d="M12 3v12"/>'
        '<polyline points="7 8 12 3 17 8"/>'
        '<path d="M5 21h14a2 2 0 0 0 2-2v-4H3v4a2 2 0 0 0 2 2z"/>'
    ),
    "database": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M3 5v6c0 1.7 4 3 9 3s9-1.3 9-3V5"/>'
        '<path d="M3 11v6c0 1.7 4 3 9 3s9-1.3 9-3v-6"/>'
    ),
}


def svg(name: str, size: int = 18, stroke_width: float = 1.8) -> str:
    """指定アイコンのSVG文字列を返す。currentColorで親要素のcolorに追従。"""
    body = ICONS.get(name, "")
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        f'stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">'
        f'{body}</svg>'
    )
