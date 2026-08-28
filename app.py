import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime

# --- SAFE IMPORT ---
try:
    from bs4 import BeautifulSoup
    BS_READY = True
except ImportError:
    BS_READY = False

# --- CONFIG ---
LAUNCH_DATE = datetime(2026, 8, 1).date()
ADMIN_KEY = "iitj2026"

def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resources 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, type TEXT, description TEXT)''')
    conn.commit()
    conn.close()

# --- THE "BROAD SEARCH" SCRAPER ENGINE ---
def run_universal_broad_scraper():
    """
    Simulates a multi-source broad scan targeting:
    - Mainstream B-School Challenges
    - Niche Corporate Hackathons
    - Management Fellowships
    - Global Virtual Internships (Forage Style)
    """
    # This data represents items scraped from aggregators like Unstop, LinkedIn, and IIM Portal Newsletters
    broad_data = [
        # --- Corporate Hackathons & Fellowships ---
        {"title": "Accenture Strategy Innovation Challenge", "org": "Accenture", "deadline": "2026-09-20", "link": "https://unstop.com", "type": "Hackathon", "desc": "Managerial hackathon for tech-strategy enthusiasts."},
        {"title": "Legrand Empowerment Fellowship", "org": "Legrand India", "deadline": "2026-08-30", "link": "https://legrand.co.in", "type": "Fellowship", "desc": "Project-based fellowship for social-impact MBA students."},
        {"title": "Schneider Electric Go Green 2026", "org": "Schneider Electric", "deadline": "2026-11-15", "link": "https://gogreen.se.com", "type": "Sustainability Challenge", "desc": "Sustainability innovation for PG students."},
        
        # --- Niche Virtual Experiences (Resumé Fillers) ---
        {"title": "J.P. Morgan Investment Banking Program", "org": "J.P. Morgan", "deadline": "2027-12-31", "link": "https://theforage.com", "type": "Live Project", "desc": "Simulated analysis project. Great for Finance profiles."},
        {"title": "KPMG Strategy Consultant Module", "org": "KPMG Global", "deadline": "2027-01-01", "link": "https://theforage.com", "type": "Live Project", "desc": "Experience a market-entry project from the BCG/KPMG desk."},
        {"title": "Data Visualization Professional Simulation", "org": "Standard Chartered", "deadline": "2026-10-30", "link": "https://forage.com", "type": "Live Project", "desc": "Hands-on data analytics for decision making."},
        
        # --- Future Case Competitions (Broad Scale) ---
        {"title": "HUL LIME 18", "org": "Unstop / HUL", "deadline": "2026-08-15", "link": "https://unstop.com", "type": "Case Comp", "desc": "Tier 1 B-School National Comp."},
        {"title": "L'Oréal Brandstorm 2027", "org": "L'Oréal", "deadline": "2027-02-15", "link": "https://brandstorm.loreal.com", "type": "Case Comp", "desc": "Global innovation challenge."},
        {"title": "P&G CEO Challenge 2027", "org": "P&G India", "deadline": "2027-01-20", "link": "https://unstop.com", "type": "Case Comp", "desc": "Operations/Marketing cross-functional case."},
        
        # --- Regional MBA Festivals (Mock Data based on Historical Patterns) ---
        {"title": "IIM Ahmedabad - Confluence '26", "org": "IIMA", "deadline": "2026-12-05", "link": "https://iima-confluence.com", "type": "Niche Comp", "desc": "Diverse managerial games and strategy events."},
        {"title": "IIT Jodhpur - Ignite Case Master", "org": "SME IIT Jodhpur", "deadline": "2026-09-30", "link": "https://sme.iitj.ac.in", "type": "Regional Comp", "desc": "In-house MBA festival case studies."}
    ]

    conn = sqlite3.connect('opportunities.db')
    added_count = 0
    for item in broad_data:
        deadline_date = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
        if deadline_date >= LAUNCH_DATE:
            check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(item['title'],))
            if check.empty:
                c = conn.cursor()
                c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                          (item['title'], item['org'], item['deadline'], item['link'], item['type'], item['desc']))
                added_count += 1
    conn.commit()
    conn.close()
    return added_count

# --- LOAD BEYOND BIG-NAME MASTER LIST ---
def load_all_categories_master():
    master_data = [
        # Niche Fellowships
        ("IDFC First Bank Fellowship", "IDFC First", "2026-12-31", "https://idfcfirstbank.com", "Fellowship", "Social entrepreneurship track."),
        ("Teach For India MBA Leadership", "TFI", "2026-09-01", "https://teachforindia.org", "Fellowship", "Management residency project."),
        # Open Courses with Certificate
        ("SQL for Management (Zero-Cost)", "Stanford Online", "2027-12-31", "https://edx.org", "Certification", "Certificate for MBA database tracking."),
        ("Google Product Strategy", "Google Careers", "2027-12-31", "https://google.com", "Certification", "Strategic thinking professional cert."),
        # Strategy Competitions
        ("Mckinsey Problem Solving Prep", "McKinsey & Co", "2027-11-01", "https://mckinsey.com", "Skill Resource", "Virtual business simulation game."),
    ]
    conn = sqlite3.connect('opportunities.db')
    for t, o, d, l, typ, desc in master_data:
        check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(t,))
        if check.empty:
            c = conn.cursor()
            c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                      (t, o, d, l, typ, desc))
    conn.commit()
    conn.close()

# --- APP NAVIGATION ---
init_db()
st.set_page_config(page_title="IITJ MBA Hub (Universal Search)", layout="wide")

st.sidebar.title("📌 Hub Selector")
view = st.sidebar.radio("Pages", ["🎯 All Case Comps & Hackathons", "🌱 Beyond Comps (Fellowships & VEPs)", "📜 Free Certification Hub", "⚙️ Admin & Link Importer"])

# PAGE 1: CASE COMPS & HACKATHONS
if view == "🎯 All Case Comps & Hackathons":
    st.title("🏆 Mainstream & Niche Competitions")
    st.caption(f"Filters active from Launch: {LAUNCH_DATE}")
    
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type IN ('Case Comp', 'Hackathon', 'Niche Comp', 'Regional Comp') ORDER BY deadline ASC", conn)
    conn.close()
    
    if df.empty:
        st.info("No active comps found. Please Sync in Admin.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.subheader(row['title'])
                col1.write(f"🏢 Organizer: {row['org']} | Category: {row['type']}")
                col2.error(f"Deadline: {row['deadline']}")
                col2.link_button("Apply / Source", row['link'])

# PAGE 2: FELLOWSHIPS & PROJECTS (VIRTUAL)
elif view == "🌱 Beyond Comps (Fellowships & VEPs)":
    st.title("💼 Experience Beyond Case Studies")
    st.markdown("Includes corporate fellowships and Virtual Experience Programs (VEPs).")
    
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type IN ('Fellowship', 'Live Project') ORDER BY deadline ASC", conn)
    conn.close()
    
    if df.empty:
        st.warning("Go to Admin -> Scrape to load Fellowships.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"💼 {row['title']}")
                st.write(f"Company: {row['org']}")
                st.write(row['description'])
                st.link_button("Claim Opportunity", row['link'])

# PAGE 3: CERTIFICATES
elif view == "📜 Free Certification Hub":
    st.title("📜 Free Certificates (Non-Audit)")
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type = 'Certification' ORDER BY title ASC", conn)
    conn.close()
    
    if df.empty:
        if st.button("Initial Load of Verified Certificates"):
            load_all_categories_master()
            st.rerun()
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"🎖️ {row['title']}")
                st.write(f"Provider: {row['org']}")
                st.link_button("Get Cert", row['link'])

# PAGE 4: ADMIN MANAGER
elif view == "⚙️ Admin & Link Importer":
    st.title("⚙️ Opportunity Aggregator Console")
    code = st.sidebar.text_input("Enter Admin Key", type="password")
    
    if code == ADMIN_KEY:
        st.subheader("Broad Scraping Engines")
        c1, c2 = st.columns(2)
        if c1.button("🔥 Scrape ALL Global Sources"):
            added = run_universal_broad_scraper()
            st.success(f"Added {added} items across all categories.")
            
        if c2.button("💾 Force Baseline Inventory Sync"):
            load_all_categories_master()
            st.info("Loaded master fellowship and cert lists.")
            
        st.divider()
        st.subheader("Add Targeted Link (Manually)")
        with st.form("admin_manual"):
            n = st.text_input("Title")
            o = st.text_input("Org")
            l = st.text_input("URL")
            t = st.selectbox("Type", ["Case Comp", "Hackathon", "Fellowship", "Live Project", "Certification"])
            d = st.date_input("Deadline")
            ds = st.text_area("One line on Why apply?")
            if st.form_submit_button("Post Live"):
                conn = sqlite3.connect('opportunities.db')
                c = conn.cursor()
                c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                          (n, o, str(d), l, t, ds))
                conn.commit()
                st.toast("Posted!")
    else:
        st.error("Admin Authentication Needed.")
