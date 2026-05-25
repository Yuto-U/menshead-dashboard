"""Streamlit 共通パスワード認証（5人以下の運用想定）。"""
from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def _logo_uri() -> str:
    path = ASSETS_DIR / "logo_icon.png"
    if not path.exists():
        return ""
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/png;base64,{data}"


def _get_expected_password() -> str | None:
    try:
        return st.secrets["password"]
    except (KeyError, FileNotFoundError):
        return None


def is_auth_enabled() -> bool:
    """secrets.toml の auth_enabled を見る（未設定なら True）。"""
    try:
        return bool(st.secrets.get("auth_enabled", True))
    except (KeyError, FileNotFoundError):
        return True


def require_password() -> None:
    """認証が通っていない場合はログインフォームを表示して停止する。auth_enabled=false ならスキップ。"""
    if not is_auth_enabled():
        st.session_state["authenticated"] = True
        return

    expected = _get_expected_password()
    if expected is None:
        st.error(
            "パスワードが設定されていません。"
            ".streamlit/secrets.toml または Streamlit Cloud の Secrets に "
            "`password = \"...\"` を追加してください。"
        )
        st.stop()

    if st.session_state.get("authenticated") is True:
        return

    st.markdown(
        f"""
        <div class="login-wrap">
            <div class="login-logo">
                <img src="{_logo_uri()}" width="64" />
            </div>
            <div class="login-title">MEN'S HEAD SPA</div>
            <div class="login-sub">経営ダッシュボード（社内限定）</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1, 2, 1])
    with cols[1]:
        with st.form("login_form", clear_on_submit=False):
            password = st.text_input("パスワード", type="password", autocomplete="current-password")
            submitted = st.form_submit_button("ログイン", use_container_width=True)
            if submitted:
                if password == expected:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("パスワードが違います。")

    st.stop()


def logout_button() -> None:
    if st.sidebar.button("🚪 ログアウト", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
