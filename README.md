# 🛡️ CreditLens: AI-Assisted Credit Risk & Early-Warning Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![SQLite](https://img.shields.io/badge/SQLite-Zero--Setup-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3+-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://scikit-learn.org)
[![Tableau](https://img.shields.io/badge/Tableau-Public-E97627?style=for-the-badge&logo=tableau&logoColor=white)](https://public.tableau.com)
[![Microsoft Excel](https://img.shields.io/badge/Microsoft_Excel-Financial_Model-217346?style=for-the-badge&logo=microsoftexcel&logoColor=white)](https://microsoft.com/excel)

---

## 📌 Executive Summary & Business Motivation

**CreditLens** is an end-to-end **Credit Risk & Early-Warning Intelligence Platform** engineered for retail banking and commercial lending portfolios. 

Traditional credit monitoring is largely **reactive**—risk management teams often discover customer distress only after an account reaches 90+ Days Past Due (DPD), at which point balance drawdowns have peaked and recovery yields plummet. CreditLens transforms this process into **proactive pre-delinquency triage** by continuously monitoring multi-month repayment velocity, credit limit utilization strain, and rolling delinquency transitions.

Engineered as a portfolio project for **Data Analyst**, **Business Analyst**, **Business Intelligence Analyst**, and **Credit Risk Analyst** roles, CreditLens delivers:
1. **Interactive Streamlit Web Application**: Multi-tab risk analytics workspace featuring dynamic cohort filtering, portfolio surveillance, underwriting policy simulation, and interactive score inspection.
2. **Predictive Credit Risk Modeling**: Random Forest Champion benchmarked against a baseline Logistic Regression across 30 engineered behavioral and financial features.
3. **Custom Credit Risk Score (300–850)**: An illustrative credit risk score mapped to standard institutional underwriting risk tiers.
4. **Relational Database & Analytical SQL**: Production schema and 6 automated analytical queries running on both zero-setup SQLite and PostgreSQL.
5. **Interactive Policy Simulator & Simplified ECL**: Decision trade-off analysis distinguishing between out-of-sample holdout validation ($N=6,000$) and whole-book tape simulations ($N=30,000$), paired with an illustrative Expected Credit Loss ($ECL$) framework.
6. **Executive Microsoft Excel Model & Tableau Extract**: Multi-tab financial workbook (`.xlsx`) with KPI scorecards and ready-to-visualize BI extracts.

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
      ┌─────────────────────────┬─────────────────┴───────┬─────────────────────────┐
      ▼                         ▼                         ▼                         ▼
[database/init_db.py]   [excel/generate_excel_model.py] [scripts/generate_model_report_docx.py] [app/streamlit_app.py]
(SQLite / Postgres DDL)    (Executive .xlsx Model)      (Comprehensive Word Report)    (Interactive UI)
      │                         │                         │                         │
      ▼                         ▼                         ▼                         ▼
[6 Analytical Queries]   [Loan Tape & Risk Matrix]    [C-Suite Documentation]    [What-If Simulator & Copilot]
```

---

## 📊 Dataset, Target Variable & Portfolio Limitations

The platform utilizes the public **[UCI Default of Credit Card Clients](https://archive.ics.uci.edu/dataset/350/default+of+credit+card+clients)** dataset (Taiwan retail bank credit card portfolio, $N=30,000$, observed April–September 2005).

### Key Portfolio Metrics:
* **Total Portfolio Borrowers**: 30,000 accounts (24,000 training / 6,000 stratified holdout test)
* **Total Credit Exposure**: NT$ 5.02 Billion (sum of `LIMIT_BAL` across all 30,000 accounts = NT$ 5,024,546,400)
* **Average Credit Line**: NT$ 167,484
* **Historical Default Prevalence**: 22.12% (6,636 accounts defaulted in the performance window)
* **Target Definition (`DEFAULT_NEXT_MONTH`)**: Binary indicator ($1 = \text{default}$, $0 = \text{non-default}$) measuring default occurrence in the subsequent billing cycle (October 2005).

### Important Dataset Limitations:
1. **Single-Issuer Historical Cohort**: The data reflects cardholders from a single Taiwanese commercial issuer during a six-month window in 2005. Findings should not be assumed to generalize across diverse economic jurisdictions without local re-calibration.
2. **Short Observation Horizon**: A 6-month historical observation period captures recent behavioral trends but cannot observe multi-year macroeconomic credit cycles.
3. **Cross-Sectional Performance Window**: The target is a 1-month future default snapshot rather than a longitudinal multi-year survival analysis panel.

---

## ⚙️ Feature Engineering & Early-Warning Surveillance (EWS)

From 23 raw attributes, the pipeline engineers 30 analytical features (`src/feature_engineering.py`) capturing behavioral dynamics across three critical credit pillars:

1. **Credit Utilization Dynamics**:
   - `AVG_UTILIZATION_RATE`: Mean rolling balance divided by credit limit across 6 statement cycles.
   - `MAX_UTILIZATION_RATE`: Peak credit utilization observed.
   - `UTILIZATION_TREND`: Ratio of most recent statement balance (`BILL_AMT1`) to oldest (`BILL_AMT6`).
2. **Repayment Delinquency Trajectory**:
   - `MAX_DELINQUENCY_MONTHS`: Worst observed payment delay across the 6-month performance window.
   - `RECENT_DELINQUENCY_STATUS`: Payment status in the most recent cycle (`PAY_0`).
   - `DELINQUENCY_TREND`: Velocity delta between recent delinquency (`PAY_0`) and oldest (`PAY_6`).
3. **Repayment Velocity & Liquidity**:
   - `AVG_PAYMENT_RATIO`: Average ratio of actual payments made (`PAY_AMT`) to billed amounts (`BILL_AMT`).
   - `REVOLVING_BURDEN_RATIO`: Outstanding unamortized revolving balance relative to assigned credit line.

### Early-Warning System (EWS) Rule:
An early-warning alert is triggered whenever a borrower meets either of two pre-delinquency stress conditions:
$$\text{EARLY\_WARNING\_FLAG} = 1 \iff \left(\text{AVG\_UTILIZATION\_RATE} \ge 80\%\right) \lor \left(\text{MAX\_DELINQUENCY\_MONTHS} \ge 1\right)$$
* **EWS Trigger Rate**: **42.3%** of the portfolio (12,678 accounts flagged).
* **Business Purpose**: Flags accounts exhibiting severe balance build-up or minor payment friction before accounts roll into severe multi-cycle write-offs.

---

## 🧮 Custom Credit Risk Score (300–850) & Policy Directives

Predicted default probabilities ($PD$) are translated into an intuitive 300–850 credit risk score using a linear scoring formula:
$$\text{Credit Risk Score} = \text{clip}\left(\text{round}\left(850 - PD \times 550\right), 300, 850\right)$$

> [!NOTE]
> **Custom Credit Risk Score Disclaimer:**
> The 300–850 score generated by CreditLens is a **custom internal credit risk score** scaled to a familiar 300–850 numerical range. It is **NOT** an official Fair Isaac Corporation (FICO) score, VantageScore, or credit bureau rating. It is an illustrative modeling tool that translates predicted probability of default into operational risk bands.

| Risk Tier | Score Range | Default Prob ($PD$) | Illustrative Policy Directive | Operational Underwriting Action |
| :--- | :---: | :---: | :--- | :--- |
| **Prime** | 720 – 850 | $< 12\%$ | Tier 1 (Low Risk) | Automatic approval; pre-approved line expansions; preferred pricing. |
| **Near-Prime** | 660 – 719 | $12\% - 25\%$ | Tier 2 (Moderate Risk) | Standard approval; routine semi-annual credit line review. |
| **Subprime** | 580 – 659 | $25\% - 45\%$ | Tier 3 (Elevated Risk) | Line freeze; risk-adjusted pricing (+250 bps); enhanced EWS monitoring. |
| **High Risk** | 300 – 579 | $\ge 45\%$ | Tier 4 (Severe Risk) | Automatic decline; merchant authorization blocks; collections outreach. |

---

## 📈 Model Benchmarking & Evaluation (Out-of-Sample Holdout)

Models were evaluated out-of-sample on **6,000 unseen holdout accounts** (stratified 20% test split, $N=6,000$, 1,327 actual defaults, 22.12% base default prevalence). The Random Forest model was selected as the champion based on superior non-linear discrimination, with Logistic Regression serving as the transparent econometric benchmark.

| Metric | Random Forest (Champion) | Logistic Regression (Benchmark) | Absolute Lift | Commercial Banking Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **ROC-AUC (Discrimination)** | **0.7781** | 0.7521 | **+0.0260 (+3.5%)** | 78% probability of ranking a true defaulter higher risk than a non-defaulter. |
| **KS Statistic (Max Separation)** | **42.57%** | 39.28% | **+3.29 points (+8.4%)** | Peak separation between good vs. bad cumulative distributions. KS > 40% represents strong retail separation power. |
| **PR-AUC (Precision-Recall)** | **0.5573** | 0.5079 | **+0.0494 (+9.7%)** | Evaluates default capture on the minority class under 22.12% baseline prevalence. |
| **Classification Accuracy** | **78.37% (78.4%)** | 74.57% (74.6%) | **+3.80%** | Overall correct decisions (~4 out of every 5 accounts correctly categorized). |
| **Precision (Approval Quality)** | **50.96%** | 44.43% | **+6.53% (+14.7%)** | When flagged as high risk, 51% are true defaults (vs. 44% for linear), minimizing false alerts. |
| **Recall (Defaulters Caught)** | **58.10%** | 59.76% | -1.66% | Intercepts ~58% of all future defaults at cycle 1 prior to balance ballooning. |
| **F1-Score (Balanced Power)** | **0.5430** | 0.5096 | **+0.0334 (+6.6%)** | Harmonic mean balancing bad debt capture against false rejections. |
| **Brier Score (Probability Error)** | **0.1685** | 0.1914 | **-0.0229 (-12.0%)** | Lower is better. Measures mean squared probability error; lower error indicates tighter probability accuracy. |

---

## ⚖️ Underwriting Policy Simulator: Holdout vs. Full Population Evaluation

To maintain analytical rigor, CreditLens explicitly distinguishes between **out-of-sample holdout validation** (data the model never saw during training) and **full population portfolio tape simulation** (whole-book commercial modeling):

| Simulation Dimension | 🎯 Unseen Holdout Test Cohort ($N=6,000$) | 📊 Full Portfolio Population Tape ($N=30,000$) | Commercial Interpretation |
| :--- | :---: | :---: | :--- |
| **Data Scope** | **Strict Out-of-Sample Validation** (Never seen by model during training) | **Whole-Book Simulation** (24k training + 6k test combined tape) | Differentiates honest out-of-sample ground truth from portfolio population modeling. |
| **Approval Cutoff Threshold** | **Score Cutoff 620** | **Score Cutoff 620** | Underwriting threshold (scores $\ge 620$ approved, $< 620$ rejected). |
| **Application Approval Rate** | **65.6%** (3,939 of 6,000 approved) | **65.4%** (19,614 of 30,000 approved) | Consistent customer acquisition volume (~65%). |
| **Portfolio Baseline Default Rate**| 22.12% (1,327 defaults) | 22.12% (6,636 defaults) | Original unmitigated portfolio default rate. |
| **Approved Default Rate** | **11.35%** (down from 22.12%) | **7.73%** (down from 22.12%) | Cuts default rate nearly in half on unseen data; 7.7% on whole-book tape. |
| **Defaulters Intercepted** | **880 accounts** (66.3% of test defaults) | **5,119 accounts** (77.1% of all defaults) | Proactively blocked before balance ballooning. |
| **Avoided Bad Debt Losses** | **NT$ 42.5M** | **NT$ 232.9M** | Cumulative write-off dollars prevented (sum of `BILL_AMT1` of true positives). |
| **Lost APR Interest (15%)** | **NT$ 6.5M** | **NT$ 26.2M** | Conservative opportunity cost on false positives (`BILL_AMT1` $\times 15\%$). |
| **Net Financial Benefit** | **+NT$ 36.0M** (extrapolated (holdout x5): **+NT$ 180.1M**) | **+NT$ 206.6M** | **Net Capital Preserved** (Avoided Bad Debt minus Lost APR). |

> [!IMPORTANT]
> **Simulation Methodology & Financial Assumptions:**
> - **Avoided Bad Debt**: Defined as the sum of `BILL_AMT1` of true positive defaults intercepted by the policy cutoff.
> - **Opportunity Cost**: Defined as 15% annual percentage rate (APR) interest income forfeited on false positive non-defaulters mistakenly rejected.
> - **Illustrative Nature**: These figures represent policy simulation scenarios under stated assumptions, not certified or guaranteed bank P&L savings.

---

## 🏛️ Simplified Expected Credit Loss (ECL) Framework

CreditLens incorporates a simplified, educational Expected Credit Loss calculation inspired by Basel III / IFRS 9 concepts:
$$\text{ECL} = \text{EAD} \times \text{PD} \times \text{LGD}$$
* **Exposure at Default (EAD)**: Billed drawn balance plus a 20% Credit Conversion Factor (CCF) applied to unutilized credit line:
  $$\text{EAD} = \text{BILL\_AMT1} + 0.20 \times \max\left(\text{LIMIT\_BAL} - \text{BILL\_AMT1}, 0\right)$$
* **Probability of Default (PD)**: Model-predicted probability of default (`PREDICTED_PD`).
* **Loss Given Default (LGD)**: Fixed standard regulatory retail benchmark of 45% for unsecured revolving credit.

> [!NOTE]
> **ECL Disclaimer:**
> This ECL calculation is a **simplified illustrative financial model** intended to demonstrate credit risk reserving principles. It is not an audited Basel III or IFRS 9 production accounting engine.

---

## 🔍 Exploratory Demographic & Fair Lending Sensitivity Analysis

An inspection of model feature importances confirms that credit decisions are overwhelmingly driven by objective financial behavior:
* **Behavioral Credit Predictors (>90% Combined Weight)**: Recent repayment delay status (`PAY_0`, `PAY_2`), rolling credit limit utilization (`AVG_UTILIZATION_RATE`), and repayment velocity (`AVG_PAYMENT_RATIO`).
* **Demographic Variables (3.05% Combined Weight)**: Age (1.24%), Education (0.91%), Sex (0.47%), and Marital Status (0.43%).

> [!WARNING]
> **Fair Lending & Regulatory Compliance Disclaimer:**
> Low demographic feature importance in an observational model does **NOT** constitute legal or regulatory proof of non-discrimination or compliance with the Equal Credit Opportunity Act (ECOA) or Fair Housing Act (FHA). In actual commercial underwriting in the United States and European Union, protected demographic attributes (such as sex, marital status, and age) are legally prohibited from being used as decision variables in credit scoring models.

---

## 🗄️ Relational Database & Analytical SQL Queries

CreditLens provides a production-grade relational database schema (`database/schema.sql`) populated into a zero-setup local SQLite database (`database/credit_lens.db`), fully compatible with PostgreSQL.

The analytical query suite (`database/analytical_queries.sql`) powers executive reporting:
1. **Query 1 — Portfolio Risk KPI Rollup**: Computes borrower counts, active exposures, average limits, and overall default prevalence.
2. **Query 2 — Delinquency Migration Analysis**: Measures default rates and balance totals segmented by repayment delay (`PAY_0`).
3. **Query 3 — Utilization Decile Risk Distribution**: Segments the portfolio into 10 utilization buckets to analyze non-linear risk escalation.
4. **Query 4 — Early-Warning System (EWS) Watchlist**: Identifies high-risk accounts exhibiting elevated utilization or payment friction.
5. **Query 5 — Risk Tier Segmentation & ECL Exposure**: Aggregates accounts across Prime, Near-Prime, Subprime, and High Risk tiers.
6. **Query 6 — Demographic Sensitivity Review**: Audits default prevalence across age and demographic brackets for exploratory parity checks.

---

## 💻 Tech Stack & Key Deliverables

* **Language & Data Processing**: Python 3.9+, `pandas`, `numpy`, `scikit-learn`, `joblib`.
* **Database & SQL Engine**: SQLite 3 (bundled zero-setup) and PostgreSQL 15 DDL.
* **Interactive UI**: Streamlit 1.30+ web application featuring interactive Plotly visualizations, loan tape filtering, underwriting policy simulator, and SQL query console.
* **Executive Excel Model**: Microsoft Excel `.xlsx` workbook generated via `openpyxl` with dynamic formulas, KPI summaries, and loan tape samples.
* **Tableau Public BI Extract**: Clean, scored extract (`data/processed/credit_lens_tableau_extract.csv`) with full metadata and guide (`tableau/README_TABLEAU.md`).
* **Executive Word Report**: Formatted `.docx` technical model report generated via `python-docx` for executive review (`scripts/generate_model_report_docx.py`).

---

## 🚀 Quickstart Guide (macOS / Linux / Windows)

Follow these simple steps to set up and run CreditLens locally:

### 1. Clone the Repository
```bash
git clone https://github.com/gitanshgarg25/creditlens.git
cd creditlens
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Run the End-to-End Pipeline
To ingest data, engineer features, train and benchmark models, seed the SQLite database, and generate the Excel model in a single step:
```bash
python3 run_all.py
```

### 4. Execute the Automated Test Suite
Run the 18 automated unit and pipeline tests to verify data integrity, score bounds, and SQL query execution:
```bash
python3 -m unittest discover -s tests -p "test_*.py"
```

### 5. Inspect the Relational Database via SQL
Run analytical queries directly against the SQLite database via CLI:
```bash
sqlite3 database/credit_lens.db < database/analytical_queries.sql
```

### 6. Launch the Interactive Streamlit Web Application
```bash
streamlit run app/streamlit_app.py
```
Open your browser to `http://localhost:8501`.

> [!NOTE]
> **Demo Analyst Profiles (Local Sandbox Only):**
> For local sandbox exploration, the application pre-initializes demo analyst profiles (`admin@creditlens.internal`, `analyst@creditlens.internal`, `guest@creditlens.internal`). Multi-user deployments can configure credentials securely via environment variables (e.g. `CREDITLENS_DEMO_ADMIN_PASSWORD`). No external API keys, personal user information, or live credentials exist or are required in this repository.

---

## 🧪 Automated Test Suite

CreditLens includes an automated test suite (`tests/test_pipeline.py`) containing 18 rigorous test cases:
* **Feature/Target Leakage**: Confirms target (`DEFAULT_NEXT_MONTH`), identifier (`ID`), and EWS flags are excluded from training features.
* **Feature Count**: Asserts exactly 30 engineered features are utilized.
* **Train/Test Integrity**: Verifies 80/20 stratified split yields 24,000 train and 6,000 test records with zero overlapping indices.
* **Probability Bounds**: Confirms predicted probabilities are bounded strictly within $[0.0, 1.0]$.
* **Score Bounds & Monotonicity**: Verifies custom scores lie within $[300, 850]$ and decrease monotonically as default probability increases.
* **Score Edge Cases**: Validates proper handling of empty inputs, NaN values, and boundary floats.
* **KS Statistic**: Validates Kolmogorov-Smirnov discrimination calculation logic.
* **Policy Simulator Denominators**: Confirms approved and rejected sums match total accounts, with safe empty DataFrame handling.
* **ECL Mathematics**: Validates EAD and ECL formulas and tests safe empty DataFrame handling.
* **Analytical SQL Queries**: Verifies all 6 queries in `database/analytical_queries.sql` execute cleanly and return non-empty datasets on `database/credit_lens.db`.
* **Metric Consistency**: Enforces exact match between README metrics and `models/model_metrics.json`.
* **Stale Metric String Prevention**: Asserts that obsolete or unverified metrics do not appear across repository files.

---

## 🎯 Resume & Interview Highlights (For Fresher Analyst Roles)

Here are high-impact, verified bullet points ready for your resume or interview talking points:

* **Machine Learning & Risk Modeling**: *Engineered an end-to-end credit default prediction engine on 30,000 accounts using scikit-learn; trained and benchmarked a Random Forest champion (0.7781 ROC-AUC, 42.57% KS, 78.4% accuracy) against a baseline Logistic Regression across 30 engineered behavioral features, achieving an +8.4% relative lift in discriminatory separation.*
* **Underwriting Policy & Loss Simulation**: *Formulated an institutional 300–850 credit risk score and simulated underwriting policy tradeoffs; demonstrated that a 620 cutoff on 6,000 unseen holdout accounts cuts default rate from 22.12% to 11.35% and avoids NT$ 42.5M in bad-debt exposure (scaling to NT$ 232.9M across the full portfolio).*
* **Full-Stack Analytics & BI Architecture**: *Developed a full-stack risk intelligence architecture integrating an interactive Streamlit platform, SQLite/PostgreSQL relational database with 6 analytical queries, automated Excel financial model, and Tableau Public extract, enabling proactive pre-delinquency triage for 12,678 early-warning accounts.*

---

## 📁 Repository Directory Structure

```
CREDIT LENS/
├── README.md                          # Comprehensive project documentation & guide
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
│   ├── risk_scoring.py                # Custom credit risk score and action policies
│   ├── model_training.py              # Train & benchmark ML models
│   └── analytics_engine.py            # Portfolio KPIs, rollups, and watchlists
├── models/
│   ├── credit_risk_model.joblib       # Serialized Random Forest model
│   ├── logistic_regression_benchmark.joblib # Serialized Logistic Regression
│   └── model_metrics.json             # Verified benchmark statistics & metadata
├── app/
│   └── streamlit_app.py               # 6-tab Streamlit web application
├── scripts/
│   └── generate_model_report_docx.py  # Comprehensive Word report generator
├── reports/
│   └── CreditLens_Comprehensive_Model_Report.docx # Formatted executive Word report
└── tests/
    └── test_pipeline.py               # Comprehensive 18-case automated test suite
```

---

## ⚖️ License & Ethical Disclaimer

This project is created for **academic and portfolio demonstration purposes**. It represents a historical-data analytical prototype and is not designed for live underwriting or automated credit denial decisions without regulatory compliance audits (Fair Lending, FCRA, ECOA). All financial metrics, simulated savings, and credit scores are illustrative calculations intended to demonstrate analytical concepts.
