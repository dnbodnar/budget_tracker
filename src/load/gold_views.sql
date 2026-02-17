-- Create gold schema for aggregated analytics
CREATE SCHEMA IF NOT EXISTS gold;

-- VIEW 1: Monthly Spending by Category
-- Shows total spending per category per month
CREATE OR REPLACE VIEW gold.monthly_spending_by_category AS
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    category,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction_amount,
    MIN(amount) AS min_amount,
    MAX(amount) AS max_amount
FROM silver.transactions
GROUP BY DATE_TRUNC('month', transaction_date), category
ORDER BY month DESC, total_spent DESC;

-- VIEW 2: Top Merchants by Total Spending
-- Shows which merchants you spend the most money at
CREATE OR REPLACE VIEW gold.top_merchants AS
SELECT
    merchant_name,
    category,
    COUNT(*) AS visit_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction,
    MIN(transaction_date) AS first_visit,
    MAX(transaction_date) AS last_visit
FROM silver.transactions
GROUP BY merchant_name, category
ORDER BY total_spent DESC;

-- VIEW 3: Card Usage Statistics
-- Shows spending breakdown by credit card
CREATE OR REPLACE VIEW gold.card_usage_stats AS
SELECT
    card_name,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction,
    COUNT(DISTINCT merchant_name) AS unique_merchants,
    COUNT(DISTINCT category) AS categories_used,
    MIN(transaction_date) AS first_transaction,
    MAX(transaction_date) AS last_transaction
FROM silver.transactions
GROUP BY card_name
ORDER BY total_spent DESC;

-- VIEW 4: Daily Spending Summary
-- Shows daily spending totals and transaction counts
CREATE OR REPLACE VIEW gold.daily_spending AS
SELECT
    transaction_date,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction,
    STRING_AGG(DISTINCT category, ', ' ORDER BY category) AS categories
FROM silver.transactions
GROUP BY transaction_date
ORDER BY transaction_date DESC;

-- VIEW 5: Category Summary (Overall)
-- Overall spending statistics by category
CREATE OR REPLACE VIEW gold.category_summary AS
SELECT
    category,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction,
    MIN(amount) AS min_transaction,
    MAX(amount) AS max_transaction,
    ROUND(100.0 * SUM(amount) / (SELECT SUM(amount) FROM silver.transactions), 2) AS percent_of_total_spending
FROM silver.transactions
GROUP BY category
ORDER BY total_spent DESC;

-- VIEW 6: Monthly Totals (All Categories)
-- Monthly spending totals across all categories
CREATE OR REPLACE VIEW gold.monthly_totals AS
SELECT
    DATE_TRUNC('month', transaction_date) AS month,
    COUNT(*) AS transaction_count,
    SUM(amount) AS total_spent,
    AVG(amount) AS avg_transaction,
    COUNT(DISTINCT merchant_name) AS unique_merchants,
    COUNT(DISTINCT category) AS categories_used
FROM silver.transactions
GROUP BY DATE_TRUNC('month', transaction_date)
ORDER BY month DESC;
