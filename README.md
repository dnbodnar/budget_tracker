# Budget Tracker ETL Pipeline

An automated personal finance tracking system that extracts credit card transactions from Gmail, categorizes them using machine learning, and stores analytics-ready data.

## Architecture

**Medallion Data Lake Pattern:**
- **Bronze Layer:** Raw transaction emails extracted from Gmail API (JSON)
- **Silver Layer:** Cleaned, ML-categorized transactions (Parquet)
- **Gold Layer:** Aggregated analytics ready for PostgreSQL *(coming soon)*

**Pipeline:**
```
Gmail API → Email Parser → ML Categorizer → Parquet Storage → PostgreSQL
           (865 emails)   (91% accuracy)    (Silver Layer)   (Gold Layer)
```

## Features

- **Automated Email Extraction:** Gmail API integration for Chase, Discover, and CapitalOne transactions
- **Machine Learning Categorization:** Logistic Regression model with TF-IDF vectorization (91% accuracy)
- **9 Spending Categories:** Dining, Shopping, Groceries, Subscriptions, Entertainment, Transportation, Bills, Travel, Other
- **Data Quality Validation:** 0% null values across 865+ transactions
- **Feature Engineering:** Amount bucketing, card encoding, temporal features

## Tech Stack

- **Python 3.12.10**
- **Pandas** - Data transformation
- **scikit-learn** - ML categorization model
- **PostgreSQL** - Analytics database
- **Docker** - Database containerization
- **Gmail API** - Transaction extraction
- **Parquet** - Columnar storage format

## Project Structure
```
budget_tracker/
├── data/
│   ├── bronze/          # Raw transaction JSONs (865 files)
│   ├── silver/          # Cleaned Parquet files
│   └── gold/            # Aggregated analytics (coming soon)
├── models/              # Trained ML models (.pkl files)
├── src/
│   ├── extract/         # Gmail API extraction
│   ├── ml/              # Model training scripts
│   └── transform/       # ETL transformation pipeline
├── credentials/         # Gmail API credentials (gitignored)
└── docker-compose.yml   # PostgreSQL container
```

## Setup

### 1. Prerequisites
```bash
# Python 3.12
python --version  # Should be 3.12.x

# Docker Desktop
docker --version
```

### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate
pip install -r requirements.txt
```

### 3. Set Up Gmail API
1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Gmail API
3. Download OAuth credentials as `credentials.json`
4. Place in `credentials/` directory

### 4. Start PostgreSQL
```bash
docker compose up -d
```

### 5. Run Pipeline
```bash
# Extract transactions from Gmail
python src/extract/extract_emails.py

# Train ML categorization model
python src/ml/train_model.py

# Transform and categorize transactions
python src/transform/transform_transactions.py
```

## Machine Learning Model

**Features:**
- Merchant name (TF-IDF vectorization)
- Transaction amount (6-tier bucketing)
- Card type (Chase, Discover, CapitalOne)
- Day of month

**Model:** Logistic Regression (max_iter=1000)  
**Training Data:** 330 manually labeled transactions  
**Accuracy:** 91%  

## Next Steps

- [ ] Gold layer aggregations (monthly summaries, category totals)
- [ ] PostgreSQL schema design and data loading
- [ ] Apache Airflow orchestration
- [ ] Dashboard with analytics queries
- [ ] Budget alerts and spending insights

## License

Personal project - not for commercial use