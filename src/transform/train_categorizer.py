import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.linear_model import LogisticRegression
import pickle

def train_model():
    """Train merchant categorization model"""

    print("Loading labeled data...")
    with open("data/labeled_transactions.json", 'r') as f:
        labeled_data = json.load(f)
    
    merchants = list(labeled_data.keys())
    categories = list(labeled_data.values())

    print(f"Total labeled merchants: {len(merchants)}")
    print(f"Unique categories: {len(set(categories))}")
    print(f"\nCategory distribution:")
    for cat in set(categories):
        count = categories.count(cat)
        print(f" {cat}: {count}")
    
    X_train, X_test, y_train, y_test = train_test_split(merchants, categories, test_size =0.2, random_state=42)

    print(f"\nTraining set: {len(X_train)}")
    print(f"Test set: {len(X_test)}")

    print("\nVectorizing merchant names...")
    vectorizer = TfidfVectorizer(lowercase=True, ngram_range=(1,2))
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)

    print("Training model...")

    model = LogisticRegression(
        class_weight='balanced',  
        max_iter=1000,            
        random_state=42
    )
    model.fit(X_train_vec, y_train)

    print("\n=== MODEL EVALUATION ===")
    y_pred = model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Accuracy: {accuracy:.2%}")

    print("\nDetailed Report:")
    print(classification_report(y_test, y_pred))

    print("\nSaving model...")
    with open("models/merchant_categorizer.pkl", 'wb') as f:
        pickle.dump(model, f)
    
    with open("models/vectorizer.pkl", 'wb') as f:
        pickle.dump(vectorizer,f)
    
    print("Model saved to models/merchant_categorizer.pkl")
    print("Vectorizer saved to models/vectorizer.pkl")

    print("\n=== SAMPLE PREDICTIONS ===")
    test_merchants = [
        "STARBUCKS STORE 22093",      
        "SHELL",                       
        "AMAZON.COM",                   
        "CHIPOTLE 2129",                
        "SPOTIFY",                      
        "WALMART STORE 01372",          
        "CIRCLE K # 20320",             
        "PUBLIX #1660",                 
        "TARGET T-1226",                
        "PROGRESSIVE *INSURANCE",
        "Cajun Seafood"      
    ]
    test_vec = vectorizer.transform(test_merchants)
    predictions = model.predict(test_vec)

    for merchant, category in zip(test_merchants, predictions):
        print(f"{merchant}-> {category}")

if __name__ == "__main__":
    import os 
    os.makedirs("models", exist_ok=True)
    train_model()