import os 

class EmailTracker:
    """Tracks which emails have been processed to avoid duplicates"""
    
    def __init__(self, tracker_file='data/processed_emails.txt'):
       self.tracker_file = tracker_file
       self.processed_ids = self._load_processed_ids()

    def _load_processed_ids(self):
        """Load previously processed email IDs from file"""
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, 'r') as f:
                return set(line.strip() for line in f)
        return set() 
    
    def is_processed(self, email_id):
        """Check if an email has already been processed"""
        return email_id in self.processed_ids
    
    def mark_processed(self, email_id):
        """Mark an email as processed"""
        if email_id not in self.processed_ids:
            self.processed_ids.add(email_id)
            with open(self.tracker_file, 'a') as f:
                f.write(f"{email_id}\n")