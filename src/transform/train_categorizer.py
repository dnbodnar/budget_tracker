import json
import pickle
from pathlib import Path
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import numpy as np
from scipy.sparse import hstack, csr_matrix

def load_training_data():
    """Load labeled merchants and merge with full transaction data from bronze"""
    
    print("Loading labeled merchants...")
    with open("data/labeled_transactions.json", 'r') as f:
        labeled_merchants = json.load(f)
    
    print(f"Found {len(labeled_merchants)} labeled merchants")
    
    print("Loading transactions from bronze layer...")
    bronze_dir = Path("data/bronze")
    transactions = []
    
    for json_file in bronze_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            transaction = json.load(f)
            merchant = transaction.get('merchant_name', '').strip()
            
            if merchant in labeled_merchants:
                transactions.append({
                    'merchant_name': merchant,
                    'amount': transaction.get('amount', 0),
                    'card_name': transaction.get('card_name', 'Unknown'),
                    'transaction_date': transaction.get('transaction_date', ''),
                    'category': labeled_merchants[merchant]
                })
    
    print(f"Found {len(transactions)} transactions matching labeled merchants\n")
    return transactions

def extract_date_features(date_str):
    """Extract day of month from transaction date"""
    if not date_str:
        return 15
    
    try:
        formats = [
            "%B %d, %Y",
            "%b %d, %Y at %I:%M %p ET",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.day
            except ValueError:
                continue
        return 15
    except:
        return 15

def amount_bucket(amt):
    """Categorize amounts into meaninful buckets"""
    if amt < 2.0:
        return 0 #Tiny (gas authorization, parking )
    elif amt < 10.0:
        return 1  #Small (some food, sweet treats)
    elif amt < 30.0:
        return 2 #Medium (dining at restaraunt, small shopping)
    elif amt < 75.0:
        return 3 #Large (groceries, full gas fillup)
    elif amt < 150.0: 
        return 4 # Very Large (shopping, travel, some bills)
    else: 
        return 5 # Huge (large shopping, travel)
    
def train_model():
    """Train merchant categorization model with enhanced features"""
    
    transactions = load_training_data()
    
    if len(transactions) < 50:
        print("ERROR: Not enough transactions found.")
        return
    
    merchant_names = [t['merchant_name'] for t in transactions]
    amounts = [float(t['amount']) if t['amount'] else 0.0 for t in transactions]
    amount_buckets = [amount_bucket(amt) for amt in amounts]
    card_names = [t['card_name'] for t in transactions]
    dates = [extract_date_features(t['transaction_date']) for t in transactions]
    categories = [t['category'] for t in transactions]
    
    print("=== FEATURE SUMMARY ===")
    print(f"Total transactions: {len(transactions)}")
    print(f"Unique merchants: {len(set(merchant_names))}")
    print(f"Unique cards: {set(card_names)}")
    print(f"Amount range: ${min(amounts):.2f} - ${max(amounts):.2f}")
    print(f"\nCategory distribution:")
    for cat in set(categories):
        count = categories.count(cat)
        print(f"  {cat}: {count}")
    
    indices = list(range(len(transactions)))
    train_idx, test_idx = train_test_split(
        indices, test_size=0.2, random_state=42, stratify=categories
    )
    
    print("\nVectorizing merchant names...")
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1, 2))
    
    merchant_train = [merchant_names[i] for i in train_idx]
    merchant_test = [merchant_names[i] for i in test_idx]
    
    X_merchant_train = vectorizer.fit_transform(merchant_train)
    X_merchant_test = vectorizer.transform(merchant_test)
    
    print("Encoding card names...")
    unique_cards = list(set(card_names))
    card_to_idx = {card: idx for idx, card in enumerate(unique_cards)}
    
    card_train = np.array([[card_to_idx[card_names[i]]] for i in train_idx])
    card_test = np.array([[card_to_idx[card_names[i]]] for i in test_idx])
    
    amount_train = np.array([[amount_buckets[i]] for i in train_idx])
    amount_test = np.array([[amount_buckets[i]] for i in test_idx])
    
    date_train = np.array([[dates[i]] for i in train_idx])
    date_test = np.array([[dates[i]] for i in test_idx])
    
    print("Combining features...")
    X_train = hstack([
        X_merchant_train,
        csr_matrix(amount_train),
        csr_matrix(card_train),
        csr_matrix(date_train)
    ])
    
    X_test = hstack([
        X_merchant_test,
        csr_matrix(amount_test),
        csr_matrix(card_test),
        csr_matrix(date_test)
    ])
    
    y_train = [categories[i] for i in train_idx]
    y_test = [categories[i] for i in test_idx]
    
    print(f"\nTraining set: {len(train_idx)} transactions")
    print(f"Test set: {len(test_idx)} transactions")
    
    print("\nTraining model...")
    model = LogisticRegression(
        class_weight='balanced',
        max_iter=2000,
        random_state=42
    )
    model.fit(X_train, y_train)
    
    print("\n=== MODEL EVALUATION ===")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2%}")
    
    print("\nDetailed Report:")
    print(classification_report(y_test, y_pred))
    
    print("\nSaving model...")
    with open("models/merchant_categorizer.pkl", 'wb') as f:
        pickle.dump(model, f)
    
    with open("models/vectorizer.pkl", 'wb') as f:
        pickle.dump(vectorizer, f)
    
    with open("models/card_mapping.pkl", 'wb') as f:
        pickle.dump(card_to_idx, f)
    
    print("Model saved to models/merchant_categorizer.pkl")
    print("Vectorizer saved to models/vectorizer.pkl")
    print("Card mapping saved to models/card_mapping.pkl")
    
    print("\n=== SAMPLE PREDICTIONS ===")
    test_samples = [
        ("STARBUCKS STORE 22093", 5.47, "Discover", 15),
        ("SHELL", 45.00, "Chase", 10),
        ("AMAZON.COM", 29.99, "CapitalOne", 20),
        ("CHIPOTLE 2129", 11.45, "CapitalOne", 5),
        ("SPOTIFY", 9.99, "Discover", 1),
    ]
    
    for merchant, amount, card, day in test_samples:
        merchant_vec = vectorizer.transform([merchant])
        card_idx = card_to_idx.get(card, 0)
        bucket = amount_bucket(amount)
        features = hstack([
            merchant_vec,
            csr_matrix([[bucket]]),
            csr_matrix([[card_idx]]),
            csr_matrix([[day]])
        ])
        prediction = model.predict(features)[0]
        print(f"{merchant} (${amount}, {card}) → {prediction}")

if __name__ == "__main__":
    import os
    os.makedirs("models", exist_ok=True)
    train_model()