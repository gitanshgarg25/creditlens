"""
CreditLens - AI-Assisted Credit Risk & Early-Warning Intelligence Platform
Enterprise Multi-User Authentication & Excel-Style Multi-Dataset Workbook
"""

import os
import sys
import json
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Setup Project Path & Dynamic Module Ingestion
# Robust resolution for Streamlit Cloud container (/mount/src/creditlens/...) and local environments
import types
import importlib.util

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(BASE_DIR, "src")
APP_DIR = os.path.dirname(os.path.abspath(__file__))

# Strip any conflicting /mount/src or /mount namespace collisions on Streamlit Cloud
sys.path = [p for p in sys.path if os.path.abspath(p) not in ("/mount/src", "/mount")]
for _p in [SRC_DIR, BASE_DIR, APP_DIR]:
    while _p in sys.path:
        sys.path.remove(_p)
    sys.path.insert(0, _p)

# Ensure 'src' package namespace exists in sys.modules
if "src" not in sys.modules:
    src_pkg = types.ModuleType("src")
    src_pkg.__path__ = [SRC_DIR]
    sys.modules["src"] = src_pkg

def _safe_load_src_module(name: str):
    """Loads module from src/ directory and registers under both `name` and `src.name`."""
    if name in sys.modules and getattr(sys.modules[name], "__file__", None):
        mod = sys.modules[name]
        sys.modules[f"src.{name}"] = mod
        setattr(sys.modules["src"], name, mod)
        return mod
    fpath = os.path.join(SRC_DIR, f"{name}.py")
    if not os.path.exists(fpath):
        fpath = os.path.join(APP_DIR, f"{name}.py")
    if os.path.exists(fpath):
        spec = importlib.util.spec_from_file_location(name, fpath)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            sys.modules[f"src.{name}"] = mod
            setattr(sys.modules["src"], name, mod)
            spec.loader.exec_module(mod)
            return mod
    try:
        mod = importlib.import_module(name)
        sys.modules[f"src.{name}"] = mod
        setattr(sys.modules["src"], name, mod)
        return mod
    except Exception:
        return importlib.import_module(f"src.{name}")

# Safely pre-load core business & authentication modules
_auth = _safe_load_src_module("auth")
_analytics = _safe_load_src_module("analytics_engine")
_risk = _safe_load_src_module("risk_scoring")
_model_train = _safe_load_src_module("model_training")

# Bind symbols directly into global namespace
init_user_db = _auth.init_user_db
register_user = _auth.register_user
authenticate_user = _auth.authenticate_user
get_user_by_username = _auth.get_user_by_username
update_profile_avatar = _auth.update_profile_avatar
list_users = _auth.list_users
update_password = _auth.update_password
authenticate_or_register_social = _auth.authenticate_or_register_social
authenticate_or_register_contact = _auth.authenticate_or_register_contact
reset_password_forgot = _auth.reset_password_forgot

get_portfolio_kpis = _analytics.get_portfolio_kpis
get_risk_tier_breakdown = _analytics.get_risk_tier_breakdown
get_delinquency_transition = _analytics.get_delinquency_transition
get_utilization_risk_matrix = _analytics.get_utilization_risk_matrix
get_watchlist = _analytics.get_watchlist

pd_to_credit_score = _risk.pd_to_credit_score
classify_risk_tier = _risk.classify_risk_tier
assign_recommended_action = _risk.assign_recommended_action

