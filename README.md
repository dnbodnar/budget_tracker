# Budget Tracker ETL Pipeline

An automated personal finance tracking system that extracts credit card transactions from Gmail, categorizes them using machine learning, and stores analytics-ready data.

## Architecture

**Medallion Data Lake Pattern:**
- **Bronze Layer:** Raw transaction emails extracted from Gmail API (JSON)
- **Silver Layer:** Cleaned, ML-categorized transactions (Parquet)
- **Gold Layer:** Pre-aggregated analytics views in PostgreSQL

**Pipeline:**
```
Gmail API → Email Parser → ML Categorizer → Parquet Storage → PostgreSQL Load → Gold Views
                           (91% accuracy)    (Silver Layer)                    (6 analytics views)
```

## Features

- **Automated Email Extraction:** Gmail API integration for Chase, Discover, and CapitalOne transactions
- **Machine Learning Categorization:** Logistic Regression model with TF-IDF vectorization (91% accuracy)
- **9 Spending Categories:** Dining, Shopping, Groceries, Subscriptions, Entertainment, Transportation, Bills, Travel, Other
- **PostgreSQL Data Warehouse:** Structured silver layer with indexed columns for fast queries
- **Gold Layer Analytics:** 6 pre-aggregated views for instant insights (monthly trends, top merchants, category breakdowns)
- **Interactive Dashboard:** Streamlit app with year/month filtering, category breakdowns, spending trends, top merchants, and card usage
- **Data Quality Validation:** Null checks across all required fields before load
- **Feature Engineering:** Amount bucketing, card encoding, temporal features

## Tech Stack

- **Python 3.12.10**
- **Pandas** - Data transformation
- **scikit-learn** - ML categorization model
- **PostgreSQL** - Analytics database
- **Docker** - Database containerization
- **Gmail API** - Transaction extraction
- **Parquet** - Columnar storage format
- **Streamlit** - Interactive dashboard
- **Plotly** - Interactive charts

## Project Structure
```
budget_tracker/
├── data/                    # gitignored
│   ├── bronze/              # Raw transaction JSONs
│   └── silver/              # Cleaned Parquet files
├── models/                  # Trained ML models (gitignored)
├── notebooks/               # Exploratory analysis
├── sql/                     # Standalone SQL scripts
│   ├── 01_create_tables.sql
│   └── 02_seed_categories.sql
├── src/
│   ├── extract/             # Gmail API extraction and parsers
│   ├── transform/           # ML categorization pipeline
│   ├── load/                # PostgreSQL schema, loader, and gold views
│   └── dashboard/           # Streamlit dashboard
├── .streamlit/              # Streamlit configuration
├── tests/                   # Test scripts
├── config/                  # Configuration files
├── requirements.txt
└── docker-compose.yml       # PostgreSQL + PgAdmin containers
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
# Step 1: Extract transactions from Gmail
python src/extract/extract_transactions.py

# Step 2: Train ML categorization model
python src/transform/train_categorizer.py

# Step 3: Transform and categorize transactions
python src/transform/transform_transactions.py

# Step 4: Load to PostgreSQL and create gold views
python src/load/load_to_postgres.py

# Step 5: Launch the dashboard
streamlit run src/dashboard/app.py
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

## Gold Layer Analytics Views

The PostgreSQL gold layer provides 6 pre-aggregated views for instant analytics:

1. **`gold.category_summary`** - Overall spending by category with percentages
2. **`gold.monthly_totals`** - Month-over-month spending trends
3. **`gold.monthly_spending_by_category`** - Detailed monthly breakdown per category
4. **`gold.top_merchants`** - Top merchants by total spending
5. **`gold.card_usage_stats`** - Credit card usage statistics
6. **`gold.daily_spending`** - Daily spending patterns

**Access via PgAdmin:**
- URL: http://localhost:5050
- Email: `admin@admin.com`
- Password: `admin`
- Server: `budget_postgres` (host), port 5432

## Next Steps

- [x] Gold layer aggregations (monthly summaries, category totals)
- [x] PostgreSQL schema design and data loading
- [x] Interactive dashboard (Streamlit) with year/month filtering
- [ ] Dashboard polish and additional views
- [ ] Apache Airflow orchestration for scheduled runs
- [ ] Budget alerts and spending insights
- [ ] Automated email reports

## License

Personal project - not for commercial use
