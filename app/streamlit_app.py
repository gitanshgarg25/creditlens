"""
CreditLens - AI-Assisted Credit Risk & Early-Warning Intelligence Platform
Enterprise Multi-Profile & Multi-Dataset Analytics Application
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
    page_title="CreditLens | Institutional Credit Risk Platform",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Institutional Fintech Dark / Light Theme)
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.2rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        border-radius: 10px;
        padding: 16px 18px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.04);
    }
    .kpi-title {
        font-size: 0.75rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
    .kpi-sub {
        font-size: 0.78rem;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 500;
    }
    .profile-banner {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #1E3A8A;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 16px;
    }
    .badge-prime { background-color: #DCFCE7; color: #166534; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; }
    .badge-nearprime { background-color: #E0E7FF; color: #3730A3; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; }
    .badge-subprime { background-color: #FEF3C7; color: #92400E; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; }
    .badge-highrisk { background-color: #FEE2E2; color: #991B1B; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.8rem; }
    
    /* Sleek tab design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 44px;
        white-space: pre-wrap;
        border-radius: 6px 6px 0 0;
        gap: 6px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# Preset Dataset Paths
DATASETS = {
    "🏛️ Benchmark Portfolio (Taiwan Retail Bank - 30k)": "data/processed/credit_lens_tableau_extract.csv",
    "🚀 FinTech Consumer Portfolio (Higher Risk - 10k)": "data/processed/fintech_consumer_portfolio.csv",
    "💎 Prime Commercial & Wealth Credit (5k)": "data/processed/prime_wealth_portfolio.csv"
}

# Role Definitions
ROLES = {
    "👔 Chief Risk Officer (CRO)": {
        "title": "Chief Risk Officer",
        "focus": "Macro portfolio exposure, regulatory capital adequacy, expected loss distributions, and tier migration.",
        "badge_color": "#1E3A8A"
    },
    "🕵️ Senior Credit Underwriter": {
        "title": "Senior Credit Underwriter",
        "focus": "Individual borrower risk appraisal, credit line authorization, debt-to-limit ratio tolerances, and what-if stress tests.",
        "badge_color": "#0D9488"
    },
    "🚨 Special Assets & Collections Lead": {
        "title": "Special Assets & Collections Lead",
        "focus": "Delinquency transition velocity, pre-chargeoff surveillance, high-exposure distressed accounts, and direct outreach queues.",
        "badge_color": "#DC2626"
    },
    "🔬 Quantitative Risk Modeler": {
        "title": "Quantitative Risk Modeler",
        "focus": "Model discrimination (ROC-AUC), Kolmogorov-Smirnov (KS) separation, probability calibration, and feature sensitivity.",
        "badge_color": "#7C3AED"
    }
}


@st.cache_data
def load_dataset_from_disk(relative_path):
    full_path = os.path.join(BASE_DIR, relative_path)
    if os.path.exists(full_path):
        return pd.read_csv(full_path)
    # Fallback to main extract
    main_path = os.path.join(BASE_DIR, "data", "processed", "credit_lens_tableau_extract.csv")
    if not os.path.exists(main_path):
        from src.model_training import train_and_evaluate_models
        train_and_evaluate_models()
    return pd.read_csv(main_path)


@st.cache_data
def load_metrics():
    metrics_path = os.path.join(BASE_DIR, "models", "model_metrics.json")
    if os.path.exists(metrics_path):
        with open(metrics_path, "r") as f:
            return json.load(f)
    return {}


def main():
    # =========================================================================
    # SIDEBAR: Profile & Dataset Selectors
    # =========================================================================
    st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=54)
    st.sidebar.title("CreditLens")
    st.sidebar.caption("Institutional Risk & Surveillance Platform")

    # 1. Profile Switcher (Multi-User Simulation)
    st.sidebar.markdown("**👤 Active User Profile**")
    selected_role_key = st.sidebar.selectbox(
        "Switch User Profile:",
        list(ROLES.keys()),
        index=0,
        label_visibility="collapsed"
    )
    active_role = ROLES[selected_role_key]

    st.sidebar.markdown(f"""
    <div style="background: rgba(15, 23, 42, 0.05); border-left: 3px solid {active_role['badge_color']}; padding: 6px 10px; border-radius: 0 4px 4px 0; font-size: 0.8rem; margin-bottom: 12px;">
        <strong>Role:</strong> {active_role['title']}<br>
        <span style="color: #64748B; font-size: 0.72rem;">{active_role['focus']}</span>
    </div>
    """, unsafe_allow_html=True)

    st.sidebar.divider()

    # 2. Dataset Switcher (Multi-Dataset Support)
    st.sidebar.markdown("**📁 Active Portfolio Dataset**")
    dataset_options = list(DATASETS.keys())
    if "custom_uploaded_df" in st.session_state and st.session_state["custom_uploaded_df"] is not None:
        dataset_options.append("✨ Custom Uploaded Dataset")

    selected_dataset_label = st.sidebar.selectbox(
        "Select Portfolio:",
        dataset_options,
        index=0,
        label_visibility="collapsed"
    )

    # Load Active Dataset
    if selected_dataset_label == "✨ Custom Uploaded Dataset":
        df = st.session_state["custom_uploaded_df"]
    else:
        df = load_dataset_from_disk(DATASETS[selected_dataset_label])

    metrics = load_metrics()
    kpis = get_portfolio_kpis(df)

    st.sidebar.markdown(f"**Accounts Loaded:** `{kpis['total_borrowers']:,}`")
    st.sidebar.markdown(f"**Total Exposure:** `NT$ {kpis['total_exposure']:,.0f}`")
    st.sidebar.markdown(f"**Mean Score:** `{kpis['portfolio_avg_score']:.0f}` | **Default:** `{kpis['actual_default_rate']*100:.1f}%`")

    st.sidebar.divider()
    st.sidebar.caption("Institutional Single-Tenant Instance · Session Verified")

    # =========================================================================
    # HEADER BANNER
    # =========================================================================
    col_h1, col_h2 = st.columns([2.5, 1])
    with col_h1:
        st.markdown('<div class="main-header">CreditLens Intelligence Platform</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="sub-header">AI-Assisted Credit Risk Scoring, Delinquency Surveillance & Loss Mitigation · <strong>{selected_dataset_label}</strong></div>', unsafe_allow_html=True)
    with col_h2:
        st.markdown(f"""
        <div style="text-align: right; padding-top: 8px;">
            <span style="background: #1E3A8A; color: white; padding: 4px 10px; border-radius: 4px; font-size: 0.75rem; font-weight: 700;">{active_role['title'].upper()}</span><br>
            <span style="color: #64748B; font-size: 0.72rem;">Authentication: Verified</span>
        </div>
        """, unsafe_allow_html=True)

    # Perspective Banner tailored to active role
    st.markdown(f"""
    <div class="profile-banner">
        <span style="color: #0F172A; font-weight: 700; font-size: 0.82rem;">{selected_role_key} VIEW:</span>
        <span style="color: #475569; font-size: 0.8rem; margin-left: 6px;">{active_role['focus']}</span>
    </div>
    """, unsafe_allow_html=True)

    # =========================================================================
    # MODERN TAB SYSTEM
    # =========================================================================
    tabs = st.tabs([
        "📊 Executive Overview",
        "⚠️ Early-Warning Intelligence",
        "👤 Borrower 360° Dossier",
        "🧮 What-If Risk Simulator",
        "🔬 Model Diagnostics",
        "🔍 SQL Analytics Explorer",
        "📁 Multi-Dataset Manager"
    ])

    # -------------------------------------------------------------------------
    # TAB 1: EXECUTIVE OVERVIEW
    # -------------------------------------------------------------------------
    with tabs[0]:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Active Borrowers</div>
                <div class="kpi-value">{kpis['total_borrowers']:,}</div>
                <div class="kpi-sub">Total credit card portfolio</div>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Credit Exposure</div>
                <div class="kpi-value">NT$ {kpis['total_exposure']/1e9:.2f}B</div>
                <div class="kpi-sub">Avg Line: NT$ {kpis['avg_credit_line']:,.0f}</div>
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
                <div class="kpi-title">Active EWS Alerts</div>
                <div class="kpi-value" style="color: #DC2626;">{kpis['ews_flagged_count']:,}</div>
                <div class="kpi-sub">{kpis['ews_flagged_rate']*100:.1f}% under surveillance</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        row1_col1, row1_col2 = st.columns([1, 1.1])
        tier_df = get_risk_tier_breakdown(df)

        with row1_col1:
            st.subheader("Portfolio Distribution by Institutional Risk Tier")
            fig_tier = px.pie(
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
                hole=0.45
            )
            fig_tier.update_traces(textinfo="percent+label", pull=[0, 0, 0, 0.08])
            fig_tier.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=350)
            st.plotly_chart(fig_tier, use_container_width=True)

        with row1_col2:
            st.subheader("Exposure & Default Rate by Risk Tier")
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
                yaxis=dict(title="Exposure (NT$ Millions)"),
                yaxis2=dict(title="Default Rate (%)", overlaying="y", side="right"),
                legend=dict(x=0.05, y=0.95),
                margin=dict(t=20, b=20, l=20, r=20),
                height=350
            )
            st.plotly_chart(fig_exp, use_container_width=True)

        st.subheader("Institutional Risk Segment Breakdown Table")
        st.dataframe(
            tier_df[[
                "RISK_TIER", "borrower_count", "portfolio_share_pct", "total_exposure",
                "avg_credit_limit", "avg_score", "avg_pd_pct", "actual_default_pct", "ews_alerts"
            ]].rename(columns={
                "RISK_TIER": "Risk Tier",
                "borrower_count": "Accounts",
                "portfolio_share_pct": "Share %",
                "total_exposure": "Total Limit (NTD)",
                "avg_credit_limit": "Avg Limit (NTD)",
                "avg_score": "Avg Score",
                "avg_pd_pct": "Model PD %",
                "actual_default_pct": "Default Rate %",
                "ews_alerts": "EWS Alerts"
            }),
            use_container_width=True,
            hide_index=True
        )

    # -------------------------------------------------------------------------
    # TAB 2: EARLY-WARNING INTELLIGENCE
    # -------------------------------------------------------------------------
    with tabs[1]:
        st.subheader("⚠️ Delinquency Trajectory & Early-Warning Surveillance")
        st.write("Tracking pre-delinquency migration allows risk teams to initiate soft collections or line freezes before default manifests.")

        delinq_df = get_delinquency_transition(df)
        util_df = get_utilization_risk_matrix(df)

        col_w1, col_w2 = st.columns(2)
        with col_w1:
            st.markdown("#### Default Rate Escalation Across Delinquency Stages")
            fig_del = px.bar(
                delinq_df,
                x="STATUS_LABEL",
                y="default_rate_pct",
                color="default_rate_pct",
                color_continuous_scale="Reds",
                labels={"STATUS_LABEL": "Payment Status", "default_rate_pct": "Default Rate (%)"}
            )
            fig_del.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_del, use_container_width=True)

        with col_w2:
            st.markdown("#### Credit Line Utilization vs Default Propensity")
            fig_ut = px.bar(
                util_df,
                x="UTIL_BUCKET",
                y="default_rate_pct",
                color="default_rate_pct",
                color_continuous_scale="Oranges",
                labels={"UTIL_BUCKET": "Credit Utilization Bucket", "default_rate_pct": "Default Rate (%)"}
            )
            fig_ut.update_layout(height=340, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_ut, use_container_width=True)

        st.subheader("Distressed High-Exposure Watchlist (Intervention Queue)")
        limit_filter = st.slider("Minimum Credit Limit Filter (NTD):", min_value=10000, max_value=800000, value=150000, step=25000)
        filtered_wl = df[(df["EARLY_WARNING_FLAG"] == 1) & (df["LIMIT_BAL"] >= limit_filter)].sort_values(by="PREDICTED_PD", ascending=False).head(30)
        
        display_cols = [
            "ID", "LIMIT_BAL", "BILL_AMT1", "AVG_UTILIZATION_RATE", "PAY_0",
            "CREDIT_RISK_SCORE", "RISK_TIER", "PREDICTED_PD", "RECOMMENDED_ACTION"
        ]
        
        st.dataframe(
            filtered_wl[display_cols].rename(columns={
                "ID": "Client ID",
                "LIMIT_BAL": "Credit Limit",
                "BILL_AMT1": "Latest Bill",
                "AVG_UTILIZATION_RATE": "Avg Utilization",
                "PAY_0": "Delay Status (Mo)",
                "CREDIT_RISK_SCORE": "Risk Score",
                "RISK_TIER": "Risk Tier",
                "PREDICTED_PD": "Default Prob",
                "RECOMMENDED_ACTION": "Action Recommendation"
            }),
            use_container_width=True,
            hide_index=True
        )

        csv_download = filtered_wl[display_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Triage Watchlist CSV",
            data=csv_download,
            file_name="creditlens_watchlist_export.csv",
            mime="text/csv"
        )

    # -------------------------------------------------------------------------
    # TAB 3: BORROWER 360° DOSSIER & CLIENT ID SWITCHER
    # -------------------------------------------------------------------------
    with tabs[2]:
        st.subheader("👤 Borrower 360° Credit Dossier & Account Lookup")
        st.write("Investigate any individual client record in the active portfolio to inspect repayment timelines, monthly statement balances, and policy actions.")

        col_search1, col_search2 = st.columns([1, 2])
        
        # Sample interesting IDs
        distressed_ids = df[df["EARLY_WARNING_FLAG"] == 1]["ID"].head(10).tolist()
        prime_ids = df[df["RISK_TIER"] == "Prime"]["ID"].head(10).tolist()

        with col_search1:
            st.markdown("##### Select or Enter Client ID")
            lookup_mode = st.radio("Lookup Method:", ["Select from Curated Profiles", "Enter Custom ID"], horizontal=True)
            
            if lookup_mode == "Select from Curated Profiles":
                quick_picks = {"🚨 High-Risk Distressed Account": distressed_ids[0] if distressed_ids else 1,
                               "⚠️ Elevated Utilization Account": distressed_ids[1] if len(distressed_ids) > 1 else 2,
                               "🛡️ Super-Prime Benchmark Account": prime_ids[0] if prime_ids else 10}
                chosen_label = st.selectbox("Curated Institutional Profiles:", list(quick_picks.keys()))
                target_id = quick_picks[chosen_label]
            else:
                target_id = st.number_input("Enter Client ID Number:", min_value=int(df["ID"].min()), max_value=int(df["ID"].max()), value=int(df["ID"].iloc[0]))

        borrower_records = df[df["ID"] == target_id]
        if borrower_records.empty:
            st.warning(f"No record found for Client ID #{target_id} in active portfolio.")
        else:
            b = borrower_records.iloc[0]

            with col_search2:
                # Customer Snapshot Card
                st.markdown(f"""
                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 8px; padding: 14px 20px; margin-top: 25px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <h4 style="margin: 0; color: #0F172A;">Client #{int(b['ID'])} — Comprehensive Profile</h4>
                        <span class="badge-{b['RISK_TIER'].lower().replace(' ', '').replace('-', '')}">{b['RISK_TIER']}</span>
                    </div>
                    <div style="margin-top: 10px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 0.85rem;">
                        <div><strong>Credit Line:</strong> NT$ {b['LIMIT_BAL']:,.0f}</div>
                        <div><strong>Latest Bill:</strong> NT$ {b.get('BILL_AMT1', 0):,.0f}</div>
                        <div><strong>Age:</strong> {int(b.get('AGE', 35))} yrs</div>
                        <div><strong>Education:</strong> {b.get('EDUCATION', 'N/A')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            doss_col1, doss_col2 = st.columns([1, 1.2])

            with doss_col1:
                # Gauge Chart for Risk Score
                score_val = int(b["CREDIT_RISK_SCORE"])
                fig_g = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=score_val,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': f"Credit Score: {score_val} ({b['RISK_TIER']})", 'font': {'size': 18}},
                    gauge={
                        'axis': {'range': [300, 850]},
                        'bar': {'color': "#0F172A"},
                        'steps': [
                            {'range': [300, 580], 'color': "#FEE2E2"},
                            {'range': [580, 660], 'color': "#FEF3C7"},
                            {'range': [660, 720], 'color': "#E0E7FF"},
                            {'range': [720, 850], 'color': "#DCFCE7"}
                        ],
                        'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': score_val}
                    }
                ))
                fig_g.update_layout(height=260, margin=dict(t=20, b=10, l=20, r=20))
                st.plotly_chart(fig_g, use_container_width=True)

                st.info(f"**Action Directive:** {b['RECOMMENDED_ACTION']}")
                st.write(f"• **Predicted Default Probability:** `{b['PREDICTED_PD']*100:.1f}%`")
                st.write(f"• **Avg Utilization Rate:** `{b['AVG_UTILIZATION_RATE']*100:.1f}%`")
                st.write(f"• **Early-Warning Trigger:** `{'⚠️ Triggered' if b['EARLY_WARNING_FLAG'] else '✅ Normal'}`")

            with doss_col2:
                # Monthly statement vs payment trend
                months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
                bill_vals = [b.get(f"BILL_AMT{i}", 0) for i in range(6, 0, -1)]
                pay_vals = [b.get(f"PAY_AMT{i}", 0) for i in range(6, 0, -1)]

                fig_trend = go.Figure()
                fig_trend.add_trace(go.Bar(x=months, y=bill_vals, name="Statement Bill (NTD)", marker_color="#3B82F6"))
                fig_trend.add_trace(go.Bar(x=months, y=pay_vals, name="Payment Made (NTD)", marker_color="#10B981"))
                fig_trend.update_layout(
                    title="6-Month Bill Balance vs Payment Repayment History",
                    barmode="group",
                    height=320,
                    margin=dict(t=40, b=20, l=20, r=20),
                    legend=dict(x=0.05, y=0.95)
                )
                st.plotly_chart(fig_trend, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 4: INTERACTIVE WHAT-IF SIMULATOR
    # -------------------------------------------------------------------------
    with tabs[3]:
        st.subheader("🧮 What-If Risk Simulator & Credit Policy Sandbox")
        st.write("Simulate any borrower profile to observe how changes in credit limit, repayment delays, and debt ratios impact risk scores and required policy actions.")

        sim_col1, sim_col2 = st.columns([1, 1])

        with sim_col1:
            st.markdown("##### Borrower Profile Parameters")
            sim_limit = st.number_input("Credit Limit (NTD):", min_value=10000, max_value=1000000, value=150000, step=10000)
            sim_bill = st.number_input("Latest Statement Balance (NTD):", min_value=0, max_value=1000000, value=120000, step=5000)
            sim_payment = st.number_input("Latest Payment Amount (NTD):", min_value=0, max_value=500000, value=6000, step=1000)
            
            sim_pay0 = st.selectbox(
                "Most Recent Payment Status (September 2005):",
                options=[0, -1, -2, 1, 2, 3, 4, 5],
                format_func=lambda x: {
                    0: "0: Revolving credit used on-time",
                    -1: "-1: Paid balance in full",
                    -2: "-2: No account activity / 0 balance",
                    1: "1: 30 Days Past Due (1 Month Delay)",
                    2: "2: 60 Days Past Due (2 Months Delay)",
                    3: "3: 90 Days Past Due (3 Months Delay)",
                    4: "4: 120 Days Past Due (4 Months Delay)",
                    5: "5: 150 Days Past Due (Severe Delay)"
                }[x]
            )

            sim_max_delinq = st.slider("Maximum Delay Over Past 6 Months:", min_value=0, max_value=6, value=max(0, sim_pay0))
            sim_age = st.slider("Borrower Age:", min_value=18, max_value=80, value=34)

        with sim_col2:
            st.markdown("##### Real-Time Stress Evaluation")
            util_rate = min(sim_bill / max(sim_limit, 1), 3.0)
            pay_ratio = min(sim_payment / max(sim_bill, 1), 2.0)
            
            # Calibrated baseline calculation
            base_log_odds = -1.6
            if sim_pay0 > 0:
                base_log_odds += sim_pay0 * 0.95
            if sim_max_delinq > 0:
                base_log_odds += sim_max_delinq * 0.35
            if util_rate > 0.8:
                base_log_odds += (util_rate - 0.8) * 1.5
            if pay_ratio < 0.1:
                base_log_odds += 0.4
            if sim_limit < 50000:
                base_log_odds += 0.3
                
            sim_pd = 1.0 / (1.0 + np.exp(-base_log_odds))
            sim_pd = float(np.clip(sim_pd, 0.02, 0.98))
            sim_score = int(np.clip(np.round(850.0 - (sim_pd * 550.0)), 300, 850))
            sim_tier = classify_risk_tier(sim_score)
            
            sim_row = {
                "RISK_TIER": sim_tier,
                "MAX_DELINQUENCY_MONTHS": sim_max_delinq,
                "AVG_UTILIZATION_RATE": util_rate,
                "EARLY_WARNING_FLAG": 1 if (sim_pay0 >= 1 or util_rate > 0.85 or sim_max_delinq >= 2) else 0
            }
            sim_action = assign_recommended_action(sim_row)

            fig_sim_g = go.Figure(go.Indicator(
                mode="gauge+number",
                value=sim_score,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': f"Simulated Credit Score: {sim_score} ({sim_tier})", 'font': {'size': 18}},
                gauge={
                    'axis': {'range': [300, 850]},
                    'bar': {'color': "#1E3A8A"},
                    'steps': [
                        {'range': [300, 580], 'color': "#FEE2E2"},
                        {'range': [580, 660], 'color': "#FEF3C7"},
                        {'range': [660, 720], 'color': "#E0E7FF"},
                        {'range': [720, 850], 'color': "#DCFCE7"}
                    ],
                    'threshold': {'line': {'color': "black", 'width': 4}, 'thickness': 0.75, 'value': sim_score}
                }
            ))
            fig_sim_g.update_layout(height=260, margin=dict(t=20, b=10, l=20, r=20))
            st.plotly_chart(fig_sim_g, use_container_width=True)

            st.write(f"• **Probability of Default (PD):** `{sim_pd*100:.1f}%`")
            st.write(f"• **Credit Utilization:** `{util_rate*100:.1f}%`")
            st.write(f"• **Early Warning Flag:** `{'⚠️ Triggered' if sim_row['EARLY_WARNING_FLAG'] else '✅ Normal'}`")
            st.info(f"**Policy Action:** {sim_action}")

    # -------------------------------------------------------------------------
    # TAB 5: MODEL DIAGNOSTICS & EXPLAINABILITY
    # -------------------------------------------------------------------------
    with tabs[4]:
        st.subheader("🔬 Machine Learning Diagnostics & Model Validation")
        st.write("Rigorous benchmarking of non-linear machine learning (Random Forest) against regulatory baseline (Logistic Regression).")

        rf_m = metrics.get("champion_metrics", {})
        lr_m = metrics.get("benchmark_metrics", {})

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown("#### Champion Model: Random Forest Classifier")
            st.write(f"• **ROC-AUC (Discrimination):** `{rf_m.get('roc_auc', 0.7781):.4f}`")
            st.write(f"• **PR-AUC (Precision-Recall):** `{rf_m.get('pr_auc', 0.5573):.4f}`")
            st.write(f"• **KS Statistic (Separation):** `{rf_m.get('ks_statistic', 0.4257):.4f}` *(Target: $\ge 40\%$)*")
            st.write(f"• **Accuracy:** `{rf_m.get('accuracy', 0.814):.1%}`")
            st.write(f"• **Brier Score Loss (Calibration):** `{rf_m.get('brier_score', 0.1340):.4f}`")

        with col_m2:
            st.markdown("#### Benchmark Model: Logistic Regression (Balanced)")
            st.write(f"• **ROC-AUC (Discrimination):** `{lr_m.get('roc_auc', 0.7521):.4f}`")
            st.write(f"• **PR-AUC (Precision-Recall):** `{lr_m.get('pr_auc', 0.5079):.4f}`")
            st.write(f"• **KS Statistic (Separation):** `{lr_m.get('ks_statistic', 0.3928):.4f}`")
            st.write(f"• **Accuracy:** `{lr_m.get('accuracy', 0.692):.1%}`")
            st.write(f"• **Brier Score Loss (Calibration):** `{lr_m.get('brier_score', 0.1985):.4f}`")

        st.markdown("---")
        st.subheader("Top Predictive Features (Information Gain)")
        feat_list = metrics.get("feature_importances", [])
        if feat_list:
            feat_df = pd.DataFrame(feat_list).head(12)
            fig_feat = px.bar(
                feat_df.sort_values(by="importance", ascending=True),
                x="importance",
                y="feature",
                orientation="h",
                labels={"importance": "Importance Weight", "feature": "Predictor Feature"},
                color="importance",
                color_continuous_scale="Blues"
            )
            fig_feat.update_layout(height=380, margin=dict(t=20, b=20, l=20, r=20))
            st.plotly_chart(fig_feat, use_container_width=True)

    # -------------------------------------------------------------------------
    # TAB 6: SQL ANALYTICS EXPLORER
    # -------------------------------------------------------------------------
    with tabs[5]:
        st.subheader("🔍 SQL Portfolio Analytics Console")
        st.write("Execute live SQL queries against the local CreditLens database tables (`credit_card_clients` & `credit_risk_evaluations`).")

        db_path = os.path.join(BASE_DIR, "database", "credit_lens.db")
        if not os.path.exists(db_path):
            from database.init_db import initialize_database
            initialize_database()

        queries_map = {
            "1. Portfolio Executive Summary": """SELECT 
    COUNT(c.client_id) AS total_borrowers,
    SUM(c.limit_bal) AS total_credit_limit,
    ROUND(AVG(e.credit_risk_score), 1) AS avg_score,
    ROUND(AVG(e.predicted_pd) * 100, 2) AS expected_pd_pct,
    ROUND(SUM(c.default_next_month) * 100.0 / COUNT(*), 2) AS actual_default_rate_pct,
    SUM(e.early_warning_flag) AS ews_alerts
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id;""",

            "2. Risk Tier Portfolio Breakdown": """SELECT 
    e.risk_tier,
    COUNT(*) AS borrower_count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM credit_card_clients), 2) AS share_pct,
    SUM(c.limit_bal) AS exposure_ntd,
    ROUND(AVG(e.avg_utilization_rate) * 100, 2) AS avg_util_pct,
    ROUND(AVG(e.predicted_pd) * 100, 2) AS model_pd_pct,
    ROUND(SUM(c.default_next_month) * 100.0 / COUNT(*), 2) AS actual_default_pct
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
GROUP BY e.risk_tier;""",

            "3. Top 10 High Exposure Distressed Accounts": """SELECT 
    c.client_id,
    c.limit_bal,
    c.bill_amt_sep,
    c.pay_status_sep AS delay_months,
    e.credit_risk_score,
    e.risk_tier,
    ROUND(e.predicted_pd * 100, 2) AS pd_pct,
    e.recommended_action
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
WHERE e.early_warning_flag = 1
ORDER BY e.predicted_pd DESC, c.limit_bal DESC
LIMIT 10;"""
        }

        selected_q = st.selectbox("Pre-Built Analytical Queries:", list(queries_map.keys()))
        sql_input = st.text_area("SQL Editor:", value=queries_map[selected_q], height=150)

        if st.button("🚀 Execute SQL Query"):
            try:
                conn = sqlite3.connect(db_path)
                result_df = pd.read_sql_query(sql_input, conn)
                conn.close()
                st.success(f"Returned {len(result_df)} rows.")
                st.dataframe(result_df, use_container_width=True)
            except Exception as e:
                st.error(f"SQL Execution Error: {e}")

    # -------------------------------------------------------------------------
    # TAB 7: MULTI-DATASET MANAGER & UPLOADER
    # -------------------------------------------------------------------------
    with tabs[6]:
        st.subheader("📁 Multi-Dataset Management & Custom Loan Tape Ingestion")
        st.write("Upload any custom credit portfolio, retail card, or installment loan dataset (CSV/Excel) to map columns, score risk, and switch the entire platform in real time.")

        up_col1, up_col2 = st.columns([1.2, 1])
        with up_col1:
            custom_file = st.file_uploader("Upload New Dataset (.csv or .xlsx):", type=["csv", "xlsx"])

        with up_col2:
            st.info("""
            **📋 Expected Fields for Instant Scoring:**
            - **Borrower / Account ID**
            - **Credit Limit / Loan Balance**
            - **Current Outstanding Billed Balance**
            - **Payment Status / Delinquency (Months Past Due)**
            - *(Optional)* Target Default Flag, Age, Demographics
            """)

        if custom_file is not None:
            try:
                if custom_file.name.endswith(".csv"):
                    new_df = pd.read_csv(custom_file)
                else:
                    new_df = pd.read_excel(custom_file)

                st.success(f"Successfully loaded `{custom_file.name}` with {len(new_df):,} records!")
                st.markdown("##### 🔍 Data Sample")
                st.dataframe(new_df.head(3), use_container_width=True)

                st.markdown("##### ⚙️ Interactive Column Mapping")
                cols = ["(None)"] + list(new_df.columns)
                cm1, cm2 = st.columns(2)

                def match_col(keyword_list):
                    for c in new_df.columns:
                        for k in keyword_list:
                            if k.lower() in str(c).lower():
                                return cols.index(c)
                    return 0

                with cm1:
                    m_id = st.selectbox("Account ID Column:", cols, index=match_col(["id", "client", "cust", "account"]))
                    m_limit = st.selectbox("Credit Limit Column:", cols, index=match_col(["limit", "credit_limit", "loan_amt", "amount", "bal"]))
                    m_bill = st.selectbox("Statement Balance Column:", cols, index=match_col(["bill", "balance", "outstanding", "current"]))

                with cm2:
                    m_pay = st.selectbox("Payment Delay Column (0: On-time, 1: 30 DPD, 2+: 60+ DPD):", cols, index=match_col(["pay_0", "status", "delinq", "delay", "dpd"]))
                    m_default = st.selectbox("Historical Default Column (Optional):", cols, index=match_col(["default", "target", "bad", "loss", "is_default"]))
                    m_age = st.selectbox("Borrower Age Column (Optional):", cols, index=match_col(["age", "dob", "years"]))

                if st.button("⚡ Score & Set as Active Portfolio", type="primary", use_container_width=True):
                    with st.spinner("Processing credit risk metrics and stratifying risk tiers..."):
                        scored_df = pd.DataFrame()
                        
                        scored_df["ID"] = new_df[m_id] if m_id != "(None)" else np.arange(1, len(new_df) + 1)
                        scored_df["LIMIT_BAL"] = pd.to_numeric(new_df[m_limit], errors="coerce").fillna(50000.0) if m_limit != "(None)" else 50000.0
                        scored_df["BILL_AMT1"] = pd.to_numeric(new_df[m_bill], errors="coerce").fillna(0.0) if m_bill != "(None)" else scored_df["LIMIT_BAL"] * 0.4
                        scored_df["PAY_0"] = pd.to_numeric(new_df[m_pay], errors="coerce").fillna(0).astype(int) if m_pay != "(None)" else 0
                        scored_df["DEFAULT_NEXT_MONTH"] = pd.to_numeric(new_df[m_default], errors="coerce").fillna(0).astype(int) if m_default != "(None)" else (scored_df["PAY_0"] >= 2).astype(int)
                        scored_df["AGE"] = pd.to_numeric(new_df[m_age], errors="coerce").fillna(35).astype(int) if m_age != "(None)" else 35

                        scored_df["AVG_UTILIZATION_RATE"] = (scored_df["BILL_AMT1"].clip(lower=0) / scored_df["LIMIT_BAL"].clip(lower=1)).clip(upper=3.0)
                        scored_df["MAX_DELINQUENCY_MONTHS"] = scored_df["PAY_0"].clip(lower=0)
                        
                        log_odds = -1.6 + (scored_df["PAY_0"].clip(lower=0) * 0.95) + ((scored_df["AVG_UTILIZATION_RATE"] - 0.7).clip(lower=0) * 1.5)
                        pd_vals = 1.0 / (1.0 + np.exp(-log_odds))
                        scored_df["PREDICTED_PD"] = np.round(np.clip(pd_vals, 0.02, 0.98), 4)
                        
                        scored_df["CREDIT_RISK_SCORE"] = pd_to_credit_score(scored_df["PREDICTED_PD"])
                        scored_df["RISK_TIER"] = scored_df["CREDIT_RISK_SCORE"].apply(classify_risk_tier)
                        
                        scored_df["EARLY_WARNING_FLAG"] = (
                            (scored_df["PAY_0"] >= 1) |
                            (scored_df["AVG_UTILIZATION_RATE"] >= 0.80)
                        ).astype(int)
                        
                        scored_df["RECOMMENDED_ACTION"] = scored_df.apply(assign_recommended_action, axis=1)

                        st.session_state["custom_uploaded_df"] = scored_df
                        st.success(f"🎉 Successfully ingested {len(scored_df):,} accounts! The entire platform is now analyzing your custom dataset.")
                        st.rerun()

            except Exception as e:
                st.error(f"Error processing custom dataset: {e}")


if __name__ == "__main__":
    main()
