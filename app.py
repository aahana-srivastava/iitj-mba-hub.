import streamlit as st
import pandas as pd
import sqlite3
import requests
from datetime import datetime

# --- SAFE IMPORT OF BEAUTIFULSOUP ---
try:
    from bs4 import BeautifulSoup
    BS_READY = True
except ImportError:
    BS_READY = False

# --- CONFIG ---
LAUNCH_DATE = datetime(2026, 8, 1).date()
ADMIN_KEY = "iitj2026"

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS resources 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, type TEXT, description TEXT)''')
    conn.commit()
    conn.close()

# --- CERTIFICATE SCRAPER (Class Central) ---
def get_class_central_certs():
    if not BS_READY:
        return "ERROR: beautifulsoup4 library not installed. Check requirements.txt."
    
    url = "https://www.classcentral.com/report/free-certificates/"
    headers = {"User-Agent": "Mozilla/5.0"}
    added = 0
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a')
        
        conn = sqlite3.connect('opportunities.db')
        for link in links:
            title = link.get_text().strip()
            href = link.get('href')
            
            if href and "http" in href:
                # Filter for High-Value MBA Skills
                mba_tags = ["Data", "Analytic", "Marketing", "Project", "Supply Chain", "Product", "Google", "AWS", "Microsoft"]
                if any(tag.lower() in title.lower() for tag in mba_tags):
                    check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(title,))
                    if check.empty:
                        c = conn.cursor()
                        c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                                  (title[:100], "Class Central Resource", "2027-12-31", href, "Certification", "Free Verified Course found via Scraper."))
                        added += 1
        conn.commit()
        conn.close()
        return f"Successfully added {added} certificates!"
    except Exception as e:
        return f"Network Error: {str(e)}"

# --- FUTURE CASE COMP SYNC (2026+) ---
def sync_case_comps():
    # Future Competitions specifically curated for Class of 2026-2028
    comps = [
        {"title": "HUL LIME Season 18", "org": "HUL", "deadline": "2026-08-15", "link": "https://unstop.com/competitions/hul-lime"},
        {"title": "Reliance TUP 7.0", "org": "Reliance", "deadline": "2026-09-05", "link": "https://unstop.com/competitions/tup"},
        {"title": "ITC Interrobang?! 2026", "org": "ITC", "deadline": "2026-10-25", "link": "https://itcltd.com"},
        {"title": "Amazon Ace Ops 2026", "org": "Amazon", "deadline": "2026-08-20", "link": "https://unstop.com"},
        {"title": "Tata Imagination Challenge", "org": "Tata Group", "deadline": "2026-11-15", "link": "https://tata.com"}
    ]
    
    conn = sqlite3.connect('opportunities.db')
    added = 0
    for item in comps:
        dead_obj = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
        if dead_obj >= LAUNCH_DATE:
            check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(item['title'],))
            if check.empty:
                c = conn.cursor()
                c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                          (item['title'], item['org'], item['deadline'], item['link'], "Case Comp", "Major B-School Competition for Batch 2026."))
                added += 1
    conn.commit()
    conn.close()
    return added

# --- LOAD MASTER LIST (When empty) ---
def load_master_certs():
    master_certs = [
        ("Google Data Analytics", "Google/Coursera", "https://coursera.org", "Gold standard for analytics roles."),
        ("Excel Skills for Business", "Macquarie University", "https://coursera.org", "Essential for Finance & Consulting."),
        ("Product Management Certification", "HubSpot", "https://academy.hubspot.com", "Free 100% Verified Certificate."),
        ("Inbound Marketing Cert", "HubSpot", "https://academy.hubspot.com", "Industry standard for marketing tracks."),
        ("Agile Project Management", "Google", "https://coursera.org", "Highly valued for Ops/Product roles."),
        ("AWS Cloud Practitioner", "Amazon", "https://aws.amazon.com", "Great for Tech-Management students."),
        ("Financial Modeling", "Corporate Finance Institute", "https://cfi.com", "Premium Finance certificate."),
    ]
    conn = sqlite3.connect('opportunities.db')
    for t, o, l, d in master_certs:
        check = pd.read_sql_query("SELECT * FROM resources WHERE title = ?", conn, params=(t,))
        if check.empty:
            c = conn.cursor()
            c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                      (t, o, "2027-12-31", l, "Certification", d))
    conn.commit()
    conn.close()

# --- UI SECTION ---
init_db()
st.set_page_config(page_title="IITJ MBA Hub", layout="wide")

page = st.sidebar.selectbox("Navigate Hub", ["📈 Case Comps (>Aug 2026)", "🎓 Certificate Hub", "⚙️ Admin Controls"])

# --- TAB 1: DASHBOARD ---
if page == "📈 Case Comps (>Aug 2026)":
    st.title("🏆 Upcoming Case Competitions")
    st.info(f"Targeting IIT Jodhpur MBA Batch 2026+ | Active after {LAUNCH_DATE}")
    
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type = 'Case Comp' ORDER BY deadline ASC", conn)
    conn.close()
    
    if df.empty:
        st.warning("No competitions currently synced. Go to Admin to fetch data.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([3,1])
                col1.subheader(row['title'])
                col1.write(f"🏢 Organizer: {row['org']}")
                col1.caption(row['description'])
                col2.error(f"⏳ Deadline: {row['deadline']}")
                col2.link_button("Register Now", row['link'])

# --- TAB 2: CERTIFICATES ---
elif page == "🎓 Certificate Hub":
    st.title("📜 Global Free Certifications")
    st.write("Full list of resume-building certificates for MBA Students.")
    
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM resources WHERE type = 'Certification' ORDER BY title ASC", conn)
    conn.close()
    
    if df.empty:
        if st.button("Load Full Master List Now"):
            load_master_certs()
            st.rerun()
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([4,1])
                col1.subheader(f"🎖️ {row['title']}")
                col1.write(f"Provider: {row['org']}")
                col1.write(row['description'])
                col2.success("Free Cert")
                col2.link_button("Start Learning", row['link'])

# --- TAB 3: ADMIN ---
elif page == "⚙️ Admin Controls":
    st.title("🛠️ Manager Access")
    key = st.sidebar.text_input("Admin Code", type="password")
    
    if key == ADMIN_KEY:
        st.subheader("Database Operations")
        c1, c2, c3 = st.columns(3)
        if c1.button("Run Class Central Scraper"):
            msg = get_class_central_certs()
            st.info(msg)
        if c2.button("Sync 2026 Case Comps"):
            added = sync_case_comps()
            st.success(f"Synced {added} competitions.")
        if c3.button("Reset & Reload Master Certs"):
            load_master_certs()
            st.success("Master List Updated!")

        st.divider()
        st.subheader("Input Private HR Links")
        with st.form("manual_entry"):
            name = st.text_input("Comp/Project Name")
            lnk = st.text_input("Target URL")
            typ = st.selectbox("Category", ["Case Comp", "Certification", "Live Project"])
            dl = st.date_input("Deadline")
            if st.form_submit_button("Publish Live"):
                conn = sqlite3.connect('opportunities.db')
                c = conn.cursor()
                c.execute("INSERT INTO resources (title, org, deadline, link, type, description) VALUES (?,?,?,?,?,?)",
                          (name, "Placement Comm", str(dl), lnk, typ, "Privately sourced by IEC Committee."))
                conn.commit()
                conn.close()
                st.toast("Published!")
    else:
        st.error("Access Restricted.")
