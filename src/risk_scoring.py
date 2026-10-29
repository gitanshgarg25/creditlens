"""
CreditLens - Risk Scoring & Strategy Module
Standardizes credit default probabilities into Custom Credit Risk Scores (300–850),
segments borrowers into strategic risk tiers, and generates policy-driven risk actions.

DISCLAIMER: The credit risk score generated herein is a custom illustrative scoring
scale (300 to 850) scaled for internal demonstration and underwriting simulation.
It is NOT an official Fair Isaac Corporation (FICO) score, bureau-issued credit score,
or an industry-validated credit bureau rating.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def pd_to_credit_score(pd_series):
    """
    Translates Probability of Default (PD) into a Custom Credit Risk Score (300–850).
    Higher scores represent lower predicted credit risk.
    Formula: Score = round(850 - (PD * 550)), clipped to [300, 850].

    Edge case handling:
    - Empty input -> empty int array.
    - Missing/NaN PD -> imputed with portfolio baseline default prevalence (0.2212).
    - Out of range (PD < 0.0 or PD > 1.0) -> strictly clipped to [300, 850].
    """
    arr = np.asarray(pd_series, dtype=float)
    if arr.size == 0:
        return np.array([], dtype=int)
    # Handle NaNs and infs safely: impute baseline default prevalence (0.2212)
    arr = np.nan_to_num(arr, nan=0.2212, posinf=1.0, neginf=0.0)
    scores = np.round(850.0 - (arr * 550.0))
    return np.clip(scores, 300, 850).astype(int)


def classify_risk_tier(score):
    """
    Maps 300-850 Custom Credit Risk Score to strategic risk tiers:
    - Prime: 720 to 850 (Illustrative low risk: PD < 12%)
    - Near-Prime: 660 to 719 (Illustrative moderate risk: PD 12% to 25%)
    - Subprime: 580 to 659 (Illustrative elevated risk: PD 25% to 45%)
    - High Risk: 300 to 579 (Illustrative high risk: PD >= 45%)
    """
    try:
        s = int(round(float(score)))
    except (ValueError, TypeError):
        return "High Risk"

    if s >= 720:
        return "Prime"
    elif s >= 660:
        return "Near-Prime"
    elif s >= 580:
        return "Subprime"
    else:
        return "High Risk"


def assign_recommended_action(row):
    """
    Generates actionable underwriting and risk management directives based on tier and flags.
    """
    tier = row.get("RISK_TIER", "High Risk")
    max_delinq = row.get("MAX_DELINQUENCY_MONTHS", 0)
    util = row.get("AVG_UTILIZATION_RATE", 0.0)
    ews = row.get("EARLY_WARNING_FLAG", 0)

    try:
        util = float(util)
    except (ValueError, TypeError):
        util = 0.0

    try:
        max_delinq = int(max_delinq)
    except (ValueError, TypeError):
        max_delinq = 0

    if tier == "Prime":
        if util > 0.85:
            return "Monitor Utilization; Temporary Line Cap"
        return "Standard Servicing; Eligible for Pre-Approved Credit Increase"
    elif tier == "Near-Prime":
        if max_delinq >= 1:
            return "Payment Reminder SMS; Hold Credit Line Increases"
        return "Routine 6-Month Review; Maintain Active Limit"
    elif tier == "Subprime":
        if ews:
            return "EWS Warning Alert; Restrict Cash Advances & Soft Collections"
        return "Freeze Credit Line; Request Partial Balance Paydown"
    else:  # High Risk
        return "Urgent Collections Outreach; Suspension of Card Privileges"


def enrich_with_scores_and_tiers(df, pd_col="PREDICTED_PD"):
    """
    Applies scoring formulas to a dataframe containing predicted PD.
    """
    df = df.copy()
    if pd_col in df.columns:
        df["CREDIT_RISK_SCORE"] = pd_to_credit_score(df[pd_col])
    elif "CREDIT_RISK_SCORE" not in df.columns:
        df["CREDIT_RISK_SCORE"] = 632
    df["RISK_TIER"] = df["CREDIT_RISK_SCORE"].apply(classify_risk_tier)
    df["RECOMMENDED_ACTION"] = df.apply(assign_recommended_action, axis=1)
    return df
