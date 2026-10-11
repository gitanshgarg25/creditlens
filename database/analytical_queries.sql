-- =============================================================================
-- CREDITLENS: INDUSTRY PORTFOLIO & RISK ANALYTICAL SQL QUERIES
-- Designed for Data Analyst, Business Analyst, BI, and Risk Analyst Portfolios
-- Compatible with PostgreSQL & SQLite (via SQLAlchemy / db interface)
-- =============================================================================

-- QUERY 1: Portfolio Executive KPI Summary
-- Business Value: Provides Chief Risk Officer (CRO) high-level exposure & risk distribution
SELECT 
    COUNT(c.client_id) AS total_borrowers,
    SUM(c.limit_bal) AS total_credit_limit,
    AVG(c.limit_bal) AS average_credit_line,
    ROUND(AVG(e.credit_risk_score), 1) AS portfolio_average_score,
    ROUND(AVG(e.predicted_pd) * 100, 2) AS expected_portfolio_pd_pct,
    ROUND(SUM(c.default_next_month) * 100.0 / COUNT(*), 2) AS actual_default_rate_pct,
    SUM(CASE WHEN e.early_warning_flag = 1 THEN 1 ELSE 0 END) AS ews_flagged_accounts
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id;


-- QUERY 2: Risk Tier Distribution & Loss Exposure Analysis
-- Business Value: Identifies where the riskiest credit exposure is concentrated
SELECT 
    e.risk_tier,
    COUNT(c.client_id) AS borrower_count,
    ROUND(COUNT(c.client_id) * 100.0 / (SELECT COUNT(*) FROM credit_card_clients), 2) AS portfolio_volume_share_pct,
    SUM(c.limit_bal) AS total_exposure_ntd,
    ROUND(SUM(c.bill_amt_sep), 2) AS current_outstanding_balance_ntd,
    ROUND(AVG(e.avg_utilization_rate) * 100, 2) AS avg_credit_utilization_pct,
    ROUND(AVG(e.predicted_pd) * 100, 2) AS avg_model_predicted_pd_pct,
    ROUND(SUM(c.default_next_month) * 100.0 / COUNT(*), 2) AS actual_default_rate_pct
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
GROUP BY e.risk_tier
ORDER BY 
    CASE e.risk_tier
        WHEN 'Prime' THEN 1
        WHEN 'Near-Prime' THEN 2
        WHEN 'Subprime' THEN 3
        WHEN 'High Risk' THEN 4
        ELSE 5
    END;


-- QUERY 3: Early-Warning Delinquency Migration Analysis
-- Business Value: Shows how repayment status in recent months drives sudden default rate escalation
SELECT 
    c.pay_status_sep AS sep_repayment_status,
    CASE 
        WHEN c.pay_status_sep <= 0 THEN 'Current / Revolving / Paid'
        WHEN c.pay_status_sep = 1 THEN '1 Month Delay (30 DPD)'
        WHEN c.pay_status_sep = 2 THEN '2 Months Delay (60 DPD)'
        ELSE '3+ Months Delay (90+ DPD Severe)'
    END AS delinquency_description,
    COUNT(*) AS total_clients,
    ROUND(AVG(e.credit_risk_score), 0) AS average_score,
    ROUND(SUM(c.default_next_month) * 100.0 / COUNT(*), 2) AS default_rate_pct,
    ROUND(SUM(c.limit_bal), 2) AS total_credit_limit_at_risk,
    ROUND(SUM(c.bill_amt_sep), 2) AS total_balance_at_risk
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
GROUP BY c.pay_status_sep
ORDER BY c.pay_status_sep ASC;


-- QUERY 4: Credit Utilization Burden vs Default Correlation
-- Business Value: Identifies over-leveraged borrowers who max out their credit lines
SELECT 
    CASE 
        WHEN e.avg_utilization_rate < 0.20 THEN '01: Low (< 20%)'
        WHEN e.avg_utilization_rate < 0.50 THEN '02: Moderate (20% - 50%)'
        WHEN e.avg_utilization_rate < 0.80 THEN '03: Elevated (50% - 80%)'
        WHEN e.avg_utilization_rate < 1.00 THEN '04: High (80% - 100%)'
        ELSE '05: Maxed / Over-limit (> 100%)'
    END AS utilization_bucket,
    COUNT(*) AS account_count,
    ROUND(AVG(c.limit_bal), 0) AS avg_limit,
    ROUND(AVG(e.credit_risk_score), 0) AS avg_score,
    ROUND(SUM(c.default_next_month) * 100.0 / COUNT(*), 2) AS default_rate_pct,
    SUM(CASE WHEN e.early_warning_flag = 1 THEN 1 ELSE 0 END) AS ews_triggers
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
GROUP BY 1
ORDER BY 1 ASC;


-- QUERY 5: Demographic & Education Segment Risk Matrix
-- Business Value: Evaluates risk disparities across client demographics for portfolio policy
SELECT 
    CASE c.education_code
        WHEN 1 THEN 'Graduate School'
        WHEN 2 THEN 'University'
        WHEN 3 THEN 'High School'
        ELSE 'Others / Vocational'
    END AS education_level,
    CASE c.sex_code
        WHEN 1 THEN 'Male'
        WHEN 2 THEN 'Female'
    END AS gender,
    COUNT(*) AS borrower_count,
    ROUND(AVG(c.limit_bal), 0) AS avg_credit_line,
    ROUND(AVG(e.credit_risk_score), 0) AS avg_score,
    ROUND(SUM(c.default_next_month) * 100.0 / COUNT(*), 2) AS default_rate_pct
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
GROUP BY c.education_code, c.sex_code
ORDER BY c.education_code ASC, c.sex_code ASC;


-- QUERY 6: Top 10 High-Exposure Distressed Accounts (Intervention Watchlist)
-- Business Value: Immediate operational pipeline for collections / relationship managers
SELECT 
    c.client_id,
    c.limit_bal,
    c.bill_amt_sep AS latest_bill_amt,
    ROUND(e.avg_utilization_rate * 100, 1) AS utilization_pct,
    c.pay_status_sep AS sep_delay_months,
    e.credit_risk_score,
    e.risk_tier,
    ROUND(e.predicted_pd * 100, 2) AS predicted_pd_pct,
    e.recommended_action
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
WHERE e.early_warning_flag = 1 AND c.limit_bal >= 200000
ORDER BY e.predicted_pd DESC, c.limit_bal DESC
LIMIT 10;
