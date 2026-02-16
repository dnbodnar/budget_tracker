import json
import pickle
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
from scipy.sparse import hstack, csr_matrix
from collections import Counter

def load_ml_model():
    print("Loading ML model...")
    
    with open("models/merchant_categorizer.pkl", 'rb') as f:
        model = pickle.load(f)
    
    with open("models/vectorizer.pkl", 'rb') as f:
        vectorizer = pickle.load(f)
    
    with open("models/card_mapping.pkl", 'rb') as f:
        card_mapping = pickle.load(f)
    
    return model, vectorizer, card_mapping

def amount_bucket(amt):
    if amt is None or amt == 0:
        return 2
    if amt < 2.0:
        return 0
    elif amt < 10.0:
        return 1
    elif amt < 30.0:
        return 2
    elif amt < 75.0:
        return 3
    elif amt < 150.0:
        return 4
    else:
        return 5

def parse_date(date_str):
    if not date_str:
        return None
    
    formats = [
        "%B %d, %Y",
        "%b %d, %Y at %I:%M %p ET",
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None

def categorize_transaction(transaction, model, vectorizer, card_mapping):
    merchant = transaction.get('merchant_name', '')
    amount = transaction.get('amount', 0)
    card = transaction.get('card_name', 'Unknown')
    date_str = parse_date(transaction.get('transaction_date', ''))

    merchant_vec = vectorizer.transform([merchant])
    card_idx = card_mapping.get(card, 0)
    bucket = amount_bucket(amount)

    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day = dt.day
    except:
        day = 15

    features = hstack([
        merchant_vec,
        csr_matrix([[bucket]]),
        csr_matrix([[card_idx]]),
        csr_matrix([[day]])
    ])

    category = model.predict(features)[0]
    
    return {
        'transaction_date': date_str,
        'merchant_name': str(merchant),
        'amount': float(amount) if amount else 0.0,
        'card_name': str(card),
        'category': str(category)
    }

def transform_transactions():
    print("=" * 60)
    print("BUDGET TRACKER - TRANSFORM LAYER")
    print("=" * 60)

    model, vectorizer, card_mapping = load_ml_model()

    print("\n1. Reading and categorizing bronze data...")
    bronze_dir = Path("data/bronze")
    json_files = list(bronze_dir.glob("*.json"))
    
    print(f"   Found {len(json_files)} files")
    
    categorized = []
    
    for i, file in enumerate(json_files):
        if (i + 1) % 100 == 0:
            print(f"   Processed {i + 1}/{len(json_files)}...")
        
        with open(file, 'r') as f:
            transaction = json.load(f)
        
        clean = categorize_transaction(transaction, model, vectorizer, card_mapping)
        categorized.append(clean)
    
    print(f"Categorized {len(categorized)} transactions")

    print("\n2. Creating DataFrame...")
    df = pd.DataFrame(categorized)
    
    print(f"Created DataFrame with {len(df)} rows")

    print("\n3. Sample data:")
    for _, row in df.head(10).iterrows():
        print(f"  {row['transaction_date']} | {row['merchant_name'][:30]:30} | ${row['amount']:6.2f} | {row['card_name']:10} | {row['category']}")

    print("\n4. Data Quality Report:")
    total = len(df)
    null_dates = df['transaction_date'].isna().sum()
    null_merchants = df['merchant_name'].isna().sum()
    null_amounts = df['amount'].isna().sum()
    null_categories = df['category'].isna().sum()
    
    print(f"   Total transactions: {total}")
    print(f"   Null dates: {null_dates} ({null_dates/total*100:.1f}%)")
    print(f"   Null merchants: {null_merchants} ({null_merchants/total*100:.1f}%)")
    print(f"   Null amounts: {null_amounts} ({null_amounts/total*100:.1f}%)")
    print(f"   Null categories: {null_categories} ({null_categories/total*100:.1f}%)")

    print("\n5. Category Distribution:")
    cat_counts = df['category'].value_counts()
    for cat, count in cat_counts.items():
        print(f"   {cat}: {count}")
    
    print("\n6. Saving to silver layer...")
    output_path = Path("data/silver/transactions")
    output_path.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path / "transactions.parquet", index=False)
    
    print(f"Saved to {output_path / 'transactions.parquet'}")
    
    print("\n" + "=" * 60)
    print("TRANSFORMATION COMPLETE!")
    print("=" * 60)

if __name__ == "__main__":
    transform_transactions()