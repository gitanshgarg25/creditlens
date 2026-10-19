"""
CreditLens - Analytics & Business Intelligence Engine
Computes core credit risk portfolio aggregations, delinquency migration,
risk concentration, and portfolio watchlists for dashboards and reports.
"""

from __future__ import annotations
import os
import json
import pandas as pd
import numpy as np


def get_portfolio_kpis(df: pd.DataFrame) -> dict:
    """
    Computes executive-level credit risk KPI metrics.
    """
    total_borrowers = len(df)
    total_exposure = float(df["LIMIT_BAL"].sum())
    avg_credit_line = float(df["LIMIT_BAL"].mean())
    avg_score = float(df["CREDIT_RISK_SCORE"].mean()) if "CREDIT_RISK_SCORE" in df.columns else 0.0
    expected_default_rate = float(df["PREDICTED_PD"].mean()) if "PREDICTED_PD" in df.columns else 0.0
    actual_default_rate = float(df["DEFAULT_NEXT_MONTH"].mean())
    ews_flagged = int(df["EARLY_WARNING_FLAG"].sum())
    ews_rate = float(ews_flagged / total_borrowers)
    
    total_outstanding = float(df["BILL_AMT1"].sum())
    avg_utilization = float(df["AVG_UTILIZATION_RATE"].mean()) if "AVG_UTILIZATION_RATE" in df.columns else 0.0

    return {
        "total_borrowers": total_borrowers,
        "total_exposure": total_exposure,
        "avg_credit_line": avg_credit_line,
        "portfolio_avg_score": round(avg_score, 1),
        "expected_default_rate": round(expected_default_rate, 4),
        "actual_default_rate": round(actual_default_rate, 4),
        "ews_flagged_count": ews_flagged,
        "ews_flagged_rate": round(ews_rate, 4),
        "total_outstanding_balance": total_outstanding,
        "avg_utilization": round(avg_utilization, 4)
    }


