"""
CreditLens - Automated Test Suite
Tests data ingestion cleaning, feature calculations, risk scoring formulas, and database connectivity.
"""

import os
import sys
import unittest
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
    load_model_metrics
)


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

    def test_credit_score_bounds(self):
        """Verifies credit score mapping matches FICO standard (300 to 850)."""
        self.assertEqual(pd_to_credit_score([0.0])[0], 850)
        self.assertEqual(pd_to_credit_score([1.0])[0], 300)
        self.assertTrue(300 <= pd_to_credit_score([0.5])[0] <= 850)

    def test_risk_tier_classification(self):
        """Verifies tier thresholds."""
        self.assertEqual(classify_risk_tier(750), "Prime")
        self.assertEqual(classify_risk_tier(680), "Near-Prime")
        self.assertEqual(classify_risk_tier(600), "Subprime")
        self.assertEqual(classify_risk_tier(500), "High Risk")

    def test_feature_engineering_math(self):
        """Verifies utilization rate and EWS flags."""
        feat_df = engineer_features(self.sample_df)
        self.assertAlmostEqual(feat_df["AVG_UTILIZATION_RATE"].iloc[0], 0.20, places=2)
        self.assertEqual(feat_df["EARLY_WARNING_FLAG"].iloc[0], 0)
        
        # Test distressed scenario
        distressed_df = self.sample_df.copy()
        distressed_df["PAY_0"] = 2
        feat_distressed = engineer_features(distressed_df)
        self.assertEqual(feat_distressed["EARLY_WARNING_FLAG"].iloc[0], 1)

    def test_portfolio_kpis(self):
        """Verifies KPI math aggregation."""
        df = self.sample_df.copy()
        df["CREDIT_RISK_SCORE"] = 750
        df["PREDICTED_PD"] = 0.05
        df["EARLY_WARNING_FLAG"] = 0
        df["AVG_UTILIZATION_RATE"] = 0.2
        kpis = get_portfolio_kpis(df)
        self.assertEqual(kpis["total_borrowers"], 1)
        self.assertEqual(kpis["total_exposure"], 100000.0)

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

    def test_underwriting_policy_tradeoff(self):
        """Verifies policy cutoff trade-off calculations."""
        test_df = pd.DataFrame([
            {"CREDIT_RISK_SCORE": 750, "DEFAULT_NEXT_MONTH": 0, "BILL_AMT1": 50000},
            {"CREDIT_RISK_SCORE": 520, "DEFAULT_NEXT_MONTH": 1, "BILL_AMT1": 40000}
        ])
        tradeoff = get_underwriting_policy_tradeoff(test_df, score_cutoff=620)
        self.assertEqual(tradeoff["approved_count"], 1)
        self.assertEqual(tradeoff["rejected_count"], 1)
        self.assertEqual(tradeoff["avoided_defaults"], 1)
        self.assertEqual(tradeoff["approved_default_rate"], 0.0)

    def test_load_model_metrics(self):
        """Verifies loading saved model metrics JSON."""
        metrics = load_model_metrics()
        self.assertIn("champion_model", metrics)
        self.assertIn("champion_metrics", metrics)
        self.assertIn("roc_auc", metrics["champion_metrics"])

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
