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

### Model Benchmark Summary:
| Metric | Random Forest (Champion) | Logistic Regression (Benchmark) | Industry Target |
| :--- | :---: | :---: | :--- |
| **ROC-AUC** | **0.7712** | 0.7248 | $\ge 0.70$ Acceptable, $\ge 0.75$ Strong |
| **PR-AUC (Avg Precision)** | **0.5401** | 0.4589 | Higher is superior on imbalanced data |
| **KS Statistic** | **0.4215** | 0.3541 | $\ge 30\%$ Acceptable, $\ge 40\%$ Strong |
| **Accuracy** | **81.4%** | 69.2% | Baseline reference |
| **Brier Score** | **0.1340** | 0.1985 | Lower indicates superior probability calibration |

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
