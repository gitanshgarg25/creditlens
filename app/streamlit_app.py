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

# Setup Project Path
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.auth import init_user_db, register_user, authenticate_user, list_users, update_password
from src.analytics_engine import (
    get_portfolio_kpis,
    get_risk_tier_breakdown,
    get_delinquency_transition,
    get_utilization_risk_matrix,
    get_watchlist
)
from src.risk_scoring import pd_to_credit_score, classify_risk_tier, assign_recommended_action

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
    .main-header {
        font-size: 2.0rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 0.92rem;
        color: #475569;
        margin-bottom: 1.0rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border-radius: 8px;
        padding: 14px 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    .kpi-title {
        font-size: 0.72rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 500;
    }
    .user-pill {
        display: inline-flex;
        align-items: center;
        background: #F1F5F9;
        border: 1px solid #CBD5E1;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        color: #1E293B;
    }
    .badge-prime { background-color: #DCFCE7; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-nearprime { background-color: #E0E7FF; color: #3730A3; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-subprime { background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }
    .badge-highrisk { background-color: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; }

    /* Excel-Style Tabs Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        border-bottom: 2px solid #CBD5E1;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #F1F5F9;
        border: 1px solid #CBD5E1;
        border-bottom: none;
        border-radius: 6px 6px 0 0;
        padding: 8px 16px;
        font-weight: 700;
        font-size: 0.85rem;
        color: #475569;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1E3A8A !important;
        border-top: 3px solid #1E3A8A !important;
    }
</style>
""", unsafe_allow_html=True)


# Initialize DB on load
init_user_db()


@st.cache_data
def load_dataset_from_disk(relative_path):
    full_path = os.path.join(BASE_DIR, relative_path)
    if os.path.exists(full_path):
        return pd.read_csv(full_path)
    main_path = os.path.join(BASE_DIR, "data", "processed", "credit_lens_tableau_extract.csv")
    if not os.path.exists(main_path):
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
    """Renders social-media style Log In and Sign Up interface."""
    st.markdown("<br>", unsafe_allow_html=True)
    _, auth_box, _ = st.columns([1, 1.4, 1])

    with auth_box:
        st.markdown("""
        <div style="background: #0F172A; border-radius: 12px; padding: 26px 32px; color: #FFFFFF; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.25);">
            <img src="https://img.icons8.com/fluency/96/shield.png" width="60" style="margin-bottom: 8px;" />
            <h2 style="color: #FFFFFF; font-size: 1.6rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;">CREDITLENS PORTAL</h2>
            <p style="color: #94A3B8; font-size: 0.85rem; margin-top: 4px;">Sign in to your account or create a new user profile</p>
        </div>
        """, unsafe_allow_html=True)

        tab_login, tab_signup, tab_reset = st.tabs(["🔑 Sign In", "✨ Create New Account", "🔄 Reset / Change Passkey"])

        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            login_user = st.text_input("Username:", placeholder="e.g. admin or your username", key="login_username_field")
            login_pass = st.text_input("Password:", type="password", placeholder="Enter your password", key="login_pass_field")

            if st.button("Log In to CreditLens", type="primary", use_container_width=True):
                user_record = authenticate_user(login_user, login_pass)
                if user_record:
                    st.session_state["current_user"] = user_record
                    st.success(f"Welcome back, {user_record['full_name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### ⚡ Quick Demo Logins")
            q_col1, q_col2 = st.columns(2)
            with q_col1:
                if st.button("Log in as Admin (CRO)", use_container_width=True):
                    st.session_state["current_user"] = authenticate_user("admin", "password123")
                    st.rerun()
            with q_col2:
                if st.button("Log in as Analyst", use_container_width=True):
                    st.session_state["current_user"] = authenticate_user("analyst", "password123")
                    st.rerun()

        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            new_name = st.text_input("Full Display Name:", placeholder="e.g. John Doe", key="signup_name")
            new_username = st.text_input("Choose Username:", placeholder="e.g. johndoe", key="signup_user")
            new_password = st.text_input("Choose Password:", type="password", placeholder="At least 4 characters", key="signup_pw")
            new_role = st.selectbox("Role / Job Title:", [
                "Senior Risk Analyst",
                "Chief Risk Officer (CRO)",
                "Credit Underwriting Manager",
                "Portfolio Analytics Specialist",
                "Guest Reviewer"
            ], key="signup_role")

            if st.button("Create My Account", type="primary", use_container_width=True):
                ok, msg = register_user(new_username, new_password, new_name, new_role)
                if ok:
                    st.success(f"{msg} You can now switch to the 'Sign In' tab to log in.")
                else:
                    st.error(msg)

        with tab_reset:
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("Update your existing account password or passkey.")
            r_user = st.text_input("Username:", placeholder="e.g. admin or analyst", key="reset_user_tab")
            r_curr = st.text_input("Current Passkey / Password:", type="password", placeholder="Enter current passkey", key="reset_curr_tab")
            r_new = st.text_input("New Passkey / Password:", type="password", placeholder="At least 4 characters", key="reset_new_tab")
            r_conf = st.text_input("Confirm New Passkey:", type="password", placeholder="Repeat new passkey", key="reset_conf_tab")

            if st.button("Update Passkey Now", type="primary", use_container_width=True):
                if not r_user or not r_curr or not r_new:
                    st.error("Please fill in all required fields.")
                elif r_new != r_conf:
                    st.error("New passwords do not match.")
                elif not authenticate_user(r_user, r_curr):
                    st.error("Verification failed: Username or current password does not match.")
                else:
                    ok, msg = update_password(r_user, r_new)
                    if ok:
                        st.success(f"✅ {msg} You can now sign in with your new passkey!")
                    else:
                        st.error(f"❌ {msg}")


# =============================================================================
# REUSABLE PORTFOLIO DASHBOARD (EXCEL SHEET CONTENT)
# =============================================================================
def render_portfolio_sheet(df: pd.DataFrame, sheet_title: str):
    """
    Renders the complete interactive analytics dashboard for a specific portfolio sheet.
    """
    kpis = get_portfolio_kpis(df)
    tier_df = get_risk_tier_breakdown(df)
    delinq_df = get_delinquency_transition(df)
    util_df = get_utilization_risk_matrix(df)

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
            <div class="kpi-sub">Model PD: {kpis['expected_default_rate']*100:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">EWS Alerts Active</div>
            <div class="kpi-value" style="color: #DC2626;">{kpis['ews_flagged_count']:,}</div>
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
        fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    with r1_col2:
        st.markdown("##### 📊 Credit Exposure & Default Escalation by Tier")
        fig_exp = go.Figure()
        fig_exp.add_trace(go.Bar(
            x=tier_df["RISK_TIER"],
            y=tier_df["total_exposure"] / 1e6,
            name="Exposure (NT$ Millions)",
            marker_color="#1E3A8A",
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
            height=320
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
        fig_del.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig_del, use_container_width=True)

    with r2_col2:
        st.markdown("##### 📈 Credit Utilization Strain vs Default Rate")
        fig_ut = px.bar(
            util_df,
            x="UTIL_BUCKET",
            y="default_rate_pct",
            color="default_rate_pct",
            color_continuous_scale="Oranges",
            labels={"UTIL_BUCKET": "Utilization Bucket", "default_rate_pct": "Default Rate (%)"}
        )
        fig_ut.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
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
    wl = get_watchlist(df, top_n=15)
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

    csv_data = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"📥 Download Full {sheet_title} Scored CSV",
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
        st.session_state["current_user"] = authenticate_user("admin", "password123")

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
    # SIDEBAR: User Account Management & Account Switcher
    # =========================================================================
    st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=54)
    st.sidebar.title("CreditLens")
    st.sidebar.caption("Multi-User Credit Risk Intelligence")

    st.sidebar.markdown(f"""
    <div style="background: #0F172A; color: white; padding: 12px 14px; border-radius: 8px; margin-bottom: 12px;">
        <div style="font-size: 0.72rem; color: #94A3B8; text-transform: uppercase; font-weight: 700;">CURRENTLY LOGGED IN AS:</div>
        <div style="font-size: 1.05rem; font-weight: 800; margin: 2px 0;">{current_u['full_name']}</div>
        <div style="font-size: 0.78rem; color: #60A5FA;">@{current_u['username']} · {current_u['role']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Switch Account Dropdown
    all_users = list_users()
    user_choices = {f"{u['full_name']} (@{u['username']})": u['username'] for u in all_users}
    
    st.sidebar.markdown("**👥 Quick Switch User Account:**")
    selected_account_label = st.sidebar.selectbox(
        "Switch User Account:",
        list(user_choices.keys()),
        index=list(user_choices.values()).index(current_u["username"]) if current_u["username"] in user_choices.values() else 0,
        label_visibility="collapsed"
    )

    if user_choices[selected_account_label] != current_u["username"]:
        if st.sidebar.button("Switch to this Account", use_container_width=True):
            st.session_state["current_user"] = authenticate_user(user_choices[selected_account_label], "password123") or {"username": user_choices[selected_account_label], "full_name": selected_account_label, "role": "Risk Analyst"}
            st.rerun()

    # Passkey / Password Update Expander
    with st.sidebar.expander("🔑 Change Passkey / Password"):
        with st.form("sidebar_change_pass_form", clear_on_submit=True):
            s_curr_pw = st.text_input("Current Passkey:", type="password", key="side_curr_pw")
            s_new_pw = st.text_input("New Passkey:", type="password", key="side_new_pw")
            s_conf_pw = st.text_input("Confirm New Passkey:", type="password", key="side_conf_pw")
            s_submit = st.form_submit_button("Update Passkey", use_container_width=True)

            if s_submit:
                if not s_curr_pw or not s_new_pw:
                    st.error("Please fill in all fields.")
                elif s_new_pw != s_conf_pw:
                    st.error("New passwords do not match.")
                elif not authenticate_user(current_u["username"], s_curr_pw):
                    st.error("Current passkey is incorrect.")
                else:
                    ok, msg = update_password(current_u["username"], s_new_pw)
                    if ok:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")

    if st.sidebar.button("🚪 Sign Out / Switch ID", use_container_width=True):
        st.session_state["current_user"] = None
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("**📑 Excel-Style Workbook Sheets**")
    for s_name in st.session_state["workbook_sheets"].keys():
        st.sidebar.caption(f"• {s_name}")
    st.sidebar.caption("Use the top sheet tabs to switch dashboards.")

    # =========================================================================
    # MAIN WORKBOOK HEADER
    # =========================================================================
    col_top1, col_top2 = st.columns([3, 1])
    with col_top1:
        st.markdown('<div class="main-header">CreditLens Portfolio Workbook</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Excel-Style Multi-Dataset Risk Dashboards · Switch tabs below to compare portfolios</div>', unsafe_allow_html=True)
    with col_top2:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 6px;">
            <span class="user-pill">👤 {current_u['full_name']}</span><br>
            <span style="font-size: 0.75rem; color: #64748B;">Role: {current_u['role']}</span>
        </div>
        """, unsafe_allow_html=True)

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
            render_portfolio_sheet(sheet_df, sheet_title)

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
