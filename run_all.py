"""
CreditLens - Master Pipeline Orchestrator
Executes the end-to-end workflow:
1. Data Ingestion & Cleaning
2. Feature Engineering & EWS Flags
3. Machine Learning Training & Evaluation
4. Database Setup & Population (SQLite/PostgreSQL)
5. Financial Excel Model Generation
6. Test Suite Execution
"""

import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)


def print_step(step_num, title):
    print("\n" + "="*70)
    print(f" STEP {step_num}: {title.upper()}")
    print("="*70)


def run_pipeline():
    start_time = time.time()
    print("\n🛡️  STARTING CREDITLENS END-TO-END PIPELINE...")

    # Step 1: Ingestion
    print_step(1, "Data Ingestion & Cleaning")
    from src.data_ingestion import run_ingestion_pipeline
    df_clean = run_ingestion_pipeline()

    # Step 2: Feature Engineering
    print_step(2, "Credit Feature Engineering & Early-Warning Flags")
    from src.feature_engineering import run_feature_engineering_pipeline
    df_features = run_feature_engineering_pipeline()

    # Step 3: Model Training
    print_step(3, "Machine Learning Model Training & Scoring")
    from src.model_training import train_and_evaluate_models
    df_scored, metrics = train_and_evaluate_models()

    # Step 4: Database Population
    print_step(4, "Database Initialization & Table Population")
    from database.init_db import initialize_database
    initialize_database()

    # Step 5: Excel Workbook Generation
    print_step(5, "Financial Excel Model Generation")
    from excel.generate_excel_model import generate_workbook
    generate_workbook()

    # Step 6: Test Suite
    print_step(6, "Automated Test Suite Verification")
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    test_result = runner.run(suite)

    elapsed = time.time() - start_time
    print("\n" + "#"*70)
    if test_result.wasSuccessful():
        print(f"🎉 CREDITLENS PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.1f}s!")
    else:
        print(f"⚠️  PIPELINE FINISHED WITH SOME TEST FAILURES IN {elapsed:.1f}s.")
    print("#"*70)
    print("\nTo launch the interactive dashboard, run:")
    print("    .venv/bin/streamlit run app/streamlit_app.py\n")


if __name__ == "__main__":
    run_pipeline()
