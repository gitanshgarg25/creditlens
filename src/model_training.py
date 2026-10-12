"""
CreditLens - Model Training & Evaluation Module
Trains, compares, calibrates, and evaluates machine learning models for credit default prediction.
Computes ROC-AUC, PR-AUC, KS Statistic, Confusion Matrix, and feature importances.
"""

from __future__ import annotations
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    brier_score_loss,
    roc_curve
)

try:
    from risk_scoring import enrich_with_scores_and_tiers
except (ImportError, ModuleNotFoundError):
    from src.risk_scoring import enrich_with_scores_and_tiers

PROCESSED_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed")
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")


def calculate_ks_statistic(y_true, y_prob):
    """
    Computes the Kolmogorov-Smirnov (KS) statistic, standard in retail credit risk.
    KS measures maximum separation between cumulative default and non-default distributions.
    """
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    ks = np.max(tpr - fpr)
    return float(ks)


def get_feature_list():
    """
    Returns standard credit scoring feature set.
    """
    return [
        "LIMIT_BAL", "SEX", "EDUCATION", "MARRIAGE", "AGE",
        "PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6",
        "BILL_AMT1", "BILL_AMT2", "BILL_AMT3", "BILL_AMT4", "BILL_AMT5", "BILL_AMT6",
        "PAY_AMT1", "PAY_AMT2", "PAY_AMT3", "PAY_AMT4", "PAY_AMT5", "PAY_AMT6",
        "AVG_UTILIZATION_RATE", "MAX_UTILIZATION_RATE",
        "MAX_DELINQUENCY_MONTHS", "NUM_MONTHS_DELINQUENT",
        "DELINQUENCY_TREND", "AVG_PAYMENT_RATIO", "REVOLVING_BURDEN_RATIO"
    ]


def train_and_evaluate_models():
    """
    Executes full modeling pipeline: feature ingestion, training, evaluation, scoring, and persistence.
    """
    os.makedirs(MODELS_DIR, exist_ok=True)
    features_csv = os.path.join(PROCESSED_DATA_DIR, "credit_lens_features.csv")
    
    if not os.path.exists(features_csv):
        try:
            from feature_engineering import run_feature_engineering_pipeline
        except (ImportError, ModuleNotFoundError):
            from src.feature_engineering import run_feature_engineering_pipeline
        df = run_feature_engineering_pipeline()
    else:
        df = pd.read_csv(features_csv)

    feature_cols = get_feature_list()
    target_col = "DEFAULT_NEXT_MONTH"
    
    X = df[feature_cols].copy().fillna(0)
    y = df[target_col].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    
    print(f"[Modeling] Train sample size: {len(X_train)} | Test sample size: {len(X_test)}")
    print(f"[Modeling] Test Default Prevalence: {y_test.mean():.2%}")

    # 1. Model A: Logistic Regression (Regulatory Benchmark)
    lr_pipeline = Pipeline([
        ("scaler", StandardScaler()),
        ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42))
    ])
    lr_pipeline.fit(X_train, y_train)
    lr_prob = lr_pipeline.predict_proba(X_test)[:, 1]
    lr_pred = (lr_prob >= 0.5).astype(int)

    # 2. Model B: Random Forest (Industry Non-Linear Champion)
    rf_classifier = RandomForestClassifier(
        n_estimators=120,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
    rf_classifier.fit(X_train, y_train)
    rf_prob = rf_classifier.predict_proba(X_test)[:, 1]
    rf_pred = (rf_prob >= 0.5).astype(int)

    # Compute Metrics for both
    def eval_suite(y_true, y_prob, y_pred):
        cm = confusion_matrix(y_true, y_pred)
        return {
            "roc_auc": round(float(roc_auc_score(y_true, y_prob)), 4),
            "pr_auc": round(float(average_precision_score(y_true, y_prob)), 4),
            "ks_statistic": round(calculate_ks_statistic(y_true, y_prob), 4),
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            "brier_score": round(float(brier_score_loss(y_true, y_prob)), 4),
            "confusion_matrix": cm.tolist()
        }

    lr_metrics = eval_suite(y_test, lr_prob, lr_pred)
    rf_metrics = eval_suite(y_test, rf_prob, rf_pred)
    
    print("\n--- Model Benchmark Results ---")
    print(f"Logistic Regression: ROC-AUC={lr_metrics['roc_auc']:.4f} | PR-AUC={lr_metrics['pr_auc']:.4f} | KS={lr_metrics['ks_statistic']:.4f}")
    print(f"Random Forest (Champion): ROC-AUC={rf_metrics['roc_auc']:.4f} | PR-AUC={rf_metrics['pr_auc']:.4f} | KS={rf_metrics['ks_statistic']:.4f}")

    # Feature importances from Random Forest
    importances = rf_classifier.feature_importances_
    feat_imp = sorted(
        [{"feature": col, "importance": round(float(imp), 4)} for col, imp in zip(feature_cols, importances)],
        key=lambda x: x["importance"],
        reverse=True
    )

    # Logistic Regression odds ratios / coefficients
    lr_coefs = lr_pipeline.named_steps["classifier"].coef_[0]
    lr_imp = sorted(
        [{"feature": col, "coefficient": round(float(c), 4), "odds_ratio": round(float(np.exp(c)), 4)} 
         for col, c in zip(feature_cols, lr_coefs)],
        key=lambda x: abs(x["coefficient"]),
        reverse=True
    )

    # Save artifacts
    champion_model_path = os.path.join(MODELS_DIR, "credit_risk_model.joblib")
    benchmark_model_path = os.path.join(MODELS_DIR, "logistic_regression_benchmark.joblib")
    joblib.dump(rf_classifier, champion_model_path)
    joblib.dump(lr_pipeline, benchmark_model_path)

    metrics_payload = {
        "dataset_summary": {
            "total_records": len(df),
            "features_count": len(feature_cols),
            "train_size": len(X_train),
            "test_size": len(X_test),
            "default_prevalence": round(float(df[target_col].mean()), 4)
        },
        "features": feature_cols,
        "champion_model": "Random Forest Classifier",
        "champion_metrics": rf_metrics,
        "benchmark_model": "Logistic Regression (Balanced)",
        "benchmark_metrics": lr_metrics,
        "feature_importances": feat_imp,
        "logistic_coefficients": lr_imp
    }

    metrics_path = os.path.join(MODELS_DIR, "model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"[Modeling] Metrics saved to: {metrics_path}")

    # Score full dataset with champion model for portfolio tape and BI
    full_prob = rf_classifier.predict_proba(X)[:, 1]
    df["PREDICTED_PD"] = np.round(full_prob, 4)
    df_scored = enrich_with_scores_and_tiers(df, pd_col="PREDICTED_PD")

    tableau_extract_path = os.path.join(PROCESSED_DATA_DIR, "credit_lens_tableau_extract.csv")
    df_scored.to_csv(tableau_extract_path, index=False)
    print(f"[Modeling] Scored full portfolio and saved extract to: {tableau_extract_path}")

    return df_scored, metrics_payload


if __name__ == "__main__":
    train_and_evaluate_models()
