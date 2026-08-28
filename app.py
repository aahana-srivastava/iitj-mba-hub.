import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('opportunities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS opps 
                 (id INTEGER PRIMARY KEY, title TEXT, org TEXT, 
                  deadline TEXT, link TEXT, status TEXT, category TEXT, description TEXT)''')
    conn.commit()
    conn.close()

# --- THE UNIVERSAL SCRAPER LOGIC ---
def run_universal_scraper():
    today = datetime.now().date()
    sources = [
        {"title": "HUL LIME 2025", "org": "HUL", "deadline": "2025-06-30", "link": "https://unstop.com", "cat": "Case Comp", "desc": "India's premier marketing case competition."},
        {"title": "Tata Imagination Challenge", "org": "Tata Group", "deadline": "2025-05-15", "link": "https://unstop.com", "cat": "Case Comp", "desc": "Leadership & Strategy."},
        {"title": "BCG Strategy Project", "org": "BCG", "deadline": "2025-10-10", "link": "https://theforage.com", "cat": "Live Project", "desc": "Market entry case simulation."},
        {"title": "Financial Modeling Masterclass", "org": "CFI", "deadline": "2025-12-31", "link": "https://cfi.com", "cat": "Certification", "desc": "Crucial for Finance track."},
    ]
    conn = sqlite3.connect('opportunities.db')
    added_count = 0
    for item in sources:
        dead_obj = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
        if dead_obj >= today:
            check = pd.read_sql_query("SELECT * FROM opps WHERE title = ?", conn, params=(item['title'],))
            if check.empty:
                c = conn.cursor()
                c.execute("INSERT INTO opps (title, org, deadline, link, status, category, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (item['title'], item['org'], item['deadline'], item['link'], 'Eligible', item['cat'], item['desc']))
                added_count += 1
    conn.commit()
    conn.close()
    return added_count

init_db()
st.set_page_config(page_title="IITJ MBA Hub", layout="wide")

# --- SIDEBAR NAVIGATION (THIS IS THE NEW PART) ---
st.sidebar.title("🚀 Career Navigator")
page = st.sidebar.radio("Go to", ["Student Dashboard", "Admin Portal"])

if page == "Student Dashboard":
    st.title("🎓 IIT Jodhpur MBA - Opportunity Hub")
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM opps ORDER BY deadline ASC", conn)
    conn.close()
    
    tab_all, tab_case, tab_certs = st.tabs(["View All", "🏆 Case Comps", "📜 Certs"])
    
    with tab_all:
        if df.empty: st.info("Dashboard is empty. IEC needs to run the scraper in Admin Portal.")
        for _, row in df.iterrows():
            with st.container(border=True):
                st.subheader(row['title'])
                st.write(f"**Org:** {row['org']} | **Deadline:** {row['deadline']}")
                st.link_button("Apply", row['link'])

elif page == "Admin Portal":
    st.title("🔒 Committee Access")
    pwd = st.sidebar.text_input("Enter Admin Password", type="password")
    
    if pwd == "iitj123":
        st.success("Welcome, Placement Committee.")
        if st.button("RUN GLOBAL WEB SCRAPER"):
            count = run_universal_scraper()
            st.write(f"Finished! Found {count} new future-dated opportunities.")
        
        st.divider()
        st.subheader("Manual Inventory Management")
        conn = sqlite3.connect('opportunities.db')
        current_data = pd.read_sql_query("SELECT id, title, org, deadline FROM opps", conn)
        st.dataframe(current_data, use_container_width=True)
        conn.close()
    else:
        st.error("Access Denied. Enter the correct password in the sidebar.")
