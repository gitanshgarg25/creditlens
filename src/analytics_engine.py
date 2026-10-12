"""
CreditLens - Analytics & Business Intelligence Engine
Computes core credit risk portfolio aggregations, delinquency migration,
risk concentration, and portfolio watchlists for dashboards and reports.
"""

from __future__ import annotations
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
