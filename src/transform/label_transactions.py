import json 
import os 
from pathlib import Path 

def load_unlabeled_transactions():
    """Load all transactions that haven't been labeled yet"""
    bronze_dir = Path("data/bronze")
    labeled_file = "data/labeled_transactions.json"

    labeled = {}
    if os.path.exists(labeled_file):
        with open(labeled_file, 'r') as f:
            labeled = json.load(f)
        
    unlabeled = []
    for json_file in bronze_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            transaction = json.load(f)
            merchant = transaction.get('merchant_name', '').strip()

            if merchant and merchant not in labeled:
                unlabeled.append(transaction)
    
    return unlabeled, labeled 

def label_interactive():
    """"Interactive labeling tool"""
    categories = [
        "1. Groceries", 
        "2. Dining",
        "3. Transportation",
        "4. Shopping",
        "5. Entertainment",
        "6. Bills",
        "7. Travel",
        "8. Subscriptions",
        "9. Other"
    ]

    category_map = {
        "1": "Groceries", "2": "Dining", "3": "Transportation", "4":"Shopping",
        "5":"Entertainment","6":"Bills", "7":"Travel", "8":"Subscriptions",
        "9":"Other"
    }

    unlabeled, labeled = load_unlabeled_transactions()

    print(f"\n=== MERCHANT LABELING TOOL ===")
    print(f"Unlabeled transactions: {len(unlabeled)}")
    print(f"Already labeled: {len(labeled)}")
    print(f"\nCategories:")
    for cat in categories:
        print(f" {cat}")
    print(f"\nPress 'q' to quit and save\n")

    labeled_count = 0 

    for transaction in unlabeled: 
        merchant = transaction.get('merchant_name', '').strip()
        amount = transaction.get('amount', 0)

        if not merchant: 
            continue 

        print(f"\n--- Transaction #{labeled_count + 1} ---")
        print(f"Merchant: {merchant}")
        print(f"Amount: ${amount}")

        choice = input("Category (1-9) or 'q' to quit: ").strip()

        if choice.lower() == 'q':
            break

        if choice in category_map:
            labeled[merchant] = category_map[choice]
            labeled_count += 1 
            print(f"Labeled as: {category_map[choice]}")
        else:
            print("Invalid choice, skipping...")
        
    with open("data/labeled_transactions.json", 'w') as f:
        json.dump(labeled, f, indent=2)

    print(f"\n=== LABELING COMPLETE ===")
    print(f"Total labeled: {len(labeled)}")
    print(f"Saved to: data/labeled_transactions.json")

if __name__ == "__main__":
    label_interactive()