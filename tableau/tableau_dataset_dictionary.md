# CreditLens — Data Dictionary for Tableau & SQL Analytics

| Column Name | Data Type | Description | Business Context |
| :--- | :--- | :--- | :--- |
| `ID` | Integer | Unique identifier for each credit card client | Primary Key |
| `LIMIT_BAL` | Decimal | Total amount of credit granted (NT dollars) | Credit line exposure |
| `SEX` | Integer | Gender (1 = Male, 2 = Female) | Demographic factor |
| `EDUCATION` | Integer | Education level (1 = Grad School, 2 = Univ, 3 = High School, 4 = Others) | Socio-economic factor |
| `MARRIAGE` | Integer | Marital status (1 = Married, 2 = Single, 3 = Others) | Demographic factor |
| `AGE` | Integer | Age in years | Borrower demographic |
| `PAY_0` | Integer | Repayment status in Sept 2005 (-2: Inactive, -1: Paid full, 0: Revolving, 1-8: Months delayed) | Core behavioral signal |
| `PAY_2` | Integer | Repayment status in August 2005 | Historical delay |
| `PAY_3` | Integer | Repayment status in July 2005 | Historical delay |
| `PAY_4` | Integer | Repayment status in June 2005 | Historical delay |
| `PAY_5` | Integer | Repayment status in May 2005 | Historical delay |
| `PAY_6` | Integer | Repayment status in April 2005 | Historical delay |
| `BILL_AMT1` to `BILL_AMT6` | Decimal | Monthly statement bill amount (Sept to April) | Outstanding obligation |
| `PAY_AMT1` to `PAY_AMT6` | Decimal | Amount paid in previous month (Sept to April) | Repayment behavior |
| `DEFAULT_NEXT_MONTH` | Integer | Ground truth default indicator (1 = Default, 0 = Non-default) | Target variable |
| `AVG_UTILIZATION_RATE` | Float | 6-month mean credit utilization (Bill / Limit) | Leverage indicator |
| `MAX_UTILIZATION_RATE` | Float | Maximum single-month credit utilization | Peak line strain |
| `MAX_DELINQUENCY_MONTHS`| Integer | Worst historical payment delay observed in 6 months | Peak delinquency severity |
| `NUM_MONTHS_DELINQUENT` | Integer | Count of months with delayed status (> 0) | Chronic delinquency flag |
| `DELINQUENCY_TREND` | Integer | Recent vs oldest repayment status (PAY_0 - PAY_6) | Deterioration direction |
| `AVG_PAYMENT_RATIO` | Float | Average payment amount relative to bill balance | Amortization velocity |
| `TOTAL_BILL_AMOUNT` | Decimal | Aggregate 6-month billed amount | Total debt usage |
| `TOTAL_PAYMENT_AMOUNT`| Decimal | Aggregate 6-month payments made | Total debt retired |
| `REVOLVING_BURDEN_RATIO`| Float | Cumulative unpaid balance divided by credit limit | Revolving debt strain |
| `EARLY_WARNING_FLAG` | Integer | 1 if account triggers early warning criteria, else 0 | EWS triage indicator |
| `PREDICTED_PD` | Float | Probability of Default predicted by Random Forest (0.0 to 1.0) | Model forecast |
| `CREDIT_RISK_SCORE` | Integer | Custom credit risk score scaled to 300–850 | Illustrative custom risk score (not official bureau FICO) |
| `RISK_TIER` | String | 'Prime', 'Near-Prime', 'Subprime', 'High Risk' | Strategic risk tier |
| `RECOMMENDED_ACTION` | String | Policy-driven credit mitigation action | Operational recommendation |
