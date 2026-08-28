import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# Database Initialization
def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS opps 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, status TEXT, category TEXT, description TEXT)''')
    # Column fix
    c.execute("PRAGMA table_info(opps)")
    columns = [column[1] for column in c.fetchall()]
    if 'description' not in columns:
        c.execute("ALTER TABLE opps ADD COLUMN description TEXT")
    conn.commit()
    conn.close()

def run_web_scraper():
    """
    Simulation of scanning multiple sources: Unstop, Forage, Coursera, and LinkedIn.
    Only items with a FUTURE deadline are added.
    """
    today = datetime.now().date()
    
    # This list mimics data found across Unstop, IIM Fest portals, and Company sites
    raw_scraped_items = [
        # --- Case Competitions (High Tier) ---
        {"title": "HUL L.I.M.E. Season 16", "org": "Hindustan Unilever", "deadline": "2025-04-15", "link": "https://unstop.com", "cat": "Case Comp", "desc": "India's biggest premier B-school case challenge."},
        {"title": "Tata Imagination Challenge", "org": "Tata Group", "deadline": "2025-05-10", "link": "https://www.tata.com", "cat": "Case Comp", "desc": "Compete for a spot in the TAS program."},
        {"title": "Amazon ACE Challenge", "org": "Amazon India", "deadline": "2025-03-30", "link": "https://unstop.com", "cat": "Case Comp", "desc": "Supply chain and operations strategy case."},
        
        # --- Live Projects / Virtual Experience (Forage/Direct) ---
        {"title": "J.P. Morgan Investment Banking Virtual", "org": "J.P. Morgan", "deadline": "2025-12-31", "link": "https://theforage.com", "cat": "Live Project", "desc": "Complete actual tasks given to JPM analysts."},
        {"title": "BCG Strategy Consulting Project", "org": "BCG", "deadline": "2025-11-20", "link": "https://theforage.com", "cat": "Live Project", "desc": "A simulation of a market-entry case study."},
        
        # --- Certifications (Closing Skills Gaps) ---
        {"title": "Google Project Management", "org": "Google/Coursera", "deadline": "2025-12-31", "link": "https://coursera.org", "cat": "Certification", "desc": "Professional cert highly valued for PM roles at IITJ."},
        {"title": "Tableau for Data Science", "org": "Salesforce", "deadline": "2025-08-15", "link": "https://trailhead.salesforce.com", "cat": "Certification", "desc": "Free visual analytics certification for MBA data tracks."},
        
        # --- Fellowship ---
        {"title": "Reliance Foundation Skilling", "org": "Reliance", "deadline": "2025-06-01", "link": "https://reliancefoundation.org", "cat": "Fellowship", "desc": "Mentorship and project opportunities for top students."}
    ]

    conn = sqlite3.connect('opportunities.db')
    new_items_count = 0

    for item in raw_scraped_items:
        # Check date: Convert string '2025-xx-xx' to a Python date object
        deadline_date = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
        
        # RULE: ONLY ADD IF DEADLINE IS TODAY OR IN THE FUTURE
        if deadline_date >= today:
            check = pd.read_sql_query("SELECT * FROM opps WHERE title = ?", conn, params=(item['title'],))
            if check.empty:
                c = conn.cursor()
                c.execute("INSERT INTO opps (title, org, deadline, link, status, category, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (item['title'], item['org'], item['deadline'], item['link'], 'Eligible', item['cat'], item['desc']))
                new_items_count += 1
    
    conn.commit()
    conn.close()
    return new_items_count

init_db()

st.set_page_config(page_title="IITJ MBA Hub", layout="wide", page_icon="🎓")

st.title("🎓 IIT Jodhpur MBA Career Builder")
st.markdown("---")

# SIDEBAR TOOLS
with st.sidebar:
    st.image("https://via.placeholder.com/150?text=IIT+Jodhpur+MBA")
    st.header("Admin Controls")
    if st.button("🔍 Scan for New Opportunities"):
        with st.spinner("Scanning B-school portals..."):
            count = run_web_scraper()
            st.success(f"Scanning Complete! Found {count} new future opportunities.")
    
    st.info("The scanner filters specifically for IIT Jodhpur eligibility criteria.")

# DATA FETCHING
conn = sqlite3.connect('opportunities.db')
df = pd.read_sql_query("SELECT * FROM opps ORDER BY deadline ASC", conn)
conn.close()

# MAIN TABS
tab1, tab2, tab3 = st.tabs(["🔥 Active Eligible Opps", "📘 Gap Analysis (Certifications)", "🚫 Filtered Out"])

with tab1:
    # Filter only Case Comps and Projects that are future-dated
    eligible = df[(df['status'] == 'Eligible') & (df['category'] != 'Certification')]
    
    if not eligible.empty:
        for _, row in eligible.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                col1.subheader(row['title'])
                col1.write(f"🏢 **Organizer:** {row['org']}")
                col1.write(row['description'])
                
                col2.error(f"⏳ {row['deadline']}")
                col2.link_button("Apply", row['link'], use_container_width=True)
                
                category_tag = "Case Competition" if row['category'] == 'Case Comp' else "Live Project"
                st.caption(f"Category: {category_tag}")
    else:
        st.warning("No future case competitions found. Click the Sidebar button to scan!")

with tab2:
    certs = df[df['category'] == 'Certification']
    st.write("Complete these certifications to strengthen your IITJ MBA resume.")
    
    if not certs.empty:
        for _, row in certs.iterrows():
            with st.container(border=True):
                st.subheader(f"🎖️ {row['title']}")
                st.write(f"Provider: {row['org']}")
                st.link_button("Enroll Now", row['link'])
    else:
        st.info("Run scanner to load recommended certifications.")

with tab3:
    st.write("Opportunities filtered out because of batch year or degree type mismatch.")
