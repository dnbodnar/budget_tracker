import imaplib
import email 
import os
from dotenv import load_dotenv 
from email_parser import ChaseParser

load_dotenv()

EMAIL = os.getenv('EMAIL_ADDRESS')
PASSWORD = os.getenv('EMAIL_PASSWORD')
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_PORT = int(os.getenv('IMAP_PORT'))

print("Connecting to Gmail....")
mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
mail.login(EMAIL, PASSWORD)
mail.select('inbox')

print("Searching for Chase Email Transactions....")
status, messages = mail.search(None, 'FROM "no.reply.alerts@chase.com"')
email_ids = messages[0].split()

print(f"Found {len(email_ids)} Chase emails")

if len(email_ids) > 0:
    #Fetch the most recent email only 
    latest_email_id = email_ids[-1]
    status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
    raw_email = msg_data[0][1]

    msg = email.message_from_bytes(raw_email)

    email_from = msg['From']
    email_subject = msg['Subject']

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
    
    print(f"\n -- EMAIL INFO ---")
    print(f"From: {email_from}")
    print(f"Subject: {email_subject}")
    print(f"\n --- Email Body (PLAIN TEXT) ---")
    print(email_body_text if email_body_text else "No plain text version")
    print(f"\n --- Email Body (HTML) ---")
    print(email_body_html if email_body_html else "No HTML version")

    email_body = email_body_html if email_body_html else email_body_text

    parser = ChaseParser()

    if parser.can_parse(email_from, email_subject):
        print("\n Parser can handle this email")
        transaction = parser.parse(email_body)

        print("\n--- PARSED TRANSACTION ---")
        print(f"Card: {transaction['card_name']}")
        print(f"Merchant: {transaction['merchant_name']}")
        print(f"Date: {transaction['transaction_date']}")
        print(f"Amount: {transaction['amount']}")
    else: 
        print("\n Parser cannot handle this email")
else:
    print("No chase emails found. Check mailbox again.")

mail.logout()