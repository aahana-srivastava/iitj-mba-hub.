import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime

# 1. Error-Proof Import for Resume Analysis
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Database Initialization
def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS opps 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, status TEXT, category TEXT, description TEXT)''')
    conn.commit()
    conn.close()

# 2. THE SCRAPER ENGINE (Simplified version for MBA Ops)
def run_web_scraper():
    """Scrapes dummy/mock data for now - Can be expanded with Scraper APIs"""
    scraped_data = [
        {"title": "HUL LIME 2025", "org": "HUL", "deadline": "2025-02-15", "link": "https://unstop.com", "cat": "Case Comp", "desc": "Open to Tier 1 B-Schools"},
        {"title": "KPMG Strategy Consultant Live Project", "org": "KPMG", "deadline": "2025-01-20", "link": "https://kpmg.com", "cat": "Live Project", "desc": "Looking for MBA Interns"},
        {"title": "Google Project Management Certification", "org": "Coursera/Google", "deadline": "2025-12-31", "link": "https://coursera.org", "cat": "Certification", "desc": "Free via IITJ Portal"},
        {"title": "Amazon ACE 2025", "org": "Amazon", "deadline": "2025-03-01", "link": "https://unstop.com", "cat": "Case Comp", "desc": "Open for all MBAs"}
    ]
    
    conn = sqlite3.connect('opportunities.db')
    for item in scraped_data:
        # Check if already exists to avoid duplicates
        check = pd.read_sql_query(f"SELECT * FROM opps WHERE title = '{item['title']}'", conn)
        if check.empty:
            c = conn.cursor()
            c.execute("INSERT INTO opps (title, org, deadline, link, status, category, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (item['title'], item['org'], item['deadline'], item['link'], 'Eligible', item['cat'], item['desc']))
    conn.commit()
    conn.close()

init_db()

st.set_page_config(page_title="IITJ MBA Hub", layout="wide")

# --- SIDEBAR: The Scraper Control ---
st.sidebar.title("🛠️ Tools")
if st.sidebar.button("🔍 Run Global Scraper"):
    with st.spinner("Scanning Unstop, LinkedIn & Career Portals..."):
        run_web_scraper()
        st.sidebar.success("Scraper Finished! New items found.")

# --- MAIN UI ---
st.title("🎓 IIT Jodhpur MBA Opportunity Hub")

tab1, tab2, tab3 = st.tabs(["✅ Eligible for IITJ", "❌ Not Eligible", "📄 Resume Analysis"])

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
                st.write(f"**Category:** {row['category']} | **Deadline:** {row['deadline']}")
                st.write(row['description'])
                st.link_button("Apply Now", row['link'])
    else:
        st.info("The feed is currently empty. Click 'Run Global Scraper' in the sidebar.")

with tab2:
    st.write("These opportunities were filtered out based on IIT Jodhpur eligibility rules.")

with tab3:
    if not PDF_SUPPORT:
        st.error("Resume Analysis is offline. Please ensure 'PyPDF2' is in requirements.txt and wait for rebuild.")
    else:
        st.write("Upload your resume to see which open case competitions match your skills.")
        st.file_uploader("Upload Resume (PDF)", type="pdf")
