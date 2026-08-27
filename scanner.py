import sqlite3
import pandas as pd
from datetime import datetime

def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS opps 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, status TEXT, category TEXT)''')
    conn.commit()
    conn.close()

def classify_opportunity(title, description):
    # Rule-based logic for IIT Jodhpur MBA
    text = (title + " " + description).lower()
    
    # Exclusion rules
    if "undergraduate" in text or "b.tech only" in text:
        return "Not Eligible"
    
    # Inclusion rules
    eligible_keywords = ["mba", "postgraduate", "all b-schools", "iit jodhpur", "management"]
    if any(word in text for word in eligible_keywords):
        return "Eligible"
    
    return "Unclear"

def add_opportunity(title, org, deadline, link, description, category):
    status = classify_opportunity(title, description)
    conn = sqlite3.connect('opportunities.db')
    df = pd.DataFrame([[title, org, deadline, link, status, category]], 
                      columns=['title', 'org', 'deadline', 'link', 'status', 'category'])
    df.to_sql('opps', conn, if_exists='append', index=False)
    conn.close()