import streamlit as st
import pandas as pd
import sqlite3
import requests
import time
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# 1. MODEL: THE DATA MANAGER (POM Architecture)
# ==========================================
class OpportunityVault:
    def __init__(self):
        self.conn_str = 'iitj_mba_opportunities.db'
        self._setup()

    def _setup(self):
        with sqlite3.connect(self.conn_str) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS data_bank 
                         (id INTEGER PRIMARY KEY, title TEXT, org TEXT, deadline TEXT, 
                          link TEXT, category TEXT, platform TEXT, description TEXT)''')

    def save_opportunities(self, items):
        added = 0
        with sqlite3.connect(self.conn_str) as conn:
            for item in items:
                # Check for duplicates by exact link
                exists = pd.read_sql_query("SELECT id FROM data_bank WHERE link = ?", conn, params=(item['link'],))
                if exists.empty:
                    conn.execute("""INSERT INTO data_bank (title, org, deadline, link, category, platform, description) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                                 (item['title'], item['org'], item['deadline'], item['link'], item['category'], item['platform'], item['description']))
                    added += 1
            conn.commit()
        return added

    def load_data(self, category):
        with sqlite3.connect(self.conn_str) as conn:
            return pd.read_sql_query(f"SELECT * FROM data_bank WHERE category = '{category}'", conn)

    def purge(self):
        with sqlite3.connect(self.conn_str) as conn:
            conn.execute("DELETE FROM data_bank")

# ==========================================
# 2. LOGIC: THE DEEP-SCAN SCRAPER
# ==========================================
class DeepScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0"}
        self.cutoff_date = datetime(2026, 8, 1).date()
        self.keywords = ["Management", "Analytics", "Project", "Strategy", "Supply Chain", "Finance", "Business", "Leadership", "Marketing", "HR", "Consulting", "Operations"]

    def scrape_swayam_broad(self):
        """Scans multiple categories on Swayam to maximize results"""
        results = []
        base_url = "https://swayam.gov.in/explorer?category="
        categories = ["Management", "Humanities", "Computer", "Engineering"] # Cross-search for Analytics/HR
        
        for cat in categories:
            try:
                time.sleep(1.5) # 'Slow down' to behave like a human
                r = requests.get(base_url + cat, headers=self.headers, timeout=10)
                soup = BeautifulSoup(r.content, 'html.parser')
                
                # Broad link matching for NPTEL/Swayam courses
                for a in soup.find_all('a', href=True):
                    t = a.get_text().strip()
                    h = a['href']
                    if any(kw.lower() in t.lower() for kw in self.keywords):
                        if "/course/" in h or "/nc_details/" in h:
                            results.append({
                                "title": t, "org": "Swayam / NPTEL", "deadline": "2027-12-31",
                                "link": f"https://swayam.gov.in{h}" if h.startswith("/") else h,
                                "category": "Certification", "platform": "Swayam", "description": "National level verified course."
                            })
            except: continue
        return results

    def scrape_class_central_deep(self):
        """Deep scan through multiple Subject pages on Class Central"""
        results = []
        subject_urls = [
            "https://www.classcentral.com/report/free-certificates/",
            "https://www.classcentral.com/subject/business",
            "https://www.classcentral.com/subject/management-and-leadership",
            "https://www.classcentral.com/subject/data-science",
            "https://www.classcentral.com/subject/marketing"
        ]
        
        for url in subject_urls:
            try:
                time.sleep(2) # Systematic slow down
                r = requests.get(url, headers=self.headers, timeout=10)
                soup = BeautifulSoup(r.content, 'html.parser')
                # Find direct links with the course paths
                for a in soup.find_all('a', href=True, class_=True):
                    t = a.get_text().strip()
                    h = a['href']
                    if len(t) > 10 and ("/course/" in h or "/report/" in h):
                        full_h = f"https://www.classcentral.com{h}" if h.startswith("/") else h
                        results.append({
                            "title": t, "org": "Global Institute", "deadline": "2027-12-31",
                            "link": full_h, "category": "Certification", "platform": "Class Central",
                            "description": "Scraped verified certification pathway."
                        })
            except: continue
        return results

    def get_seed_links(self):
        """Precise application paths for major MBA case competitions 2026+"""
        return [
            {"title": "HUL LIME 18 Portal", "org": "Unstop / HUL", "deadline": "2026-08-15", "link": "https://unstop.com/competitions/hul-lime", "category": "Case Comp", "platform": "Unstop", "description": "Direct Case Study Registration."},
            {"title": "Reliance TUP 7.0 Challenge", "org": "Reliance Industries", "deadline": "2026-09-01", "link": "https://unstop.com/competitions/tup", "category": "Case Comp", "platform": "Unstop", "description": "National Innovation Portal Link."},
            {"title": "Amazon Operations ACE Hub", "org": "Amazon", "deadline": "2026-08-25", "link": "https://unstop.com/p/amazon-ace-2026", "category": "Case Comp", "platform": "Direct", "description": "Exact link for Operations Management."},
            {"title": "BCG Virtual Strategy Experience", "org": "BCG / Forage", "deadline": "2027-12-31", "link": "https://www.theforage.com/virtual-internships/S7699i85S2nBnyA7q", "category": "Live Project", "platform": "Forage", "description": "Strategic case modules from BCG mentors."}
        ]

# ==========================================
# 3. PRESENTATION: STREAMLIT APP UI
# ==========================================
vault = OpportunityVault()
scraper = DeepScraper()

st.set_page_config(page_title="IITJ MBA Hub", layout="wide", page_icon="🎓")

page = st.sidebar.radio("Navigate Hub", ["📈 Active Dashboard", "🛠️ IEC Admin Portal"])

if page == "📈 Active Dashboard":
    st.title("🎓 Career Readiness Portal - IIT Jodhpur")
    t1, t2, t3 = st.tabs(["🏆 Case Competitions", "💼 Live Projects (Virtual)", "📜 Free Certificates (Swayam+)"])

    def display_results(category, enforce_date=False):
        df = vault.load_data(category)
        if df.empty:
            st.info(f"The list for {category} is currently empty. Run a Sync from Admin.")
            return

        if enforce_date:
            df['dt_obj'] = pd.to_datetime(df['deadline']).dt.date
            df = df[df['dt_obj'] >= scraper.cutoff_date]

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.subheader(row['title'])
                c1.write(f"🏢 Platform: {row['platform']} | Organizer: {row['org']}")
                c1.caption(row['description'])
                c2.error(f"⏳ {row['deadline']}")
                c2.link_button("Go To Path →", row['link'], width='stretch')

    with t1: display_results("Case Comp", enforce_date=True)
    with t2: display_results("Live Project", enforce_date=True)
    with t3: 
        st.caption("Certs are year-round - No August 2026 date restriction applied.")
        display_results("Certification", enforce_date=False)

elif page == "🛠️ IEC Admin Portal":
    st.title("⚙️ Opportunity Aggregation Console")
    pw = st.sidebar.text_input("Enter Admin Key", type="password")
    
    if pw == "iitj2026":
        st.success("Authorization: Placement Committee Access")
        
        st.subheader("Deep Scan Trigger")
        st.write("This process will search through 10+ category pages across the web.")
        
        if st.button("🔥 RUN DEEP-SYNC (SLOW/STAY CALM)"):
            progress = st.progress(0)
            status = st.empty()
            
            # Step 1: Seeds
            status.text("Step 1/3: Loading Industry Verified Seed Paths...")
            added_s = vault.save_opportunities(scraper.get_seed_links())
            progress.progress(30)
            
            # Step 2: Swayam
            status.text("Step 2/3: Searching Swayam Multi-Subject Hubs (Be Patient)...")
            swayam_results = scraper.scrape_swayam_broad()
            added_sw = vault.save_opportunities(swayam_results)
            progress.progress(60)
            
            # Step 3: Class Central
            status.text("Step 3/3: Parsing Class Central Subject Portals (Finalizing)...")
            cc_results = scraper.scrape_class_central_deep()
            added_cc = vault.save_opportunities(cc_results)
            
            progress.progress(100)
            status.success(f"Scanning Finished! Total new opportunities found: {added_s + added_sw + added_cc}")
            st.write(f"Detailed Discovery: Seeds: {added_s}, Swayam: {added_sw}, Class Central: {added_cc}")

        if st.sidebar.button("🧹 PURGE LOCAL DATABASE"):
            vault.purge()
            st.rerun()
            
        st.divider()
        st.subheader("Manual Internal Post")
        with st.form("manual"):
            t = st.text_input("Link Title")
            l = st.text_input("Direct Landing Page URL")
            ty = st.selectbox("Type", ["Case Comp", "Live Project", "Certification"])
            dl = st.date_input("Closing Date")
            if st.form_submit_button("Post Live"):
                vault.save_opportunities([{"title":t, "org":"Placement Comm", "deadline":str(dl), "link":l, "category":ty, "platform":"IEC Internal", "description":"Sourced link."}])
                st.toast("Success: Link Published.")
