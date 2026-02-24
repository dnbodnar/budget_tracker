import os
import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def load_to_postgres():
    print("=" * 60)
    print("BUDGET TRACKER - LOAD TO POSTGRESQL")
    print("=" * 60)

    print("\n1. Connecting to PostgreSQL...")
    connection_string = os.getenv(
        "SUPABASE_DB_URL",
        "postgresql://budget_user:budget_pass@localhost:5432/budget_tracker"
    )
    engine = create_engine(connection_string)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"   Connected to: {version.split(',')[0]}")
    except Exception as e:
        print(f"   ERROR: Could not connect to database")
        print(f"   {str(e)}")
        return

    print("\n2. Reading silver layer data...")
    silver_path = Path("data/silver/transactions/transactions.parquet")

    if not silver_path.exists():
        print(f"   ERROR: {silver_path} not found")
        return

    df = pd.read_parquet(silver_path)
    print(f"   Loaded {len(df)} transactions from Parquet")

    print("\n3. Data validation before load...")
    total = len(df)
    null_dates = df['transaction_date'].isna().sum()
    null_merchants = df['merchant_name'].isna().sum()
    null_amounts = df['amount'].isna().sum()
    null_categories = df['category'].isna().sum()

    print(f"   Total records: {total}")
    print(f"   Null dates: {null_dates} ({null_dates/total*100:.1f}%)")
    print(f"   Null merchants: {null_merchants} ({null_merchants/total*100:.1f}%)")
    print(f"   Null amounts: {null_amounts} ({null_amounts/total*100:.1f}%)")
    print(f"   Null categories: {null_categories} ({null_categories/total*100:.1f}%)")

    if null_dates > 0 or null_merchants > 0 or null_amounts > 0 or null_categories > 0:
        print("   WARNING: Found null values in required fields!")

    print("\n4. Sample data to be loaded:")
    for _, row in df.head(5).iterrows():
        print(f"  {row['transaction_date']} | {row['merchant_name'][:30]:30} | ${row['amount']:6.2f} | {row['card_name']:10} | {row['category']}")

    print("\n5. Preparing database table...")
    print(f"   Target: silver.transactions")

    with engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS silver;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver.transactions (
                id SERIAL PRIMARY KEY,
                transaction_date DATE NOT NULL,
                merchant_name VARCHAR(255) NOT NULL,
                amount NUMERIC(10, 2) NOT NULL,
                card_name VARCHAR(50) NOT NULL,
                category VARCHAR(50) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.commit()

    print("\n6. Deduplicating against existing records...")
    existing = pd.read_sql("""
        SELECT transaction_date, merchant_name, amount, card_name
        FROM silver.transactions
    """, engine)

    df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.date
    existing['transaction_date'] = pd.to_datetime(existing['transaction_date']).dt.date

    merge_key = ['transaction_date', 'merchant_name', 'amount', 'card_name']
    existing['_exists'] = True
    merged = df.merge(existing, on=merge_key, how='left')
    new_rows = df[merged['_exists'].isna()].copy()

    print(f"   Existing rows in DB: {len(existing)}")
    print(f"   Rows in Parquet: {len(df)}")
    print(f"   New rows to insert: {len(new_rows)}")

    if len(new_rows) == 0:
        print("   Nothing new to load.")
    else:
        print(f"\n7. Loading {len(new_rows)} new rows to PostgreSQL...")

    start_time = datetime.now()

    try:
        if len(new_rows) > 0:
            new_rows.to_sql(
                name='transactions',
                schema='silver',
                con=engine,
                if_exists='append',
                index=False,
                method='multi',
                chunksize=100
            )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print(f"   Inserted {len(new_rows)} rows in {duration:.2f} seconds")

    except Exception as e:
        print(f"   ERROR during load: {str(e)}")
        return

    print("\n7. Verifying loaded data...")
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM silver.transactions"))
        count = result.fetchone()[0]
        print(f"   Rows in database: {count}")

        result = conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM silver.transactions
            GROUP BY category
            ORDER BY count DESC
        """))

        print("\n8. Category distribution in database:")
        for row in result:
            print(f"   {row[0]}: {row[1]}")

        result = conn.execute(text("""
            SELECT
                MIN(transaction_date) as earliest,
                MAX(transaction_date) as latest,
                COUNT(DISTINCT merchant_name) as unique_merchants,
                SUM(amount) as total_spent
            FROM silver.transactions
        """))

        stats = result.fetchone()
        print("\n9. Database statistics:")
        print(f"   Earliest transaction: {stats[0]}")
        print(f"   Latest transaction: {stats[1]}")
        print(f"   Unique merchants: {stats[2]}")
        print(f"   Total amount: ${stats[3]:,.2f}")

    print("\n" + "=" * 60)
    print("LOAD COMPLETE!")
    print("=" * 60)
    print(f"\nDashboard: https://drewbudget.duckdns.org")

if __name__ == "__main__":
    load_to_postgres()
