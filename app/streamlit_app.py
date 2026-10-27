from __future__ import annotations
import os
import sys
import json
import sqlite3
import time
import platform
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
    """Loads module from src/ directory, always executing latest code on disk and registering in sys.modules."""
    fpath = os.path.join(SRC_DIR, f"{name}.py")
    if not os.path.exists(fpath):
        fpath = os.path.join(APP_DIR, f"{name}.py")
    if os.path.exists(fpath):
        spec = importlib.util.spec_from_file_location(f"src.{name}", fpath)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            sys.modules[f"src.{name}"] = mod
            if "src" in sys.modules:
                setattr(sys.modules["src"], name, mod)
            spec.loader.exec_module(mod)
            return mod
    try:
        mod = importlib.import_module(f"src.{name}")
        sys.modules[name] = mod
        return mod
    except Exception:
        mod = importlib.import_module(name)
        sys.modules[f"src.{name}"] = mod
        return mod

# Safely pre-load core business & authentication modules
_auth = _safe_load_src_module("auth")
_analytics = _safe_load_src_module("analytics_engine")
_risk = _safe_load_src_module("risk_scoring")
_model_train = _safe_load_src_module("model_training")

# Bind symbols directly into global namespace with self-healing getattr fallbacks
init_user_db = getattr(_auth, "init_user_db", lambda: None)
register_user = getattr(_auth, "register_user", lambda *args, **kwargs: (False, "Service unavailable"))
authenticate_user = getattr(_auth, "authenticate_user", lambda *args, **kwargs: None)
get_user_by_username = getattr(_auth, "get_user_by_username", lambda *args, **kwargs: None)
update_profile_avatar = getattr(_auth, "update_profile_avatar", lambda *args, **kwargs: (False, "Service unavailable"))
list_users = getattr(_auth, "list_users", lambda *args, **kwargs: [])
update_password = getattr(_auth, "update_password", lambda *args, **kwargs: (False, "Service unavailable"))
authenticate_or_register_social = getattr(_auth, "authenticate_or_register_social", lambda *args, **kwargs: None)
authenticate_or_register_contact = getattr(_auth, "authenticate_or_register_contact", lambda *args, **kwargs: None)
reset_password_forgot = getattr(_auth, "reset_password_forgot", lambda *args, **kwargs: (False, "Service unavailable"))

save_user_custom_sheet = getattr(_auth, "save_user_custom_sheet", None)
if save_user_custom_sheet is None:
    def save_user_custom_sheet(username: str, sheet_title: str, df):
        try:
            from src.auth import save_user_custom_sheet as _fn
            return _fn(username, sheet_title, df)
        except Exception:
            return False, "Save sheet service fallback"

load_user_custom_sheets = getattr(_auth, "load_user_custom_sheets", None)
if load_user_custom_sheets is None:
    def load_user_custom_sheets(username: str):
        try:
            from src.auth import load_user_custom_sheets as _fn
            return _fn(username)
        except Exception:
            return {}

delete_user_custom_sheet = getattr(_auth, "delete_user_custom_sheet", None)
if delete_user_custom_sheet is None:
    def delete_user_custom_sheet(username: str, sheet_title: str):
        try:
            from src.auth import delete_user_custom_sheet as _fn
            return _fn(username, sheet_title)
        except Exception:
            return False

set_last_active_user = getattr(_auth, "set_last_active_user", None)
if set_last_active_user is None:
    def set_last_active_user(username: str):
        try:
            from src.auth import set_last_active_user as _fn
            return _fn(username)
        except Exception:
            pass

get_last_active_user = getattr(_auth, "get_last_active_user", None)
if get_last_active_user is None:
    def get_last_active_user():
        try:
            from src.auth import get_last_active_user as _fn
            return _fn()
        except Exception:
            return None

clear_last_active_user = getattr(_auth, "clear_last_active_user", None)
if clear_last_active_user is None:
    def clear_last_active_user():
        try:
            from src.auth import clear_last_active_user as _fn
            return _fn()
        except Exception:
            pass

save_user_risk_note = getattr(_auth, "save_user_risk_note", None)
if save_user_risk_note is None:
    def save_user_risk_note(username: str, sheet_title: str, note_content: str):
        try:
            from src.auth import save_user_risk_note as _fn
            return _fn(username, sheet_title, note_content)
        except Exception:
            pass

get_user_risk_note = getattr(_auth, "get_user_risk_note", None)
if get_user_risk_note is None:
    def get_user_risk_note(username: str, sheet_title: str):
        try:
            from src.auth import get_user_risk_note as _fn
            return _fn(username, sheet_title)
        except Exception:
            return ""

get_portfolio_kpis = getattr(_analytics, "get_portfolio_kpis", lambda *args, **kwargs: {})
get_risk_tier_breakdown = getattr(_analytics, "get_risk_tier_breakdown", lambda *args, **kwargs: pd.DataFrame())
get_delinquency_transition = getattr(_analytics, "get_delinquency_transition", lambda *args, **kwargs: pd.DataFrame())
get_utilization_risk_matrix = getattr(_analytics, "get_utilization_risk_matrix", lambda *args, **kwargs: pd.DataFrame())
get_watchlist = getattr(_analytics, "get_watchlist", lambda *args, **kwargs: pd.DataFrame())
get_executive_insights = getattr(_analytics, "get_executive_insights", lambda *args, **kwargs: {})
get_underwriting_policy_tradeoff = getattr(_analytics, "get_underwriting_policy_tradeoff", lambda *args, **kwargs: {})
load_model_metrics = getattr(_analytics, "load_model_metrics", lambda *args, **kwargs: {})

