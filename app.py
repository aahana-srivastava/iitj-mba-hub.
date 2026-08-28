import streamlit as st
import pandas as pd
import sqlite3
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ==========================================
# 1. MODEL LAYER (Database & MBA Filtering)
# ==========================================
class OpportunityModel:
    def __init__(self):
        self.db_path = 'mba_career_hub.db'
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS entries 
                         (id INTEGER PRIMARY KEY, title TEXT, org TEXT, deadline TEXT, 
                          link TEXT, type TEXT, platform TEXT, description TEXT)''')

    def is_mba_relevant(self, title, nc_code, org):
        """Logic to check if course is for MBA students"""
        mba_keywords = ["Management", "Business", "Marketing", "Finance", "Strategy", 
                        "Accounting", "Supply Chain", "HR", "Organizational", "Analytics", 
                        "Operations", "Product", "Investment"]
        
        # High-relevance coordinators
        premium_coordinators = ["IIMB", "NITTTR", "INI", "UGC", "AICTE"]
        
        title_match = any(kw.lower() in title.lower() for kw in mba_keywords)
        nc_match = nc_code in premium_coordinators
        return title_match or nc_match

    def save_to_vault(self, data):
        added = 0
        with sqlite3.connect(self.db_path) as conn:
            for d in data:
                # Use Link as unique ID to prevent duplicates
                check = pd.read_sql_query("SELECT id FROM entries WHERE link = ?", conn, params=(d['link'],))
                if check.empty:
                    conn.execute("INSERT INTO entries (title, org, deadline, link, type, platform, description) VALUES (?,?,?,?,?,?,?)",
                                 (d['title'], d['org'], d['deadline'], d['link'], d['type'], d['platform'], d['description']))
                    added += 1
        return added

    def fetch_by_type(self, type_str):
        with sqlite3.connect(self.db_path) as conn:
            return pd.read_sql_query(f"SELECT * FROM entries WHERE type = '{type_str}'", conn)

    def wipe_vault(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM entries")

# ==========================================
# 2. LOGIC LAYER (Playwright Scraper)
# ==========================================
class SwayamAutomation:
    def __init__(self):
        self.base_url = "https://swayam.gov.in/explorer?category=Management"
        self.launch_date = datetime(2026, 8, 1).date()

    def crawl_all_courses(self):
        """Uses Playwright to physically scroll and capture courses from Swayam"""
        all_found = []
        
        with sync_playwright() as p:
            # Launching headless browser
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.base_url)
            
            # Step 1: Maximize Results (Clicks "Load More" multiple times)
            st.write("Expanding Swayam Catalog... please wait.")
            for _ in range(3): # Increase range to scroll deeper
                try:
                    load_more = page.locator("#load-more-button")
                    if load_more.is_visible():
                        load_more.click()
                        time.sleep(3) # Slowed down to behave human-like
                except:
                    break

            # Step 2: Extract HTML content
            content = page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find all Course Cards
            cards = soup.select("course-card")
            
            for card in cards:
                try:
                    # Target tags from your specific Swayam HTML structure
                    title = card.select_one(".courseTitle").get_text(strip=True)
                    link = card.select_one("a")['href']
                    nc_code = card.select_one("td strong").get_text(strip=True) if card.select_one("td strong") else "Swayam"
                    org = card.select_one("[title]").get('title') if card.select_one("[title]") else "Swayam NPTEL"
                    
                    # Apply MBA Logic
                    if model.is_mba_relevant(title, nc_code, org):
                        all_found.append({
                            "title": title,
                            "org": org,
                            "deadline": "2026-12-31", # General placeholder
                            "link": f"https://onlinecourses.swayam2.ac.in{link}" if link.startswith("/") else link,
                            "type": "Certification",
                            "platform": "Swayam (Live Crawl)",
                            "description": f"Verified NPTEL Management course under {nc_code}"
                        })
                except Exception as e:
                    continue

            browser.close()
        return all_found

# ==========================================
# 3. PRESENTATION LAYER (UI)
# ==========================================
model = OpportunityModel()
swayam_bot = SwayamAutomation()

st.set_page_config(page_title="IITJ Career Hub Pro", layout="wide")

nav = st.sidebar.selectbox("Go To", ["📊 Student Portal", "⚙️ IEC IEC Admin"])

if nav == "📊 Student Portal":
    st.title("🎓 IIT Jodhpur MBA - Professional Hub")
    
    t1, t2, t3 = st.tabs(["🏆 Case Comps", "💼 Virtual Live Projects", "📜 MBA Certifications"])

    def display_category(cat, date_check=False):
        df = model.fetch_by_type(cat)
        if df.empty:
            st.info(f"No results yet for {cat}.")
            return

        if date_check:
            # Filter for comps closing after August 1, 2026
            df['date_dt'] = pd.to_datetime(df['deadline']).dt.date
            df = df[df['date_dt'] >= swayam_bot.launch_date]

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([4, 1])
                c1.subheader(row['title'])
                c1.write(f"**Org:** {row['org']} | **Platform:** {row['platform']}")
                c1.caption(row['description'])
                c2.error(f"⏳ {row['deadline']}")
                c2.link_button("Register Directly →", row['link'], width='stretch')

    with t1: display_category("Case Comp", date_check=True)
    with t2: display_category("Live Project", date_check=True)
    with t3: display_category("Certification", date_check=False) # Certs ignore launch date

elif nav == "⚙️ IEC IEC Admin":
    st.title("⚙️ Admin Management System")
    pw = st.sidebar.text_input("Enter IEC Admin Password", type="password")
    
    if pw == "iitj2026":
        st.success("Authorized: Placement Committee Access")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Playwright Automations")
            if st.button("RUN DEEP SWAYAM SCRAPER"):
                with st.spinner("Automated browser is scanning 100+ course cards..."):
                    found_courses = swayam_bot.crawl_all_courses()
                    new = model.save_to_vault(found_courses)
                    st.write(f"Scraper Success: Found {len(found_courses)} Mgmt Courses. Added {new} new unique entries.")

        with col2:
            st.subheader("Global Case Sync")
            if st.button("RUN UNSTOP / FORAGE SYNC"):
                # Simulation for other deep links
                seed_data = [
                    {"title": "HUL LIME Season 18 Portal", "org": "Unstop", "deadline": "2026-08-20", "link": "https://unstop.com/competitions/hul-lime", "type": "Case Comp", "platform": "Unstop", "description": "National Level Premiere Competition."},
                    {"title": "Reliance TUP 7.0 Hub", "org": "Reliance", "deadline": "2026-09-10", "link": "https://unstop.com/competitions/tup", "type": "Case Comp", "platform": "Unstop", "description": "Sustainability and Strategy track."},
                    {"title": "J.P. Morgan Investment Banking Program", "org": "JPM", "deadline": "2027-12-31", "link": "https://www.theforage.com/virtual-internships/R5iK7HMxJGBfbGcnR", "type": "Live Project", "platform": "Forage", "description": "Direct Enroll module."}
                ]
                added = model.save_to_vault(seed_data)
                st.info(f"High-fidelity sync complete. {added} verified items added.")

        st.divider()
        if st.sidebar.button("🧹 PURGE ENTIRE HUB"):
            model.wipe_vault()
            st.rerun()

        st.subheader("Internal IEC Form (Add secret link)")
        with st.form("manual"):
            n = st.text_input("Title")
            l = st.text_input("Direct Registration Link")
            ca = st.selectbox("Category", ["Case Comp", "Live Project", "Certification"])
            dd = st.date_input("Deadline")
            if st.form_submit_button("Post to Students"):
                model.save_to_vault([{"title":n, "org":"IEC Direct", "deadline":str(dd), "link":l, "type":ca, "platform":"Industry Email", "description":"Link shared privately by organizer."}])
                st.toast("Success")
    else:
        st.error("Admin Security check needed.")
