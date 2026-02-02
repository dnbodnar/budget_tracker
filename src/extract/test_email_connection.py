import imaplib
import os
from dotenv import load_dotenv 

# Load environment variables from .env file
load_dotenv()

#Get credentials from .env 
EMAIL = os.getenv('EMAIL_ADDRESS')
PASSWORD = os.getenv('EMAIL_PASSWORD')
IMAP_SERVER = os.getenv('IMAP_SERVER')
IMAP_PORT = int(os.getenv('IMAP_PORT'))

print(f"Attempting to connect to {IMAP_SERVER}...")
print(f"Using email: {EMAIL}")

try:
    #Connect to Gmail via IMAP
    mail = imaplib.IMAP4_SSL(IMAP_SERVER,IMAP_PORT)
    mail.login(EMAIL, PASSWORD)
    print("Successfully connected to gmail.")

    # List all mailbox folders 
    status, folders = mail.list()
    print(f"Found {len(folders)} folders in your mailbox.")

    #Select the inbox 
    mail.select('inbox')
    print("Successfully selected inbox")

    #Search for all emails in inbox
    status, messages = mail.search(None, 'ALL')
    email_ids = messages[0].split()
    print(f"Found {len(email_ids)} total emails in inbox")

    #Discconect 
    mail.logout()
    print("\n Connection test successful.")
except Exception as e:
    print(f"\n Error connecting to Gmail:")
    print(f"    {e}")

    