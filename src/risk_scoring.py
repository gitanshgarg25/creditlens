"""
CreditLens - Risk Scoring & Strategy Module
Standardizes credit default probabilities into 300-850 Credit Risk Scores,
segments borrowers into risk tiers, and generates policy-driven risk actions.
"""

import numpy as np
import pandas as pd


def pd_to_credit_score(pd_series):
    """
    Translates Probability of Default (PD) into a standard 300-850 Credit Risk Score.
    Score = round(850 - (PD * 550)), clipped to [300, 850].
    """
    scores = np.round(850.0 - (np.asarray(pd_series) * 550.0))
    return np.clip(scores, 300, 850).astype(int)


def classify_risk_tier(score):
    """
    Maps 300-850 score to institutional risk tiers.
    """
    if score >= 720:
        return "Prime"
    elif score >= 660:
        return "Near-Prime"
    elif score >= 580:
        return "Subprime"
    else:
        return "High Risk"


def assign_recommended_action(row):
    """
    Generates actionable underwriting and risk management directives.
    """
    tier = row.get("RISK_TIER")
    max_delinq = row.get("MAX_DELINQUENCY_MONTHS", 0)
    util = row.get("AVG_UTILIZATION_RATE", 0.0)
    ews = row.get("EARLY_WARNING_FLAG", 0)
    
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
    df["CREDIT_RISK_SCORE"] = pd_to_credit_score(df[pd_col])
    df["RISK_TIER"] = df["CREDIT_RISK_SCORE"].apply(classify_risk_tier)
    df["RECOMMENDED_ACTION"] = df.apply(assign_recommended_action, axis=1)
    return df
