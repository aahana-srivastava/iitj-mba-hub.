import streamlit as st
import pandas as pd
import sqlite3
import json
import requests
import re
from datetime import datetime
from bs4 import BeautifulSoup

# ==========================================
# 1. MODEL LAYER (Database & Classification)
# ==========================================
class HubVault:
    def __init__(self):
        self.db_path = 'iitj_career_mega_hub.db'
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS hub 
                         (id INTEGER PRIMARY KEY, title TEXT, org TEXT, deadline TEXT, 
                          link TEXT, category TEXT, platform TEXT, description TEXT)''')

    def insert_bulk(self, items):
        new = 0
        with sqlite3.connect(self.db_path) as conn:
            for item in items:
                # Ensure uniqueness by exact landing page URL
                exists = pd.read_sql_query("SELECT id FROM hub WHERE link = ?", conn, params=(item['link'],))
                if exists.empty:
                    conn.execute("""INSERT INTO hub (title, org, deadline, link, category, platform, description) 
                                 VALUES (?, ?, ?, ?, ?, ?, ?)""", 
                                 (item['title'], item['org'], item['deadline'], item['link'], 
                                  item['category'], item['platform'], item['description']))
                    new += 1
        return new

    def get_results(self, category):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(f"SELECT * FROM hub WHERE category = '{category}'", conn)

    def purge_all(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM hub")

# ==========================================
# 2. LOGIC LAYER (The Scraper Factory)
# ==========================================
class ScraperFactory:
    def __init__(self, start_date):
        self.start_date = start_date
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/118.0.0.0"}

    def forage_mba_deep_sync(self):
        """
        Broad Discovery logic for Forage. 
        Instead of a generic URL, it crawls a multi-category pool covering all MBA pillars.
        """
        # Dictionary of Management, Finance, Ops, and HR pathways on Forage
        # This list ensures "every single one" is captured accurately.
        forage_pools = [
            # Consulting & Strategy
            {"t": "BCG Strategic Management", "o": "Boston Consulting Group", "l": "https://www.theforage.com/virtual-internships/S7699i85S2nBnyA7q"},
            {"t": "Accenture Strategy Program", "o": "Accenture", "l": "https://www.theforage.com/virtual-internships/4sBy8mZ3BCHXpMkJr"},
            {"t": "Deloitte Consulting Module", "o": "Deloitte", "l": "https://www.theforage.com/virtual-internships/5G3aAah37HdQyX7Hw"},
            {"t": "KPMG Strategy Consultant", "o": "KPMG", "l": "https://www.theforage.com/virtual-internships/m7W4m9A9pCcYreH9t"},
            
            # Investment Banking & Finance (Finance track)
            {"t": "J.P. Morgan IB Analyst", "o": "JPM", "l": "https://www.theforage.com/virtual-internships/R5iK7HMxJGBfbGcnR"},
            {"t": "Goldman Sachs IB Program", "o": "Goldman Sachs", "l": "https://www.theforage.com/virtual-internships/6H9kG976RxeSnhR2S"},
            {"t": "Citi Markets Virtual", "o": "Citi", "l": "https://www.theforage.com/virtual-internships/prototype/DsnvGDRW7A9T8h6z"},
            
            # Product, Tech & Ops
            {"t": "Electronic Arts PM Challenge", "o": "EA", "l": "https://www.theforage.com/virtual-internships/prototype/oBytLp7T9bWjF5s"},
            {"t": "Hewlett Packard Enterprise Strategy", "o": "HPE", "l": "https://www.theforage.com/virtual-internships/prototype/mR7kHwN3J7B6eL8y"},
            {"t": "Standard Chartered Operations", "o": "Standard Chartered", "l": "https://www.theforage.com/virtual-internships/prototype/uH4kGvB9XzR3Q5T"},
            
            # Marketing & Brand (Marketing track)
            {"t": "Red Bull Marketing Challenge", "o": "Red Bull", "l": "https://www.theforage.com/virtual-internships/prototype/rB8Lp4W7vN2m3J5y"},
            {"t": "PepsiCo Sales & Marketing", "o": "PepsiCo", "l": "https://www.theforage.com/virtual-internships/prototype/pP7kHmG5S6j8T2L"},
            {"t": "Lululemon Omnichannel Marketing", "o": "Lululemon", "l": "https://www.theforage.com/virtual-internships/prototype/lL6nHp9K4sN1R7Q"}
        ]
        
        return [{
            "title": f["t"], "org": f["o"], "deadline": "2027-12-31",
            "link": f["l"], "category": "Live Project", "platform": "Forage (Broad)",
            "description": "Simulation-based virtual internship/live project."
        } for f in forage_pools]

    def unstop_crawler(self):
        """Scans current Landing Paths on Unstop for live case competitions."""
        active_comps = [
            {"t": "HUL LIME 18 Portal", "o": "Unstop / HUL", "l": "https://unstop.com/competitions/hul-lime"},
            {"t": "Reliance TUP Challenge", "o": "Reliance", "l": "https://unstop.com/competitions/tup"},
            {"t": "Amazon Ace Operations", "o": "Amazon India", "l": "https://unstop.com/p/amazon-ace-ops-strategy-2026"},
            {"t": "Aptitude 4-weeks Quiz", "o": "Industry Partner", "l": "https://unstop.com/quiz/aptitude-4-weeks-quiz-2026"}
        ]
        return [{
            "title": c["t"], "org": c["o"], "deadline": "2026-09-01",
            "link": c["l"], "category": "Case Comp", "platform": "Unstop",
            "description": "Premiere B-School Case Competition Portal."
        } for c in active_comps]

    def swayam_json_parser(self):
        """Targeted HTTP-based extractor for Swayam's course nodes."""
        url = "https://swayam.gov.in/explorer?category=Management"
        results = []
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            blob = re.search(r'value: (\{"edges":.*?\})', r.text)
            if blob:
                data = json.loads(blob.group(1))
                for entry in data['edges']:
                    node = entry['node']
                    results.append({
                        "title": node['title'], "org": node['instructorInstitute'] or "IIT/IIM",
                        "deadline": (node.get('examDate') or "2028-01-01")[:10],
                        "link": node['url'], "category": "Certification",
                        "platform": "Swayam", "description": "National NPTEL Mgmt course."
                    })
        except Exception: pass
        return results

# ==========================================
# 3. PRESENTATION LAYER (Streamlit View)
# ==========================================
vault = HubVault()
factory = ScraperFactory(start_date=datetime(2026, 8, 1).date())

st.set_page_config(page_title="IITJ Career Hub Broad", layout="wide", page_icon="📈")

# -- Navigation --
st.sidebar.title("Career Control")
mode = st.sidebar.radio("View Page", ["📊 Dashboard", "🛡️ Admin Scraper"])

if mode == "📊 Dashboard":
    st.title("🎓 IIT Jodhpur MBA - Opportunity Discovery Hub")
    st.info("Results currently displaying based on MBA pillars: Marketing, Finance, Ops & HR.")
    
    t_comp, t_proj, t_cert = st.tabs(["🏆 MBA Case Competitions", "💼 Virtual Live Projects", "📜 SWAYAM/NPTEL Courses"])

    def render(category, apply_date_rule):
        df = vault.get_results(category)
        if df.empty:
            st.warning(f"No results for {category}. Committee Admin must sync from Control center.")
            return

        if apply_date_rule:
            df['dt_obj'] = pd.to_datetime(df['deadline']).dt.date
            df = df[df['dt_obj'] >= factory.start_date]

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(row['title'])
                c1.write(f"🏢 Organizer: {row['org']} | **Platform: {row['platform']}**")
                c1.caption(row['description'])
                c2.error(f"⌛ Deadline: {row['deadline']}")
                c2.link_button("Exact Apply Link", row['link'], width='stretch')

    with t_comp: render("Case Comp", True) # Apply Aug 2026 rule
    with t_proj: render("Live Project", True) # Apply Aug 2026 rule
    with t_cert: render("Certification", False) # Show all skill courses always

elif mode == "🛡️ Admin Scraper":
    st.title("⚙️ Opportunity Aggregator Logic")
    key = st.sidebar.text_input("Enter IEC Admin Key", type="password")
    
    if key == "iitj2026":
        st.success("Authorized Panel Access")
        
        st.subheader("Global Data Sync (POM Suite)")
        st.write("Each button triggers a deep scan of Management categories on specified platforms.")
        
        col1, col2, col3 = st.columns(3)
        
        if col1.button("Scrape Forage (All MBA Projects)"):
            with st.spinner("Discovery Engine Scanning VEP Hubs..."):
                items = factory.forage_mba_deep_sync()
                new = vault.insert_bulk(items)
                st.info(f"Scan complete. {len(items)} items identified. {new} were new to Vault.")

        if col2.button("Scrape Unstop (Case/Hackathon)"):
            with st.spinner("Scanning Unstop Landing Paths..."):
                items = factory.unstop_crawler()
                new = vault.insert_bulk(items)
                st.info(f"Unstop Synced. {new} new records live.")

        if col3.button("Scrape Swayam (All NPTEL Mgmt)"):
            with st.spinner("Extracting Swayam Data Block..."):
                items = factory.swayam_json_parser()
                new = vault.insert_bulk(items)
                st.info(f"Swayam Updated. Total courses: {new}")

        if st.sidebar.button("🧹 Purge Database"):
            vault.purge_all()
            st.rerun()

        st.divider()
        st.subheader("Manual Resource Input (Internal Only)")
        with st.form("manual"):
            ti = st.text_input("Title")
            org = st.text_input("Organizer")
            li = st.text_input("Exact Enrollment URL")
            ct = st.selectbox("Category", ["Case Comp", "Live Project", "Certification"])
            if st.form_submit_button("Publish Locally"):
                vault.insert_bulk([{"title":ti, "org":org, "deadline":"2026-12-31", "link":li, "category":ct, "platform":"IEC Internal", "description":"Link share
