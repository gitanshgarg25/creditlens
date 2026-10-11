# CreditLens — Tableau Public Dashboard Architecture & Implementation Guide

This guide provides instructions and formulas for building an executive-grade **Credit Risk & Early-Warning Intelligence Dashboard** on **Tableau Public** using the prepared CreditLens extract.

---

## 1. Data Source Connection
1. Open **Tableau Public** (or Tableau Desktop).
2. Click **Connect to Data** -> **Text file** -> select:
   ```
   data/processed/credit_lens_tableau_extract.csv
   ```
3. Verify that all 30,000 client records load with 32 columns.

---

## 2. Tableau Calculated Fields (Ready to Paste)

Create the following calculated fields in Tableau to standardize labels and business metrics:

### `[Default Status Name]`
```tableau
IF [DEFAULT_NEXT_MONTH] = 1 THEN "Defaulted"
ELSE "Current / Performing"
END
```

### `[EWS Alert Status]`
```tableau
IF [EARLY_WARNING_FLAG] = 1 THEN "⚠️ Active Early-Warning Alert"
ELSE "✅ Normal Status"
END
```

### `[Delinquency Severity Label]`
```tableau
IF [PAY_0] <= 0 THEN "0 Months (Current / Paid)"
ELSEIF [PAY_0] = 1 THEN "30 Days Past Due (1 Mo)"
ELSEIF [PAY_0] = 2 THEN "60 Days Past Due (2 Mo)"
ELSEIF [PAY_0] >= 3 THEN "90+ Days Past Due (Severe)"
ELSE "Other"
END
```

### `[Credit Utilization %]`
```tableau
[AVG_UTILIZATION_RATE] * 100
```

### `[Default Rate %]`
```tableau
SUM([DEFAULT_NEXT_MONTH]) / COUNT([ID])
```

### `[Exposure at Risk]`
```tableau
IF [EARLY_WARNING_FLAG] = 1 THEN [LIMIT_BAL] ELSE 0 END
```

---

## 3. Recommended Tableau Worksheets & Visualizations

### Sheet 1: Executive KPI Scorecard (BANs - Big Ass Numbers)
- **Measures**:
  - Total Borrowers: `COUNT([ID])` -> Format: `#,##0`
  - Total Exposure: `SUM([LIMIT_BAL])` -> Format: Currency `NT$#,##0`
  - Portfolio Average Credit Score: `AVG([CREDIT_RISK_SCORE])` -> Format: `0`
  - Actual Default Rate: `[Default Rate %]` -> Format: `0.0%`
  - EWS Alert Volume: `SUM([EARLY_WARNING_FLAG])` -> Format: `#,##0`
- **Design**: 5 horizontal cards at top with clean gray/navy typography.

### Sheet 2: Portfolio Exposure & Default Rate by Risk Tier
- **Columns**: `[RISK_TIER]` (Prime, Near-Prime, Subprime, High Risk)
- **Rows**: Dual Axis:
  - Bar: `SUM([LIMIT_BAL])` (Color: Navy `#1E3A8A`)
  - Line: `[Default Rate %]` (Color: Coral/Red `#DC2626`)
- **Insight**: Demonstrates that default risk escalates sharply from Prime (under 5%) to High Risk (over 65%).

### Sheet 3: Early-Warning Delinquency Trajectory Heatmap
- **Columns**: `[Delinquency Severity Label]`
- **Rows**: `[RISK_TIER]`
- **Color**: `[Default Rate %]` (Diverging Red-Green palette)
- **Label**: `[Default Rate %]` and `COUNT([ID])`
- **Insight**: Identifies that accounts with 60+ DPD in High Risk tier exhibit over 75% transition to default.

### Sheet 4: Credit Utilization vs. Default Propensity
- **Columns**: Binned `[AVG_UTILIZATION_RATE]` (0-20%, 20-50%, 50-80%, 80-100%, >100%)
- **Rows**: `[Default Rate %]`
- **Bar Color**: Gradient based on default rate.
- **Insight**: Highlights the sudden risk spike once credit utilization crosses 80%.

### Sheet 5: High-Exposure Watchlist Table
- **Rows**: `[ID]`, `[LIMIT_BAL]`, `[CREDIT_RISK_SCORE]`, `[RISK_TIER]`, `[Delinquency Severity Label]`, `[RECOMMENDED_ACTION]`
- **Filter**: `[EARLY_WARNING_FLAG] = 1` and `[LIMIT_BAL] > NT$ 200,000`
- **Sort**: `[PREDICTED_PD]` descending.

---

## 4. Executive Dashboard Layout Composition
- **Resolution**: 1400 x 900 px (Desktop Browser).
- **Top Row**: Header Title + 5 KPI Cards.
- **Middle Row**:
  - Left: Exposure & Default Rate by Risk Tier (Bar/Line).
  - Right: Delinquency Trajectory Heatmap.
- **Bottom Row**:
  - Left: Utilization vs Default Distribution.
  - Right: Distressed Borrower Watchlist Table.

---

## 5. Publishing to Tableau Public
1. In Tableau Public: **File** -> **Save to Tableau Public As...**
2. Name the workbook: `CreditLens - Credit Risk & Early-Warning Intelligence Platform`
3. Add tags: `#CreditRisk #FinTech #Banking #DataAnalytics #RiskManagement #MachineLearning`
4. Copy your public dashboard URL and embed it in your project `README.md`.
