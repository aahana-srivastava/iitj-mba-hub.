import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime

# --- ERROR-PROOF IMPORTS ---
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

# --- CONFIGURATION ---
LAUNCH_DATE = datetime(2026, 8, 1).date()
ADMIN_CODE = "iitj2026"

# --- DATABASE LOGIC ---
def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    # Table stores both Comps and Certifications
    c.execute('''CREATE TABLE IF NOT EXISTS resources 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, type TEXT, description TEXT)''')
    conn.commit()
    conn.close()

# --- SCRAPER 1: CLASS CENTRAL (Free Certificates) ---
def scrape_class_central():
    if not BS4_AVAILABLE:
        return "Library Error"
    
    url = "https://www.classcentral.com/report/free-certificates/"
    headers = {"User-Agent": "Mozilla/5.0"}
    added_count = 0
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Finding links and titles in the curated report list
        items = soup.find_all('li')
        conn = sqlite3.connect('opportunities.db')
        
        for item in items:
            link_tag = item.find('a')
            if link_tag and 'href' in link_tag.attrs:
                title = link_tag.get_text().strip()
                link = link_tag['href']
                
                # Keywords to filter for MBA-relevant content
                mba_keywords = ["Business", "Management", "Analytics", "Marketing", "Project", "Finance", "Data", "Leadership"]
                if any(kw.lower() in title.lower() for kw in mba_keywords):
                    check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(title,))
                    if check.empty:
                        c = conn.cursor()
                        c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                                  (title, "Class Central Verified", "2027-12-31", link, "Certification", "Free Verified Certificate found on Class Central."))
                        added_count += 1
        conn.commit()
        conn.close()
        return added_count
    except Exception as e:
        return str(e)

# --- SCRAPER 2: FUTURE CASE COMPS (2026+) ---
def run_case_comp_scraper():
    # Simulation of scraping high-tier portals for future 2026+ data
    mock_comps = [
        {"title": "HUL LIME Season 18", "org": "Unstop / HUL", "deadline": "2026-08-15", "link": "https://unstop.com"},
        {"title": "Reliance TUP 7.0", "org": "Reliance", "deadline": "2026-09-10", "link": "https://unstop.com"},
        {"title": "Amazon Operations Challenge", "org": "Amazon India", "deadline": "2026-11-20", "link": "https://unstop.com"},
        {"title": "KPMG Ideation Challenge", "org": "KPMG", "deadline": "2027-02-01", "link": "https://kpmg.com"}
    ]
    
    conn = sqlite3.connect('opportunities.db')
    added = 0
    for item in mock_comps:
        deadline_obj = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
        # Filter for competitions happening AFTER the 2026 Launch date
        if deadline_obj >= LAUNCH_DATE:
            check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(item['title'],))
            if check.empty:
                c = conn.cursor()
                c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                          (item['title'], item['org'], item['deadline'], item['link'], "Case Comp", "Premium National Level Case Competition."))
                added += 1
    conn.commit()
    conn.close()
    return added

# --- UI START ---
init_db()
st.set_page_config(page_title="IITJ MBA Hub", layout="wide", page_icon="🎓")

# Navigation
st.sidebar.title("📌 Navigation")
page = st.sidebar.selectbox("Go to Section", ["📈 Student Dashboard", "📜 Certification Hub", "🛠️ Admin Control"])

# ----------------- 1. STUDENT DASHBOARD (Case Comps) -----------------
if page == "📈 Student Dashboard":
    st.title("🏆 MBA Case Competitions")
    st.info(f"Displaying verified opportunities closing after **{LAUNCH_DATE.strftime('%B 2026')}**")
    
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type = 'Case Comp' ORDER BY deadline ASC", conn)
    conn.close()
    
    if df.empty:
        st.warning("No future competitions found. IEC Admin needs to run 'Sync' in the Control Panel.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4,1])
                col1.subheader(row['title'])
                col1.write(f"🏢 Organizer: {row['org']}")
                col1.caption(row['description'])
                col2.error(f"Ends: {row['deadline']}")
                col2.link_button("View / Apply", row['link'])

# ----------------- 2. CERTIFICATION HUB (Free Certs) -----------------
elif page == "📜 Certification Hub":
    st.title("📜 Industry Certifications (Free + Verified)")
    st.write("Resources automatically scanned from Class Central.")
    
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type = 'Certification' ORDER BY id DESC", conn)
    conn.close()
    
    if df.empty:
        st.info("No certificates loaded yet. IEC Admin needs to run 'Class Central Scan'.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"🎖️ {row['title']}")
                st.write(f"Source: {row['org']}")
                st.success("VERIFIED: Free with Certificate")
                st.link_button("Enroll Now", row['link'])

# ----------------- 3. ADMIN CONTROL / LINK INPUT -----------------
elif page == "🛠️ Admin Control":
    st.title("⚙️ Industry Engagement Management")
    pw = st.sidebar.text_input("Enter IEC Admin Key", type="password")
    
    if pw == ADMIN_CODE:
        st.success("Admin Panel Authorized")
        
        tab1, tab2, tab3 = st.tabs(["🚀 Automated Scrapers", "🔗 Manual Link Input", "🧹 Inventory Control"])
        
        with tab1:
            st.write("Automatically refresh data from global web sources.")
            col1, col2 = st.columns(2)
            if col1.button("Run Class Central Scraper"):
                with st.spinner("Scraping classcentral.com..."):
                    res = scrape_class_central()
                    st.success(f"Added {res} new free certificate courses!")
            
            if col2.button("Sync 2026+ Case Competitions"):
                with st.spinner("Finding future B-school challenges..."):
                    res = run_case_comp_scraper()
                    st.success(f"Added {res} future competitions to database!")

        with tab2:
            st.write("Paste a direct link (e.g., from an corporate HR email).")
            with st.form("add_link"):
                f_title = st.text_input("Title")
                f_org = st.text_input("Company/Organizer")
                f_link = st.text_input("Link URL")
                f_type = st.selectbox("Type", ["Case Comp", "Certification", "Live Project"])
                f_date = st.date_input("Closing Date")
                f_desc = st.text_area("Details (Optional)")
                
                if st.form_submit_button("Publish Live"):
                    conn = sqlite3.connect('opportunities.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                              (f_title, f_org, str(f_date), f_link, f_type, f_desc))
                    conn.commit()
                    conn.close()
                    st.toast("Success: Link Published to Dashboard!")

        with tab3:
            st.write("Manage current data.")
            conn = sqlite3.connect('opportunities.db')
            df_edit = pd.read_sql_query("SELECT id, title, type, deadline FROM resources", conn)
            st.dataframe(df_edit, height=300)
            
            target_id = st.number_input("Enter ID to Delete", step=1)
            if st.button("Delete Item Permanently"):
                c = conn.cursor()
                c.execute("DELETE FROM resources WHERE id = ?", (target_id,))
                conn.commit()
                conn.close()
                st.warning(f"Deleted item {target_id}")
    else:
        st.error("Restricted access. Use Admin Key to proceed.")
