"""
CreditLens - Database Initialization Script
Sets up SQLite (default local zero-setup) and PostgreSQL (if DATABASE_URL is set).
Creates tables, populates historical client data and credit risk evaluations, and verifies integrity.
"""

import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROCESSED_DATA = os.path.join(BASE_DIR, "data", "processed", "credit_lens_tableau_extract.csv")
DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, "database", "credit_lens.db")


def get_db_engine():
    """
    Returns SQLAlchemy engine. Uses PostgreSQL if DATABASE_URL is present, else local SQLite.
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        print(f"[Database] Connecting to configured database: {db_url.split('@')[-1]}")
        return create_engine(db_url)
    
    os.makedirs(os.path.dirname(DEFAULT_SQLITE_PATH), exist_ok=True)
    sqlite_url = f"sqlite:///{DEFAULT_SQLITE_PATH}"
    print(f"[Database] Using local SQLite database: {DEFAULT_SQLITE_PATH}")
    return create_engine(sqlite_url)


def initialize_database():
    """
    Creates tables and loads scored portfolio data.
    """
    if not os.path.exists(PROCESSED_DATA):
        print("[Database] Scored dataset not found. Running training pipeline...")
        from src.model_training import train_and_evaluate_models
        train_and_evaluate_models()
        
    df = pd.read_csv(PROCESSED_DATA)
    print(f"[Database] Loaded {len(df)} rows from processed extract.")

    engine = get_db_engine()

    # 1. Prepare credit_card_clients dataframe
    clients_df = pd.DataFrame({
        "client_id": df["ID"].astype(int),
        "limit_bal": df["LIMIT_BAL"].astype(float),
        "sex_code": df["SEX"].astype(int),
        "education_code": df["EDUCATION"].astype(int),
        "marriage_code": df["MARRIAGE"].astype(int),
        "age": df["AGE"].astype(int),
        "pay_status_sep": df["PAY_0"].astype(int),
        "pay_status_aug": df["PAY_2"].astype(int),
        "pay_status_jul": df["PAY_3"].astype(int),
        "pay_status_jun": df["PAY_4"].astype(int),
        "pay_status_may": df["PAY_5"].astype(int),
        "pay_status_apr": df["PAY_6"].astype(int),
        "bill_amt_sep": df["BILL_AMT1"].astype(float),
        "bill_amt_aug": df["BILL_AMT2"].astype(float),
        "bill_amt_jul": df["BILL_AMT3"].astype(float),
        "bill_amt_jun": df["BILL_AMT4"].astype(float),
        "bill_amt_may": df["BILL_AMT5"].astype(float),
        "bill_amt_apr": df["BILL_AMT6"].astype(float),
        "pay_amt_sep": df["PAY_AMT1"].astype(float),
        "pay_amt_aug": df["PAY_AMT2"].astype(float),
        "pay_amt_jul": df["PAY_AMT3"].astype(float),
        "pay_amt_jun": df["PAY_AMT4"].astype(float),
        "pay_amt_may": df["PAY_AMT5"].astype(float),
        "pay_amt_apr": df["PAY_AMT6"].astype(float),
        "default_next_month": df["DEFAULT_NEXT_MONTH"].astype(int)
    })

    # 2. Prepare credit_risk_evaluations dataframe
    evaluations_df = pd.DataFrame({
        "evaluation_id": df["ID"].astype(int),
        "client_id": df["ID"].astype(int),
        "predicted_pd": df["PREDICTED_PD"].astype(float),
        "credit_risk_score": df["CREDIT_RISK_SCORE"].astype(int),
        "risk_tier": df["RISK_TIER"].astype(str),
        "avg_utilization_rate": df["AVG_UTILIZATION_RATE"].astype(float),
        "max_delinquency_months": df["MAX_DELINQUENCY_MONTHS"].astype(int),
        "revolving_burden_ratio": df["REVOLVING_BURDEN_RATIO"].astype(float),
        "early_warning_flag": df["EARLY_WARNING_FLAG"].astype(int),
        "recommended_action": df["RECOMMENDED_ACTION"].astype(str)
    })

    print("[Database] Writing tables to database...")
    with engine.begin() as conn:
        clients_df.to_sql("credit_card_clients", conn, if_exists="replace", index=False)
        evaluations_df.to_sql("credit_risk_evaluations", conn, if_exists="replace", index=False)

    print("[Database] Tables successfully created and indexed.")

    # Verification query
    with engine.connect() as conn:
        client_count = conn.execute(text("SELECT COUNT(*) FROM credit_card_clients")).scalar()
        eval_count = conn.execute(text("SELECT COUNT(*) FROM credit_risk_evaluations")).scalar()
        avg_score = conn.execute(text("SELECT AVG(credit_risk_score) FROM credit_risk_evaluations")).scalar()
        ews_count = conn.execute(text("SELECT COUNT(*) FROM credit_risk_evaluations WHERE early_warning_flag = 1")).scalar()

    print("\n--- Database Verification ---")
    print(f"Total Clients Loaded: {client_count}")
    print(f"Total Risk Evaluations Loaded: {eval_count}")
    print(f"Portfolio Average Score: {avg_score:.1f}")
    print(f"Total Early Warning Alerts: {ews_count}")
    print("[Database] Initialization complete!\n")


if __name__ == "__main__":
    initialize_database()
