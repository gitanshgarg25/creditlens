"""
CreditLens - Comprehensive Automated Test Suite
Tests data ingestion cleaning, feature calculations, risk scoring formulas,
train/test separation, model probability bounds, policy simulation tradeoffs,
illustrative ECL calculations, database connectivity, and SQL query execution.
"""

import os
import sys
import unittest
import sqlite3
import joblib
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from src.risk_scoring import pd_to_credit_score, classify_risk_tier, assign_recommended_action
from src.feature_engineering import engineer_features
from src.analytics_engine import (
    get_portfolio_kpis,
    get_executive_insights,
    get_underwriting_policy_tradeoff,
    compute_ecl,
    load_model_metrics
)
from src.model_training import get_feature_list, calculate_ks_statistic


class TestCreditLensPipeline(unittest.TestCase):

    def setUp(self):
        # Create minimal synthetic record for validation
        self.sample_df = pd.DataFrame([{
            "ID": 1,
            "LIMIT_BAL": 100000.0,
            "SEX": 1,
            "EDUCATION": 1,
            "MARRIAGE": 2,
            "AGE": 30,
            "PAY_0": 0, "PAY_2": 0, "PAY_3": 0, "PAY_4": 0, "PAY_5": 0, "PAY_6": 0,
            "BILL_AMT1": 20000.0, "BILL_AMT2": 20000.0, "BILL_AMT3": 20000.0,
            "BILL_AMT4": 20000.0, "BILL_AMT5": 20000.0, "BILL_AMT6": 20000.0,
            "PAY_AMT1": 2000.0, "PAY_AMT2": 2000.0, "PAY_AMT3": 2000.0,
            "PAY_AMT4": 2000.0, "PAY_AMT5": 2000.0, "PAY_AMT6": 2000.0,
            "DEFAULT_NEXT_MONTH": 0
        }])

    def test_credit_score_bounds_and_direction(self):
        """Verifies custom credit score scale (300 to 850) and monotonic inverse direction with PD."""
        self.assertEqual(pd_to_credit_score([0.0])[0], 850)
        self.assertEqual(pd_to_credit_score([1.0])[0], 300)
        self.assertTrue(300 <= pd_to_credit_score([0.5])[0] <= 850)

        # Monotonicity test: as PD increases, score must decrease monotonically
        pds = np.linspace(0.0, 1.0, 50)
        scores = pd_to_credit_score(pds)
        for i in range(len(scores) - 1):
            self.assertGreaterEqual(
                scores[i], scores[i + 1],
                f"Score non-monotonic at index {i}: PD {pds[i]} -> {scores[i]}, PD {pds[i+1]} -> {scores[i+1]}"
            )

    def test_credit_score_edge_cases(self):
        """Verifies credit score behavior on empty, NaN, negative, and out-of-range inputs."""
        # Empty input
        empty_res = pd_to_credit_score([])
        self.assertEqual(len(empty_res), 0)

        # NaN input (must impute baseline default rate ~0.2212 without raising runtime warnings)
        nan_res = pd_to_credit_score([np.nan])
        self.assertEqual(len(nan_res), 1)
        self.assertTrue(300 <= nan_res[0] <= 850)

        # Out-of-range floats
        self.assertEqual(pd_to_credit_score([-0.5])[0], 850)
        self.assertEqual(pd_to_credit_score([1.5])[0], 300)

    def test_risk_tier_classification(self):
        """Verifies risk tier cutoff thresholds and safe non-numeric fallback."""
        self.assertEqual(classify_risk_tier(750), "Prime")
        self.assertEqual(classify_risk_tier(680), "Near-Prime")
        self.assertEqual(classify_risk_tier(600), "Subprime")
        self.assertEqual(classify_risk_tier(500), "High Risk")
        # Boundary edges
        self.assertEqual(classify_risk_tier(720), "Prime")
        self.assertEqual(classify_risk_tier(660), "Near-Prime")
        self.assertEqual(classify_risk_tier(580), "Subprime")
        self.assertEqual(classify_risk_tier(300), "High Risk")
        # Fallback for None/NaN
        self.assertEqual(classify_risk_tier(None), "High Risk")

    def test_assign_recommended_action(self):
        """Verifies policy action assignment by tier and early warning flag."""
        action_prime = assign_recommended_action({"RISK_TIER": "Prime", "AVG_UTILIZATION_RATE": 0.20})
        self.assertIn("Eligible for Pre-Approved Credit Increase", action_prime)

        action_prime_high_util = assign_recommended_action({"RISK_TIER": "Prime", "AVG_UTILIZATION_RATE": 0.90})
        self.assertIn("Monitor Utilization", action_prime_high_util)

        action_high_risk = assign_recommended_action({"RISK_TIER": "High Risk"})
        self.assertIn("Urgent Collections Outreach", action_high_risk)

    def test_feature_engineering_math(self):
        """Verifies utilization rate and early warning trigger logic."""
        feat_df = engineer_features(self.sample_df)
        self.assertAlmostEqual(feat_df["AVG_UTILIZATION_RATE"].iloc[0], 0.20, places=2)
        self.assertEqual(feat_df["EARLY_WARNING_FLAG"].iloc[0], 0)
        
        # Test distressed scenario (delinquency >= 1 month triggers EWS)
        distressed_df = self.sample_df.copy()
        distressed_df["PAY_0"] = 2
        feat_distressed = engineer_features(distressed_df)
        self.assertEqual(feat_distressed["EARLY_WARNING_FLAG"].iloc[0], 1)

        # Test high utilization trigger (avg utilization >= 80% triggers EWS)
        high_util_df = self.sample_df.copy()
        for i in range(1, 7):
            high_util_df[f"BILL_AMT{i}"] = 85000.0
        feat_high_util = engineer_features(high_util_df)
        self.assertEqual(feat_high_util["EARLY_WARNING_FLAG"].iloc[0], 1)

    def test_feature_target_separation(self):
        """Verifies that no target, identifier, or leak variables are present in model feature list."""
        features = get_feature_list()
        leak_candidates = ["DEFAULT_NEXT_MONTH", "ID", "EARLY_WARNING_FLAG", "PREDICTED_PD", "CREDIT_RISK_SCORE", "IS_TEST_SAMPLE"]
        for leak in leak_candidates:
            self.assertNotIn(
                leak, features,
                f"Data leakage risk: '{leak}' found in model training feature list!"
            )

    def test_expected_feature_count(self):
        """Verifies model utilizes exactly 30 engineered features."""
        features = get_feature_list()
        self.assertEqual(len(features), 30, f"Expected 30 features, but found {len(features)}")

    def test_train_test_split_integrity(self):
        """Verifies 80/20 train/test split on full dataset yields 24k/6k records with zero overlap."""
        raw_csv = os.path.join(BASE_DIR, "data", "processed", "credit_lens_clean.csv")
        if not os.path.exists(raw_csv):
            self.skipTest(f"Clean CSV not found at {raw_csv}")

        from sklearn.model_selection import train_test_split
        df = pd.read_csv(raw_csv)
        self.assertEqual(len(df), 30000, f"Expected 30,000 records, found {len(df)}")

        target_col = "DEFAULT_NEXT_MONTH"
        X = df.drop(columns=[target_col])
        y = df[target_col]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=42, stratify=y
        )

        self.assertEqual(len(X_train), 24000)
        self.assertEqual(len(X_test), 6000)

        # Disjoint verification
        overlap = set(X_train.index).intersection(set(X_test.index))
        self.assertEqual(len(overlap), 0, "Train and Test sets contain overlapping index rows!")

        # Stratification check (prevalence ~ 22.12%)
        train_prev = y_train.mean()
        test_prev = y_test.mean()
        self.assertAlmostEqual(train_prev, 0.2212, places=3)
        self.assertAlmostEqual(test_prev, 0.2212, places=3)

    def test_champion_model_prediction_bounds(self):
        """Verifies loaded champion model predicts probabilities bounded strictly within [0, 1]."""
        model_path = os.path.join(BASE_DIR, "models", "credit_risk_model.joblib")
        self.assertTrue(os.path.exists(model_path), f"Champion model missing at {model_path}")

        rf_model = joblib.load(model_path)
        feature_cols = get_feature_list()

        # Build synthetic test dataframe containing all 30 engineered features
        engineered = engineer_features(self.sample_df)
        X_sample = engineered[feature_cols]

        prob = rf_model.predict_proba(X_sample)[:, 1]
        self.assertEqual(len(prob), 1)
        self.assertGreaterEqual(prob[0], 0.0)
        self.assertLessEqual(prob[0], 1.0)

    def test_ks_statistic_calculation(self):
        """Verifies Kolmogorov-Smirnov statistic returns valid float in [0.0, 1.0]."""
        y_true = np.array([0, 0, 0, 1, 1, 1])
        # Perfect discrimination
        y_prob_perf = np.array([0.05, 0.10, 0.15, 0.85, 0.90, 0.95])
        ks_perf = calculate_ks_statistic(y_true, y_prob_perf)
        self.assertAlmostEqual(ks_perf, 1.0, places=2)

        # Random guessing
        y_prob_rand = np.array([0.5, 0.5, 0.5, 0.5, 0.5, 0.5])
        ks_rand = calculate_ks_statistic(y_true, y_prob_rand)
        self.assertAlmostEqual(ks_rand, 0.0, places=2)

    def test_underwriting_policy_tradeoff_logic_and_empty(self):
        """Verifies underwriting policy tradeoff logic and empty DataFrame safety."""
        test_df = pd.DataFrame([
            {"CREDIT_RISK_SCORE": 750, "DEFAULT_NEXT_MONTH": 0, "BILL_AMT1": 50000.0},
            {"CREDIT_RISK_SCORE": 650, "DEFAULT_NEXT_MONTH": 0, "BILL_AMT1": 30000.0},
            {"CREDIT_RISK_SCORE": 520, "DEFAULT_NEXT_MONTH": 1, "BILL_AMT1": 40000.0}
        ])
        tradeoff = get_underwriting_policy_tradeoff(test_df, score_cutoff=620)
        self.assertEqual(tradeoff["approved_count"], 2)
        self.assertEqual(tradeoff["rejected_count"], 1)
        self.assertEqual(tradeoff["avoided_defaults"], 1)
        self.assertEqual(tradeoff["approved_default_rate"], 0.0)
        self.assertEqual(tradeoff["approved_count"] + tradeoff["rejected_count"], 3)

        # Empty DataFrame safety test
        empty_tradeoff = get_underwriting_policy_tradeoff(pd.DataFrame(), score_cutoff=620)
        self.assertIsInstance(empty_tradeoff, dict)
        self.assertEqual(empty_tradeoff["approved_count"], 0)
        self.assertEqual(empty_tradeoff["net_financial_benefit"], 0.0)

    def test_compute_ecl_math_and_empty(self):
        """Verifies illustrative ECL calculation math and empty DataFrame safety."""
        # Drawn = 20k, Limit = 100k -> Undrawn = 80k.
        # CCF = 20% -> EAD = 20k + 0.20 * 80k = 36,000 NTD.
        # PD = 0.10, LGD = 0.45 -> ECL = 36,000 * 0.10 * 0.45 = 1,620 NTD.
        sample_ecl = pd.DataFrame([{
            "LIMIT_BAL": 100000.0,
            "BILL_AMT1": 20000.0,
            "PREDICTED_PD": 0.10
        }])
        res = compute_ecl(sample_ecl, lgd=0.45, ccf=0.20)
        self.assertEqual(res["total_ead"], 36000.0)
        self.assertEqual(res["total_ecl"], 1620.0)
        self.assertAlmostEqual(res["portfolio_ecl_coverage_pct"], 4.5, places=1)

        # Empty DataFrame test
        empty_ecl = compute_ecl(pd.DataFrame())
        self.assertIsInstance(empty_ecl, dict)
        self.assertEqual(empty_ecl["total_ead"], 0.0)
        self.assertEqual(empty_ecl["total_ecl"], 0.0)

    def test_portfolio_kpis(self):
        """Verifies KPI aggregation mathematics."""
        df = self.sample_df.copy()
        df["CREDIT_RISK_SCORE"] = 750
        df["PREDICTED_PD"] = 0.05
        df["EARLY_WARNING_FLAG"] = 0
        df["AVG_UTILIZATION_RATE"] = 0.2
        kpis = get_portfolio_kpis(df)
        self.assertEqual(kpis["total_borrowers"], 1)
        self.assertEqual(kpis["total_exposure"], 100000.0)
        self.assertEqual(kpis["portfolio_avg_score"], 750.0)

    def test_executive_insights(self):
        """Verifies executive insights calculations."""
        test_df = pd.DataFrame([
            {"PAY_0": 0, "LIMIT_BAL": 250000, "AVG_UTILIZATION_RATE": 0.2, "DEFAULT_NEXT_MONTH": 0, "BILL_AMT1": 50000, "RISK_TIER": "Prime", "PREDICTED_PD": 0.05},
            {"PAY_0": 2, "LIMIT_BAL": 40000, "AVG_UTILIZATION_RATE": 0.9, "DEFAULT_NEXT_MONTH": 1, "BILL_AMT1": 36000, "RISK_TIER": "High Risk", "PREDICTED_PD": 0.85}
        ])
        insights = get_executive_insights(test_df)
        self.assertIn("delinq_multiplier", insights)
        self.assertIn("limit_multiplier", insights)
        self.assertIn("util_multiplier", insights)
        self.assertEqual(insights["distressed_accounts"], 1)

    def test_load_model_metrics(self):
        """Verifies structure and keys in model_metrics.json."""
        metrics = load_model_metrics()
        self.assertIn("champion_model", metrics)
        self.assertIn("champion_metrics", metrics)
        self.assertIn("benchmark_metrics", metrics)
        self.assertIn("holdout_confusion_dollars", metrics)
        self.assertIn("dataset_summary", metrics)
        self.assertIn("risk_drivers", metrics)
        self.assertIn("roc_auc", metrics["champion_metrics"])

    def test_analytical_sql_queries_execution(self):
        """Verifies all 6 SQL queries in analytical_queries.sql execute cleanly on credit_lens.db."""
        db_path = os.path.join(BASE_DIR, "database", "credit_lens.db")
        sql_path = os.path.join(BASE_DIR, "database", "analytical_queries.sql")
        self.assertTrue(os.path.exists(db_path), f"SQLite DB missing at {db_path}")
        self.assertTrue(os.path.exists(sql_path), f"SQL script missing at {sql_path}")

        with open(sql_path, "r", encoding="utf-8") as f:
            sql_text = f.read()

        raw_queries = sql_text.split(";")
        conn = sqlite3.connect(db_path)
        executed_count = 0
        try:
            for q in raw_queries:
                clean_lines = [l for l in q.splitlines() if not l.strip().startswith("--")]
                stmt = "\n".join(clean_lines).strip()
                if stmt:
                    cursor = conn.execute(stmt)
                    rows = cursor.fetchall()
                    self.assertGreater(
                        len(rows), 0,
                        f"SQL query returned 0 rows: {stmt[:60]}..."
                    )
                    executed_count += 1
        finally:
            conn.close()

        self.assertEqual(executed_count, 6, f"Expected 6 SQL analytical queries, executed {executed_count}")

    def test_readme_benchmark_metrics_match_json(self):
        """
        Parses the README benchmark table and asserts every metric equals
        models/model_metrics.json champion (RF) and benchmark (LR) to printed precision.
        """
        import re
        metrics = load_model_metrics()
        rf_m = metrics["champion_metrics"]
        lr_m = metrics["benchmark_metrics"]

        readme_path = os.path.join(BASE_DIR, "README.md")
        self.assertTrue(os.path.exists(readme_path), "README.md not found")

        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()

        table_lines = [
            line.strip() for line in content.splitlines()
            if line.strip().startswith("|") and "**" in line
        ]

        metric_key_map = {
            "ROC-AUC": "roc_auc",
            "KS Statistic": "ks_statistic",
            "PR-AUC": "pr_auc",
            "Classification Accuracy": "accuracy",
            "Precision": "precision",
            "Recall": "recall",
            "F1-Score": "f1_score",
            "Brier Score": "brier_score"
        }

        def parse_metric_cell(cell_str):
            clean = cell_str.replace("*", "").strip()
            m_pct = re.search(r"([0-9]+\.[0-9]+)%", clean)
            if m_pct:
                return float(m_pct.group(1)) / 100.0
            m_dec = re.search(r"([0-9]+\.[0-9]+)", clean)
            if m_dec:
                return float(m_dec.group(1))
            return None

        matched_count = 0
        for line in table_lines:
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) < 3:
                continue
            metric_label = parts[0].replace("*", "").strip()
            found_key = None
            for prefix, key in metric_key_map.items():
                if metric_label.startswith(prefix):
                    found_key = key
                    break
            if not found_key:
                continue

            rf_readme_val = parse_metric_cell(parts[1])
            lr_readme_val = parse_metric_cell(parts[2])

            self.assertIsNotNone(rf_readme_val, f"Failed to parse RF value from '{parts[1]}' for {metric_label}")
            self.assertIsNotNone(lr_readme_val, f"Failed to parse LR value from '{parts[2]}' for {metric_label}")

            self.assertAlmostEqual(
                rf_readme_val, rf_m[found_key], places=4,
                msg=f"RF metric {found_key} mismatch between README ({rf_readme_val}) and JSON ({rf_m[found_key]})"
            )
            self.assertAlmostEqual(
                lr_readme_val, lr_m[found_key], places=4,
                msg=f"LR metric {found_key} mismatch between README ({lr_readme_val}) and JSON ({lr_m[found_key]})"
            )
            matched_count += 1

        self.assertEqual(matched_count, 8, f"Expected 8 benchmark metric rows in README, found {matched_count}")

    def test_no_stale_metric_strings(self):
        """
        Fails if any obsolete/unverified metric strings appear in README.md,
        app/streamlit_app.py, or scripts/generate_model_report_docx.py:
        '128.2', '114.1', '54.3%', '34.2%', '2.1x', '29.2%', '5.03'.
        """
        stale_strings = ["128.2", "114.1", "54.3%", "34.2%", "2.1x", "29.2%", "5.03"]
        files_to_check = [
            os.path.join(BASE_DIR, "README.md"),
            os.path.join(BASE_DIR, "app", "streamlit_app.py"),
            os.path.join(BASE_DIR, "scripts", "generate_model_report_docx.py")
        ]

        violations = []
        for file_path in files_to_check:
            self.assertTrue(os.path.exists(file_path), f"File {file_path} not found")
            with open(file_path, "r", encoding="utf-8") as f:
                for line_idx, line in enumerate(f, start=1):
                    for stale in stale_strings:
                        if stale in line:
                            violations.append(f"{os.path.basename(file_path)}:L{line_idx} contains '{stale}': {line.strip()}")

        self.assertEqual(violations, [], f"Found stale metric strings:\n" + "\n".join(violations))


if __name__ == "__main__":
    unittest.main()
