# CreditLens — Project Log

## [2026-10-11] Environment Inspection & Verification

### Objective
Perform non-destructive environment audit for CreditLens on Apple Silicon Mac to check project workspace state and prerequisites (Python 3, Git, PostgreSQL).

### Initial Findings
- Directory: `/Users/gitanshgarg/Documents/CREDIT LENS` (clean directory).
- Apple Developer Tools missing.

---

## [2026-10-11] Verification Following Command Line Tools Installation
- `python3 --version`: Python 3.9.6 (Functional)
- `git --version`: git version 2.54.0 (Apple Git-157) (Functional)
- `psql` / `postgres`: Not installed.

---

## [2026-10-11] End-to-End Platform Build & Pipeline Execution

### Objective
Implement the full CreditLens platform matching all specifications for Data Analyst, Business Analyst, BI, and Risk Analyst portfolios.

### Key Milestones Completed:
1. **Virtual Environment & Dependencies**:
   - Initialized `.venv` using Python 3.9.6.
   - Installed core scientific stack: `pandas`, `numpy`, `scikit-learn`, `SQLAlchemy`, `openpyxl`, `xlrd`, `streamlit`, `plotly`, `requests`, `joblib`.
   - Frozen into `requirements.txt`.

2. **Data Ingestion (`src/data_ingestion.py`)**:
   - Acquired official UCI Default of Credit Card Clients dataset (30,000 clients).
   - Standardized column headers and mapped categorical anomalies.
   - Exported clean baseline to `data/processed/credit_lens_clean.csv`.

3. **Feature Engineering (`src/feature_engineering.py`)**:
   - Generated 50 domain-specific financial features:
     * 6-month average and maximum credit utilization (`AVG_UTILIZATION_RATE`).
     * Maximum delinquency delay months (`MAX_DELINQUENCY_MONTHS`).
     * Delinquency trend (`DELINQUENCY_TREND`).
     * Payment-to-bill velocity ratios (`AVG_PAYMENT_RATIO`).
     * Revolving debt burden ratio (`REVOLVING_BURDEN_RATIO`).
     * Early-Warning System (EWS) trigger flag (`EARLY_WARNING_FLAG`).

4. **Machine Learning & Risk Scoring (`src/model_training.py`, `src/risk_scoring.py`)**:
   - Evaluated 80/20 stratified split.
   - Benchmarked regulatory Logistic Regression against Champion Random Forest:
     * Logistic Regression: ROC-AUC = 0.7521, KS = 0.3928, Brier = 0.1985
     * Random Forest: ROC-AUC = **0.7781**, PR-AUC = **0.5573**, KS = **0.4257**, Brier = **0.1340**
   - Transformed Probability of Default into FICO-aligned Credit Risk Scores (300 - 850).
   - Assigned Risk Tiers ('Prime', 'Near-Prime', 'Subprime', 'High Risk') and operational action directives.
   - Saved serialized model to `models/credit_risk_model.joblib`.

5. **Database Layer (`database/`)**:
   - Authored PostgreSQL DDL (`database/schema.sql`) with tables, indexes, and analytical views.
   - Initialized local SQLite database (`database/credit_lens.db`) loaded with 30,000 clients and 30,000 risk evaluations.
   - Authored 6 executive portfolio SQL queries (`database/analytical_queries.sql`).

6. **Financial Excel Model (`excel/generate_excel_model.py`)**:
   - Generated institutional workbook `excel/CreditLens_Portfolio_Model.xlsx` with openpyxl:
     * Executive Summary sheet with KPI cards, risk tier breakdown, and delinquency tables.
     * Loan Tape Sample (500 formatted records).
     * Model Diagnostics and Feature Importance rankings.

7. **Tableau Public BI Package (`tableau/`)**:
   - Exported scored dataset `data/processed/credit_lens_tableau_extract.csv`.
   - Authored step-by-step workbook build guide `tableau/README_TABLEAU.md` with calculated field formulas.
   - Created full 32-column data dictionary `tableau/tableau_dataset_dictionary.md`.

8. **Streamlit Web Application (`app/streamlit_app.py`)**:
   - 6 interactive modules: Executive Overview, Early-Warning Surveillance, What-If Simulator, Model Diagnostics, SQL Query Console, and Grounded AI Risk Assistant.

9. **Verification**:
   - 100% test pass rate in `tests/test_pipeline.py`.
   - Entire pipeline orchestrated via one-click script `run_all.py`.
