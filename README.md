# Budget Tracker ETL Pipeline

An automated personal finance tracking system that extracts credit card transactions from Gmail, categorizes them using machine learning, and serves a live dashboard.

## Architecture

**Medallion Data Lake Pattern:**
- **Bronze Layer:** Raw transaction emails extracted from Gmail API (JSON)
- **Silver Layer:** Cleaned, ML-categorized transactions (Parquet)
- **Gold Layer:** Pre-aggregated analytics views in PostgreSQL (Supabase)

**Pipeline:**
```
Gmail API → Email Parser → ML Categorizer → Parquet Storage → Supabase PostgreSQL → Gold Views → Streamlit Dashboard
                           (91% accuracy)    (Silver Layer)    (hosted cloud DB)                  (live at drewbudget.duckdns.org)
```

**Infrastructure:**
- **Supabase** — hosted PostgreSQL database (cloud)
- **Oracle Cloud VM** — always-on Ubuntu server hosting the Streamlit dashboard
- **nginx + Let's Encrypt** — reverse proxy with SSL termination
- **DuckDNS** — free DNS for `drewbudget.duckdns.org`

## Features

- **Automated Email Extraction:** Gmail API integration for Chase, Discover, and CapitalOne transactions
- **Machine Learning Categorization:** Logistic Regression model with TF-IDF vectorization (91% accuracy)
- **9 Spending Categories:** Dining, Shopping, Groceries, Subscriptions, Entertainment, Transportation, Bills, Travel, Other
- **Supabase PostgreSQL:** Cloud-hosted data warehouse with indexed columns for fast queries
- **Gold Layer Analytics:** 6 pre-aggregated views for instant insights (monthly trends, top merchants, category breakdowns)
- **Live Dashboard:** Password-protected Streamlit app at `https://drewbudget.duckdns.org` with a current month snapshot (MTD spend, MoM/YoY deltas, cumulative daily chart) and a historical deep dive (category, monthly trends, top merchants, card usage)
- **Data Quality Validation:** Null checks across all required fields before load

## Tech Stack

- **Python 3.12.10**
- **Pandas** - Data transformation
- **scikit-learn** - ML categorization model
- **PostgreSQL / Supabase** - Cloud analytics database
- **Gmail API** - Transaction extraction
- **Parquet** - Columnar storage format
- **Streamlit** - Interactive dashboard
- **Plotly** - Interactive charts
- **nginx** - Reverse proxy and SSL termination
- **Oracle Cloud** - VM hosting (Always Free tier)

## Project Structure
```
budget_tracker/
├── data/                    # gitignored
│   ├── bronze/              # Raw transaction JSONs
│   └── silver/              # Cleaned Parquet files
├── models/                  # Trained ML models (gitignored)
├── notebooks/               # Exploratory analysis
├── sql/                     # Standalone SQL scripts
├── src/
│   ├── extract/             # Gmail API extraction and parsers
│   ├── transform/           # ML categorization pipeline
│   ├── load/                # PostgreSQL schema, loader, and gold views
│   └── dashboard/           # Streamlit dashboard
├── .streamlit/              # Streamlit configuration
├── tests/                   # Test scripts
├── requirements.txt
└── docker-compose.yml       # Local PostgreSQL + PgAdmin (dev only)
```

## Setup

### 1. Prerequisites
```bash
python --version  # Should be 3.12.x
```

### 2. Install Dependencies
```bash
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\Activate
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the project root:
```
SUPABASE_DB_URL=postgresql://...
EMAIL_ADDRESS=...
EMAIL_PASSWORD=...
IMAP_SERVER=imap.gmail.com
IMAP_PORT=993
DASHBOARD_PASSWORD=...
```

### 4. Set Up Gmail API
1. Create project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Gmail API
3. Download OAuth credentials as `credentials.json`
4. Place in `credentials/` directory

### 5. Run Pipeline
```bash
# Step 1: Extract transactions from Gmail
python src/extract/extract_transactions.py

# Step 2: Train ML categorization model (first time only)
python src/transform/train_categorizer.py

# Step 3: Transform and categorize transactions
python src/transform/transform_transactions.py

# Step 4: Load to PostgreSQL
python src/load/load_to_postgres.py

# Step 5: Launch the dashboard locally
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

6 pre-aggregated views in Supabase for instant analytics:

1. **`gold.category_summary`** - Overall spending by category with percentages
2. **`gold.monthly_totals`** - Month-over-month spending trends
3. **`gold.monthly_spending_by_category`** - Detailed monthly breakdown per category
4. **`gold.top_merchants`** - Top merchants by total spending
5. **`gold.card_usage_stats`** - Credit card usage statistics
6. **`gold.daily_spending`** - Daily spending patterns

## Next Steps

- [x] Gold layer aggregations (monthly summaries, category totals)
- [x] PostgreSQL schema design and data loading
- [x] Interactive dashboard — current month snapshot and historical deep dive
- [x] Cloud deployment — Supabase DB, Oracle VM, nginx, SSL, custom domain
- [x] Password-protected live dashboard at `https://drewbudget.duckdns.org`
- [ ] GitHub Actions for daily automated pipeline runs
- [ ] Budget alerts and spending insights

## License

Personal project - not for commercial use
