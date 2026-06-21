from __future__ import annotations

import streamlit as st

from app.auth.service import AuthService
from app.models.auth import AuthUser


AUTH_SESSION_KEY = "authenticated_user"


def authenticated_user(auth: AuthService) -> AuthUser | None:
    payload = st.session_state.get(AUTH_SESSION_KEY)
    if not isinstance(payload, dict) or not payload.get("id"):
        return None
    user = auth.repository.find_by_id(str(payload["id"]))
    if user is None:
        st.session_state.pop(AUTH_SESSION_KEY, None)
    return user


def render_auth_gate(auth: AuthService) -> AuthUser | None:
    user = authenticated_user(auth)
    if user:
        return user

    st.markdown(
        """
        <section class="auth-hero">
            <div class="auth-brand">خانه‌یاب</div>
            <h1>جست‌وجوی هوشمند ملک، متناسب با شما</h1>
            <p>برای نگهداری امن سابقه جست‌وجو و پیشنهادهای شخصی وارد حساب خود شوید.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )
    login_tab, register_tab = st.tabs(("ورود", "ثبت‌نام"))
    with login_tab:
        _render_login(auth)
    with register_tab:
        _render_registration(auth)
    return None


def logout() -> None:
    for key in tuple(st.session_state):
        del st.session_state[key]


def _render_login(auth: AuthService) -> None:
    with st.form("login_form"):
        username = st.text_input("نام کاربری", key="login_username")
        password = st.text_input(
            "رمز عبور", type="password", key="login_password"
        )
        submitted = st.form_submit_button("ورود به حساب", type="primary", width="stretch")
    if submitted:
        try:
            user = auth.authenticate(username, password)
            _set_session(user)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _render_registration(auth: AuthService) -> None:
    with st.form("registration_form"):
        display_name = st.text_input("نام نمایشی", key="register_display_name")
        username = st.text_input("نام کاربری", key="register_username")
        password = st.text_input(
            "رمز عبور", type="password", key="register_password"
        )
        confirmation = st.text_input(
            "تکرار رمز عبور", type="password", key="register_confirmation"
        )
        st.caption("رمز عبور حداقل ۸ کاراکتر و شامل حرف و عدد باشد.")
        submitted = st.form_submit_button("ساخت حساب", type="primary", width="stretch")
    if submitted:
        try:
            user = auth.register(username, password, confirmation, display_name)
            _set_session(user)
            st.rerun()
        except ValueError as exc:
            st.error(str(exc))


def _set_session(user: AuthUser) -> None:
    st.session_state[AUTH_SESSION_KEY] = {
        "id": user.id,
        "username": user.username,
        "display_name": user.display_name,
    }
