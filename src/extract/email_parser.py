import re
from datetime import datetime 
from html.parser import HTMLParser

class MLStripper(HTMLParser):
    """Strips HTML from the email body for clean parsing"""
    
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []

    def handle_data(self,d):
        self.text.append(d)
    
    def get_data(self):
        return ''.join(self.text)
    
def strip_html_tags(html):
    """Remove HTML tagas from a string"""
    s = MLStripper()
    s.feed(html)
    return s.get_data()
    
class DiscoverParser:
    """Parser for Discover card transaction emails"""

    def __init__(self):
        self.card_name = "Discover"

    def can_parse(self, email_from, email_subject):
        """Check if this email is a Discover transaction"""
        return email_from == 'Discover Card <discover@services.discover.com>' and email_subject == 'Transaction Alert'
    
    def parse(self, email_body):
        """Extract transaction data from email body"""
        
        clean_body = strip_html_tags(email_body)

        merchant_name = None 
        transaction_date = None 
        amount = None

        #Extract merchant name
        merchant_match = re.search(r'Merchant:\s*(.+)', clean_body)
        if merchant_match:
            merchant_name = merchant_match.group(1).strip()

        #Extract transaction date    
        date_match = re.search(r'Date:\s*(.+)', clean_body)
        if date_match:
            transaction_date = date_match.group(1).strip()

        #Extract amount    
        amount_match = re.search(r'\$(\d+\.\d{2})', clean_body)
        if amount_match:
            amount = float(amount_match.group(1))

        #Build the transaction dictionary with the extracted values
        transaction = {
            'card_name':self.card_name,
            'merchant_name': merchant_name,
            'transaction_date': transaction_date,
            'amount': amount,
            'raw_email_data': email_body
        }

        return transaction

class ChaseParser:
    """Parser for Chase card transaction emails"""

    def __init__(self):
        self.card_name = "Chase"

    def can_parse(self, email_from, email_subject):
        """Check if this email is a Chase transaction"""
        return email_from == 'Chase <no.reply.alerts@chase.com>' and email_subject.startswith('You made a')
    
    def parse(self, email_body):
        """Extract transaction data from email body"""
        
        clean_body = strip_html_tags(email_body)

        merchant_name = None 
        transaction_date = None 
        amount = None

        #Extract merchant name
        merchant_match = re.search(r'Merchant\s*(.+)', clean_body)
        if merchant_match:
            merchant_name = merchant_match.group(1).strip()

        #Extract transaction date    
        date_match = re.search(r'Date\s*(.+)', clean_body)
        if date_match:
            transaction_date = date_match.group(1).strip()

        #Extract amount    
        amount_match = re.search(r'\$(\d+\.\d{2})', clean_body)
        if amount_match:
            amount = float(amount_match.group(1))

        #Build the transaction dictionary with the extracted values
        transaction = {
            'card_name':self.card_name,
            'merchant_name': merchant_name,
            'transaction_date': transaction_date,
            'amount': amount,
            'raw_email_data': email_body
        }

        return transaction

class CapitalOneParser:
    """Parser for CapitalOne card transaction emails"""

    def __init__(self):
        self.card_name = "CapitalOne"

    def can_parse(self, email_from, email_subject):
        """Check if this email is a CapitalOne transaction"""
        return email_from == '"Capital One | Savor" <capitalone@notification.capitalone.com>' and email_subject == 'A new transaction was charged to your account'
    
    def parse(self, email_body):
        """Extract transaction data from email body"""
        
        clean_body = strip_html_tags(email_body)

        merchant_name = None 
        transaction_date = None 
        amount = None

        #Extract merchant name
        merchant_match = re.search(r'at (.+?), a pending', clean_body)
        if merchant_match:
            merchant_name = merchant_match.group(1).strip()

        #Extract transaction date    
        date_match = re.search(r'on (.+?), at', clean_body)
        if date_match:
            transaction_date = date_match.group(1).strip()

        #Extract amount    
        amount_match = re.search(r'amount of \$(\d+\.\d{2})', clean_body)
        if amount_match:
            amount = float(amount_match.group(1))

        #Build the transaction dictionary with the extracted values
        transaction = {
            'card_name':self.card_name,
            'merchant_name': merchant_name,
            'transaction_date': transaction_date,
            'amount': amount,
            'raw_email_data': email_body
        }

        return transaction