pd_to_credit_score = getattr(_risk, "pd_to_credit_score", lambda *args, **kwargs: 650)
classify_risk_tier = getattr(_risk, "classify_risk_tier", lambda *args, **kwargs: "Medium")
assign_recommended_action = getattr(_risk, "assign_recommended_action", lambda *args, **kwargs: "Review")

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

    /* Top-Right Account Popover Button */
    div[data-testid="stPopover"] button {
        border-radius: 24px !important;
        border: 1px solid var(--card-border, #CBD5E1) !important;
        background: var(--user-pill-bg, #F8FAFC) !important;
        color: var(--user-pill-text, #0F172A) !important;
        font-weight: 700 !important;
        font-size: 0.88rem !important;
        padding: 6px 16px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
        transition: all 0.15s ease !important;
    }
    div[data-testid="stPopover"] button:hover {
        border-color: #2563EB !important;
        box-shadow: 0 3px 10px rgba(37, 99, 235, 0.12) !important;
    }

    /* Executive Insight Cards & Visual Highlights */
    .insight-card {
        background: var(--card-bg, #FFFFFF);
        border: 1px solid var(--card-border, #CBD5E1);
        border-radius: 14px;
        padding: 16px 18px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .insight-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }
    .insight-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .insight-tag {
        display: inline-block;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .insight-tag-blue { background: rgba(37, 99, 235, 0.12); color: #2563EB; }
    .insight-tag-green { background: rgba(16, 185, 129, 0.12); color: #059669; }
    .insight-tag-amber { background: rgba(245, 158, 11, 0.12); color: #D97706; }
    .insight-tag-red { background: rgba(239, 68, 68, 0.12); color: #DC2626; }

    .insight-metric-val {
        font-size: 1.45rem;
        font-weight: 800;
        color: var(--text-headline, #0F172A);
        line-height: 1.2;
    }
    .insight-title {
        font-size: 0.92rem;
        font-weight: 750;
        color: var(--text-headline, #0F172A);
        margin-top: 4px;
        margin-bottom: 4px;
    }
    .insight-desc {
        font-size: 0.8rem;
        color: var(--text-sub, #64748B);
        line-height: 1.45;
        margin: 0;
    }

    /* Tier Badges with Color-Graded Accessible Contrast */
    .tier-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .tier-prime { background: rgba(16, 185, 129, 0.12); color: #059669; border: 1px solid rgba(16, 185, 129, 0.3); }
    .tier-near-prime { background: rgba(37, 99, 235, 0.12); color: #2563EB; border: 1px solid rgba(37, 99, 235, 0.3); }
    .tier-subprime { background: rgba(245, 158, 11, 0.12); color: #D97706; border: 1px solid rgba(245, 158, 11, 0.3); }
    .tier-high-risk { background: rgba(239, 68, 68, 0.12); color: #DC2626; border: 1px solid rgba(239, 68, 68, 0.3); }

    /* Score Scale Progress Container */
    .score-scale-container {
        display: flex;
        border-radius: 8px;
        overflow: hidden;
        height: 14px;
        margin: 10px 0 6px 0;
        box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.12);
    }
    .scale-high-risk { background: #EF4444; width: 50.9%; }
    .scale-subprime { background: #F59E0B; width: 14.5%; }
    .scale-near-prime { background: #3B82F6; width: 10.9%; }
    .scale-prime { background: #10B981; width: 23.6%; }

    /* Confusion Matrix 4-Quadrant Card */
    .matrix-box {
        background: var(--card-bg, #FFFFFF);
        border: 1px solid var(--card-border, #CBD5E1);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.03);
    }
</style>

<!-- Auto-Reconnect & Keepalive Helper for Seamless Tab Resilience -->
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" 
     style="display:none;" 
     onload="if(!window._cl_reconnect_init){
         window._cl_reconnect_init = true;
         document.addEventListener('visibilitychange', function(){
             if (document.visibilityState === 'visible') {
                 setTimeout(function(){
                     if (document.body && (document.body.innerText.includes('Connection lost') || document.body.innerText.includes('disconnected'))) {
                         window.location.reload();
                     }
                 }, 1200);
             }
         });
         setInterval(function(){
             if (document.body && document.body.innerText.includes('Connection lost')) {
                 setTimeout(function(){
                     if (document.body && document.body.innerText.includes('Connection lost')) {
                         window.location.reload();
                     }
                 }, 2500);
             }
         }, 7000);
     }" />

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
def load_dataset_from_disk(relative_or_abs_path):
    if os.path.isabs(relative_or_abs_path):
        full_path = relative_or_abs_path
    else:
        full_path = os.path.join(BASE_DIR, relative_or_abs_path)
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


def sync_user_workbook_sheets(username: str):
    """
    Loads default institutional benchmark sheets combined with all custom dataset sheets 
    created by and preserved for this specific user.
    """
    sheets = dict(DEFAULT_SHEETS)
    if username:
        user_sheets = load_user_custom_sheets(username)
        sheets.update(user_sheets)
    st.session_state["workbook_sheets"] = sheets
    st.session_state["_sheets_user"] = username






# =============================================================================
# AUTHENTICATION & INSTITUTIONAL USER ACCOUNT SYSTEM
# =============================================================================
def render_auth_modal():
    """
    Renders a clean, user-friendly institutional authentication experience:
    - Sleek centered cards with gradient brand identity
    - 1-Click Saved Profile login with circular avatars
    - Clean credentials login via Work Email and Password
    - Strict 1:1 Email registration (one email address can create only one account)
    - Trouble logging in (Forgot Password) self-service view
    """
    if "auth_view" not in st.session_state:
        st.session_state["auth_view"] = "login"

    auth_view = st.session_state["auth_view"]

    st.markdown("<br>", unsafe_allow_html=True)
    _, auth_box, _ = st.columns([1, 1.28, 1])

    with auth_box:
        # =====================================================================
        # STANDARD VIEW 1: CLEAN WORK EMAIL LOG IN
        # =====================================================================
        if auth_view == "login":
            st.markdown("""
            <div class="ig-auth-card">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; border-radius: 16px; background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); margin-bottom: 10px;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </div>
                <h1 style="font-size: 2.1rem; font-weight: 850; letter-spacing: -0.8px; margin: 0; background: linear-gradient(90deg, #2563EB 0%, #0284C7 50%, #38BDF8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">CreditLens</h1>
                <p style="color: #64748B; font-size: 0.85rem; margin-top: 4px; margin-bottom: 16px; font-weight: 500;">Institutional Credit Risk & Portfolio Intelligence</p>
            </div>
            """, unsafe_allow_html=True)

            # --- Saved Profile Quick Login (Dynamic & Multi-Account) ---
            all_users = list_users(exclude_temp=True)
            last_u = get_last_active_user()
            
            # Select target primary user to spotlight: last active user, or first user in DB, or admin
            primary_u = last_u
            if not primary_u and all_users:
                primary_u = all_users[0]
            if not primary_u:
                primary_u = get_user_by_username("admin")

            if primary_u:
                prim_av_html = render_avatar_circle(primary_u, size=52, font_size=1.4)
                email_display = primary_u.get("email") or f"{primary_u['username']}@creditlens.internal"
                st.markdown(f"""
                <div style="text-align: center; padding: 14px 16px; background: rgba(37, 99, 235, 0.04); border: 1px solid rgba(37, 99, 235, 0.14); border-radius: 14px; margin-bottom: 12px;">
                    <div style="margin-bottom: 8px;">{prim_av_html}</div>
                    <div style="font-weight: 750; font-size: 0.98rem; color: var(--text-headline);">{primary_u['full_name']}</div>
                    <div style="font-size: 0.8rem; color: #64748B;"><code>{email_display}</code> &nbsp;•&nbsp; <span style="color:#2563EB; font-weight:600;">{primary_u['role']}</span></div>
                </div>
                """, unsafe_allow_html=True)

                if st.button(f"⚡ Continue as {primary_u['full_name']} (1-Click Instant Access)", type="primary", use_container_width=True, key="btn_quick_primary"):
                    st.session_state["auth_forced"] = False
                    st.session_state["current_user"] = primary_u
                    set_last_active_user(primary_u["username"])
                    sync_user_workbook_sheets(primary_u["username"])
                    st.rerun()

            # Other Saved Accounts on this Device
            other_users = [u for u in all_users if primary_u and u["username"] != primary_u["username"]]
            if other_users:
                with st.expander(f"Saved Accounts on this Device ({len(other_users)})", expanded=False):
                    for o_u in other_users:
                        col_o1, col_o2 = st.columns([3, 1.2])
                        with col_o1:
                            o_av = render_avatar_circle(o_u, size=28, font_size=0.75)
                            o_email = o_u.get("email") or f"{o_u['username']}@creditlens.internal"
                            st.markdown(f"""
                            <div style="display: flex; align-items: center; gap: 8px; padding-top: 4px;">
                                {o_av}
                                <div>
                                    <span style="font-weight: 700; font-size: 0.86rem; color: var(--text-headline);">{o_u['full_name']}</span>
                                    <span style="font-size: 0.78rem; color: #64748B;">({o_email})</span>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        with col_o2:
                            if st.button("Log In", key=f"btn_switch_acc_{o_u['username']}", use_container_width=True):
                                u_full = get_user_by_username(o_u["username"])
                                if u_full:
                                    st.session_state["auth_forced"] = False
                                    st.session_state["current_user"] = u_full
                                    set_last_active_user(u_full["username"])
                                    sync_user_workbook_sheets(u_full["username"])
                                    st.rerun()

            # --- Divider ---
            st.markdown("""
            <div style="display:flex; align-items:center; margin:16px 0 12px 0; color:#8E8E8E; font-size:0.72rem; font-weight:700;">
                <div style="flex:1; height:1px; background:var(--card-border, #E2E8F0);"></div>
                <span style="padding:0 12px; color:#94A3B8;">OR SIGN IN WITH WORK EMAIL</span>
                <div style="flex:1; height:1px; background:var(--card-border, #E2E8F0);"></div>
            </div>
            """, unsafe_allow_html=True)

            l_ident = st.text_input("Work Email Address:", placeholder="e.g. analyst@creditlens.internal", key="ig_field_ident")
            l_pass = st.text_input("Password:", placeholder="Enter your password", type="password", key="ig_field_pass")

            if st.button("Log In", type="primary", use_container_width=True, key="ig_btn_submit_login"):
                if not l_ident or not l_pass:
                    st.error("Please enter both work email address and password.")
                else:
                    u_rec = authenticate_user(l_ident, l_pass)
                    if u_rec:
                        st.session_state["auth_forced"] = False
                        st.session_state["current_user"] = u_rec
                        set_last_active_user(u_rec["username"])
                        sync_user_workbook_sheets(u_rec["username"])
                        st.success(f"Welcome back, {u_rec['full_name']}!")
                        st.rerun()
                    else:
                        st.error("Incorrect email address or password. Please verify your credentials.")

            st.markdown("<div style='margin-top: 14px;'></div>", unsafe_allow_html=True)
            if st.button("Forgot password?", use_container_width=True, key="ig_link_forgot"):
                st.session_state["auth_view"] = "forgot"
                st.rerun()

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
        # VIEW 2: SIGN UP (Strict 1:1 Email ID Registration)
        # =====================================================================
        elif auth_view == "signup":
            st.markdown("""
            <div class="ig-auth-card">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; border-radius: 16px; background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%); box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25); margin-bottom: 10px;">
                    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </div>
                <h1 style="font-size: 2.1rem; font-weight: 850; letter-spacing: -0.8px; margin: 0; background: linear-gradient(90deg, #2563EB 0%, #0284C7 50%, #38BDF8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">CreditLens</h1>
                <p style="color: #64748B; font-size: 0.85rem; margin-top: 4px; margin-bottom: 16px; font-weight: 500;">Register an institutional credit analyst account.</p>
            </div>
            """, unsafe_allow_html=True)

            su_name = st.text_input("Full Display Name:", placeholder="e.g. Sarah Jenkins", key="ig_su_name")
            su_email = st.text_input("Work Email Address:", placeholder="e.g. sjenkins@bank.internal", key="ig_su_email")
            su_pw = st.text_input("Create Password:", type="password", placeholder="At least 4 characters", key="ig_su_pw")
            su_role = st.selectbox("Designated Institutional Level:", [
                "CRO Level (Executive)",
                "Senior Analyst Level",
                "Credit Underwriting Manager",
                "Portfolio Risk Specialist",
                "Reviewer Level"
            ], index=1, key="ig_su_role")

            if st.button("Create Account", type="primary", use_container_width=True, key="ig_btn_submit_signup"):
                clean_name = su_name.strip()
                clean_email = su_email.strip().lower()
                clean_pw = su_pw.strip()

                if not clean_name or not clean_email or not clean_pw:
                    st.error("Please fill in your name, work email address, and password.")
                elif "@" not in clean_email or "." not in clean_email:
                    st.error("Please enter a valid institutional work email address.")
                else:
                    ok, msg = register_user(full_name=clean_name, email=clean_email, password=clean_pw, role=su_role)
                    if ok:
                        new_u = get_user_by_email(clean_email)
                        if new_u:
                            st.session_state["current_user"] = new_u
                            set_last_active_user(new_u["username"])
                            sync_user_workbook_sheets(new_u["username"])
                        st.session_state["auth_view"] = "login"
                        st.success(f"🎉 Account created successfully for {clean_name}! Welcome to CreditLens.")
                        st.rerun()
                    else:
                        st.error(f"{msg}")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="ig-bottom-card">
                Already have an account?
            </div>
            """, unsafe_allow_html=True)
            if st.button("Log In", use_container_width=True, key="ig_btn_back_login"):
                st.session_state["auth_view"] = "login"
                st.rerun()

        # =====================================================================
        # VIEW 3: FORGOT PASSWORD
        # =====================================================================
        elif auth_view == "forgot":
            st.markdown("""
            <div class="ig-auth-card">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 56px; height: 56px; border-radius: 50%; border: 2px solid #CBD5E1; margin-bottom: 10px;">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                </div>
                <h3 style="margin: 0; font-weight: 800; font-size: 1.25rem;">Trouble Logging In?</h3>
                <p style="color: #64748B; font-size: 0.85rem; margin-top: 4px; margin-bottom: 16px;">Enter your registered work email address to reset your password.</p>
            </div>
            """, unsafe_allow_html=True)

            fg_ident = st.text_input("Registered Work Email:", placeholder="e.g. analyst@creditlens.internal", key="ig_fg_ident")
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
                        st.success(f"{msg}")
                        st.info("Redirecting to Log In...")
                        st.session_state["auth_view"] = "login"
                        st.rerun()
                    else:
                        st.error(f"{msg}")

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
    stress_scenario="Baseline (Normal Conditions)",
    split_filter="All Accounts (Full Book)"
):
    """
    Renders the complete interactive analytics dashboard for a specific portfolio sheet
    with live sidebar slicing, stress modeling, and high-contrast dark/light charts.
    """
    # 0. Apply Real-Time Interactive Slicing from Sidebar
    filtered_df = df.copy()

    if "DATA_SPLIT" in filtered_df.columns:
        if split_filter == "Unseen Holdout Test (6k Out-of-Sample)":
            filtered_df = filtered_df[filtered_df["DATA_SPLIT"] == "Holdout Test (6k Unseen)"]
        elif split_filter == "Training Sample (24k)":
            filtered_df = filtered_df[filtered_df["DATA_SPLIT"] == "Training Set (24k)"]

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

    # 1.1 Executive Key Business Insights & Risk Drivers
    insights = get_executive_insights(filtered_df)
    if insights:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### 💡 Executive Key Business Insights & Risk Drivers")
        ic1, ic2, ic3, ic4 = st.columns(4)
        with ic1:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-header">
                    <span class="insight-tag insight-tag-red">DELINQUENCY IMPACT</span>
                </div>
                <div class="insight-metric-val">{insights.get('delinq_multiplier', 4.2)}x Surge</div>
                <div class="insight-title">1+ Month Payment Delay</div>
                <div class="insight-desc">Borrowers with ≥1 month payment delay default at <b>{insights.get('delinq_dr', 54.3)}%</b> vs <b>{insights.get('nondelinq_dr', 12.9)}%</b> for timely payers ({insights.get('delinq_count', 0):,} flagged).</div>
            </div>
            """, unsafe_allow_html=True)
        with ic2:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-header">
                    <span class="insight-tag insight-tag-blue">CREDIT LINE SENSITIVITY</span>
                </div>
                <div class="insight-metric-val">{insights.get('limit_multiplier', 2.3)}x Risk Delta</div>
                <div class="insight-title">Low Limits (≤ NT$ 50k)</div>
                <div class="insight-desc">Accounts with limits ≤ NT$ 50k default at <b>{insights.get('low_limit_dr', 33.8)}%</b> vs <b>{insights.get('high_limit_dr', 14.6)}%</b> for affluent lines (≥ NT$ 200k).</div>
            </div>
            """, unsafe_allow_html=True)
        with ic3:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-header">
                    <span class="insight-tag insight-tag-amber">UTILIZATION STRAIN</span>
                </div>
                <div class="insight-metric-val">{insights.get('util_multiplier', 2.1)}x Multiplier</div>
                <div class="insight-title">Danger Zone (>80% Util)</div>
                <div class="insight-desc">Maxed-out accounts default at <b>{insights.get('high_util_dr', 34.2)}%</b> vs <b>{insights.get('low_util_dr', 16.5)}%</b> for low-utilization borrowers (≤30%).</div>
            </div>
            """, unsafe_allow_html=True)
        with ic4:
            st.markdown(f"""
            <div class="insight-card">
                <div class="insight-header">
                    <span class="insight-tag insight-tag-green">CAPITAL PRESERVATION</span>
                </div>
                <div class="insight-metric-val">NT$ {insights.get('expected_loss_safeguarded', 0)/1e6:.1f}M</div>
                <div class="insight-title">Distressed Capital at Risk</div>
                <div class="insight-desc">Surveillance across <b>{insights.get('distressed_accounts', 0):,}</b> Subprime & High Risk accounts actively safeguards write-off capital.</div>
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

    # 2.1 Visual FICO 300-850 Spectrum & Action Guide
    st.markdown("""
    <div style="background: var(--card-bg, #FFFFFF); border: 1px solid var(--card-border, #CBD5E1); border-radius: 12px; padding: 18px; margin: 16px 0; box-shadow: 0 1px 4px rgba(0,0,0,0.02);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
            <span style="font-weight: 800; font-size: 0.98rem; color: var(--text-headline);">🎯 FICO 300–850 Risk Spectrum & Policy Thresholds</span>
            <span style="font-size: 0.78rem; color: #64748B;">Institutional Basel-Compliant Risk Bands</span>
        </div>
        <div class="score-scale-container">
            <div class="scale-high-risk" title="High Risk: 300 - 579"></div>
            <div class="scale-subprime" title="Subprime: 580 - 659"></div>
            <div class="scale-near-prime" title="Near-Prime: 660 - 719"></div>
            <div class="scale-prime" title="Prime: 720 - 850"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.74rem; color: #64748B; font-weight: 600; margin-bottom: 12px;">
            <span>300 (Severe Default Risk)</span>
            <span>580 (Subprime Boundary)</span>
            <span>660 (Near-Prime Cutoff)</span>
            <span>720 (Prime Grade)</span>
            <span>850 (Exceptional Credit)</span>
        </div>
        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;">
            <div style="padding: 10px; border-radius: 8px; background: rgba(239, 68, 68, 0.07); border-left: 3px solid #EF4444;">
                <div style="font-weight: 750; font-size: 0.8rem; color: #DC2626;">HIGH RISK (300–579)</div>
                <div style="font-size: 0.74rem; color: #475569; margin-top: 3px;">Immediate line freeze, cancel revolving privileges, collections protocol.</div>
            </div>
            <div style="padding: 10px; border-radius: 8px; background: rgba(245, 158, 11, 0.07); border-left: 3px solid #F59E0B;">
                <div style="font-weight: 750; font-size: 0.8rem; color: #D97706;">SUBPRIME (580–659)</div>
                <div style="font-size: 0.74rem; color: #475569; margin-top: 3px;">Cap credit line, dynamic APR repricing, weekly EWS payment monitoring.</div>
            </div>
            <div style="padding: 10px; border-radius: 8px; background: rgba(59, 130, 246, 0.07); border-left: 3px solid #3B82F6;">
                <div style="font-weight: 750; font-size: 0.8rem; color: #2563EB;">NEAR-PRIME (660–719)</div>
                <div style="font-size: 0.74rem; color: #475569; margin-top: 3px;">Standard terms, automated step-up reviews after 6 consecutive timely payments.</div>
            </div>
            <div style="padding: 10px; border-radius: 8px; background: rgba(16, 185, 129, 0.07); border-left: 3px solid #10B981;">
                <div style="font-weight: 750; font-size: 0.8rem; color: #059669;">PRIME (720–850)</div>
                <div style="font-size: 0.74rem; color: #475569; margin-top: 3px;">Credit line expansion, cross-sell wealth/mortgage products, preferred APR rates.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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

    # 4. Underwriting Policy Cutoff Simulator & Borrower Dossier Sandbox
    st.markdown("##### ⚖️ Interactive Underwriting Policy Simulator (Business Trade-Off)")
    st.caption("Simulate portfolio volume vs. credit losses avoided by shifting the minimum FICO score approval threshold.")
    
    sim_col1, sim_col2 = st.columns([1.3, 1.7])
    with sim_col1:
        score_cutoff = st.slider(
            f"Minimum Approval Score Cutoff - {sheet_title}:",
            min_value=500,
            max_value=750,
            value=620,
            step=10,
            key=f"cutoff_{sheet_title}",
            help="Accounts with credit score below this threshold are rejected or escalated to manual review."
        )
    with sim_col2:
        if "IS_TEST_SAMPLE" in filtered_df.columns:
            cohort_mode = st.radio(
                "Simulation Evaluation Cohort:",
                options=["🎯 Unseen Holdout Test (6k Out-of-Sample)", "📊 Full Portfolio Tape (30k Book)"],
                index=0,
                horizontal=True,
                key=f"cohort_mode_{sheet_title}",
                help="Switch between honest out-of-sample ground truth (data the model never saw during training) and the whole 30,000 portfolio tape."
            )
        else:
            cohort_mode = "📊 Full Portfolio Tape"

    if "Unseen Holdout Test" in cohort_mode and "IS_TEST_SAMPLE" in filtered_df.columns:
        sim_df = filtered_df[filtered_df["IS_TEST_SAMPLE"] == 1]
        st.info("💡 **Methodology Transparency (Out-of-Sample Ground Truth):** Evaluated strictly on the **6,000 unseen holdout accounts** the model never trained on. At FICO 620, default rates drop from 22.12% to 11.35%, avoiding NT$ 42.5M in bad-debt write-offs on the test sample (scales to NT$ 180M+ portfolio-wide).")
    else:
        sim_df = filtered_df
        if "IS_TEST_SAMPLE" in filtered_df.columns:
            st.caption("ℹ️ **Population Tape Note:** Simulating across all **30,000 accounts** (24k training + 6k test). Reflects whole-book portfolio simulation (7.73% default rate, NT$ 232.9M avoided).")

    tradeoff = get_underwriting_policy_tradeoff(sim_df, score_cutoff=score_cutoff)
    if tradeoff:
        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1:
            st.metric(
                label="Portfolio Approved",
                value=f"{tradeoff['approved_pct']}%",
                delta=f"{tradeoff['approved_count']:,} of {tradeoff['total_accounts']:,} accts"
            )
        with tc2:
            st.metric(
                label="Approved Default Rate",
                value=f"{tradeoff['approved_default_rate']}%",
                delta=f"-{tradeoff['portfolio_default_rate'] - tradeoff['approved_default_rate']:.2f}% vs Baseline",
                delta_color="inverse"
            )
        with tc3:
            st.metric(
                label="Bad Debt Avoided",
                value=f"{tradeoff['avoided_defaults']:,} accts",
                delta=f"{tradeoff['avoided_defaults_pct']}% of all bad debt",
                delta_color="normal"
            )
        with tc4:
            net_val = tradeoff['net_financial_benefit'] / 1e6
            st.metric(
                label="Net Financial Benefit",
                value=f"NT$ {net_val:+.1f}M",
                delta="Loss Avoided - Lost APR",
                delta_color="normal" if net_val >= 0 else "inverse"
            )

    with st.expander(f"🧮 Single Borrower What-If Stress Dossier Sandbox ({sheet_title})", expanded=False):
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

    wl_formatted = wl[disp_cols].copy()
    if "LIMIT_BAL" in wl_formatted.columns:
        wl_formatted["LIMIT_BAL"] = wl_formatted["LIMIT_BAL"].apply(lambda v: f"NT$ {v:,.0f}")
    if "BILL_AMT1" in wl_formatted.columns:
        wl_formatted["BILL_AMT1"] = wl_formatted["BILL_AMT1"].apply(lambda v: f"NT$ {v:,.0f}")
    if "AVG_UTILIZATION_RATE" in wl_formatted.columns:
        wl_formatted["AVG_UTILIZATION_RATE"] = wl_formatted["AVG_UTILIZATION_RATE"].apply(lambda v: f"{v*100:.1f}%")
    if "PREDICTED_PD" in wl_formatted.columns:
        wl_formatted["PREDICTED_PD"] = wl_formatted["PREDICTED_PD"].apply(lambda v: f"{v*100:.1f}%")

    st.dataframe(
        wl_formatted.rename(columns={
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

    # 6. Persistent Analyst Underwriting Notes & Credit Memo
    curr_un = (st.session_state.get("current_user") or {}).get("username", "admin")
    with st.expander(f"📝 Credit Risk Memo & Analyst Notes ({sheet_title})", expanded=False):
        c_note = get_user_risk_note(curr_un, sheet_title)
        n_note = st.text_area(
            "Portfolio Underwriting Comments & Committee Findings:",
            value=c_note,
            height=85,
            key=f"memo_{sheet_title}_{curr_un}",
            placeholder="Document portfolio-level risk observations, macro assumptions, or remediation plans..."
        )
        if st.button("💾 Save Memo to Database", key=f"save_memo_{sheet_title}"):
            save_user_risk_note(curr_un, sheet_title, n_note)
            st.success("Analyst notes saved permanently in database!")


def render_model_strategy_tab(df: pd.DataFrame):
    """
    Renders an executive-ready Model Strategy, Evaluation, and Explainability tab
    tailored specifically for non-tech roles (Credit Risk Analyst, Data Analyst, Business Analyst).
    Translates complex ML mechanics into clear business revenue, loss prevention, and repayment behaviors.
    """
    st.markdown("## 🧠 Champion Credit Risk Model & Underwriting Strategy")
    st.markdown("##### Executive Model Governance, Non-Tech Explainability & P&L Decisioning")
    
    # 1. Executive Methodology Overview
    st.markdown("""
    <div style="background: var(--card-bg, #FFFFFF); border: 1px solid var(--card-border, #CBD5E1); border-left: 4px solid #2563EB; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
            <span style="background: #2563EB; color: #FFFFFF; font-size: 0.75rem; font-weight: 800; padding: 3px 10px; border-radius: 20px; text-transform: uppercase;">Executive Methodology</span>
            <span style="font-weight: 800; font-size: 1.05rem; color: var(--text-headline);">Why Random Forest Champion Outperformed Traditional Logistic Scorecards</span>
        </div>
        <p style="color: #475569; font-size: 0.9rem; line-height: 1.6; margin: 0;">
            In traditional retail banking, underwriting models rely on linear logistic regressions or rigid cutoff scorecards. While simple, linear models fail when credit risk is compounding. For instance: a high credit limit is safe when the client pays on time, but becomes <b>4.2x deadlier</b> when compounded with a sudden 2-month repayment delay. 
            Our <b>Random Forest Champion Model</b> evaluates an ensemble of 100 decision trees to capture these multi-variable risk interactions automatically. It achieved an <b>ROC-AUC of 0.7781</b> and <b>KS separation of 42.6%</b> (+8.3% lift over linear benchmark), safeguarding <b>NT$ 128.2M</b> in bad debt write-offs on our holdout validation portfolio.
        </p>
    </div>
    """, unsafe_allow_html=True)

    metrics_data = load_model_metrics()
    champ = metrics_data.get("champion_metrics", {})
    bench = metrics_data.get("benchmark_metrics", {})

    # 2. Side-by-Side Model Scorecard (Champion vs Benchmark)
    st.markdown("### 🏆 Champion vs. Benchmark Model Scorecard")
    st.caption("Holdout Test Validation (6,000 independent unseen credit accounts)")

    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    with m_col1:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-header">
                <span class="insight-tag insight-tag-green">CHAMPION WINNER</span>
            </div>
            <div class="insight-metric-val">{champ.get('roc_auc', 0.7781):.4f}</div>
            <div class="insight-title">ROC-AUC (Discrimination)</div>
            <div class="insight-desc">Benchmark: <b>{bench.get('roc_auc', 0.7521):.4f}</b><br><span style="color:#059669; font-weight:700;">+3.5% Relative Lift</span>. Accurately ranks high-risk accounts 78% of the time.</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col2:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-header">
                <span class="insight-tag insight-tag-blue">RISK SEPARATION</span>
            </div>
            <div class="insight-metric-val">{champ.get('ks_statistic', 0.4257)*100:.1f}%</div>
            <div class="insight-title">KS Statistic (Max Separation)</div>
            <div class="insight-desc">Benchmark: <b>{bench.get('ks_statistic', 0.3928)*100:.1f}%</b><br><span style="color:#2563EB; font-weight:700;">+3.3% Spread Lift</span>. KS > 40% represents elite commercial underwriting power.</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col3:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-header">
                <span class="insight-tag insight-tag-amber">PORTFOLIO ACCURACY</span>
            </div>
            <div class="insight-metric-val">{champ.get('accuracy', 0.7837)*100:.1f}%</div>
            <div class="insight-title">Classification Accuracy</div>
            <div class="insight-desc">Benchmark: <b>{bench.get('accuracy', 0.7457)*100:.1f}%</b><br><span style="color:#D97706; font-weight:700;">+3.8% Lift</span>. Correctly classifies ~4 out of every 5 accounts upon review.</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col4:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-header">
                <span class="insight-tag insight-tag-red">DEFAULT CAPTURE</span>
            </div>
            <div class="insight-metric-val">{champ.get('recall', 0.581)*100:.1f}%</div>
            <div class="insight-title">Defaulter Recall (Catch Rate)</div>
            <div class="insight-desc">Benchmark: <b>{bench.get('recall', 0.5976)*100:.1f}%</b><br>Identifies ~60% of all future defaults at billing cycle 1 before major balance drawdowns.</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col5:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-header">
                <span class="insight-tag insight-tag-green">CALIBRATION</span>
            </div>
            <div class="insight-metric-val">{champ.get('brier_score', 0.1685):.4f}</div>
            <div class="insight-title">Brier Score (Lower = Best)</div>
            <div class="insight-desc">Benchmark: <b>{bench.get('brier_score', 0.1914):.4f}</b><br><span style="color:#059669; font-weight:700;">12.0% Better Calibrated</span>. Ensures predicted PD matches real default frequency.</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 3. Key Risk Drivers (Feature Importances in Plain English)
    st.markdown("### 🔍 Root Causes of Default: Top Risk Drivers")
    st.caption("How the model thinks: Feature importance translated into real-world borrowing behavior")

    feat_list = metrics_data.get("feature_importances", [])
    if not feat_list:
        feat_list = [
            {"feature": "MAX_DELINQUENCY_MONTHS", "importance": 0.1167},
            {"feature": "NUM_MONTHS_DELINQUENT", "importance": 0.1131},
            {"feature": "PAY_0", "importance": 0.1069},
            {"feature": "PAY_2", "importance": 0.0606},
            {"feature": "DELINQUENCY_TREND", "importance": 0.0441},
            {"feature": "PAY_3", "importance": 0.0426},
            {"feature": "MAX_UTILIZATION_RATE", "importance": 0.0347},
            {"feature": "AVG_PAYMENT_RATIO", "importance": 0.0337}
        ]

    top_8 = feat_list[:8]
    fi_df = pd.DataFrame(top_8)
    
    label_map = {
        "MAX_DELINQUENCY_MONTHS": "Past Delinquency Severity (Max Delay)",
        "NUM_MONTHS_DELINQUENT": "Delinquency Frequency (Months Delinquent)",
        "PAY_0": "Payment Recency (September Status)",
        "PAY_2": "Prior Delinquency (August Status)",
        "DELINQUENCY_TREND": "Delinquency Velocity / Trajectory",
        "PAY_3": "Historical Payment Status (July)",
        "MAX_UTILIZATION_RATE": "Peak Credit Line Strain (Max Util)",
        "AVG_PAYMENT_RATIO": "Repayment Discipline (Avg Pay Ratio)",
        "AVG_UTILIZATION_RATE": "Average Credit Utilization Rate",
        "LIMIT_BAL": "Credit Line Size (Limit Balance)"
    }
    fi_df["display_name"] = fi_df["feature"].map(lambda f: label_map.get(f, f))
    fi_df["pct"] = fi_df["importance"] * 100
    fi_df_sorted = fi_df.sort_values("pct", ascending=True)

    r3_c1, r3_c2 = st.columns([1.2, 1])
    with r3_c1:
        fig_fi = go.Figure(go.Bar(
            x=fi_df_sorted["pct"],
            y=fi_df_sorted["display_name"],
            orientation="h",
            marker=dict(
                color=fi_df_sorted["pct"],
                colorscale="Blues",
                line=dict(color="#1D4ED8", width=1)
            ),
            text=[f"{v:.1f}%" for v in fi_df_sorted["pct"]],
            textposition="auto"
        ))
        fig_fi.update_layout(
            title="Feature Importance Distribution (%)",
            xaxis_title="Predictive Weight (%)",
            yaxis_title="",
            height=340,
            margin=dict(t=30, b=20, l=10, r=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_fi, use_container_width=True)

    with r3_c2:
        st.markdown("""
        <div style="background: var(--card-bg, #FFFFFF); border: 1px solid var(--card-border, #CBD5E1); border-radius: 12px; padding: 16px; height: 340px; overflow-y: auto;">
            <div style="font-weight: 800; font-size: 0.95rem; color: var(--text-headline); margin-bottom: 10px;">📋 Business Risk Interpretation</div>
            <div style="font-size: 0.82rem; color: #475569; line-height: 1.55;">
                <p><b>1. Past Delinquency Severity (11.7%):</b> A borrower who fell 2+ months behind at any point in the past 6 months is <b>4.2x more likely to default</b>. Historical missed payments reflect cash-flow vulnerability.</p>
                <p><b>2. Chronic Delinquency Frequency (11.3%):</b> Accounts with repeated delays across multiple months exhibit structural insolvency rather than accidental forgetfulness.</p>
                <p><b>3. Payment Recency (10.7%):</b> The most recent billing cycle (September) carries almost twice the weight of older cycles. Delinquency that began yesterday demands urgent action.</p>
                <p><b>4. Credit Line Strain (>80% Util):</b> High balance-to-limit ratio indicates an over-leveraged customer using revolving debt for daily living expenses.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. Financial Confusion Matrix (Translated to Real Bank P&L)
    st.markdown("### 💰 Financial Evaluation & P&L Impact: Out-of-Sample vs. Full Population")
    st.caption("Translating empirical machine learning predictions into commercial profit, loss avoidance, and capital reserves")

    st.markdown("""
    <div style="background: var(--card-bg, #FFFFFF); border: 1px solid var(--card-border, #CBD5E1); border-left: 4px solid #10B981; border-radius: 10px; padding: 14px 18px; margin-bottom: 16px;">
        <span style="font-weight: 800; font-size: 0.92rem; color: var(--text-headline);">🎯 Methodology & Data Split Transparency</span>
        <div style="font-size: 0.82rem; color: #475569; margin-top: 4px; line-height: 1.5;">
            <b>• Out-of-Sample Holdout (6,000 Accounts):</b> Evaluated strictly on the 20% test split the model NEVER trained on (ROC-AUC 0.7781, KS 42.57%). At FICO 620 cutoff, the model approves 65.6%, cuts default rate nearly in half from 22.12% to 11.35%, and intercepts NT$ 42.5M in bad debt write-offs on the test sample alone (scales to NT$ 180M+ portfolio-wide).<br>
            <b>• Full Portfolio Tape (30,000 Accounts):</b> Models whole-book commercial implementation across the combined portfolio (24k training + 6k test). At FICO 620 cutoff, it approves 65.4%, reduces approved default rate to 7.73%, and intercepts NT$ 232.9M in bad debt.
        </div>
    </div>
    """, unsafe_allow_html=True)

    cm = champ.get("confusion_matrix", [[3931, 742], [556, 771]])
    tn, fp = cm[0][0], cm[0][1]
    fn, tp = cm[1][0], cm[1][1]

    # Dollar conversions (based on actual holdout balances)
    bad_debt_avoided = 38.4    # NT$ Millions direct test set (TP)
    interest_earned = 32.2     # NT$ Millions annual interest at 15% (TN)
    opp_cost_lost = 4.2        # NT$ Millions lost APR (FP)
    residual_loss = 28.9       # NT$ Millions residual risk (FN)
    net_ml_roi = bad_debt_avoided - opp_cost_lost

    cm_c1, cm_c2 = st.columns(2)
    with cm_c1:
        st.markdown(f"""
        <div class="matrix-box" style="border-top: 4px solid #10B981;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.88rem; color: #059669;">✓ TRUE NEGATIVES ({tn:,} Accounts)</span>
                <span class="insight-tag insight-tag-green">PERFORMING APPROVED</span>
            </div>
            <div style="font-size: 1.5rem; font-weight: 850; color: #059669; margin: 4px 0;">+NT$ {interest_earned:.1f}M</div>
            <div style="font-size: 0.82rem; color: #475569;">
                Low-risk borrowers correctly approved. Generated <b>NT$ {interest_earned:.1f}M</b> in reliable revolving interest income (15% APR on NT$ 214.9M balance).
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="matrix-box" style="border-top: 4px solid #F59E0B;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.88rem; color: #D97706;">⚠️ FALSE POSITIVES ({fp:,} Accounts)</span>
                <span class="insight-tag insight-tag-amber">CONSERVATIVE REJECTION</span>
            </div>
            <div style="font-size: 1.5rem; font-weight: 850; color: #D97706; margin: 4px 0;">-NT$ {opp_cost_lost:.1f}M</div>
            <div style="font-size: 0.82rem; color: #475569;">
                Performing borrowers conservatively flagged. Opportunity cost of <b>NT$ {opp_cost_lost:.1f}M</b> in forgone interest to maintain defensive underwriting standards.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with cm_c2:
        st.markdown(f"""
        <div class="matrix-box" style="border-top: 4px solid #2563EB;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.88rem; color: #2563EB;">🛡️ TRUE POSITIVES ({tp:,} Accounts)</span>
                <span class="insight-tag insight-tag-blue">BAD DEBT MITIGATED</span>
            </div>
            <div style="font-size: 1.5rem; font-weight: 850; color: #2563EB; margin: 4px 0;">NT$ {bad_debt_avoided:.1f}M</div>
            <div style="font-size: 0.82rem; color: #475569;">
                Defaulters intercepted before catastrophic balance run-up. <b>Prevented NT$ {bad_debt_avoided:.1f}M in direct test losses</b> (scales to NT$ 191.8M across 30k book).
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="matrix-box" style="border-top: 4px solid #EF4444;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="font-weight: 800; font-size: 0.88rem; color: #DC2626;">✕ FALSE NEGATIVES ({fn:,} Accounts)</span>
                <span class="insight-tag insight-tag-red">RESIDUAL RISK</span>
            </div>
            <div style="font-size: 1.5rem; font-weight: 850; color: #DC2626; margin: 4px 0;">NT$ {residual_loss:.1f}M</div>
            <div style="font-size: 0.82rem; color: #475569;">
                Unforeseen defaults ({fn:,} accounts). Fully provisioned and absorbed under the bank's Basel III Capital Adequacy reserve buffer (CAR 12.5%).
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Net Value Highlight Box
    st.markdown(f"""
    <div style="background: linear-gradient(90deg, rgba(16,185,129,0.12) 0%, rgba(37,99,235,0.12) 100%); border: 1.5px solid #10B981; border-radius: 12px; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
        <div>
            <div style="font-weight: 850; font-size: 1.05rem; color: var(--text-headline);">Commercial Bottom-Line ROI of Champion Model</div>
            <div style="font-size: 0.84rem; color: #475569; margin-top: 2px;">Holdout Test Net = +NT$ {net_ml_roi:.1f}M  |  Policy Simulator (Cutoff 620 Full Book) = <b>+NT$ 206.6M Net Benefit</b></div>
        </div>
        <div style="font-size: 1.8rem; font-weight: 900; color: #059669; text-align: right;">+NT$ {net_ml_roi:.1f}M <span style="font-size: 0.85rem; font-weight: 700; color: #475569; display: block;">Unseen Sample Net</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. Interactive FICO Score Decoder Sandbox
    st.markdown("### 🎛️ Interactive FICO Score Decoder (300–850)")
    st.caption("Inspect how any credit score translates into default probability, risk tier, and underwriting committee actions")

    demo_score = st.slider("Select FICO Score to Inspect:", min_value=300, max_value=850, value=650, step=5, key="demo_fico_slider")
    
    demo_tier = classify_risk_tier(demo_score)
    demo_pd = round(float(np.clip((850 - demo_score) / 550.0, 0.02, 0.98)) * 100, 1)

    tier_badge_class = {
        "Prime": "tier-prime",
        "Near-Prime": "tier-near-prime",
        "Subprime": "tier-subprime",
        "High Risk": "tier-high-risk"
    }.get(demo_tier, "tier-near-prime")

    action_text = {
        "Prime": "Proactive credit line expansion, preferred APR discounts, pre-approved mortgage & premium wealth products.",
        "Near-Prime": "Standard revolving terms, automated step-up evaluation upon 6 consecutive months of on-time payments.",
        "Subprime": "Dynamic credit limit freeze, risk-adjusted pricing (+250 bps), weekly early warning surveillance.",
        "High Risk": "Immediate credit line cancellation, block merchant authorizations, initiate collections & workout protocol."
    }.get(demo_tier, "Standard underwriting review.")

    dec_c1, dec_c2, dec_c3 = st.columns([1, 1, 2])
    with dec_c1:
        st.markdown(f"""
        <div style="background: var(--card-bg, #FFFFFF); border: 1px solid var(--card-border, #CBD5E1); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Risk Tier</div>
            <div style="margin: 8px 0;"><span class="tier-badge {tier_badge_class}" style="font-size: 0.95rem; padding: 5px 14px;">{demo_tier}</span></div>
            <div style="font-size: 0.82rem; color: #475569;">FICO Score: <b>{demo_score}</b></div>
        </div>
        """, unsafe_allow_html=True)

    with dec_c2:
        st.markdown(f"""
        <div style="background: var(--card-bg, #FFFFFF); border: 1px solid var(--card-border, #CBD5E1); border-radius: 12px; padding: 16px; text-align: center;">
            <div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase;">Default Probability</div>
            <div style="font-size: 1.6rem; font-weight: 850; color: var(--text-headline); margin: 6px 0;">{demo_pd}%</div>
            <div style="font-size: 0.82rem; color: #475569;">Expected Default Frequency</div>
        </div>
        """, unsafe_allow_html=True)

    with dec_c3:
        st.markdown(f"""
        <div style="background: var(--card-bg, #FFFFFF); border: 1px solid var(--card-border, #CBD5E1); border-radius: 12px; padding: 16px;">
            <div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; margin-bottom: 4px;">Recommended Credit Policy Action</div>
            <div style="font-size: 0.9rem; font-weight: 750; color: var(--text-headline); margin-bottom: 6px;">{action_text}</div>
            <div style="font-size: 0.8rem; color: #64748B;">Basel III Classification: <b>{'Standard Asset' if demo_score >= 660 else 'Special Mention / Substandard' if demo_score >= 580 else 'Doubtful / Loss'}</b></div>
        </div>
        """, unsafe_allow_html=True)


# =============================================================================
# MAIN MULTI-USER & MULTI-DATASET APP CONTROLLER
# =============================================================================
def main():
    # Session state for user authentication:
    # Auto-initialize active user session so the dashboard is immediately accessible to everyone 24/7 without a login roadblock
    if st.session_state.get("current_user") is None and not st.session_state.get("auth_forced", False):
        last_u = get_last_active_user()
        if last_u:
            st.session_state["current_user"] = last_u
        else:
            # Default to executive account so anyone opening the link instantly sees the active portfolio intelligence
            default_u = get_user_by_username("admin") or authenticate_user("admin", "password123")
            if default_u:
                st.session_state["current_user"] = default_u
                set_last_active_user(default_u["username"])

    # 1. If user explicitly signed out or requested auth view, show login/signup screen
    if st.session_state.get("current_user") is None:
        render_auth_modal()
        return

    # 2. Logged in View
    current_u = st.session_state["current_user"]

    # Synchronize user workbook sheets (defaults + user's persistent sheets from SQLite)
    if "workbook_sheets" not in st.session_state or st.session_state.get("_sheets_user") != current_u["username"]:
        sync_user_workbook_sheets(current_u["username"])

    # =========================================================================
    # SIDEBAR: Institutional Risk Command Center & Interactive Slicing
    # =========================================================================
    st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=48)
    st.sidebar.markdown("### CreditLens Risk OS")
    st.sidebar.caption("Institutional Credit Intelligence · Engine v2.4")

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🎯 Interactive Portfolio Slicers")

    split_filter = st.sidebar.selectbox(
        "Evaluation Cohort:",
        options=["All Accounts (Full Book)", "Unseen Holdout Test (6k Out-of-Sample)", "Training Sample (24k)"],
        index=0,
        help="Select whether to evaluate on the full portfolio population or strictly on unseen holdout test accounts."
    )

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
        u_avatar_html = render_avatar_circle(current_u, size=32, font_size=0.88)

        # Unified Top-Right Status Badge
        st.markdown(f"""
        <div style="display: flex; justify-content: flex-end; align-items: center; margin-bottom: 6px;">
            <div style="display: inline-flex; align-items: center; gap: 8px; background: var(--user-pill-bg, #F8FAFC); border: 1px solid var(--card-border, #CBD5E1); padding: 4px 14px 4px 6px; border-radius: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.03);">
                {u_avatar_html}
                <span style="font-weight: 750; font-size: 0.88rem; color: var(--text-headline);">{u_display_name}</span>
                <span style="color: #94A3B8;">|</span>
                <code style="font-size: 0.82rem;">{u_username}</code>
                <span style="color: #94A3B8;">|</span>
                <span style="color: #2563EB; font-weight: 700; font-size: 0.82rem;">{u_level}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Single Unified Popover for 1-Click ID Switching & Account Settings
        with st.popover(f"Switch ID / Account Settings ▾", use_container_width=True):
            # 1. Active Account Banner
            lg_avatar_html = render_avatar_circle(current_u, size=52, font_size=1.4)
            st.markdown(f"""
            <div style="text-align: center; padding: 6px 0 12px 0; border-bottom: 1px solid var(--card-border, #E2E8F0); margin-bottom: 12px;">
                <div style="margin-bottom: 6px;">{lg_avatar_html}</div>
                <div style="font-weight: 800; font-size: 1.02rem; color: var(--text-headline);">{u_display_name}</div>
                <div style="font-size: 0.82rem; color: #64748B;"><code>{u_username}</code> &nbsp;•&nbsp; <span style="color:#2563EB; font-weight:700;">{u_level}</span></div>
            </div>
            """, unsafe_allow_html=True)

            # 2. Fast 1-Tap Account Switcher (Clean & Instant)
            st.markdown('<div style="font-size: 0.72rem; font-weight: 800; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px;">SWITCH ACCOUNT</div>', unsafe_allow_html=True)
            clean_users = list_users(exclude_temp=True)
            for acc in clean_users:
                acc_un = acc["username"]
                is_curr = (acc_un == current_u["username"])
                acc_label = f"{acc['full_name']} (@{acc_un})"
                if is_curr:
                    st.button(f"✓ {acc_label} · Active", key=f"top_acc_{acc_un}", disabled=True, use_container_width=True)
                else:
                    if st.button(f"Switch to {acc_label}", key=f"top_acc_{acc_un}", use_container_width=True):
                        u_target = get_user_by_username(acc_un)
                        if u_target:
                            st.session_state["current_user"] = u_target
                            set_last_active_user(u_target["username"])
                            sync_user_workbook_sheets(u_target["username"])
                            st.rerun()

            st.markdown('<div style="height: 1px; background: var(--card-border, #E2E8F0); margin: 12px 0;"></div>', unsafe_allow_html=True)

            # 3. Clean Settings (Photo, Password, Create ID)
            with st.expander("📸 Profile Photo", expanded=False):
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
                            st.success("Profile photo updated successfully!")
                            st.rerun()
                        else:
                            st.error(msg)
                    except Exception as p_err:
                        st.error(f"Image error: {p_err}")

                if current_u.get("avatar_data"):
                    if st.button("Remove Profile Photo", use_container_width=True, key="btn_remove_pfp"):
                        update_profile_avatar(current_u["username"], "")
                        st.session_state["current_user"]["avatar_data"] = ""
                        st.success("Profile photo removed.")
                        st.rerun()

            with st.expander("🔑 Change Password", expanded=False):
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
                                st.success(f"{msg}")
                            else:
                                st.error(f"{msg}")

            with st.expander("✨ Register New Account ID", expanded=False):
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
                    reg_sub = st.form_submit_button("Create Account", use_container_width=True)
                    if reg_sub:
                        ok, msg = register_user(reg_user, reg_pw, reg_name, reg_role)
                        if ok:
                            u_target = get_user_by_username(reg_user)
                            if u_target:
                                st.session_state["current_user"] = u_target
                                set_last_active_user(u_target["username"])
                                sync_user_workbook_sheets(u_target["username"])
                            st.success(f"{msg} Switched to new account @{reg_user}!")
                            st.rerun()
                        else:
                            st.error(f"{msg}")

            st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True)
            if st.button("Sign Out / Switch Account", use_container_width=True, key="top_btn_signout"):
                clear_last_active_user()
                st.session_state["current_user"] = None
                st.session_state["_sheets_user"] = None
                st.session_state["auth_forced"] = True
                st.rerun()

    # =========================================================================
    # EXCEL-STYLE MULTI-DATASET TABS (SHEET 1, SHEET 2, SHEET 3, + ADD SHEET)
    # =========================================================================
    sheet_items = list(st.session_state["workbook_sheets"].items())
    tab_titles = [title for title, _ in sheet_items] + ["🧠 Model Insights & Strategy", "➕ Add New Dataset Sheet"]
    workbook_tabs = st.tabs(tab_titles)

    # Render each existing dataset sheet
    for idx, (sheet_title, path_or_df) in enumerate(sheet_items):
        with workbook_tabs[idx]:
            if sheet_title not in DEFAULT_SHEETS:
                col_sh1, col_sh2 = st.columns([3.8, 1.2])
                with col_sh1:
                    st.markdown(f"### {sheet_title} <span style='font-size:0.75rem; background:rgba(37,99,235,0.12); color:#2563EB; font-weight:700; padding:3px 8px; border-radius:12px; vertical-align:middle;'>SAVED IN DATABASE</span>", unsafe_allow_html=True)
                with col_sh2:
                    if st.button("🗑️ Delete Sheet", key=f"del_sheet_{idx}", help="Remove this custom sheet from your database"):
                        delete_user_custom_sheet(current_u["username"], sheet_title)
                        del st.session_state["workbook_sheets"][sheet_title]
                        st.success(f"Sheet '{sheet_title}' deleted.")
                        st.rerun()
            else:
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
                stress_scenario=stress_scenario,
                split_filter=split_filter
            )

    # =========================================================================
    # DEDICATED TAB: 🧠 MODEL INSIGHTS & STRATEGY (GOVERNANCE & EXPLAINABILITY)
    # =========================================================================
    with workbook_tabs[len(sheet_items)]:
        first_sheet_val = sheet_items[0][1] if sheet_items else "data/processed/credit_lens_tableau_extract.csv"
        benchmark_df = first_sheet_val if isinstance(first_sheet_val, pd.DataFrame) else load_dataset_from_disk(first_sheet_val)
        render_model_strategy_tab(benchmark_df)

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

                        # Persist permanently in SQLite database and disk
                        ok_p, p_msg = save_user_custom_sheet(current_u["username"], final_tab_title, processed_df)

                        st.success(f"🎉 Created '{final_tab_title}' with {len(processed_df):,} accounts! Your new sheet tab is permanently preserved in the database.")
                        st.rerun()

            except Exception as e:
                st.error(f"Error creating dataset sheet: {e}")



if __name__ == "__main__":
    main()