# Streamlit Page Config
st.set_page_config(
    page_title="CreditLens | Multi-User Risk Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Excel / Institutional Fintech Aesthetic)
st.markdown("""
<style>
    /* -------------------------------------------------------------------------
       Institutional High-Contrast Theme (Adaptive Light & Dark Mode)
       ------------------------------------------------------------------------- */
    :root {
        --text-headline: #0F172A;
        --text-sub: #475569;
        --card-bg: rgba(255, 255, 255, 0.95);
        --card-border: #E2E8F0;
        --kpi-val: #0F172A;
        --tab-bg: #F1F5F9;
        --tab-active-bg: #FFFFFF;
        --tab-text: #475569;
        --tab-active-text: #1E3A8A;
        --user-pill-bg: #F8FAFC;
        --user-pill-border: #CBD5E1;
        --user-pill-text: #0F172A;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --text-headline: #F8FAFC;
            --text-sub: #94A3B8;
            --card-bg: #1E293B;
            --card-border: #334155;
            --kpi-val: #F8FAFC;
            --tab-bg: #1E293B;
            --tab-active-bg: #0F172A;
            --tab-text: #94A3B8;
            --tab-active-text: #38BDF8;
            --user-pill-bg: #1E293B;
            --user-pill-border: #475569;
            --user-pill-text: #F8FAFC;
        }
    }

    /* Streamlit Cloud Dark Mode Container Overrides */
    [data-theme="dark"], .stApp[data-theme="dark"], body.dark-mode {
        --text-headline: #F8FAFC !important;
        --text-sub: #94A3B8 !important;
        --card-bg: #1E293B !important;
        --card-border: #334155 !important;
        --kpi-val: #F8FAFC !important;
        --tab-bg: #1E293B !important;
        --tab-active-bg: #0F172A !important;
        --tab-text: #94A3B8 !important;
        --tab-active-text: #38BDF8 !important;
        --user-pill-bg: #1E293B !important;
        --user-pill-border: #475569 !important;
        --user-pill-text: #F8FAFC !important;
    }

    /* Main Heading: High-Vibrancy Blue/Cyan Gradient - 100% visible in BOTH Dark and Light Mode! */
    .main-header {
        font-size: 2.15rem;
        font-weight: 850;
        background: linear-gradient(90deg, #2563EB 0%, #0284C7 50%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.6px;
        margin-bottom: 0.15rem;
        display: inline-block;
    }
    .sub-header {
        font-size: 0.92rem;
        color: var(--text-sub, #64748B) !important;
        margin-bottom: 0.85rem;
        font-weight: 500;
    }

    .kpi-card {
        background: var(--card-bg, #FFFFFF) !important;
        border-radius: 10px;
        padding: 16px 18px;
        border: 1px solid var(--card-border, #E2E8F0) !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
    }
    .kpi-title {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.7rem;
        font-weight: 800;
        color: var(--kpi-val, #0F172A) !important;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.76rem;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 500;
    }

    /* Top-Right Profile Badge */
    .user-profile-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: var(--user-pill-bg, #F8FAFC) !important;
        border: 1px solid var(--user-pill-border, #CBD5E1) !important;
        color: var(--user-pill-text, #0F172A) !important;
        padding: 7px 14px;
        border-radius: 8px;
        font-size: 0.84rem;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    .badge-prime { background-color: #DCFCE7; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-nearprime { background-color: #E0E7FF; color: #3730A3; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-subprime { background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-highrisk { background-color: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }

    /* Excel-Style Tabs Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 2px solid var(--card-border, #CBD5E1);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: var(--tab-bg, #F1F5F9);
        border: 1px solid var(--card-border, #CBD5E1);
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        font-weight: 700;
        font-size: 0.85rem;
        color: var(--tab-text, #475569);
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--tab-active-bg, #FFFFFF) !important;
        color: var(--tab-active-text, #1E3A8A) !important;
        border-top: 3px solid #2563EB !important;
    }

    /* Instagram/Snapchat Social UI Elements */
    .ig-auth-card {
        background: var(--card-bg, #FFFFFF) !important;
        border: 1px solid var(--card-border, #CBD5E1) !important;
        border-radius: 16px;
        padding: 30px 28px 24px 28px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.06);
        text-align: center;
        margin-bottom: 14px;
    }
    .ig-bottom-card {
        background: var(--card-bg, #FFFFFF) !important;
        border: 1px solid var(--card-border, #CBD5E1) !important;
        border-radius: 12px;
        padding: 16px 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        font-size: 0.88rem;
    }
    .user-avatar-circle {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        background: linear-gradient(135deg, #2563EB 0%, #7C3AED 50%, #EC4899 100%);
        color: #FFFFFF !important;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: 800;
        font-size: 0.95rem;
        border: 2px solid #FFFFFF;
        box-shadow: 0 2px 6px rgba(37, 99, 235, 0.35);
        text-transform: uppercase;
        flex-shrink: 0;
    }
    .user-avatar-img {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #3B82F6;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
        flex-shrink: 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize DB on load
init_user_db()


def render_avatar_circle(user_dict, size=36, font_size=0.95):
    """
    Renders circular avatar HTML:
    - If user has avatar_data (base64 image), renders the image inside a circle.
    - If no avatar_data, renders the first initial of the user's name encircled with a vibrant modern gradient.
    """
    if not user_dict:
        initial = "U"
        avatar_img = ""
    else:
        name = user_dict.get("full_name", "") or user_dict.get("username", "") or "User"
        initial = name.strip()[:1].upper() if name.strip() else "U"
        avatar_img = user_dict.get("avatar_data", "")

    if avatar_img:
        return f'<img src="{avatar_img}" style="width:{size}px; height:{size}px; border-radius:50%; object-fit:cover; border:2px solid #3B82F6; box-shadow:0 2px 6px rgba(0,0,0,0.15); display:inline-block; vertical-align:middle; flex-shrink:0;" />'
    else:
        return f'<div style="width:{size}px; height:{size}px; border-radius:50%; background:linear-gradient(135deg, #2563EB 0%, #7C3AED 50%, #EC4899 100%); color:#FFFFFF !important; display:inline-flex; align-items:center; justify-content:center; font-size:{font_size}rem; font-weight:800; border:2px solid rgba(255,255,255,0.9); box-shadow:0 2px 8px rgba(37,99,235,0.35); vertical-align:middle; text-transform:uppercase; flex-shrink:0;">{initial}</div>'


@st.cache_data
def load_dataset_from_disk(relative_path):
    full_path = os.path.join(BASE_DIR, relative_path)
    if os.path.exists(full_path):
        return pd.read_csv(full_path)
    main_path = os.path.join(BASE_DIR, "data", "processed", "credit_lens_tableau_extract.csv")
    if not os.path.exists(main_path):
        if _model_train and hasattr(_model_train, "train_and_evaluate_models"):
            _model_train.train_and_evaluate_models()
        else:
            try:
                from model_training import train_and_evaluate_models
            except (ImportError, ModuleNotFoundError):
                from src.model_training import train_and_evaluate_models
            train_and_evaluate_models()
    return pd.read_csv(main_path)


# Default Workbook Sheets
DEFAULT_SHEETS = {
    "📑 Taiwan Retail Bank (Benchmark - 30k)": "data/processed/credit_lens_tableau_extract.csv",
    "📑 FinTech Consumer Loans (10k)": "data/processed/fintech_consumer_portfolio.csv",
    "📑 Prime Wealth Credit (5k)": "data/processed/prime_wealth_portfolio.csv"
}


# =============================================================================
# AUTHENTICATION & SOCIAL-STYLE USER ACCOUNT SYSTEM
# =============================================================================
def render_auth_modal():
    """
    Renders an Instagram / Snapchat level social login and sign-up experience:
    - Sleek centered cards with gradient brand identity
    - Instagram-style "One-Click Saved Account Login" (instant access with circular avatars)
    - Clean credentials login (username, email, or contact)
    - Social SSO integration (Google, Apple, Phone)
    - Instagram-style separate bottom cards to switch between Log In and Sign Up
    - Trouble logging in (Forgot Password) self-service view
    """
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"
    if "social_mode" not in st.session_state:
        st.session_state["social_mode"] = None

    auth_view = st.session_state["auth_view"]

    st.markdown("<br>", unsafe_allow_html=True)
    _, auth_box, _ = st.columns([1, 1.28, 1])

    with auth_box:
        # =====================================================================
        # VIEW 1: LOG IN (INSTAGRAM / SNAPCHAT STYLE)
        # =====================================================================
        if auth_view == "login":
            st.markdown("""
            <div class="ig-auth-card">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 20px; background: linear-gradient(45deg, #F58529, #FEDA77, #DD2A7B, #8134AF, #515BD4); box-shadow: 0 4px 18px rgba(221, 42, 123, 0.35); margin-bottom: 12px;">
                    <span style="font-size: 32px;">🛡️</span>
                </div>
                <h1 style="font-size: 2.3rem; font-weight: 850; letter-spacing: -0.8px; margin: 0; background: linear-gradient(90deg, #2563EB 0%, #7C3AED 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">CreditLens</h1>
                <p style="color: #64748B; font-size: 0.86rem; margin-top: 4px; margin-bottom: 18px; font-weight: 500;">Institutional Credit Risk & Portfolio Intelligence</p>
            </div>
            """, unsafe_allow_html=True)

            # --- Instagram Saved Profile Quick Login ---
            default_u = get_user_by_username("admin")
            if default_u:
                def_av_html = render_avatar_circle(default_u, size=64, font_size=1.7)
                st.markdown(f"""
                <div style="text-align: center; padding: 14px 16px; background: rgba(37, 99, 235, 0.05); border: 1px solid rgba(37, 99, 235, 0.15); border-radius: 14px; margin-bottom: 14px;">
                    <div style="margin-bottom: 8px;">{def_av_html}</div>
                    <div style="font-weight: 750; font-size: 0.96rem; color: var(--text-headline);">{default_u['full_name']}</div>
                    <div style="font-size: 0.78rem; color: #64748B;">@{default_u['username']} &nbsp;•&nbsp; <span style="color:#2563EB; font-weight:600;">{default_u['role']}</span></div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"Log In as {default_u['full_name']}", type="primary", use_container_width=True, key="ig_btn_quick_admin"):
                    st.session_state["current_user"] = default_u
                    st.rerun()

                # Fast chips for other profiles
                c_chip1, c_chip2 = st.columns(2)
                with c_chip1:
                    u_ana = get_user_by_username("analyst")
                    if st.button("📊 Lead Analyst (@analyst)", use_container_width=True, key="ig_chip_analyst"):
                        st.session_state["current_user"] = u_ana or authenticate_user("analyst", "password123")
                        st.rerun()
                with c_chip2:
                    u_gst = get_user_by_username("guest")
                    if st.button("🔍 Auditor (@guest)", use_container_width=True, key="ig_chip_guest"):
                        st.session_state["current_user"] = u_gst or authenticate_user("guest", "guest123")
                        st.rerun()

            # --- Divider ---
            st.markdown("""
            <div style="display:flex; align-items:center; margin:18px 0 14px 0; color:#8E8E8E; font-size:0.74rem; font-weight:700;">
                <div style="flex:1; height:1px; background:#E2E8F0;"></div>
                <span style="padding:0 12px; color:#94A3B8;">OR LOG IN WITH CREDENTIALS</span>
                <div style="flex:1; height:1px; background:#E2E8F0;"></div>
            </div>
            """, unsafe_allow_html=True)

            # --- Standard Inputs ---
            l_ident = st.text_input("Username, email, or contact:", placeholder="Phone number, username, or email", key="ig_field_ident")
            l_pass = st.text_input("Password:", placeholder="Password", type="password", key="ig_field_pass")

            if st.button("Log In", type="primary", use_container_width=True, key="ig_btn_submit_login"):
                if not l_ident or not l_pass:
                    st.error("Please enter both username/email and password.")
                else:
                    u_rec = authenticate_user(l_ident, l_pass)
                    if u_rec:
                        st.session_state["current_user"] = u_rec
                        st.success(f"Welcome back, {u_rec['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Incorrect username or password. Check your credentials or reset your password.")

            # --- Social SSO Buttons (Instagram & Snapchat style) ---
            st.markdown("""
            <div style="display:flex; align-items:center; margin:16px 0 12px 0; color:#8E8E8E; font-size:0.74rem; font-weight:700;">
                <div style="flex:1; height:1px; background:#E2E8F0;"></div>
                <span style="padding:0 12px; color:#94A3B8;">OR CONTINUE WITH</span>
                <div style="flex:1; height:1px; background:#E2E8F0;"></div>
            </div>
            """, unsafe_allow_html=True)

            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                if st.button("🔴 Google", use_container_width=True, key="btn_sso_g"):
                    st.session_state["social_mode"] = "Google" if st.session_state.get("social_mode") != "Google" else None
                    st.rerun()
            with sc2:
                if st.button("🍏 Apple", use_container_width=True, key="btn_sso_a"):
                    st.session_state["social_mode"] = "Apple" if st.session_state.get("social_mode") != "Apple" else None
                    st.rerun()
            with sc3:
                if st.button("📱 Phone", use_container_width=True, key="btn_sso_p"):
                    st.session_state["social_mode"] = "Phone" if st.session_state.get("social_mode") != "Phone" else None
                    st.rerun()

            # Social SSO Drawer
            if st.session_state.get("social_mode") == "Google":
                with st.container():
                    st.markdown("---")
                    st.info("🔴 **Google One-Tap / Workspace SSO**")
                    g_mail = st.text_input("Enter your Google Account email:", placeholder="name@company.com or name@gmail.com", key="ig_g_mail")
                    g_name = st.text_input("Display Name:", placeholder="e.g. Gitansh Garg", key="ig_g_name")
                    g_role = st.selectbox("Designated Level:", ["CRO Level (Executive)", "Senior Analyst Level", "Credit Underwriting Manager", "Portfolio Risk Specialist", "Reviewer Level"], index=1, key="ig_g_role")
                    if st.button("Continue with Google Workspace", type="primary", use_container_width=True, key="ig_btn_g_cont"):
                        if g_mail.strip():
                            u_rec = authenticate_or_register_social("Google", g_mail, g_name, g_role)
                            if u_rec:
                                st.session_state["current_user"] = u_rec
                                st.session_state["social_mode"] = None
                                st.rerun()
                        else:
                            st.error("Please enter a valid email address.")

            elif st.session_state.get("social_mode") == "Apple":
                with st.container():
                    st.markdown("---")
                    st.info("🍏 **Apple ID Secure Authentication**")
                    a_mail = st.text_input("Enter your Apple ID email:", placeholder="name@icloud.com or name@privaterelay.appleid.com", key="ig_a_mail")
                    a_name = st.text_input("Display Name:", placeholder="e.g. Gitansh Garg", key="ig_a_name")
                    a_role = st.selectbox("Designated Level:", ["CRO Level (Executive)", "Senior Analyst Level", "Credit Underwriting Manager", "Portfolio Risk Specialist", "Reviewer Level"], index=1, key="ig_a_role")
                    if st.button("Continue with Apple ID", type="primary", use_container_width=True, key="ig_btn_a_cont"):
                        if a_mail.strip():
                            u_rec = authenticate_or_register_social("Apple", a_mail, a_name, a_role)
                            if u_rec:
                                st.session_state["current_user"] = u_rec
                                st.session_state["social_mode"] = None
                                st.rerun()
                        else:
                            st.error("Please enter a valid Apple ID email address.")

            elif st.session_state.get("social_mode") == "Phone":
                with st.container():
                    st.markdown("---")
                    st.info("📱 **Phone Number / SMS Access**")
                    p_num = st.text_input("Mobile Phone Number:", placeholder="+1 (555) 000-0000 or 9876543210", key="ig_p_num")
                    p_name = st.text_input("Full Name (for new profiles):", placeholder="e.g. Alex Morgan", key="ig_p_name")
                    p_pref = st.text_input("Preferred User ID (Optional):", placeholder="e.g. amorgan", key="ig_p_pref")
                    p_role = st.selectbox("Designated Level:", ["CRO Level (Executive)", "Senior Analyst Level", "Credit Underwriting Manager", "Portfolio Risk Specialist", "Reviewer Level"], index=1, key="ig_p_role")
                    
                    if "phone_otp" not in st.session_state:
                        st.session_state["phone_otp"] = None
                    
                    if st.button("Request Security Code", use_container_width=True, key="ig_btn_req_otp"):
                        if p_num.strip():
                            import random
                            st.session_state["phone_otp"] = str(random.randint(100000, 999999))
                            st.session_state["phone_target"] = p_num.strip()
                            st.info(f"🔒 **Verification Code**: Your 6-digit access code is **`{st.session_state['phone_otp']}`**")
                        else:
                            st.error("Please enter a valid phone number.")

                    if st.session_state.get("phone_otp"):
                        p_code = st.text_input("Enter 6-digit code:", key="ig_p_code")
                        if st.button("Verify Code & Log In", type="primary", use_container_width=True, key="ig_btn_p_verify"):
                            if p_code.strip() == st.session_state["phone_otp"]:
                                u_rec = authenticate_or_register_contact(st.session_state["phone_target"], full_name=p_name, role=p_role, preferred_id=p_pref)
                                if u_rec:
                                    st.session_state["current_user"] = u_rec
                                    st.session_state["phone_otp"] = None
                                    st.session_state["social_mode"] = None
                                    st.rerun()
                            else:
                                st.error("Incorrect verification code.")

            # Forgot Password link
            st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)
            if st.button("Forgot password?", use_container_width=True, key="ig_link_forgot"):
                st.session_state["auth_view"] = "forgot"
                st.rerun()

            # Secondary Bottom Card (Instagram style)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="ig-bottom-card">
                Don't have an account?
            </div>
            """, unsafe_allow_html=True)
            if st.button("Sign Up", use_container_width=True, key="ig_btn_go_signup"):
                st.session_state["auth_view"] = "signup"
                st.rerun()

        # =====================================================================
        # VIEW 2: SIGN UP (INSTAGRAM / SNAPCHAT STYLE)
        # =====================================================================
        elif auth_view == "signup":
            st.markdown("""
            <div class="ig-auth-card">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 64px; height: 64px; border-radius: 20px; background: linear-gradient(45deg, #F58529, #FEDA77, #DD2A7B, #8134AF, #515BD4); box-shadow: 0 4px 18px rgba(221, 42, 123, 0.35); margin-bottom: 12px;">
                    <span style="font-size: 32px;">🛡️</span>
                </div>
                <h1 style="font-size: 2.3rem; font-weight: 850; letter-spacing: -0.8px; margin: 0; background: linear-gradient(90deg, #2563EB 0%, #7C3AED 50%, #EC4899 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">CreditLens</h1>
                <p style="color: #64748B; font-size: 0.86rem; margin-top: 4px; margin-bottom: 16px; font-weight: 500;">Sign up to view portfolios, analyze risk tiers, and model stress scenarios.</p>
            </div>
            """, unsafe_allow_html=True)

            su_col1, su_col2 = st.columns(2)
            with su_col1:
                if st.button("🔴 Google Sign Up", use_container_width=True, key="ig_su_g"):
                    st.session_state["social_mode"] = "Google"
                    st.session_state["auth_view"] = "login"
                    st.rerun()
            with su_col2:
                if st.button("🍏 Apple Sign Up", use_container_width=True, key="ig_su_a"):
                    st.session_state["social_mode"] = "Apple"
                    st.session_state["auth_view"] = "login"
                    st.rerun()

            st.markdown("""
            <div style="display:flex; align-items:center; margin:16px 0 14px 0; color:#8E8E8E; font-size:0.74rem; font-weight:700;">
                <div style="flex:1; height:1px; background:#E2E8F0;"></div>
                <span style="padding:0 12px; color:#94A3B8;">OR SIGN UP WITH DETAILS</span>
                <div style="flex:1; height:1px; background:#E2E8F0;"></div>
            </div>
            """, unsafe_allow_html=True)

            su_name = st.text_input("Full Display Name:", placeholder="e.g. Sarah Jenkins", key="ig_su_name")
            su_user = st.text_input("Choose Username / ID:", placeholder="e.g. sjenkins", key="ig_su_user")
            su_email = st.text_input("Work Email Address:", placeholder="e.g. sjenkins@bank.internal", key="ig_su_email")
            su_phone = st.text_input("Mobile Phone (Optional):", placeholder="e.g. +1-555-0199", key="ig_su_phone")
            su_pw = st.text_input("Choose Password:", type="password", placeholder="At least 4 characters", key="ig_su_pw")
            su_role = st.selectbox("Designated Institutional Level:", [
                "CRO Level (Executive)",
                "Senior Analyst Level",
                "Credit Underwriting Manager",
                "Portfolio Risk Specialist",
                "Reviewer Level"
            ], index=1, key="ig_su_role")

            if st.button("Sign Up", type="primary", use_container_width=True, key="ig_btn_submit_signup"):
                if not su_name or not su_user or not su_pw:
                    st.error("Please fill in your name, desired username, and password.")
                else:
                    ok, msg = register_user(su_user, su_pw, su_name, su_role, su_email, su_phone)
                    if ok:
                        st.success(f"✅ {msg} Redirecting to login...")
                        st.session_state["auth_view"] = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="ig-bottom-card">
                Have an account?
            </div>
            """, unsafe_allow_html=True)
            if st.button("Log In", use_container_width=True, key="ig_btn_back_login"):
                st.session_state["auth_view"] = "login"
                st.rerun()

        # =====================================================================
        # VIEW 3: FORGOT PASSWORD (INSTAGRAM TROUBLE LOGGING IN STYLE)
        # =====================================================================
        elif auth_view == "forgot":
            st.markdown("""
            <div class="ig-auth-card">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 68px; height: 68px; border-radius: 50%; border: 2px solid #CBD5E1; margin-bottom: 12px; font-size: 32px;">
                    🔒
                </div>
                <h3 style="margin: 0; font-weight: 800; font-size: 1.3rem;">Trouble Logging In?</h3>
                <p style="color: #64748B; font-size: 0.85rem; margin-top: 6px; margin-bottom: 18px;">Enter your username, email, or contact number to reset your password and recover your account.</p>
            </div>
            """, unsafe_allow_html=True)

            fg_ident = st.text_input("Username, Email, or Contact Number:", placeholder="e.g. admin or analyst@creditlens.internal", key="ig_fg_ident")
            fg_new = st.text_input("New Password:", type="password", placeholder="At least 4 characters", key="ig_fg_new")
            fg_conf = st.text_input("Confirm New Password:", type="password", placeholder="Re-type new password", key="ig_fg_conf")

            if st.button("Reset Password", type="primary", use_container_width=True, key="ig_btn_reset_pw"):
                if not fg_ident or not fg_new:
                    st.error("Please fill in all fields.")
                elif fg_new != fg_conf:
                    st.error("New passwords do not match.")
                else:
                    ok, msg = reset_password_forgot(fg_ident, fg_new)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.info("👉 Redirecting to Log In...")
                        st.session_state["auth_view"] = "login"
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="ig-bottom-card">
                Remember your credentials?
            </div>
            """, unsafe_allow_html=True)
            if st.button("Back to Login", use_container_width=True, key="ig_btn_back_login_fg"):
                st.session_state["auth_view"] = "login"
                st.rerun()


# =============================================================================
# REUSABLE PORTFOLIO DASHBOARD (EXCEL SHEET CONTENT)
# =============================================================================
def render_portfolio_sheet(
    df: pd.DataFrame, 
    sheet_title: str,
    selected_tiers=None,
    delinq_filter="All Accounts",
    credit_range=(10000, 1000000),
    stress_scenario="Baseline (Normal Conditions)"
):
    """
    Renders the complete interactive analytics dashboard for a specific portfolio sheet
    with live sidebar slicing, stress modeling, and high-contrast dark/light charts.
    """
    # 0. Apply Real-Time Interactive Slicing from Sidebar
    filtered_df = df.copy()

    if selected_tiers and "RISK_TIER" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["RISK_TIER"].isin(selected_tiers)]

    if "PAY_0" in filtered_df.columns:
        if delinq_filter == "Delinquent Only (>= 1 Mo)":
            filtered_df = filtered_df[filtered_df["PAY_0"] > 0]
        elif delinq_filter == "Non-Delinquent Only":
            filtered_df = filtered_df[filtered_df["PAY_0"] <= 0]

    if "LIMIT_BAL" in filtered_df.columns and credit_range:
        filtered_df = filtered_df[
            (filtered_df["LIMIT_BAL"] >= credit_range[0]) & 
            (filtered_df["LIMIT_BAL"] <= credit_range[1])
        ]

    # Stress Multipliers
    stress_mult = 1.0
    if "Inflation" in stress_scenario:
        stress_mult = 1.15
    elif "Severe" in stress_scenario:
        stress_mult = 1.40
    elif "Liquidity" in stress_scenario:
        stress_mult = 1.25

    if len(filtered_df) == 0:
        st.warning("⚠️ No borrower accounts match the active sidebar filter criteria. Please broaden your selection in the left sidebar.")
        return

    # Slicing Status Indicator
    f_pct = (len(filtered_df) / max(len(df), 1)) * 100
    st.markdown(f"""
    <div style="font-size: 0.82rem; margin-bottom: 14px; padding: 7px 14px; background: rgba(37, 99, 235, 0.08); border-left: 3px solid #2563EB; border-radius: 6px;">
        🎯 <b>Active Slicing View:</b> Displaying <b>{len(filtered_df):,}</b> of <b>{len(df):,}</b> accounts (<b>{f_pct:.1f}%</b>) &nbsp;|&nbsp; Macro Mode: <b>{stress_scenario}</b>
    </div>
    """, unsafe_allow_html=True)

    kpis = get_portfolio_kpis(filtered_df)
    tier_df = get_risk_tier_breakdown(filtered_df)
    delinq_df = get_delinquency_transition(filtered_df)
    util_df = get_utilization_risk_matrix(filtered_df)

    # 1. Executive BAN Scorecards
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Active Borrowers</div>
            <div class="kpi-value">{kpis['total_borrowers']:,}</div>
            <div class="kpi-sub">Total credit exposure count</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Exposure</div>
            <div class="kpi-value">NT$ {kpis['total_exposure']/1e9:.2f}B</div>
            <div class="kpi-sub">Avg Limit: NT$ {kpis['avg_credit_line']:,.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Portfolio Mean Score</div>
            <div class="kpi-value">{kpis['portfolio_avg_score']:.0f}</div>
            <div class="kpi-sub">FICO Scale (300 - 850)</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Actual Default Rate</div>
            <div class="kpi-value">{kpis['actual_default_rate']*100:.1f}%</div>
            <div class="kpi-sub">Stressed PD: {min(kpis['expected_default_rate']*stress_mult*100, 100.0):.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        flagged_stressed = int(kpis['ews_flagged_count'] * stress_mult)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">EWS Alerts Active</div>
            <div class="kpi-value" style="color: #DC2626;">{flagged_stressed:,}</div>
            <div class="kpi-sub">{kpis['ews_flagged_rate']*100:.1f}% under surveillance</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 2. Risk Tier Exposure & Distributions
    r1_col1, r1_col2 = st.columns([1, 1.1])
    with r1_col1:
        st.markdown("##### 🍩 Portfolio Volume by Risk Tier")
        fig_pie = px.pie(
            tier_df,
            names="RISK_TIER",
            values="borrower_count",
            color="RISK_TIER",
            color_discrete_map={
                "Prime": "#10B981",
                "Near-Prime": "#3B82F6",
                "Subprime": "#F59E0B",
                "High Risk": "#EF4444"
            },
            hole=0.42
        )
        fig_pie.update_traces(textinfo="percent+label", pull=[0, 0, 0, 0.08])
        fig_pie.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with r1_col2:
        st.markdown("##### 📊 Credit Exposure & Default Escalation by Tier")
        fig_exp = go.Figure()
        fig_exp.add_trace(go.Bar(
            x=tier_df["RISK_TIER"],
            y=tier_df["total_exposure"] / 1e6,
            name="Exposure (NT$ Millions)",
            marker_color="#2563EB",
            yaxis="y"
        ))
        fig_exp.add_trace(go.Scatter(
            x=tier_df["RISK_TIER"],
            y=tier_df["actual_default_pct"],
            name="Default Rate (%)",
            marker_color="#DC2626",
            mode="lines+markers",
            yaxis="y2",
            line=dict(width=3)
        ))
        fig_exp.update_layout(
            yaxis=dict(title="Exposure (NT$M)"),
            yaxis2=dict(title="Default Rate (%)", overlaying="y", side="right"),
            legend=dict(x=0.05, y=0.95),
            margin=dict(t=20, b=20, l=20, r=20),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_exp, use_container_width=True)

    # 3. Delinquency Surveillance & Utilization
    r2_col1, r2_col2 = st.columns(2)
    with r2_col1:
        st.markdown("##### ⚠️ Delinquency Severity vs Default Rate")
        fig_del = px.bar(
            delinq_df,
            x="STATUS_LABEL",
            y="default_rate_pct",
            color="default_rate_pct",
            color_continuous_scale="Reds",
            labels={"STATUS_LABEL": "Payment Status", "default_rate_pct": "Default Rate (%)"}
        )
        fig_del.update_layout(
            height=300, 
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_del, use_container_width=True)

    with r2_col2:
        st.markdown("##### 📈 Credit Utilization Strain vs Default Rate")
        fig_ut = px.bar(
            util_df,
            x="UTIL_BUCKET",
            y="default_rate_pct",
            color="default_rate_pct",
            color_continuous_scale="Blues",
            labels={"UTIL_BUCKET": "Utilization Bucket", "default_rate_pct": "Default Rate (%)"}
        )
        fig_ut.update_layout(
            height=300, 
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_ut, use_container_width=True)

    # 4. What-If Simulator & Borrower Dossier Sandbox
    with st.expander(f"🧮 Interactive What-If Stress Simulator for {sheet_title}", expanded=False):
        sim_c1, sim_c2 = st.columns([1, 1])
        with sim_c1:
            s_lim = st.number_input(f"Simulated Limit (NTD) - {sheet_title}:", min_value=10000, max_value=1000000, value=120000, step=10000, key=f"s_lim_{sheet_title}")
            s_bill = st.number_input(f"Current Statement Balance - {sheet_title}:", min_value=0, max_value=1000000, value=95000, step=5000, key=f"s_bill_{sheet_title}")
            s_delay = st.slider(f"Payment Delay (Months Past Due) - {sheet_title}:", min_value=0, max_value=6, value=1, key=f"s_delay_{sheet_title}")

        with sim_c2:
            u_ratio = min(s_bill / max(s_lim, 1), 3.0)
            l_odds = -1.6 + (s_delay * 0.95) + ((u_ratio - 0.7) * 1.5 if u_ratio > 0.7 else 0)
            p_val = float(np.clip(1.0 / (1.0 + np.exp(-l_odds)), 0.02, 0.98))
            sc_val = int(np.clip(np.round(850.0 - (p_val * 550.0)), 300, 850))
            t_val = classify_risk_tier(sc_val)

            st.write(f"• **Simulated Credit Score:** `{sc_val}` ({t_val})")
            st.write(f"• **Probability of Default:** `{p_val*100:.1f}%`")
            st.write(f"• **Utilization Strain:** `{u_ratio*100:.1f}%`")
            st.info(f"**Policy Action:** {assign_recommended_action({'RISK_TIER': t_val, 'AVG_UTILIZATION_RATE': u_ratio, 'MAX_DELINQUENCY_MONTHS': s_delay})}")

    # 5. Distressed Watchlist & Export
    st.markdown("##### 🚨 Top Distressed Accounts Watchlist")
    wl = get_watchlist(filtered_df, top_n=15)
    disp_cols = ["ID", "LIMIT_BAL", "BILL_AMT1", "AVG_UTILIZATION_RATE", "PAY_0", "CREDIT_RISK_SCORE", "RISK_TIER", "PREDICTED_PD", "RECOMMENDED_ACTION"]
    disp_cols = [c for c in disp_cols if c in wl.columns]

    st.dataframe(
        wl[disp_cols].rename(columns={
            "ID": "Client ID",
            "LIMIT_BAL": "Credit Limit",
            "BILL_AMT1": "Statement Bill",
            "AVG_UTILIZATION_RATE": "Avg Util",
            "PAY_0": "Delay (Mo)",
            "CREDIT_RISK_SCORE": "Risk Score",
            "RISK_TIER": "Risk Tier",
            "PREDICTED_PD": "Default Prob",
            "RECOMMENDED_ACTION": "Action Recommendation"
        }),
        use_container_width=True,
        hide_index=True
    )

    csv_data = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Download Scored CSV ({len(filtered_df):,} records)",
        data=csv_data,
        file_name=f"{sheet_title.lower().replace(' ', '_')}_scored.csv",
        mime="text/csv",
        key=f"dl_{sheet_title}"
    )


# =============================================================================
# MAIN MULTI-USER & MULTI-DATASET APP CONTROLLER
# =============================================================================
def main():
    # Session state for user authentication
    if "current_user" not in st.session_state:
        # Default to admin so user immediately sees the working dashboard!
        st.session_state["current_user"] = get_user_by_username("admin") or authenticate_user("admin", "password123")

    # Session state for workbook sheets (datasets)
    if "workbook_sheets" not in st.session_state:
        st.session_state["workbook_sheets"] = dict(DEFAULT_SHEETS)

    # 1. If not logged in, show login/signup screen
    if st.session_state["current_user"] is None:
        render_auth_modal()
        return

    # 2. Logged in View
    current_u = st.session_state["current_user"]

    # =========================================================================
    # SIDEBAR: Institutional Risk Command Center & Interactive Slicing
    # =========================================================================
    st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=48)
    st.sidebar.markdown("### CreditLens Risk OS")
    st.sidebar.caption("Institutional Credit Intelligence · Engine v2.4")

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🎯 Interactive Portfolio Slicers")

    selected_tiers = st.sidebar.multiselect(
        "Filter by Risk Tier:",
        options=["Prime", "Near-Prime", "Subprime", "High Risk"],
        default=["Prime", "Near-Prime", "Subprime", "High Risk"],
        help="Slice the portfolio data hand-in-hand in real-time"
    )

    delinq_filter = st.sidebar.radio(
        "Delinquency Status:",
        options=["All Accounts", "Delinquent Only (>= 1 Mo)", "Non-Delinquent Only"],
        index=0
    )

    credit_range = st.sidebar.slider(
        "Credit Limit Range (NT$):",
        min_value=10000,
        max_value=1000000,
        value=(10000, 1000000),
        step=25000,
        format="NT$ %d"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⚡ Macro Stress Testing")
    stress_scenario = st.sidebar.selectbox(
        "Macro Scenario Preset:",
        [
            "Baseline (Normal Conditions)",
            "Inflation & Rate Hike (+15% Strain)",
            "Severe Recession (+40% Default Shock)",
            "Liquidity Crunch (+25% Spike)"
        ]
    )

    with st.sidebar.expander("🏛️ Basel III Capital Reserve Tool"):
        st.caption("Standardized Regulatory Capital Requirement Calculator (CAR 12.5% Target).")
        target_car = st.slider("Target CAR (%):", 8.0, 18.0, 12.5, 0.5)
        st.info(f"Target Reserve Adequacy: **{target_car:.1f}%** applied to risk-weighted assets (RWA).")

    with st.sidebar.expander("📥 Executive Export Center"):
        st.caption("Download reports and financial models for C-suite presentation.")
        excel_path = os.path.join(BASE_DIR, "excel", "CreditLens_Portfolio_Model.xlsx")
        if os.path.exists(excel_path):
            with open(excel_path, "rb") as ef:
                st.download_button(
                    "📊 Download Portfolio Model (.xlsx)",
                    data=ef.read(),
                    file_name="CreditLens_Executive_Model.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        st.caption("Includes ECL schedule, transition matrix, and sensitivity sheets.")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        <div style="font-size: 0.72rem; color: #94A3B8; line-height: 1.45;">
            🟢 <b>Champion Model:</b> Random Forest<br>
            🎯 <b>ROC-AUC:</b> 0.7781 · <b>KS:</b> 0.4257<br>
            💾 <b>Database:</b> SQLite (30,000 Records)<br>
            🔒 <b>Session:</b> Verified Local Instance
        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================================
    # TOP HEADER & TOP-RIGHT PROFILE / ID ACTION BAR
    # =========================================================================
    col_top1, col_top2 = st.columns([1.5, 1.5])
    with col_top1:
        st.markdown('<div class="main-header">CreditLens Portfolio Workbook</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Institutional Credit Risk Intelligence · Excel-Style Multi-Dataset Worksheets</div>', unsafe_allow_html=True)

    with col_top2:
        u_display_name = current_u['full_name']
        u_username = f"@{current_u['username']}"
        u_level = current_u.get('role', 'Risk Analyst')

        # Top-right encircled initial / profile photo badge: (user name , user id , cro level)
        u_avatar_html = render_avatar_circle(current_u, size=36, font_size=0.95)
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 6px;">
            <span class="user-profile-badge" style="display: inline-flex; align-items: center; gap: 8px; padding: 4px 14px 4px 6px; border-radius: 24px;">
                {u_avatar_html}
                <span style="font-weight: 750; font-size: 0.88rem;">{u_display_name}</span>
                <span style="color: #94A3B8;">|</span>
                <code>{u_username}</code>
                <span style="color: #94A3B8;">|</span>
                <span style="color:#2563EB; font-weight:700;">{u_level}</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

        c_act1, c_act2 = st.columns([1.8, 1])
        with c_act1:
            with st.popover("⚙️ Profile & ID Management", use_container_width=True):
                lg_avatar_html = render_avatar_circle(current_u, size=64, font_size=1.8)
                st.markdown(f"""
                <div style="text-align: center; padding: 6px 0 10px 0;">
                    {lg_avatar_html}
                    <div style="font-weight: 800; font-size: 1.05rem; margin-top: 8px; color: var(--text-headline);">{u_display_name}</div>
                    <div style="font-size: 0.82rem; color: #64748B;"><code>{u_username}</code> &nbsp;•&nbsp; <b>{u_level}</b></div>
                </div>
                """, unsafe_allow_html=True)

                # Custom Profile Picture Uploader
                with st.expander("📸 Add / Change Profile Picture", expanded=False):
                    st.caption("Upload your custom photo to display encircled on the top right.")
                    pfp_upload = st.file_uploader("Upload Profile Image (PNG, JPG):", type=["png", "jpg", "jpeg"], key="pfp_uploader_widget")
                    if pfp_upload is not None:
                        try:
                            import io, base64
                            from PIL import Image
                            p_img = Image.open(pfp_upload)
                            if p_img.mode not in ("RGB", "RGBA"):
                                p_img = p_img.convert("RGBA")
                            pw, ph = p_img.size
                            p_min = min(pw, ph)
                            p_img = p_img.crop(((pw - p_min)//2, (ph - p_min)//2, (pw + p_min)//2, (ph + p_min)//2))
                            p_img.thumbnail((256, 256), Image.Resampling.LANCZOS)
                            p_buf = io.BytesIO()
                            p_img.save(p_buf, format="PNG", optimize=True)
                            b64_str = f"data:image/png;base64,{base64.b64encode(p_buf.getvalue()).decode('utf-8')}"
                            ok, msg = update_profile_avatar(current_u["username"], b64_str)
                            if ok:
                                st.session_state["current_user"]["avatar_data"] = b64_str
                                st.success("✅ Profile picture updated successfully!")
                                st.rerun()
                            else:
                                st.error(msg)
                        except Exception as p_err:
                            st.error(f"Image error: {p_err}")

                    if current_u.get("avatar_data"):
                        if st.button("🗑️ Remove Profile Photo (Restore Encircled Initial)", use_container_width=True, key="btn_remove_pfp"):
                            update_profile_avatar(current_u["username"], "")
                            st.session_state["current_user"]["avatar_data"] = ""
                            st.success("Profile photo removed! Initial circle restored.")
                            st.rerun()

                st.divider()

                pop_t1, pop_t2, pop_t3 = st.tabs(["👥 Switch ID", "🔑 Change Password", "✨ Create ID"])

                with pop_t1:
                    st.markdown("##### Switch Profile Account")
                    clean_users = list_users(exclude_temp=True)
                    u_map = {f"{u['full_name']} (@{u['username']} · {u['role']})": u['username'] for u in clean_users}

                    cur_label = next((k for k, v in u_map.items() if v == current_u["username"]), list(u_map.keys())[0] if u_map else "")
                    sel_acc = st.selectbox("Select Account:", list(u_map.keys()), index=list(u_map.keys()).index(cur_label) if cur_label in u_map else 0, key="top_sel_acc")

                    if st.button("Switch to Selected Account", type="primary", use_container_width=True, key="top_btn_switch"):
                        target_user = u_map[sel_acc]
                        u_target = get_user_by_username(target_user)
                        if u_target:
                            st.session_state["current_user"] = u_target
                            st.rerun()
                        else:
                            st.error(f"Could not load account details for @{target_user}.")

                with pop_t2:
                    st.markdown("##### Change Your Passkey / Password")
                    with st.form("top_change_pw_form", clear_on_submit=True):
                        tp_curr = st.text_input("Current Password:", type="password", key="top_cpw_curr")
                        tp_new = st.text_input("New Password:", type="password", key="top_cpw_new")
                        tp_conf = st.text_input("Confirm New Password:", type="password", key="top_cpw_conf")
                        tp_sub = st.form_submit_button("Update Password", use_container_width=True)

                        if tp_sub:
                            if not tp_curr or not tp_new:
                                st.error("Please fill in all fields.")
                            elif tp_new != tp_conf:
                                st.error("New passwords do not match.")
                            elif not authenticate_user(current_u["username"], tp_curr):
                                st.error("Current password incorrect.")
                            else:
                                ok, msg = update_password(current_u["username"], tp_new)
                                if ok:
                                    st.success(f"✅ {msg}")
                                else:
                                    st.error(f"❌ {msg}")

                with pop_t3:
                    st.markdown("##### Register a New User ID")
                    with st.form("top_reg_form", clear_on_submit=True):
                        reg_name = st.text_input("Full Display Name:", placeholder="e.g. Elena Rostova", key="top_reg_name")
                        reg_user = st.text_input("Username / ID:", placeholder="e.g. erostova", key="top_reg_user")
                        reg_role = st.selectbox("Organizational Level:", [
                            "CRO Level (Executive)",
                            "Senior Analyst Level",
                            "Credit Underwriting Manager",
                            "Portfolio Risk Specialist",
                            "Reviewer Level"
                        ], key="top_reg_role")
                        reg_pw = st.text_input("Password:", type="password", placeholder="Min 4 characters", key="top_reg_pw")
                        reg_sub = st.form_submit_button("Create Account ID", use_container_width=True)

                        if reg_sub:
                            ok, msg = register_user(reg_user, reg_pw, reg_name, reg_role)
                            if ok:
                                st.success(f"✅ {msg} You can now switch to @{reg_user.lower()}.")
                            else:
                                st.error(f"❌ {msg}")

        with c_act2:
            if st.button("🚪 Sign Out", use_container_width=True, key="top_btn_signout"):
                st.session_state["current_user"] = None
                st.rerun()

    # =========================================================================
    # EXCEL-STYLE MULTI-DATASET TABS (SHEET 1, SHEET 2, SHEET 3, + ADD SHEET)
    # =========================================================================
    sheet_names = list(st.session_state["workbook_sheets"].keys()) + ["➕ Add New Dataset Sheet"]
    workbook_tabs = st.tabs(sheet_names)

    # Render each existing dataset sheet
    for idx, (sheet_title, path_or_df) in enumerate(st.session_state["workbook_sheets"].items()):
        with workbook_tabs[idx]:
            st.markdown(f"### {sheet_title}")
            if isinstance(path_or_df, pd.DataFrame):
                sheet_df = path_or_df
            else:
                sheet_df = load_dataset_from_disk(path_or_df)
            render_portfolio_sheet(
                sheet_df, 
                sheet_title,
                selected_tiers=selected_tiers,
                delinq_filter=delinq_filter,
                credit_range=credit_range,
                stress_scenario=stress_scenario
            )

    # =========================================================================
    # TAB: ➕ ADD NEW DATASET SHEET (CREATE NEW EXCEL SHEET TAB)
    # =========================================================================
    with workbook_tabs[-1]:
        st.subheader("➕ Create a New Dataset Dashboard Sheet")
        st.write("Upload any CSV or Excel file to add a brand-new dataset sheet tab to your CreditLens workbook, just like adding a new sheet in Microsoft Excel!")

        col_new1, col_new2 = st.columns([1.2, 1])

        with col_new1:
            new_sheet_name = st.text_input("New Sheet Tab Name:", placeholder="e.g. 📑 Q4 Auto & Personal Loans", value="📑 Custom Loan Tape")
            new_file = st.file_uploader("Upload Dataset (.csv or .xlsx):", type=["csv", "xlsx"], key="new_sheet_uploader")

        with col_new2:
            st.info("""
            **📋 Dynamic Column Mapper:**
            CreditLens will automatically detect and score:
            - **Credit Limit / Loan Amount**
            - **Current Billed Balance**
            - **Repayment Delay (Months Past Due)**
            - Calculates FICO 300–850 scores & Risk Tiers instantly!
            """)

        if new_file is not None:
            try:
                if new_file.name.endswith(".csv"):
                    uploaded_df = pd.read_csv(new_file)
                else:
                    uploaded_df = pd.read_excel(new_file)

                st.success(f"File `{new_file.name}` parsed ({len(uploaded_df):,} rows, {len(uploaded_df.columns)} columns).")
                st.dataframe(uploaded_df.head(3), use_container_width=True)

                st.markdown("##### ⚙️ Quick Column Mapping")
                cols = ["(Auto-Detect / None)"] + list(uploaded_df.columns)
                cm1, cm2 = st.columns(2)

                def match_col(keyword_list):
                    for c in uploaded_df.columns:
                        for k in keyword_list:
                            if k.lower() in str(c).lower():
                                return cols.index(c)
                    return 0

                with cm1:
                    m_lim = st.selectbox("Credit Limit / Amount Column:", cols, index=match_col(["limit", "loan_amt", "amount", "bal"]), key="m_lim_add")
                    m_bill = st.selectbox("Current Balance / Bill Column:", cols, index=match_col(["bill", "balance", "outstanding"]), key="m_bill_add")

                with cm2:
                    m_pay = st.selectbox("Delay / Delinquency Column:", cols, index=match_col(["pay_0", "status", "delinq", "delay", "dpd"]), key="m_pay_add")
                    m_target = st.selectbox("Default Flag (Optional):", cols, index=match_col(["default", "target", "bad", "loss"]), key="m_target_add")

                if st.button("🚀 Create & Add New Sheet to Workbook", type="primary", use_container_width=True):
                    with st.spinner("Scoring portfolio and generating new dashboard sheet..."):
                        processed_df = pd.DataFrame()
                        processed_df["ID"] = np.arange(1, len(uploaded_df) + 1)
                        processed_df["LIMIT_BAL"] = pd.to_numeric(uploaded_df[m_lim], errors="coerce").fillna(50000.0) if m_lim != "(Auto-Detect / None)" else 50000.0
                        processed_df["BILL_AMT1"] = pd.to_numeric(uploaded_df[m_bill], errors="coerce").fillna(0.0) if m_bill != "(Auto-Detect / None)" else processed_df["LIMIT_BAL"] * 0.45
                        processed_df["PAY_0"] = pd.to_numeric(uploaded_df[m_pay], errors="coerce").fillna(0).astype(int) if m_pay != "(Auto-Detect / None)" else 0
                        processed_df["DEFAULT_NEXT_MONTH"] = pd.to_numeric(uploaded_df[m_target], errors="coerce").fillna(0).astype(int) if m_target != "(Auto-Detect / None)" else (processed_df["PAY_0"] >= 2).astype(int)
                        processed_df["AGE"] = 35

                        # Calculated features
                        processed_df["AVG_UTILIZATION_RATE"] = (processed_df["BILL_AMT1"].clip(lower=0) / processed_df["LIMIT_BAL"].clip(lower=1)).clip(upper=3.0)
                        processed_df["MAX_DELINQUENCY_MONTHS"] = processed_df["PAY_0"].clip(lower=0)

                        # PD & 300-850 Score
                        l_odds = -1.6 + (processed_df["PAY_0"].clip(lower=0) * 0.95) + ((processed_df["AVG_UTILIZATION_RATE"] - 0.7).clip(lower=0) * 1.5)
                        pd_arr = 1.0 / (1.0 + np.exp(-l_odds))
                        processed_df["PREDICTED_PD"] = np.round(np.clip(pd_arr, 0.02, 0.98), 4)
                        processed_df["CREDIT_RISK_SCORE"] = pd_to_credit_score(processed_df["PREDICTED_PD"])
                        processed_df["RISK_TIER"] = processed_df["CREDIT_RISK_SCORE"].apply(classify_risk_tier)
                        processed_df["EARLY_WARNING_FLAG"] = ((processed_df["PAY_0"] >= 1) | (processed_df["AVG_UTILIZATION_RATE"] >= 0.80)).astype(int)
                        processed_df["RECOMMENDED_ACTION"] = processed_df.apply(assign_recommended_action, axis=1)

                        # Add sheet to workbook dictionary
                        final_tab_title = new_sheet_name.strip() or f"📑 Dataset Sheet {len(st.session_state['workbook_sheets'])+1}"
                        st.session_state["workbook_sheets"][final_tab_title] = processed_df

                        st.success(f"🎉 Created '{final_tab_title}' with {len(processed_df):,} accounts! Your new sheet tab is ready.")
                        st.rerun()

            except Exception as e:
                st.error(f"Error creating dataset sheet: {e}")


if __name__ == "__main__":
    main()
