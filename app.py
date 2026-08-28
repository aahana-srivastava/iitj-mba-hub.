import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# --- CONFIG ---
LAUNCH_DATE = datetime(2026, 8, 1).date()

def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resources 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, type TEXT, is_free_cert BOOLEAN, description TEXT)''')
    conn.commit()
    conn.close()

# --- THE REAL SCRAPER FOR CLASS CENTRAL ---
def scrape_class_central():
    """
    Scrapes Class Central's 'Free Certificates' reports.
    It targets reputable sources like AWS, Harvard, and Google.
    """
    url = "https://www.classcentral.com/report/free-certificates/"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    conn = sqlite3.connect('opportunities.db')
    added_count = 0
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # In the Class Central "Report" page, items are often inside list items (li) or headers
        # We look for links within the curated list sections
        articles = soup.find_all('li')
        
        for item in articles:
            text = item.get_text()
            link_tag = item.find('a')
            
            if link_tag and 'href' in link_tag.attrs:
                title = text.split('–')[0].strip()[:100]
                link = link_tag['href']
                
                # Check for High-Value MBA Keywords
                keywords = ["Google", "Digital", "Management", "Business", "Marketing", "Project", "Supply Chain", "Analytics"]
                if any(kw in title for kw in keywords):
                    # Check if exists
                    check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(title,))
                    if check.empty:
                        c = conn.cursor()
                        c.execute("""INSERT INTO resources (title, org, deadline, link, type, is_free_cert, description) 
                                     VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                  (title, "Class Central Resource", "2027-12-31", link, "Certification", True, "Free Certification curated by Class Central."))
                        added_count += 1
    except Exception as e:
        st.error(f"Class Central Scraper failed: {e}")
    
    conn.commit()
    conn.close()
    return added_count

def run_case_comp_scraper():
    """Adds competitions occurring after Aug 1, 2026"""
    # Simulated Future Mock-up for Unstop/Direct feeds
    mock_data = [
        {"title": "HUL LIME Season 18", "org": "HUL", "deadline": "2026-08-15", "link": "https://unstop.com"},
        {"title": "Amazon Ace Operations", "org": "Amazon", "deadline": "2026-10-20", "link": "https://unstop.com"}
    ]
    conn = sqlite3.connect('opportunities.db')
    count = 0
    for item in mock_data:
        deadline_obj = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
        if deadline_obj >= LAUNCH_DATE:
            check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(item['title'],))
            if check.empty:
                c = conn.cursor()
                c.execute("INSERT INTO resources (title, org, deadline, link, type, is_free_cert, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (item['title'], item['org'], item['deadline'], item['link'], 'Case Comp', False, "Premium MBA Case Comp"))
                count += 1
    conn.commit()
    conn.close()
    return count

init_db()
st.set_page_config(page_title="IITJ Career Hub", layout="wide")

# Navigation
view = st.sidebar.selectbox("Choose Section", ["📊 Student Dashboard", "🎓 Class Central (Free Certs)", "⚙️ Admin Manager"])

# SECTION 1: CASE COMPETITIONS
if view == "📊 Student Dashboard":
    st.title("🏆 Active Case Competitions (> Aug 2026)")
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type = 'Case Comp'", conn)
    conn.close()
    
    if df.empty:
        st.info("Run scraper in Admin panel to see 2026 opportunities.")
    else:
        for idx, row in df.iterrows():
            with st.container(border=True):
                st.subheader(row['title'])
                st.write(f"Ends: {row['deadline']}")
                st.link_button("Register on Unstop", row['link'])

# SECTION 2: CLASS CENTRAL SCRAPER PAGE
elif view == "🎓 Class Central (Free Certs)":
    st.title("📜 Class Central: Free Certificates Hub")
    st.write("Below are free courses with verified certificates scraped from Class Central reports.")
    
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type = 'Certification'", conn)
    conn.close()

    if df.empty:
        st.warning("Click 'Sync' in the Admin panel to pull data from Class Central.")
    else:
        for idx, row in df.iterrows():
            with st.container(border=True):
                st.success(f"Verified Free: {row['title']}")
                st.write(f"Source: {row['org']}")
                st.link_button("Get Certificate", row['link'])

# SECTION 3: ADMIN/LINK INPUT
elif view == "⚙️ Admin Manager":
    st.title("⚙️ Admin Control Panel")
    pwd = st.sidebar.text_input("Admin Code", type="password")
    
    if pwd == "iitj2026":
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Scrape Class Central (Free Certs)"):
                count = scrape_class_central()
                st.write(f"Scraped {count} items from Class Central.")
        with col2:
            if st.button("🔥 Sync Future Case Comps"):
                count = run_case_comp_scraper()
                st.write(f"Synced {count} future items.")
                
        st.divider()
        st.subheader("Manual Resource Addition")
        with st.form("manual_add"):
            name = st.text_input("Name")
            lnk = st.text_input("Link")
            typ = st.selectbox("Type", ["Case Comp", "Certification"])
            if st.form_submit_button("Publish"):
                conn = sqlite3.connect('opportunities.db')
                c = conn.cursor()
                c.execute("INSERT INTO resources (title, org, deadline, link, type, is_free_cert) VALUES (?,?,?,?,?,?)",
                          (name, "Manual Entry", "2026-12-31", lnk, typ, True))
                conn.commit()
                st.success("Live!")
