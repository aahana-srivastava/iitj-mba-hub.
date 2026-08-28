import streamlit as st
import pandas as pd
import sqlite3
import json
import requests
import re
from datetime import datetime
from openai import OpenAI
import PyPDF2
import io

# ==========================================
# 1. MODEL LAYER (Persistent Hub Vault)
# ==========================================
class OpportunityModel:
    def __init__(self):
        self.db_path = 'iitj_career_ai_hub.db'
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS hub 
                (id INTEGER PRIMARY KEY, title TEXT, org TEXT, deadline TEXT, 
                 link TEXT, category TEXT, platform TEXT, tag TEXT)''')
            conn.commit()

    def add_unique(self, items):
        today = datetime.now().date()
        added = 0
        with sqlite3.connect(self.db_path) as conn:
            for it in items:
                # Registration Filter
                dead_dt = datetime.strptime(it['deadline'], '%Y-%m-%d').date()
                if dead_dt < today: continue

                check = pd.read_sql_query("SELECT id FROM hub WHERE link = ?", conn, params=(it['link'],))
                if check.empty:
                    conn.execute("INSERT INTO hub (title, org, deadline, link, category, platform, tag) VALUES (?,?,?,?,?,?,?)",
                                 (it['title'], it['org'], it['deadline'], it['link'], it['category'], it['platform'], it['tag']))
                    added += 1
        return added

    def fetch(self, cat):
        with sqlite3.connect(self.db_path) as conn:
            today = datetime.now().strftime('%Y-%m-%d')
            return pd.read_sql_query(f"SELECT * FROM hub WHERE category = '{cat}' AND deadline >= '{today}'", conn)

    def purge(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM hub")

# ==========================================
# 2. LOGIC LAYER (The AI & Scraper Factory)
# ==========================================
class AIProjectEngine:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.cutoff = datetime(2026, 8, 1).date()

    def analyze_resume_fit(self, resume_text, job_titles):
        """Uses AI to rank job opportunities based on student's resume."""
        if not self.client: return "AI Not Authorized."
        
        prompt = f"Student Resume: {resume_text[:2000]}... Opportunities: {job_titles}. Rank top 2 and why."
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

    def scrape_swayam_plus(self):
        # Uses JSON node extraction from Swayam HTML payload
        headers = {"User-Agent": "Mozilla/5.0"}
        found = []
        try:
            r = requests.get("https://swayam.gov.in/explorer?category=Management", headers=headers, timeout=10)
            blob = re.search(r'value: (\{"edges":.*?\})', r.text)
            if blob:
                data = json.loads(blob.group(1))
                for e in data['edges']:
                    n = e['node']
                    found.append({
                        "title": n['title'], "org": n['instructorInstitute'] or "IIT",
                        "deadline": (n.get('examDate') or "2027-12-31")[:10],
                        "link": n['url'], "category": "Certification", "platform": "Swayam", "tag": "Govt-Verified"
                    })
        except: pass
        return found

    def get_forage_deep_catalog(self):
        """Master Registry of deep paths for 100% Fit MBA Virtual Internships"""
        f_date = "2027-12-31"
        pool = [
            {"t": "BCG Global Strategic Analysis", "o": "BCG", "l": "https://www.theforage.com/virtual-internships/prototype/S7699i85S2nBnyA7q"},
            {"t": "JPM Investment Banking VEP", "o": "J.P. Morgan", "l": "https://www.theforage.com/virtual-internships/prototype/R5iK7HMxJGBfbGcnR"},
            {"t": "KPMG Strategy Consultant Module", "o": "KPMG", "l": "https://www.theforage.com/virtual-internships/prototype/m7W4m9A9pCcYreH9t"},
            {"t": "Accenture Supply Chain track", "o": "Accenture", "l": "https://www.theforage.com/virtual-internships/prototype/4sBy8mZ3BCHXpMkJr"},
            {"t": "Red Bull Marketing/Brand Masterclass", "o": "Red Bull", "l": "https://www.theforage.com/virtual-internships/prototype/rB8Lp4W7vN2m3J5y"},
            {"t": "Goldman Sachs IB simulation", "o": "Goldman Sachs", "l": "https://www.theforage.com/virtual-internships/prototype/6H9kG976RxeSnhR2S"}
        ]
        return [{
            "title": i["t"], "org": i["o"], "deadline": f_date,
            "link": i["l"], "category": "Live Project", "platform": "Forage DeepPath", "tag": "Simulated work-ex"
        } for i in pool]

# ==========================================
# 3. PRESENTATION LAYER (The UI)
# ==========================================
st.set_page_config(page_title="IITJ career hub", layout="wide")
vault = OpportunityModel()

# Sidebar Control
st.sidebar.title("Career Portal")
access = st.sidebar.radio("View", ["📊 Student Feed", "📄 Resume Analysis", "⚙️ Admin & Sync"])

if access == "📊 Student Feed":
    st.title("🚀 Career Readiness Hub | IIT Jodhpur MBA")
    t1, t2, t3 = st.tabs(["🏆 Premium Case Comps", "💼 Virtual Live Projects", "📜 Certified Courses"])

    def render(category, enforce_2026):
        df = vault.fetch(category)
        if df.empty: 
            st.info("Nothing here yet. Admin needs to sync data.")
            return

        if enforce_2026:
            df['d_obj'] = pd.to_datetime(df['deadline']).dt.date
            df = df[df['d_obj'] >= datetime(2026, 8, 1).date()]

        for _, row in df.iterrows():
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                c1.subheader(row['title'])
                c1.write(f"🏢 Organizer: {row['org']} | Tag: {row['tag']}")
                c2.error(f"⏳ Closes: {row['deadline']}")
                c2.link_button("Exact Path →", row['link'], width='stretch')

    with t1: render("Case Comp", True)
    with t2: render("Live Project", True)
    with t3: 
        st.caption("Skills building certifications are available instantly.")
        render("Certification", False)

elif access == "📄 Resume Analysis":
    st.title("🧠 AI Profile-Opportunity Match")
    up = st.file_uploader("Upload Resume (PDF) to find your matches", type="pdf")
    ak = st.text_input("OpenAI API Key (Enter to unlock matching)", type="password")
    
    if up and ak:
        # PDF Reading
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(up.read()))
        resume_txt = "".join([p.extract_text() for p in pdf_reader.pages])
        
        # Load Jobs
        df_proj = vault.fetch("Live Project")
        titles = list(df_proj['title'])
        
        with st.spinner("AI is evaluating matches..."):
            engine = AIProjectEngine(api_key=ak)
            feedback = engine.analyze_resume_fit(resume_txt, str(titles))
            st.success("Analysis Complete!")
            st.write(feedback)

elif access == "⚙️ Admin & Sync":
    st.title("🛠️ Resource Master Command")
    key = st.sidebar.text_input("IEC Admin Code", type="password")
    
    if key == "iitj2026":
        st.success("Authorized IEC Access")
        col1, col2 = st.columns(2)
        factory = AIProjectEngine(api_key=None) # Admin only needs Scraper part
        
        if col1.button("Sync Swayam Management"):
            c = vault.add_unique(factory.scrape_swayam_plus())
            st.toast(f"Found {c} new courses.")
            
        if col2.button("Sync Global Forage Projects"):
            c = vault.add_unique(factory.get_forage_deep_catalog())
            st.toast(f"Updated: {c} items live.")
            
        st.divider()
        st.subheader("Manual High-Trust Link Push")
        with st.form("manual"):
            ti = st.text_input("Opp Name")
            li = st.text_input("Deep Link (Registration page)")
            dd = st.date_input("Deadline")
            ct = st.selectbox("Category", ["Case Comp", "Live Project", "Certification"])
            if st.form_submit_button("Push"):
                vault.add_unique([{"title":ti, "org":"Internal", "deadline":str(dd), "link":li, "category":ct, "platform":"IEC", "tag":"Curated"}])
                st.success("Posted!")

        if st.sidebar.button("🧹 Purge Local Cache"):
            vault.wipe()
            st.rerun()
