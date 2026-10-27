# 🛡️ CreditLens: AI-Assisted Credit Risk & Early-Warning Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Tableau](https://img.shields.io/badge/Tableau-Public-E97627?style=for-the-badge&logo=tableau&logoColor=white)](https://public.tableau.com)
[![Microsoft Excel](https://img.shields.io/badge/Microsoft_Excel-Financial_Model-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white)](https://microsoft.com/excel)

---

## 📌 Executive Summary

**CreditLens** is an end-to-end **Credit Risk & Early-Warning Intelligence Platform** engineered for commercial lending and retail credit portfolio surveillance. 

Traditional credit monitoring is largely **reactive**—risk teams often identify distressed borrowers only after they reach 90+ Days Past Due (DPD). CreditLens shifts the operating paradigm from reactive recovery to **proactive pre-delinquency triage** by continuously tracking multi-month payment velocity, credit line utilization strain, and rolling delinquency migrations.

This project delivers a complete portfolio prototype for **Data Analyst**, **Business Analyst**, **BI Analyst**, and **Credit Risk Analyst** roles, featuring:
1. **Interactive Streamlit Web Application**: Multi-module executive dashboard with real-time risk simulations.
2. **Machine Learning Credit Risk Scoring**: FICO-aligned (300–850) calibrated scoring comparing Random Forest champion to regulatory Logistic Regression.
3. **Relational Database & Analytical SQL**: Production DDL and portfolio queries compatible with both PostgreSQL and zero-setup SQLite.
4. **Institutional Microsoft Excel Model**: Structured `.xlsx` workbook with KPI cards, risk tier segmentations, and loan tape samples.
5. **Tableau Public Extract & Implementation Guide**: Pre-calculated BI extracts and dashboard formulas.
6. **Grounded AI Risk Assistant**: Analytical copilot grounded entirely in verified portfolio metrics.

---

## 🏗️ Architecture & Data Pipeline

```
                                  [UCI Credit Card Clients Data]
                                      (30,000 Borrowers, Taiwan)
                                                  │
                                                  ▼
                                      [src/data_ingestion.py]
                                (Data Cleaning & Normalization)
                                                  │
                                                  ▼
                                   [src/feature_engineering.py]
                        (Utilization Ratios, Delinquency Trends, EWS Flags)
                                                  │
                                                  ▼
                                      [src/model_training.py]
                        (Random Forest Champion vs. Logistic Regression Benchmark)
                                                  │
                        ┌─────────────────────────┼─────────────────────────┐
                        ▼                         ▼                         ▼
             [database/init_db.py]      [excel/generate_model.py]     [app/streamlit_app.py]
             (SQLite / PostgreSQL DDL)   (Executive .xlsx Model)      (Interactive Platform)
                        │                         │                         │
                        ▼                         ▼                         ▼
             [6 Analytical Queries]    [Loan Tape & Risk Matrix]   [What-If Simulator & Copilot]
```

---

## 📊 Dataset & Core Metrics

The platform utilizes the public **[UCI Default of Credit Card Clients](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients)** dataset (Taiwan retail bank credit card portfolio, $N=30,000$).

### Key Portfolio Metrics:
* **Total Portfolio Borrowers**: 30,000 accounts
* **Total Credit Exposure**: NT$ 5.03 Billion
* **Average Credit Line**: NT$ 167,484
* **Historical Default Rate**: 22.12% (6,636 accounts)
* **Early-Warning Trigger Rate**: 29.2% (Accounts exhibiting utilization $\ge 80\%$ or recent payment delays)

### Feature Engineering Highlights:
* **Average Credit Utilization (`AVG_UTILIZATION_RATE`)**: Rolling 6-month billed balance divided by credit limit.
* **Maximum Delinquency Months (`MAX_DELINQUENCY_MONTHS`)**: Worst observed delay status across the 6-month observation window.
* **Delinquency Trend (`DELINQUENCY_TREND`)**: Delta between recent payment status (September) and oldest (April).
* **Payment-to-Bill Ratio (`AVG_PAYMENT_RATIO`)**: Repayment velocity against outstanding statement balances.
* **Revolving Debt Burden (`REVOLVING_BURDEN_RATIO`)**: Unamortized revolving balance relative to limit.

---

## 🧮 Model Benchmarking & Risk Scoring

Credit default probabilities are scaled into a standard institutional risk score:
$$\text{Credit Risk Score} = \text{clip}\left(\text{round}\left(850 - PD \times 550\right), 300, 850\right)$$

| Risk Tier | Score Range | Default Prob ($PD$) | Policy Directive |
| :--- | :---: | :---: | :--- |
| **Prime** | 720 – 850 | $< 12\%$ | Normal Servicing; Pre-Approved Line Increases |
| **Near-Prime** | 660 – 719 | $12\% - 25\%$ | Maintain Limit; Semi-Annual Monitoring |
| **Subprime** | 580 – 659 | $25\% - 45\%$ | Freeze Line Expansion; High Utilization Surveillance |
| **High Risk** | 300 – 579 | $\ge 45\%$ | Immediate Pre-Delinquency Outreach; Suspension of Privileges |

### Model Benchmark Summary (Evaluated on 6,000 Unseen Holdout Accounts):
| Metric | Random Forest (Champion) | Logistic Regression (Benchmark) | Absolute Lift | Commercial Banking Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **ROC-AUC (Discrimination)** | **0.7781** | 0.7521 | **+0.0260 (+3.5%)** | 78% probability of correctly ranking a true defaulter higher risk than a good borrower. |
| **KS Statistic (Max Separation)** | **42.57%** | 39.28% | **+3.29% (+8.3%)** | Peak separation between good vs. bad cumulative distributions. KS > 40% is top-tier in retail lending. |
| **PR-AUC (Precision-Recall)** | **0.5573** | 0.5079 | **+0.0494 (+9.7%)** | Evaluates default capture on minority class under 22.12% base default prevalence. |
| **Classification Accuracy** | **78.37% (78.4%)** | 74.57% (74.6%) | **+3.80%** | Overall correct decisions (~4 out of every 5 accounts correctly categorized). |
| **Precision (Approval Quality)** | **50.96%** | 44.43% | **+6.53% (+14.7%)** | When flagged as high risk, 51% are true defaults (vs. 44% linear), minimizing false alarms. |
| **Recall (Defaulters Caught)** | **58.10%** | 59.76% | -1.66% | Intercepts ~58% of all future defaults at billing cycle 1 before balance drawdowns. |
| **F1-Score (Balanced Power)** | **0.5430** | 0.5096 | **+0.0334 (+6.6%)** | Harmonic balance between catching bad debt and avoiding false rejections. |
| **Brier Score (Calibration)** | **0.1685** | 0.1914 | **-0.0229 (-12.0%)** | Lower is better. Tighter calibration ensures predicted PD matches actual default frequency for Basel capital reserves. |

> [!NOTE]
> **Methodology & Data Split Integrity:**
> All benchmark metrics above are evaluated strictly out-of-sample on the **6,000 unseen holdout test accounts** (20% stratified test split, $N=6,000$). The model never saw these accounts during training.

---

### ⚖️ Underwriting Policy Simulator: Unseen Holdout vs. Full Portfolio Evaluation

To provide total analytical honesty and prevent confusion between test data and portfolio-level simulations, CreditLens explicitly distinguishes between **out-of-sample holdout validation** and **full population portfolio tape simulation**:

| Simulation Dimension | 🎯 Unseen Holdout Test Cohort ($N=6,000$) | 📊 Full Portfolio Population Tape ($N=30,000$) | Commercial Interpretation |
| :--- | :---: | :---: | :--- |
| **Data Scope** | **Strict Out-of-Sample Validation** (Never seen by model during training) | **Whole-Book Simulation** (24k training + 6k test combined tape) | Differentiates honest out-of-sample ground truth from portfolio population modeling. |
| **Approval Cutoff Threshold** | **FICO 620** | **FICO 620** | Optimal institutional approval threshold. |
| **Application Approval Rate** | **65.6%** (3,939 of 6,000 approved) | **65.4%** (19,614 of 30,000 approved) | Consistent customer acquisition volume (~65%). |
| **Portfolio Baseline Default Rate**| 22.12% (1,327 defaults) | 22.12% (6,636 defaults) | Original unmitigated portfolio default rate. |
| **Approved Default Rate** | **11.35%** (down from 22.12%) | **7.73%** (down from 22.12%) | Cuts default rate nearly in half on unseen data; 7.7% on whole-book tape. |
| **Defaulters Intercepted** | **880 accounts** (66.3% of test defaults) | **5,119 accounts** (77.1% of all defaults) | Proactively blocked before balance ballooning. |
| **Avoided Bad Debt Losses** | **NT$ 42.5M** | **NT$ 232.9M** | Cumulative write-off dollars prevented. |
| **Lost APR Interest (15%)** | **NT$ 6.5M** | **NT$ 26.2M** | Conservative false-positive opportunity cost. |
| **Net Financial Benefit** | **+NT$ 36.0M** (Scales to **+NT$ 180.1M** on 30k) | **+NT$ 206.6M** | **Net Capital Preserved** (Avoided Bad Debt minus Lost APR). |

> [!TIP]
> **Interview Talking Point on Unseen Data vs. Full Portfolio:**
> *"Our model evaluation metrics (ROC-AUC 0.778, KS 42.6%, Accuracy 78.4%) come strictly from the 6,000 unseen holdout test accounts. In the policy simulator, on completely unseen accounts at FICO 620, the model cuts default rates from 22.1% to 11.4% and avoids NT$ 42.5M in bad debt on the 6k sample (scaling to NT$ 180M+ portfolio-wide). When simulated across the bank's entire 30,000 customer tape, the approved default rate drops to 7.7% and avoids NT$ 232.9M in bad debt. We provide both views to maintain 100% scientific integrity."*

---

## 💻 Tech Stack & Deliverables

* **Python 3.9+**: Core processing pipeline with `pandas`, `numpy`, `scikit-learn`, `joblib`.
* **Database & SQL**: PostgreSQL DDL (`database/schema.sql`) and SQLite zero-setup database (`database/credit_lens.db`) with 6 executive queries (`database/analytical_queries.sql`).
* **Interactive UI**: Streamlit web application (`app/streamlit_app.py`) featuring interactive Plotly charts, loan tape filtering, live What-If calculator, SQL console, and grounded AI assistant.
* **Microsoft Excel**: Formatted workbook (`excel/CreditLens_Portfolio_Model.xlsx`) with executive KPI scorecards, risk matrices, and loan tape samples.
* **Tableau Public**: Clean extract (`data/processed/credit_lens_tableau_extract.csv`) and implementation guide (`tableau/README_TABLEAU.md`).

---

## 🚀 Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/creditlens.git
cd creditlens
```

### 2. Activate Python Environment & Install Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Run the End-to-End Orchestrator
To download data, train models, initialize databases, and generate the Excel model in one step:
```bash
python3 run_all.py
```

### 4. Launch the Interactive Dashboard
```bash
streamlit run app/streamlit_app.py
```
Open your browser to `http://localhost:8501`.

---

## 📁 Repository Directory Structure

```
CREDIT LENS/
├── README.md                          # Comprehensive project documentation
├── PROJECT_STATUS.md                  # Project milestones and status log
├── PROJECT_LOG.md                     # Detailed audit of engineering actions
├── requirements.txt                   # Production package dependencies
├── run_all.py                         # Master one-click pipeline runner
├── .gitignore                         # Standard Python/OS ignore rules
├── data/
│   ├── raw/                           # Raw UCI download artifacts
│   └── processed/                     # Clean, featured, and scored CSV extracts
├── database/
│   ├── schema.sql                     # PostgreSQL DDL and views
│   ├── analytical_queries.sql         # 6 portfolio and risk analysis queries
│   ├── init_db.py                     # SQLite & PostgreSQL database loader
│   └── credit_lens.db                 # Populated SQLite database
├── excel/
│   ├── generate_excel_model.py        # openpyxl financial workbook generator
│   └── CreditLens_Portfolio_Model.xlsx# Generated executive workbook
├── tableau/
│   ├── README_TABLEAU.md              # Tableau Public dashboard setup guide
│   └── tableau_dataset_dictionary.md  # Detailed column reference
├── src/
│   ├── data_ingestion.py              # Download and clean UCI dataset
│   ├── feature_engineering.py         # Calculate credit metrics and EWS flags
│   ├── risk_scoring.py                # FICO-scale conversion and action policies
│   ├── model_training.py              # Train & benchmark ML models
│   └── analytics_engine.py            # Portfolio KPIs, rollups, and watchlists
├── models/
│   ├── credit_risk_model.joblib       # Serialized Random Forest model
│   └── model_metrics.json             # Benchmark statistics and feature importance
├── app/
│   └── streamlit_app.py               # 6-tab Streamlit web application
└── tests/
    └── test_pipeline.py               # Unit test suite
```

---

## ⚖️ License & Disclaimer

This project is created for **academic and portfolio demonstration purposes**. It represents a historical-data analytical prototype and is not designed for live underwriting or automated credit denial decisions without regulatory compliance audits (Fair Lending, FCRA, ECOA).
