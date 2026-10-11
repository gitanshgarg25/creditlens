"""
CreditLens - Data Ingestion Module
Downloads, validates, cleans, and standardizes the UCI Default of Credit Card Clients dataset.
"""

import os
import io
import zipfile
import requests
import pandas as pd
import numpy as np

UCI_ZIP_URL = "https://archive.ics.uci.edu/static/public/350/default+of+credit+card+clients.zip"
GITHUB_CSV_MIRROR = "https://raw.githubusercontent.com/yhat/Data-Science-in-Python/master/data/default_of_credit_card_clients.csv"

RAW_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")
PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")


def download_and_extract_raw():
    """
    Downloads UCI Default of Credit Card Clients dataset and saves raw file.
    Returns path to downloaded file.
    """
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
    
    xls_path = os.path.join(RAW_DATA_DIR, "default_of_credit_card_clients.xls")
    csv_path = os.path.join(RAW_DATA_DIR, "default_of_credit_card_clients.csv")
    
    if os.path.exists(xls_path):
        print(f"[Ingestion] Using existing raw XLS: {xls_path}")
        return xls_path
    if os.path.exists(csv_path):
        print(f"[Ingestion] Using existing raw CSV: {csv_path}")
        return csv_path

    print(f"[Ingestion] Fetching dataset from UCI Repository: {UCI_ZIP_URL}")
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(UCI_ZIP_URL, headers=headers, timeout=30)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            namelist = z.namelist()
            print(f"[Ingestion] Files in archive: {namelist}")
            # Locate .xls or .xlsx
            target_name = next((n for n in namelist if n.endswith((".xls", ".xlsx"))), None)
            if target_name:
                extracted_path = z.extract(target_name, path=RAW_DATA_DIR)
                # Normalize filename
                os.replace(extracted_path, xls_path)
                print(f"[Ingestion] Successfully extracted raw dataset to: {xls_path}")
                return xls_path
    except Exception as e:
        print(f"[Ingestion] UCI Zip download failed ({e}). Trying GitHub mirror...")
        try:
            resp_csv = requests.get(GITHUB_CSV_MIRROR, headers=headers, timeout=30)
            resp_csv.raise_for_status()
            with open(csv_path, "wb") as f:
                f.write(resp_csv.content)
            print(f"[Ingestion] Downloaded CSV mirror to: {csv_path}")
            return csv_path
        except Exception as err:
            raise RuntimeError(f"Failed to fetch dataset from both primary and mirror sources: {err}")


def load_raw_dataset(file_path):
    """
    Loads raw excel or csv file, handling header variations.
    """
    if file_path.endswith((".xls", ".xlsx")):
        # UCI Excel file typically has metadata row 0 ('X1', 'X2'...) and actual names in row 1
        try:
            df = pd.read_excel(file_path, header=1)
        except Exception:
            df = pd.read_excel(file_path)
    else:
        # CSV load
        df = pd.read_csv(file_path)
        if "X1" in df.iloc[0].values or "LIMIT_BAL" in df.iloc[0].values:
            df = pd.read_csv(file_path, skiprows=1)
            
    # Clean up column names
    df.columns = [c.strip().upper() for c in df.columns]
    
    # Rename PAY_0 to PAY_1 if needed for consistency, or standardize to PAY_0
    rename_map = {
        "PAY_1": "PAY_0",
        "DEFAULT PAYMENT NEXT MONTH": "DEFAULT_NEXT_MONTH",
        "DEFAULT.PAYMENT.NEXT.MONTH": "DEFAULT_NEXT_MONTH",
        "Y": "DEFAULT_NEXT_MONTH"
    }
    df = df.rename(columns=rename_map)
    return df


def clean_dataset(df):
    """
    Cleans and standardizes columns and categorical values.
    """
    # Standardize column naming
    standard_cols = {
        "LIMIT_BAL": "LIMIT_BAL",
        "SEX": "SEX",
        "EDUCATION": "EDUCATION",
        "MARRIAGE": "MARRIAGE",
        "AGE": "AGE",
        "PAY_0": "PAY_0",
        "PAY_2": "PAY_2",
        "PAY_3": "PAY_3",
        "PAY_4": "PAY_4",
        "PAY_5": "PAY_5",
        "PAY_6": "PAY_6",
        "BILL_AMT1": "BILL_AMT1",
        "BILL_AMT2": "BILL_AMT2",
        "BILL_AMT3": "BILL_AMT3",
        "BILL_AMT4": "BILL_AMT4",
        "BILL_AMT5": "BILL_AMT5",
        "BILL_AMT6": "BILL_AMT6",
        "PAY_AMT1": "PAY_AMT1",
        "PAY_AMT2": "PAY_AMT2",
        "PAY_AMT3": "PAY_AMT3",
        "PAY_AMT4": "PAY_AMT4",
        "PAY_AMT5": "PAY_AMT5",
        "PAY_AMT6": "PAY_AMT6",
        "DEFAULT_NEXT_MONTH": "DEFAULT_NEXT_MONTH"
    }
    
    if "ID" in df.columns:
        standard_cols["ID"] = "ID"
        
    df = df[[c for c in standard_cols if c in df.columns]].copy()
    
    # Convert numerical columns
    num_cols = ["LIMIT_BAL", "AGE", "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
                "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
                "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
                "DEFAULT_NEXT_MONTH"]
    
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
            
    df = df.dropna(subset=["DEFAULT_NEXT_MONTH"])
    df["DEFAULT_NEXT_MONTH"] = df["DEFAULT_NEXT_MONTH"].astype(int)
    
    # Standardize Categorical Anomalies:
    # EDUCATION: 1: Grad School, 2: Univ, 3: High School, 4: Others (Map 0, 5, 6 to 4)
    df["EDUCATION"] = df["EDUCATION"].apply(lambda x: 4 if x not in [1, 2, 3] else int(x))
    
    # MARRIAGE: 1: Married, 2: Single, 3: Others (Map 0 to 3)
    df["MARRIAGE"] = df["MARRIAGE"].apply(lambda x: 3 if x not in [1, 2] else int(x))
    
    # SEX: 1: Male, 2: Female
    df["SEX"] = df["SEX"].apply(lambda x: 1 if x == 1 else 2)
    
    if "ID" not in df.columns:
        df["ID"] = np.arange(1, len(df) + 1)
    else:
        df["ID"] = df["ID"].astype(int)

    return df


def run_ingestion_pipeline():
    """
    Full ingestion workflow.
    """
    raw_file = download_and_extract_raw()
    df_raw = load_raw_dataset(raw_file)
    df_clean = clean_dataset(df_raw)
    
    output_path = os.path.join(PROCESSED_DATA_DIR, "credit_lens_clean.csv")
    df_clean.to_csv(output_path, index=False)
    print(f"[Ingestion] Complete! Saved {len(df_clean)} cleaned rows to: {output_path}")
    print(f"[Ingestion] Default Rate: {df_clean['DEFAULT_NEXT_MONTH'].mean():.2%}")
    return df_clean


if __name__ == "__main__":
    run_ingestion_pipeline()