def get_risk_tier_breakdown(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates volume, exposure, default rates, and alert counts by institutional risk tier.
    """
    if "RISK_TIER" not in df.columns:
        return pd.DataFrame()
        
    grouped = df.groupby("RISK_TIER").agg(
        borrower_count=("ID", "count"),
        total_exposure=("LIMIT_BAL", "sum"),
        avg_credit_limit=("LIMIT_BAL", "mean"),
        avg_score=("CREDIT_RISK_SCORE", "mean"),
        avg_pd=("PREDICTED_PD", "mean"),
        actual_default_rate=("DEFAULT_NEXT_MONTH", "mean"),
        ews_alerts=("EARLY_WARNING_FLAG", "sum"),
        avg_utilization=("AVG_UTILIZATION_RATE", "mean")
    ).reset_index()

    total_count = len(df)
    grouped["portfolio_share_pct"] = np.round((grouped["borrower_count"] / total_count) * 100.0, 2)
    grouped["avg_score"] = np.round(grouped["avg_score"], 0).astype(int)
    grouped["avg_pd_pct"] = np.round(grouped["avg_pd"] * 100.0, 2)
    grouped["actual_default_pct"] = np.round(grouped["actual_default_rate"] * 100.0, 2)
    grouped["avg_utilization_pct"] = np.round(grouped["avg_utilization"] * 100.0, 2)
    
    # Sort logically by credit quality
    tier_order = {"Prime": 1, "Near-Prime": 2, "Subprime": 3, "High Risk": 4}
    grouped["sort_order"] = grouped["RISK_TIER"].map(tier_order).fillna(5)
    grouped = grouped.sort_values("sort_order").drop(columns=["sort_order"])
    
    return grouped


def get_delinquency_transition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analyzes delinquency status severity in September and correlation with default rates.
    """
    status_map = {
        -2: "No Consumption (-2)",
        -1: "Paid in Full (-1)",
        0: "Revolving (0)",
        1: "30 DPD (1 Month)",
        2: "60 DPD (2 Months)",
        3: "90 DPD (3 Months)",
        4: "120 DPD (4 Months)",
        5: "150 DPD (5 Months)",
        6: "180 DPD (6 Months)",
        7: "210 DPD (7 Months)",
        8: "240+ DPD (8 Months)"
    }
    
    df_temp = df.copy()
    df_temp["STATUS_LABEL"] = df_temp["PAY_0"].map(status_map).fillna("Other")
    
    trans = df_temp.groupby(["PAY_0", "STATUS_LABEL"]).agg(
        accounts=("ID", "count"),
        total_balance=("BILL_AMT1", "sum"),
        avg_score=("CREDIT_RISK_SCORE", "mean"),
        default_rate=("DEFAULT_NEXT_MONTH", "mean"),
        avg_pd=("PREDICTED_PD", "mean")
    ).reset_index().sort_values("PAY_0")
    
    trans["share_pct"] = np.round(trans["accounts"] / len(df) * 100.0, 2)
    trans["default_rate_pct"] = np.round(trans["default_rate"] * 100.0, 2)
    trans["avg_pd_pct"] = np.round(trans["avg_pd"] * 100.0, 2)
    trans["avg_score"] = np.round(trans["avg_score"], 0).astype(int)
    
    return trans


def get_utilization_risk_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Groups accounts by utilization buckets to show over-leveraging risks.
    """
    bins = [-np.inf, 0.20, 0.50, 0.80, 1.00, np.inf]
    labels = ["Low (< 20%)", "Moderate (20-50%)", "Elevated (50-80%)", "High (80-100%)", "Over-Limit (> 100%)"]
    
    df_temp = df.copy()
    df_temp["UTIL_BUCKET"] = pd.cut(df_temp["AVG_UTILIZATION_RATE"], bins=bins, labels=labels)
    
    grouped = df_temp.groupby("UTIL_BUCKET", observed=False).agg(
        accounts=("ID", "count"),
        avg_limit=("LIMIT_BAL", "mean"),
        avg_score=("CREDIT_RISK_SCORE", "mean"),
        default_rate=("DEFAULT_NEXT_MONTH", "mean"),
        ews_alerts=("EARLY_WARNING_FLAG", "sum")
    ).reset_index()
    
    grouped["share_pct"] = np.round(grouped["accounts"] / len(df) * 100.0, 2)
    grouped["default_rate_pct"] = np.round(grouped["default_rate"] * 100.0, 2)
    grouped["avg_score"] = np.round(grouped["avg_score"], 0).astype(int)
    grouped["avg_limit"] = np.round(grouped["avg_limit"], 0)
    
    return grouped


def get_watchlist(df: pd.DataFrame, top_n: int = 25) -> pd.DataFrame:
    """
    Returns top distressed borrower accounts requiring collections or underwriting review.
    """
    flagged = df[df["EARLY_WARNING_FLAG"] == 1].copy()
    sorted_wl = flagged.sort_values(by=["PREDICTED_PD", "LIMIT_BAL"], ascending=[False, False])
    
    cols = [
        "ID", "LIMIT_BAL", "BILL_AMT1", "AVG_UTILIZATION_RATE", "PAY_0",
        "CREDIT_RISK_SCORE", "RISK_TIER", "PREDICTED_PD", "RECOMMENDED_ACTION"
    ]
    cols = [c for c in cols if c in sorted_wl.columns]
    return sorted_wl[cols].head(top_n)


def get_executive_insights(df: pd.DataFrame) -> dict:
    """
    Computes key executive business insights and risk drivers from the portfolio data.
    """
    total_acc = len(df)
    if total_acc == 0:
        return {}

    # 1. Delinquency Driver (PAY_0)
    has_pay0 = "PAY_0" in df.columns and "DEFAULT_NEXT_MONTH" in df.columns
    if has_pay0:
        delinq_mask = df["PAY_0"] > 0
        nondelinq_mask = df["PAY_0"] <= 0
        delinq_dr = float(df[delinq_mask]["DEFAULT_NEXT_MONTH"].mean()) if delinq_mask.any() else 0.0
        nondelinq_dr = float(df[nondelinq_mask]["DEFAULT_NEXT_MONTH"].mean()) if nondelinq_mask.any() else 0.0
        delinq_mult = round(delinq_dr / max(nondelinq_dr, 0.001), 1)
        delinq_count = int(delinq_mask.sum())
    else:
        delinq_dr, nondelinq_dr, delinq_mult, delinq_count = 0.0, 0.0, 1.0, 0

    # 2. Credit Line Driver (LIMIT_BAL)
    has_limit = "LIMIT_BAL" in df.columns and "DEFAULT_NEXT_MONTH" in df.columns
    if has_limit:
        low_lim_mask = df["LIMIT_BAL"] <= 50000
        high_lim_mask = df["LIMIT_BAL"] >= 200000
        low_lim_dr = float(df[low_lim_mask]["DEFAULT_NEXT_MONTH"].mean()) if low_lim_mask.any() else 0.0
        high_lim_dr = float(df[high_lim_mask]["DEFAULT_NEXT_MONTH"].mean()) if high_lim_mask.any() else 0.0
        limit_mult = round(low_lim_dr / max(high_lim_dr, 0.001), 1)
    else:
        low_lim_dr, high_lim_dr, limit_mult = 0.0, 0.0, 1.0

    # 3. Utilization Driver (AVG_UTILIZATION_RATE)
    has_util = "AVG_UTILIZATION_RATE" in df.columns and "DEFAULT_NEXT_MONTH" in df.columns
    if has_util:
        high_util_mask = df["AVG_UTILIZATION_RATE"] > 0.80
        low_util_mask = df["AVG_UTILIZATION_RATE"] <= 0.30
        high_util_dr = float(df[high_util_mask]["DEFAULT_NEXT_MONTH"].mean()) if high_util_mask.any() else 0.0
        low_util_dr = float(df[low_util_mask]["DEFAULT_NEXT_MONTH"].mean()) if low_util_mask.any() else 0.0
        util_mult = round(high_util_dr / max(low_util_dr, 0.001), 1)
        high_util_count = int(high_util_mask.sum())
    else:
        high_util_dr, low_util_dr, util_mult, high_util_count = 0.0, 0.0, 1.0, 0

    # 4. Distressed Capital Preservation (Subprime & High Risk)
    if "RISK_TIER" in df.columns and "BILL_AMT1" in df.columns:
        sub_mask = df["RISK_TIER"].isin(["Subprime", "High Risk"])
        distressed_accounts = int(sub_mask.sum())
        distressed_balance = float(df[sub_mask]["BILL_AMT1"].sum())
        if "PREDICTED_PD" in df.columns:
            expected_loss = float((df[sub_mask]["BILL_AMT1"] * df[sub_mask]["PREDICTED_PD"]).sum())
        else:
            expected_loss = distressed_balance * 0.45
    else:
        distressed_accounts, distressed_balance, expected_loss = 0, 0.0, 0.0

    return {
        "delinq_dr": round(delinq_dr * 100, 1),
        "nondelinq_dr": round(nondelinq_dr * 100, 1),
        "delinq_multiplier": delinq_mult,
        "delinq_count": delinq_count,
        "low_limit_dr": round(low_lim_dr * 100, 1),
        "high_limit_dr": round(high_lim_dr * 100, 1),
        "limit_multiplier": limit_mult,
        "high_util_dr": round(high_util_dr * 100, 1),
        "low_util_dr": round(low_util_dr * 100, 1),
        "util_multiplier": util_mult,
        "high_util_count": high_util_count,
        "distressed_accounts": distressed_accounts,
        "distressed_balance": distressed_balance,
        "expected_loss_safeguarded": expected_loss
    }


def get_underwriting_policy_tradeoff(df: pd.DataFrame, score_cutoff: int = 620) -> dict:
    """
    Simulates business trade-offs (Volume Approved vs. Losses Prevented)
    for a chosen minimum FICO risk score cut-off threshold.
    """
    total = len(df)
    if total == 0 or "CREDIT_RISK_SCORE" not in df.columns:
        return {}

    approved_mask = df["CREDIT_RISK_SCORE"] >= score_cutoff
    rejected_mask = ~approved_mask

    approved_count = int(approved_mask.sum())
    rejected_count = total - approved_count
    approved_pct = round((approved_count / total) * 100, 1)

    has_target = "DEFAULT_NEXT_MONTH" in df.columns
    total_defaults = int(df["DEFAULT_NEXT_MONTH"].sum()) if has_target else 0
    portfolio_default_rate = round((total_defaults / max(total, 1)) * 100, 2)

    if has_target:
        approved_defaults = int(df[approved_mask]["DEFAULT_NEXT_MONTH"].sum())
        approved_default_rate = round((approved_defaults / max(approved_count, 1)) * 100, 2)
        avoided_defaults = int(df[rejected_mask]["DEFAULT_NEXT_MONTH"].sum())
        avoided_defaults_pct = round((avoided_defaults / max(total_defaults, 1)) * 100, 1)
    else:
        approved_defaults = 0
        approved_default_rate = 0.0
        avoided_defaults = 0
        avoided_defaults_pct = 0.0

    # Financial translation:
    # Avoided credit losses = billed balance of rejected default accounts
    if has_target and "BILL_AMT1" in df.columns:
        rej_defaults_balance = float(df[rejected_mask & (df["DEFAULT_NEXT_MONTH"] == 1)]["BILL_AMT1"].sum())
        # Opportunity cost: interest income lost on rejected performing accounts (assume 15% APR)
        rej_good_balance = float(df[rejected_mask & (df["DEFAULT_NEXT_MONTH"] == 0)]["BILL_AMT1"].sum())
        lost_interest_income = rej_good_balance * 0.15
        net_financial_benefit = rej_defaults_balance - lost_interest_income
    else:
        rej_defaults_balance = 0.0
        lost_interest_income = 0.0
        net_financial_benefit = 0.0

    return {
        "score_cutoff": score_cutoff,
        "total_accounts": total,
        "approved_count": approved_count,
        "approved_pct": approved_pct,
        "rejected_count": rejected_count,
        "portfolio_default_rate": portfolio_default_rate,
        "approved_default_rate": approved_default_rate,
        "avoided_defaults": avoided_defaults,
        "avoided_defaults_pct": avoided_defaults_pct,
        "avoided_losses_ntd": rej_defaults_balance,
        "lost_interest_income": lost_interest_income,
        "net_financial_benefit": net_financial_benefit
    }


def load_model_metrics() -> dict:
    """
    Loads saved model evaluation metrics, benchmark comparison, and feature importances.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    metrics_path = os.path.join(base_dir, "models", "model_metrics.json")
    if os.path.exists(metrics_path):
        try:
            with open(metrics_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

