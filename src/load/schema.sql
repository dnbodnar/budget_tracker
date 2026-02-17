-- Create silver schema for transformed data
CREATE SCHEMA IF NOT EXISTS silver;

-- Drop existing table if re-running
DROP TABLE IF EXISTS silver.transactions CASCADE;

-- Main transactions table
CREATE TABLE silver.transactions (
    id SERIAL PRIMARY KEY,
    transaction_date DATE NOT NULL,
    merchant_name VARCHAR(255) NOT NULL,
    amount NUMERIC(10, 2) NOT NULL,
    card_name VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for common query patterns
CREATE INDEX idx_transaction_date ON silver.transactions(transaction_date);
CREATE INDEX idx_category ON silver.transactions(category);
CREATE INDEX idx_card_name ON silver.transactions(card_name);
CREATE INDEX idx_merchant_name ON silver.transactions(merchant_name);

