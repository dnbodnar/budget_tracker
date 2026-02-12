from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, trim, lower 
from pyspark.sql.types import StringType, DateType
from datetime import datetime 
import os 

spark = SparkSession.builder \
    .appName("Budget Tracker - Transform") \
    .master("local[*]") \
    .getOrCreate()

def parse_date(date_str):
    """Parse various date formats into YYYY-MM-DD"""
    if not date_str:
        return None 
    
    date_str = date_str.strip()

    # List the different transaction date formats 
    formats = [
        "%B %d, %Y", #Discover / CapitalOne
        "%b %d, %Y at %I:%M %p ET", #Chase
    ]

    for fmt in formats: 
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    return None

print(parse_date("February 4, 2026"))          # Should print: 2026-02-04
print(parse_date("Aug 9, 2025 at 5:49 PM ET")) # Should print: 2025-08-09
print(parse_date("January 07, 2026"))          # Should print: 2026-01-07