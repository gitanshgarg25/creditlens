-- =============================================================================
-- CREDITLENS: AI-ASSISTED CREDIT RISK & EARLY-WARNING INTELLIGENCE PLATFORM
-- PostgreSQL Database Schema & Analytical Views DDL
-- Dataset: UCI Default of Credit Card Clients (Taiwan)
-- =============================================================================

-- Drop tables if existing (for clean re-runs)
DROP VIEW IF EXISTS view_portfolio_segment_risk;
DROP VIEW IF EXISTS view_early_warning_delinquency_summary;
DROP VIEW IF EXISTS view_executive_portfolio_summary;
DROP TABLE IF EXISTS credit_risk_evaluations;
DROP TABLE IF EXISTS credit_card_clients;

-- 1. Base Clients Table
CREATE TABLE credit_card_clients (
    client_id                   INTEGER PRIMARY KEY,
    limit_bal                   NUMERIC(12, 2) NOT NULL,
    sex_code                    SMALLINT NOT NULL,              -- 1: Male, 2: Female
    education_code              SMALLINT NOT NULL,              -- 1: Grad School, 2: Univ, 3: High School, 4: Others/Unknown
    marriage_code               SMALLINT NOT NULL,              -- 1: Married, 2: Single, 3: Others
    age                         INTEGER NOT NULL,
    
    -- Repayment Status: -2: Inactive/No usage, -1: Paid full, 0: Revolving credit, 1-9: Payment delay months
    pay_status_sep              SMALLINT NOT NULL,
    pay_status_aug              SMALLINT NOT NULL,
    pay_status_jul              SMALLINT NOT NULL,
    pay_status_jun              SMALLINT NOT NULL,
    pay_status_may              SMALLINT NOT NULL,
    pay_status_apr              SMALLINT NOT NULL,
    
    -- Bill Statement Amounts (NTD)
    bill_amt_sep                NUMERIC(12, 2) NOT NULL,
    bill_amt_aug                NUMERIC(12, 2) NOT NULL,
    bill_amt_jul                NUMERIC(12, 2) NOT NULL,
    bill_amt_jun                NUMERIC(12, 2) NOT NULL,
    bill_amt_may                NUMERIC(12, 2) NOT NULL,
    bill_amt_apr                NUMERIC(12, 2) NOT NULL,
    
    -- Previous Payment Amounts (NTD)
    pay_amt_sep                 NUMERIC(12, 2) NOT NULL,
    pay_amt_aug                 NUMERIC(12, 2) NOT NULL,
    pay_amt_jul                 NUMERIC(12, 2) NOT NULL,
    pay_amt_jun                 NUMERIC(12, 2) NOT NULL,
    pay_amt_may                 NUMERIC(12, 2) NOT NULL,
    pay_amt_apr                 NUMERIC(12, 2) NOT NULL,
    
    -- Historical Default Ground Truth (1: Defaulted, 0: Current)
    default_next_month          SMALLINT NOT NULL DEFAULT 0,
    created_at                  TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performant filtering and aggregation
CREATE INDEX idx_clients_default ON credit_card_clients(default_next_month);
CREATE INDEX idx_clients_age ON credit_card_clients(age);
CREATE INDEX idx_clients_limit ON credit_card_clients(limit_bal);
CREATE INDEX idx_clients_pay_sep ON credit_card_clients(pay_status_sep);

-- 2. Credit Risk Model Predictions & Early Warning Scores Table
CREATE TABLE credit_risk_evaluations (
    evaluation_id               SERIAL PRIMARY KEY,
    client_id                   INTEGER NOT NULL REFERENCES credit_card_clients(client_id) ON DELETE CASCADE,
    predicted_pd                NUMERIC(6, 4) NOT NULL,         -- Probability of Default (0.0000 - 1.0000)
    credit_risk_score           INTEGER NOT NULL,              -- Standardized Credit Score (300 - 850)
    risk_tier                   VARCHAR(20) NOT NULL,           -- 'Prime', 'Near-Prime', 'Subprime', 'High Risk'
    avg_utilization_rate        NUMERIC(6, 4) NOT NULL,         -- Mean (Bill / Limit)
    max_delinquency_months      SMALLINT NOT NULL,              -- Highest delay status across 6 months
    revolving_burden_ratio      NUMERIC(6, 4) NOT NULL,         -- Total unpaid balance to credit limit
    early_warning_flag          BOOLEAN NOT NULL DEFAULT FALSE, -- Triggered if utilization > 80% or delinquency >= 2
    recommended_action          VARCHAR(100) NOT NULL,          -- e.g. 'Credit Limit Review', 'Direct Outreach', 'Normal Monitoring'
    evaluated_at                TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_eval_client_id ON credit_risk_evaluations(client_id);
CREATE INDEX idx_eval_risk_tier ON credit_risk_evaluations(risk_tier);
CREATE INDEX idx_eval_score ON credit_risk_evaluations(credit_risk_score);
CREATE INDEX idx_eval_ews ON credit_risk_evaluations(early_warning_flag);

-- 3. Executive Portfolio Summary View
CREATE OR REPLACE VIEW view_executive_portfolio_summary AS
SELECT 
    COUNT(c.client_id) AS total_borrowers,
    SUM(c.limit_bal) AS total_credit_exposure,
    AVG(c.limit_bal) AS avg_credit_limit,
    AVG(e.credit_risk_score) AS portfolio_avg_score,
    AVG(e.predicted_pd) AS portfolio_expected_default_rate,
    ROUND(SUM(CASE WHEN c.default_next_month = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS actual_default_rate_pct,
    SUM(CASE WHEN e.early_warning_flag THEN 1 ELSE 0 END) AS total_early_warning_alerts,
    ROUND(SUM(CASE WHEN e.early_warning_flag THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS early_warning_rate_pct
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id;

-- 4. Segment Risk Profile View
CREATE OR REPLACE VIEW view_portfolio_segment_risk AS
SELECT 
    e.risk_tier,
    COUNT(c.client_id) AS borrower_count,
    ROUND(COUNT(c.client_id) * 100.0 / SUM(COUNT(c.client_id)) OVER (), 2) AS portfolio_share_pct,
    SUM(c.limit_bal) AS segment_exposure,
    ROUND(AVG(c.limit_bal), 2) AS avg_credit_limit,
    ROUND(AVG(e.avg_utilization_rate) * 100, 2) AS avg_utilization_pct,
    ROUND(AVG(e.predicted_pd) * 100, 2) AS model_expected_default_pct,
    ROUND(SUM(CASE WHEN c.default_next_month = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS actual_default_rate_pct,
    SUM(CASE WHEN e.early_warning_flag THEN 1 ELSE 0 END) AS active_alerts
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
GROUP BY e.risk_tier
ORDER BY avg_credit_limit DESC;

-- 5. Early Warning Trajectory View
CREATE OR REPLACE VIEW view_early_warning_delinquency_summary AS
SELECT 
    CASE 
        WHEN c.pay_status_sep <= 0 THEN '0 Months (Current / Paid)'
        WHEN c.pay_status_sep = 1 THEN '30 Days Past Due (1 Mo)'
        WHEN c.pay_status_sep = 2 THEN '60 Days Past Due (2 Mo)'
        ELSE '90+ Days Past Due (Severe)'
    END AS delinquency_status_sep,
    COUNT(c.client_id) AS account_count,
    ROUND(AVG(e.avg_utilization_rate) * 100, 2) AS avg_utilization_pct,
    ROUND(AVG(e.predicted_pd) * 100, 2) AS avg_model_pd_pct,
    ROUND(SUM(CASE WHEN c.default_next_month = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS default_rate_pct,
    SUM(c.bill_amt_sep) AS total_outstanding_balance
FROM credit_card_clients c
JOIN credit_risk_evaluations e ON c.client_id = e.client_id
GROUP BY 1
ORDER BY default_rate_pct ASC;
