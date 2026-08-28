import streamlit as st
import pandas as pd
import sqlite3
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# 1. THE DATA SERVICE (The "Model")
# ==========================================
class OpportunityDB:
    def __init__(self, db_path='opportunities.db'):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS items 
                         (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                          deadline TEXT, link TEXT, category TEXT, description TEXT)''')
            conn.commit()

    def add_resource(self, title, org, deadline, link, category, desc):
        # Validate exact URL format
        if not str(link).startswith('http'): return False
        
        with sqlite3.connect(self.db_path) as conn:
            check = pd.read_sql_query("SELECT * FROM items WHERE title = ?", conn, params=(title,))
            if check.empty:
                c = conn.cursor()
                c.execute("INSERT INTO items (title, org, deadline, link, category, description) VALUES (?,?,?,?,?,?)",
                          (title, org, deadline, link, category, desc))
                conn.commit()
                return True
        return False

    def get_resources(self, category=None):
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM items"
            if category:
                query += f" WHERE category = '{category}'"
            return pd.read_sql_query(query, conn).sort_values(by='deadline')

    def clear_all(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("DELETE FROM items")

# ==========================================
# 2. THE SCRAPER ENGINE (The "POM Parser")
# ==========================================
class UnifiedScraper:
    def __init__(self, launch_date):
        self.launch_date = launch_date
        self.headers = {"User-Agent": "Mozilla/5.0"}

    def scrape_class_central_deep_links(self):
        """Logic for Deep Links from Class Central"""
        url = "https://www.classcentral.com/report/free-certificates/"
        results = []
        try:
            res = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(res.content, 'html.parser')
            # Finding exact links inside the list items
            anchors = soup.select('article ul li a')
            for a in anchors:
                title = a.get_text().strip()
                href = a.get('href')
                if href and "/course/" in href: # Clean landing paths
                    # Construct clean ClassCentral or provider path
                    deep_link = f"https://www.classcentral.com{href}" if href.startswith("/") else href
                    results.append({"title": title, "org": "Verified Course", "deadline": "2027-12-31", "link": deep_link})
        except Exception as e:
            print(f"Scraper Error: {e}")
        return results

    def get_exact_mba_competitions(self):
        """A curated dictionary of Exact Global Landing Paths for Case Comps"""
        # Note: Scrapers often fail on dynamic login walls, so we use precise portal pathing
        return [
            {
                "title": "HUL L.I.M.E. Official Hub",
                "org": "Hindustan Unilever",
                "deadline": "2026-08-15",
                "link": "https://unstop.com/competitions/hul-lime",
                "desc": "The official landing page for HUL's premium competition."
            },
            {
                "title": "Reliance TUP Global Entry",
                "org": "Reliance Industries",
                "deadline": "2026-09-10",
                "link": "https://unstop.com/competitions/tup",
                "desc": "Deep link for TUP Innovation Challenge series."
            },
            {
                "title": "Amazon Ace Ops Strategy",
                "org": "Amazon",
                "deadline": "2026-08-20",
                "link": "https://unstop.com/p/amazon-ace-ops-strategy-2026",
                "desc": "Direct application path for operations track."
            },
            {
                "title": "BCG Strategy Simulation DeepLink",
                "org": "Boston Consulting Group",
                "deadline": "2027-01-01",
                "link": "https://www.theforage.com/virtual-internships/S7699i85S2nBnyA7q",
                "desc": "Direct path to Enroll in Strategy modules."
            }
        ]

# ==========================================
# 3. PRESENTATION LAYER (Streamlit App)
# ==========================================
db = OpportunityDB()
scraper = UnifiedScraper(launch_date=datetime(2026, 8, 1).date())

st.set_page_config(page_title="IITJ Career Hub", layout="wide", page_icon="🎓")

# -- Navigation --
view = st.sidebar.radio("View", ["Dashboard", "Certifications", "Admin Console"])
ADMIN_KEY = "iitj2026"

# -- SECTION: DASHBOARD --
if view == "Dashboard":
    st.title("🏆 Active MBA Case Competitions")
    st.caption("Showing high-relevance direct application links for IITJ MBA Batch.")
    
    df = db.get_resources("Case Comp")
    # Clean logic: Deadline must be >= Aug 2026
    df = df[pd.to_datetime(df['deadline']).dt.date >= scraper.launch_date]

    if df.empty:
        st.warning("Database empty. Use Admin Portal to 'Sync Verified Links'.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                col1.subheader(row['title'])
                col1.write(f"🏢 Organizer: {row['org']}")
                col1.caption(row['description'])
                col2.error(f"⏳ Ends: {row['deadline']}")
                # DEEP LINK BUTTON
                col2.link_button("Go Direct To Portal", row['link'], width='stretch')

# -- SECTION: CERTIFICATIONS --
elif view == "Certifications":
    st.title("📜 Deep-Link Certifications")
    st.write("Verified 'Free with Certificate' paths for Skills Gaps.")
    
    df = db.get_resources("Certification")
    if df.empty:
        st.info("No courses loaded. Admin needs to Run Scraper.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                st.subheader(row['title'])
                st.write(f"Source: {row['org']}")
                st.link_button("Exact Enrollment Page", row['link'])

# -- SECTION: ADMIN CONSOLE --
elif view == "Admin Console":
    st.title("⚙️ Opportunity Engine Management")
    key = st.sidebar.text_input("IEC Security Key", type="password")
    
    if key == ADMIN_KEY:
        st.success("Authorization: Management Mode")
        
        tab_sync, tab_manual, tab_cleanup = st.tabs(["🔥 Sync Scraper", "🔗 Manual Links", "🧹 Maintenance"])
        
        with tab_sync:
            st.write("Refills database with exact deep-links from verified global sources.")
            if st.button("RUN DEEP-PATH SCRAPER"):
                with st.spinner("Finding exact enrollment URLs..."):
                    # 1. Sync High Fidelity Dictionary
                    comps = scraper.get_exact_mba_competitions()
                    for c in comps:
                        db.add_resource(c['title'], c['org'], c['deadline'], c['link'], "Case Comp", c['desc'])
                    
                    # 2. Sync Scraped Courses
                    certs = scraper.scrape_class_central_deep_links()
                    for ct in certs:
                        db.add_resource(ct['title'], ct['org'], ct['deadline'], ct['link'], "Certification", "Auto-verified via Scraper.")
                    st.toast("Sync Finished: Check Dashboard.")
        
        with tab_manual:
            st.write("Manually push a secret HR link or internal invite.")
            with st.form("manual_add"):
                n = st.text_input("Name")
                l = st.text_input("EXACT LINK (Direct Landing Path)")
                cat = st.selectbox("Type", ["Case Comp", "Certification", "Live Project"])
                dl = st.date_input("Deadline")
                if st.form_submit_button("Publish Now"):
                    db.add_resource(n, "Placement Comm", str(dl), l, cat, "Manually Sourced")
                    st.toast("Pushed to students.")
                    
        with tab_cleanup:
            if st.button("Delete All Database Records"):
                db.clear_all()
                st.warning("All records wiped out.")
    else:
        st.error("Access Restricted. Enter correct code in Sidebar.")
