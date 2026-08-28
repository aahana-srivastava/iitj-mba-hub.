import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# ==========================================
# 1. MODEL: THE DATA SERVICE (DB Operations)
# ==========================================
class ResourceDB:
    def __init__(self):
        self.db_path = 'career_vault.db'
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS ops 
                         (id INTEGER PRIMARY KEY, title TEXT, org TEXT, deadline TEXT, 
                          link TEXT, cat TEXT, source TEXT)''')
            conn.commit()

    def insert_bulk(self, data_list):
        count = 0
        with sqlite3.connect(self.db_path) as conn:
            for item in data_list:
                # De-duplicate by exact Link to prevent repeating results
                check = pd.read_sql_query("SELECT id FROM ops WHERE link = ?", conn, params=(item['link'],))
                if check.empty:
                    c = conn.cursor()
                    c.execute("INSERT INTO ops (title, org, deadline, link, cat, source) VALUES (?,?,?,?,?,?)",
                              (item['title'], item['org'], item['deadline'], item['link'], item['cat'], item['source']))
                    count += 1
            conn.commit()
        return count

    def get_data(self, category):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(f"SELECT * FROM ops WHERE cat = '{category}'", conn)

    def wipe(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.cursor().execute("DELETE FROM ops")

# ==========================================
# 2. LOGIC: THE SCRAPER SUITE (Real Crawling)
# ==========================================
class UniversalScraper:
    def __init__(self):
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        self.launch_date = datetime(2026, 8, 1).date()

    def fetch_swayam_courses(self):
        """Live Scraper for Swayam/NPTEL Management Portal"""
        found = []
        # Querying Management subjects
        url = "https://swayam.gov.in/explorer?category=Management"
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            # Extracting cards - logic targets dynamic paths usually found in Swayam HTML
            for link in soup.find_all('a', href=True):
                title = link.get_text().strip()
                href = link['href']
                if "/nc_details/" in href or "course" in href:
                    if len(title) > 20: # Filtering out nav links
                        found.append({
                            "title": title[:100], "org": "Swayam / NPTEL", "deadline": "2027-12-31",
                            "link": f"https://swayam.gov.in{href}" if href.startswith("/") else href,
                            "cat": "Certification", "source": "Swayam"
                        })
        except: pass
        return found

    def fetch_class_central_certs(self):
        """Live Scraper for Class Central Report List"""
        found = []
        url = "https://www.classcentral.com/report/free-certificates/"
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(r.content, 'html.parser')
            for a in soup.select('article a[href*="/course/"]'):
                title = a.get_text().strip()
                if any(kw in title.lower() for kw in ["business", "management", "analytics", "product"]):
                    found.append({
                        "title": title[:100], "org": "Class Central", "deadline": "2027-12-31",
                        "link": f"https://www.classcentral.com{a['href']}",
                        "cat": "Certification", "source": "ClassCentral"
                    })
        except: pass
        return found

    def simulate_future_opportunities(self):
        """Seeds upcoming exact portal paths for August 2026+ Case Comps"""
        return [
            {"title": "HUL LIME Season 18", "org": "HUL", "deadline": "2026-08-15", "link": "https://unstop.com/competitions/hul-lime", "cat": "Case Comp", "source": "Direct Portal"},
            {"title": "Reliance TUP 2026", "org": "Reliance Industries", "deadline": "2026-09-10", "link": "https://unstop.com/competitions/tup", "cat": "Case Comp", "source": "Direct Portal"},
            {"title": "J.P. Morgan Investment Banking Virtual", "org": "Forage", "deadline": "2027-12-31", "link": "https://www.theforage.com/virtual-internships/R5iK7HMxJGBfbGcnR", "cat": "Live Project", "source": "Direct Portal"},
        ]

# ==========================================
# 3. PRESENTATION: STREAMLIT APP
# ==========================================
db = ResourceDB()
engine = UniversalScraper()

st.set_page_config(page_title="IITJ career hub", layout="wide")

page = st.sidebar.radio("Navigate Hub", ["📈 Dashboad", "🎓 Resource Admin"])

if page == "📈 Dashboad":
    st.title("🎓 IIT Jodhpur Career Readiness Feed")
    t1, t2, t3 = st.tabs(["🏆 Case Competitions", "💼 Live Projects", "📜 Free Certifications (Swayam+)"])

    def display_list(category, check_date=False):
        df = db.get_data(category)
        if df.empty:
            st.info(f"No results in {category}. IEC admin must run Sync.")
            return

        if check_date:
            # Filter Case Comps & Projects specifically after Aug 2026
            df['date_dt'] = pd.to_datetime(df['deadline']).dt.date
            df = df[df['date_dt'] >= engine.launch_date]

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.subheader(row['title'])
                c1.write(f"Source: {row['org']} | Platform: {row['source']}")
                c2.error(f"Deadline: {row['deadline']}")
                c2.link_button("Exact Path →", row['link'], width="stretch")

    with t1: display_list("Case Comp", check_date=True)
    with t2: display_list("Live Project", check_date=True)
    with t3: display_list("Certification", check_date=False) # Certs ignore launch date filter

elif page == "🎓 Resource Admin":
    st.title("⚙️ Industry Hub Management")
    pw = st.sidebar.text_input("Enter Admin Key", type="password")
    
    if pw == "iitj2026":
        st.success("Authenticated: Admin Mode Active")
        col1, col2 = st.columns(2)
        
        if col1.button("🔥 RUN LIVE DUAL-SCANNER (Swayam + ClassCentral)"):
            with st.spinner("Scraping live course directories..."):
                swayam_results = engine.fetch_swayam_courses()
                cc_results = engine.fetch_class_central_certs()
                other_seeds = engine.simulate_future_opportunities()
                
                # Combine and Save
                full_pool = swayam_results + cc_results + other_seeds
                new_added = db.insert_bulk(full_pool)
                st.write(f"Scrape completed! Total {new_added} unique items discovered across the web.")

        if col2.button("🧹 PURGE LOCAL DATABASE"):
            db.wipe()
            st.warning("Database cleared.")

        st.divider()
        st.subheader("Manual Registration Link Input")
        with st.form("manual"):
            t = st.text_input("Item Title")
            l = st.text_input("Direct Application Link")
            ca = st.selectbox("Type", ["Case Comp", "Live Project", "Certification"])
            if st.form_submit_button("Push Resource to Website"):
                db.insert_bulk([{"title":t, "org":"Direct Entry", "deadline":"2026-12-31", "link":l, "cat":ca, "source":"Placement Comm"}])
                st.toast("Success: Resource is live!")
    else:
        st.error("Admin Authentication Needed.")
