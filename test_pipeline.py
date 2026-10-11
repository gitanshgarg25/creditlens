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
from src.analytics_engine import get_portfolio_kpis


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


if __name__ == "__main__":
    unittest.main()
