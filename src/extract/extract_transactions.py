import imaplib
import email
import os 
import json 
from datetime import datetime 
from dotenv import load_dotenv
from email_parser import DiscoverParser, ChaseParser, CapitalOneParser
from email_tracker import EmailTracker

load_dotenv()

EMAIL = os.getenv('EMAIL_ADDRESS')
PASSWORD = os.getenv('EMAIL_PASSWORD')
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_PORT = int(os.getenv('IMAP_PORT'))

parsers = [
    DiscoverParser(),
    ChaseParser(),
    CapitalOneParser()
]

tracker = EmailTracker()

def get_email_body(msg):
    """Extract email body from message (handles multipart)"""
    email_body_text = None 
    email_body_html = None 

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                email_body_text = part.get_payload(decode=True).decode()
            elif content_type == "text/html":
                email_body_html = part.get_payload(decode=True).decode()
    else: 
        email_body = msg.get_payload(decode=True).decode()
        if msg.get_content_type() == "text/plain":
            email_body_text = email_body 
        else: 
            email_body_html = email_body
    
    return email_body_html if email_body_html else email_body_text

def save_transaction(transaction, email_id):
    """Save transaction to JSON file in data/bronze/"""
    os.makedirs('data/bronze', exist_ok=True)

    card_name = transaction['card_name'].lower().replace(' ', '_')
    date_str = datetime.now().strftime('%Y%m%d')

    filename = f"transaction_{date_str}_{card_name}_{email_id}.json"
    filepath = os.path.join('data','bronze', filename)

    with open(filepath, 'w') as f:
        json.dump(transaction, f, indent=2)
    
    print(f"Saved: {filename}")

def extract_all_transactions(): 
    """Main extraction function"""
    print("Connecting to Gmail...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(EMAIL,PASSWORD)
    mail.select('inbox')
    
    search_queries = [
        'FROM "discover@services.discover.com"',
        'FROM "no.reply.alerts@chase.com"',
        'FROM "capitalone@notification.capitalone.com"'
    ]

    total_processed = 0
    total_skipped = 0

    for query in search_queries:
        print(f"\nSearching: {query}")
        status, messages = mail.search(None, query)
        email_ids = messages[0].split()

        print(f"Found {len(email_ids)} emails")

        for email_id in email_ids:
            email_id_str = email_id.decode()

            #Skip if already processed 
            if tracker.is_processed(email_id_str):
                total_skipped += 1
                continue

            try:
                status, msg_data = mail.fetch(email_id, '(RFC822)')
                raw_email = msg_data[0][1]

                msg = email.message_from_bytes(raw_email)

                email_from = msg['From']
                email_subject = msg['Subject']
                email_body = get_email_body(msg)

                # Find the correct parser
                matched_parser = None 
                for parser in parsers:
                    if parser.can_parse(email_from, email_subject):
                        matched_parser = parser 
                        break
                
                if matched_parser:
                    transaction = matched_parser.parse(email_body)
                    save_transaction(transaction, email_id_str)
                else: 
                    print(f"No parser matched for email {email_id_str}")
            except Exception as e: 
                print(f"Error processing email {email_id_str}: {e}")
                continue
            
            tracker.mark_processed(email_id_str)
            total_processed +=1 
    
    mail.logout()

    print(f"\n=== EXTRACTION COMPLETE ===")
    print(f"Processed: {total_processed} new transactions")
    print(f"Skipped: {total_skipped} already processed")

if __name__ == "__main__":
    extract_all_transactions()
