"""
CreditLens - Feature Engineering Module
Computes credit risk metrics, financial ratios, delinquency trajectories,
and early-warning indicators for credit risk modeling and portfolio monitoring.
"""

import os
import pandas as pd
import numpy as np

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes industry-standard credit risk features from cleaned client data.
    """
    df = df.copy()
    
    # 1. Credit Utilization Ratios (Clamped to prevent negative or infinite artifacts)
    bill_cols = ["BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6"]
    pay_cols = ["PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6"]
    status_cols = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]
    
    for i, col in enumerate(bill_cols, start=1):
        # Clip negative bills (credits) to 0 for utilization
        util_col = f"UTILIZATION_{i}"
        df[util_col] = (df[col].clip(lower=0) / df["LIMIT_BAL"]).clip(upper=3.0)

    util_feature_cols = [f"UTILIZATION_{i}" for i in range(1, 7)]
    df["AVG_UTILIZATION_RATE"] = df[util_feature_cols].mean(axis=1)
    df["MAX_UTILIZATION_RATE"] = df[util_feature_cols].max(axis=1)
    df["UTILIZATION_SEP"] = df["UTILIZATION_1"]
    
    # 2. Delinquency Trajectory & Severity
    # Max delay experienced across the 6-month window
    df["MAX_DELINQUENCY_MONTHS"] = df[status_cols].max(axis=1).clip(lower=0)
    # Number of months with past-due status (> 0)
    df["NUM_MONTHS_DELINQUENT"] = (df[status_cols] > 0).sum(axis=1)
    # Delinquency Trend: September status minus April status (positive = worsening)
    df["DELINQUENCY_TREND"] = df["PAY_0"].clip(lower=0) - df["PAY_6"].clip(lower=0)
    
    # 3. Payment to Bill Ratios (Ability to amortize debt)
    for i, (b_col, p_col) in enumerate(zip(bill_cols, pay_cols), start=1):
        ratio_col = f"PAY_TO_BILL_{i}"
        safe_bill = df[b_col].clip(lower=1.0)
        df[ratio_col] = (df[p_col] / safe_bill).clip(upper=2.0)
        
    pay_ratio_cols = [f"PAY_TO_BILL_{i}" for i in range(1, 7)]
    df["AVG_PAYMENT_RATIO"] = df[pay_ratio_cols].mean(axis=1)
    df["LATEST_PAY_RATIO"] = df["PAY_TO_BILL_1"]

    # 4. Total Aggregate Balances & Net Debt Expansion
    df["TOTAL_BILL_AMOUNT"] = df[bill_cols].sum(axis=1)
    df["TOTAL_PAYMENT_AMOUNT"] = df[pay_cols].sum(axis=1)
    df["NET_BALANCE_GROWTH"] = df["BILL_AMT1"] - df["BILL_AMT6"]
    
    # Unpaid revolving burden relative to limit
    unpaid_balance = (df["TOTAL_BILL_AMOUNT"] - df["TOTAL_PAYMENT_AMOUNT"]).clip(lower=0)
    df["REVOLVING_BURDEN_RATIO"] = (unpaid_balance / (df["LIMIT_BAL"] + 1)).clip(upper=5.0)

    # 5. Early-Warning System (EWS) Trigger Flag
    df["EARLY_WARNING_FLAG"] = compute_early_warning_flags(df)

    return df


def compute_early_warning_flags(df: pd.DataFrame) -> pd.Series:
    """
    Computes Early-Warning System (EWS) triage indicator for pre-delinquency credit surveillance.
    
    Unified Rule (Educational Prototype):
    An account triggers an early-warning alert (flag = 1) if EITHER condition is met:
    1. Average Credit Line Utilization >= 80% (AVG_UTILIZATION_RATE >= 0.80):
       Indicates severe borrowing strain, high revolving balance burden, and near-exhaustion of available limit.
    2. Payment Delinquency >= 1 Month (MAX_DELINQUENCY_MONTHS >= 1):
       Indicates observable repayment friction, payment delay, or past-due status during the 6-month window.
       
    Safe Missing/Invalid Data Handling:
    If either utilization or delinquency values are missing (NaN), null, or invalid for an account,
    it is conservatively treated as flagged (1) for human underwriting review rather than silently
    assumed to be performing and safe.
    
    Returns:
        pd.Series (int): Binary indicator (1 = Active Warning Alert, 0 = Normal Status).
    """
    if "AVG_UTILIZATION_RATE" not in df.columns or "MAX_DELINQUENCY_MONTHS" not in df.columns:
        return pd.Series(1, index=df.index, dtype=int)

    util = pd.to_numeric(df["AVG_UTILIZATION_RATE"], errors="coerce")
    delinq = pd.to_numeric(df["MAX_DELINQUENCY_MONTHS"], errors="coerce")

    # Missing or corrupted values are conservatively treated as alerts
    is_missing = util.isna() | delinq.isna()
    is_high_util = util >= 0.80
    is_delinquent = delinq >= 1

    return (is_high_util | is_delinquent | is_missing).astype(int)


def run_feature_engineering_pipeline():
    """
    Loads cleaned data, engineers features, and saves output.
    """
    clean_path = os.path.join(PROCESSED_DATA_DIR, "credit_lens_clean.csv")
    if not os.path.exists(clean_path):
        try:
            from data_ingestion import run_ingestion_pipeline
        except (ImportError, ModuleNotFoundError):
            from src.data_ingestion import run_ingestion_pipeline
        df = run_ingestion_pipeline()
    else:
        df = pd.read_csv(clean_path)
        
    df_featured = engineer_features(df)
    features_path = os.path.join(PROCESSED_DATA_DIR, "credit_lens_features.csv")
    df_featured.to_csv(features_path, index=False)
    print(f"[Feature Engineering] Success! Engineered {df_featured.shape[1]} features for {len(df_featured)} records.")
    print(f"[Feature Engineering] Saved to: {features_path}")
    print(f"[Feature Engineering] Early-Warning Flag Trigger Rate: {df_featured['EARLY_WARNING_FLAG'].mean():.2%}")
    return df_featured


if __name__ == "__main__":
    run_feature_engineering_pipeline()
