import streamlit as st
import pandas as pd
import sqlite3
import os

# Database Initialization with Auto-Fix for columns
def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    # Create the basic table
    c.execute('''CREATE TABLE IF NOT EXISTS opps 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, status TEXT, category TEXT)''')
    
    # AUTO-FIX: Check if 'description' column exists, if not, add it
    c.execute("PRAGMA table_info(opps)")
    columns = [column[1] for column in c.fetchall()]
    if 'description' not in columns:
        c.execute("ALTER TABLE opps ADD COLUMN description TEXT")
        
    conn.commit()
    conn.close()

def run_web_scraper():
    """Injects real sample data into the dashboard"""
    scraped_data = [
        {"title": "HUL LIME Season 16", "org": "Hindustan Unilever", "deadline": "2025-02-15", "link": "https://unstop.com", "cat": "Case Comp", "desc": "Premium case competition for MBA students."},
        {"title": "KPMG Strategy Consultant", "org": "KPMG India", "deadline": "2025-01-20", "link": "https://kpmg.com", "cat": "Live Project", "desc": "2-month virtual live project."},
        {"title": "Google PM Certification", "org": "Google", "deadline": "2025-12-31", "link": "https://coursera.org", "cat": "Certification", "desc": "Highly recommended for IITJ MBA product track."}
    ]
    
    conn = sqlite3.connect('opportunities.db')
    for item in scraped_data:
        # Check if exists by title to prevent duplicates
        check = pd.read_sql_query("SELECT * FROM opps WHERE title = ?", conn, params=(item['title'],))
        if check.empty:
            c = conn.cursor()
            c.execute("INSERT INTO opps (title, org, deadline, link, status, category, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (item['title'], item['org'], item['deadline'], item['link'], 'Eligible', item['cat'], item['desc']))
    conn.commit()
    conn.close()

# Run the DB fix every time app starts
init_db()

st.set_page_config(page_title="IITJ MBA Hub", layout="wide")

st.title("🎓 IIT Jodhpur MBA Opportunity Hub")

# SIDEBAR
with st.sidebar:
    st.header("Admin Tools")
    if st.button("🔍 Run Web Scraper"):
        with st.spinner("Finding opportunities..."):
            run_web_scraper()
            st.success("Database Updated!")

# TABS
tab1, tab2 = st.tabs(["✅ Eligible Opps", "❌ Not Eligible"])

def get_data():
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM opps", conn)
    conn.close()
    return df

all_data = get_data()

with tab1:
    eligible = all_data[all_data['status'] == 'Eligible']
    if not eligible.empty:
        for _, row in eligible.iterrows():
            with st.expander(f"{row['title']} - {row['org']}"):
                st.write(f"**Type:** {row['category']} | **Deadline:** {row['deadline']}")
                st.write(row['description'] if row['description'] else "No description available.")
                st.link_button("View/Apply", row['link'])
    else:
        st.info("No data yet. Click the Scraper button in the sidebar.")
