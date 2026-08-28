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
    """
    Simulation of scanning specific sites: Unstop, Forage, Coursera, LinkedIn.
    Only items with a FUTURE deadline are pulled into the Eligible database.
    """
    today = datetime.now().date()
    
    sources = [
        # B-SCHOOL SOURCES (UNSTOP)
        {"title": "HUL LIME 2025", "org": "Unstop / HUL", "deadline": "2025-06-30", "link": "https://unstop.com", "cat": "Case Comp", "desc": "India's premier marketing case competition."},
        {"title": "Marico Over The Wall", "org": "Unstop / Marico", "deadline": "2025-05-15", "link": "https://unstop.com", "cat": "Case Comp", "desc": "Supply Chain & Ops focus."},
        
        # CONSULTING SOURCES (FORAGE/Direct)
        {"title": "Deloitte Tech Consulting Project", "org": "The Forage / Deloitte", "deadline": "2025-12-01", "link": "https://theforage.com", "cat": "Live Project", "desc": "Virtual experience module in Cloud Transformation."},
        {"title": "EY Strategy Simulation", "org": "EY", "deadline": "2025-10-10", "link": "https://theforage.com", "cat": "Live Project", "desc": "Analyze a market entry strategy for a global retail client."},

        # SKILL SOURCES (COURSERA / CERTIFICATIONS)
        {"title": "Financial Modeling Masterclass", "org": "Corporate Finance Institute", "deadline": "2025-12-31", "link": "https://cfi.com", "cat": "Certification", "desc": "Crucial for Finance-specialized MBA students."},
        {"title": "SQL for Business Intelligence", "org": "Google", "deadline": "2025-09-30", "link": "https://coursera.org", "cat": "Certification", "desc": "Mandatory for MBA Data Science tracks."},
    ]

    conn = sqlite3.connect('opportunities.db')
    added_count = 0

    for item in sources:
        dead_obj = datetime.strptime(item['deadline'], '%Y-%m-%d').date()
        # Ensure only future deadlines are kept
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

# --- MAIN APP LOGIC ---
init_db()
st.set_page_config(page_title="IITJ MBA Opportunity Hub", layout="wide")

# Sidebar Navigation
st.sidebar.title("🚀 Career Navigator")
page = st.sidebar.radio("Go to", ["Student Dashboard", "Admin/Committee Portal"])

# ----------------- PAGE 1: STUDENT DASHBOARD -----------------
if page == "Student Dashboard":
    st.title("🎓 IIT Jodhpur MBA - Opportunity Hub")
    st.caption(f"Showing updated opportunities for Class of 2024-2028 | Date: {datetime.now().strftime('%d %b %Y')}")
    
    # Filter Tabs
    tab_all, tab_case, tab_projects, tab_certs = st.tabs(["View All", "🏆 Case Competitions", "💼 Live Projects", "📜 Certifications"])

    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query("SELECT * FROM opps ORDER BY deadline ASC", conn)
    conn.close()

    def show_opps(dataframe):
        if dataframe.empty:
            st.info("No future opportunities found in this category currently.")
        else:
            for _, row in dataframe.iterrows():
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"### {row['title']}")
                    c1.write(f"**Organizer:** {row['org']}")
                    c1.write(row['description'])
                    c2.error(f"Deadline: {row['deadline']}")
                    c2.link_button("Apply Now", row['link'], use_container_width=True)

    with tab_all:
        show_opps(df)
    with tab_case:
        show_opps(df[df['category'] == 'Case Comp'])
    with tab_projects:
        show_opps(df[df['category'] == 'Live Project'])
    with tab_certs:
        show_opps(df[df['category'] == 'Certification'])

# ----------------- PAGE 2: ADMIN PORTAL -----------------
elif page == "Admin/Committee Portal":
    st.title("🔒 Industry Engagement Committee (IEC) Panel")
    
    password = st.sidebar.text_input("Enter Admin Password", type="password")
    
    if password == "iitj123": # Simple security for MVP
        st.success("Authorized: Placement Committee Access")
        
        st.subheader("1. Batch Refresh (Multi-Source Scraper)")
        if st.button("RUN GLOBAL WEB SCRAPER"):
            count = run_universal_scraper()
            st.write(f"Scraper ran through Unstop, The Forage, and Coursera. {count} new future items added.")

        st.divider()
        
        st.subheader("2. Manually Update a Resource")
        with st.form("manual_add"):
            title = st.text_input("Opp Name (e.g. KPMG Case Study)")
            org = st.text_input("Organizer")
            deadline = st.date_input("Deadline Date")
            link = st.text_input("Application Link")
            cat = st.selectbox("Category", ["Case Comp", "Live Project", "Certification", "Fellowship"])
            desc = st.text_area("One-line Description")
            
            if st.form_submit_button("Push Resource to Website"):
                conn = sqlite3.connect('opportunities.db')
                c = conn.cursor()
                c.execute("INSERT INTO opps (title, org, deadline, link, status, category, description) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (title, org, str(deadline), link, 'Eligible', cat, desc))
                conn.commit()
                conn.close()
                st.info("Manual resource pushed to live dashboard.")

        st.divider()

        st.subheader("3. Current Resource Inventory (Edit/Delete)")
        conn = sqlite3.connect('opportunities.db')
        all_opps = pd.read_sql_query("SELECT id, title, org, deadline FROM opps", conn)
        st.dataframe(all_opps, use_container_width=True)
        
        id_to_delete = st.number_input("Enter ID of opportunity to remove:", step=1)
        if st.button("Delete Resource Permanently"):
            c = conn.cursor()
            c.execute("DELETE FROM opps WHERE id = ?", (id_to_delete,))
            conn.commit()
            st.warning(f"Deleted Resource ID {id_to_delete}")
        conn.close()

    else:
        st.error("Please enter the Placement Committee password in the sidebar to modify data.")
