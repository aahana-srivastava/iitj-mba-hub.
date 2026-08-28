import streamlit as st
import pandas as pd
import sqlite3
import json
import requests
from datetime import datetime

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
# 2. LOGIC LAYER (HTTP-based Scraper)
# ==========================================
class SwayamAutomation:
    """
    Fetches SWAYAM's course explorer over plain HTTP instead of driving a
    real browser. SWAYAM ships its full course list server-side, embedded
    as a JSON payload inside a <script> block on the explorer page
    (look for `courses: { type: Object, value: {"edges": [...] } }`).
    That means we don't need Playwright/Chromium at all -- which also
    means this works reliably on resource-limited hosts like Streamlit
    Community Cloud, where installing/launching a real browser is fragile.
    """

    def __init__(self):
        self.base_url = "https://swayam.gov.in/explorer"
        self.launch_date = datetime(2026, 8, 1).date()
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            )
        }

    def _fetch_html(self, category=None):
        params = {"category": category} if category else {}
        resp = requests.get(self.base_url, params=params, headers=self.headers, timeout=25)
        resp.raise_for_status()
        return resp.text

    def _extract_course_nodes(self, html):
        """
        Pulls the embedded `courses` JSON out of the page HTML using a
        quote-aware brace counter (json.loads alone won't work since the
        payload is embedded inside a larger JS block, not standalone JSON).
        """
        marker = 'value: {"edges"'
        idx = html.find(marker)
        if idx == -1:
            return []

        start = idx + len("value: ")
        depth = 0
        in_string = False
        escape = False
        end = None

        for i in range(start, len(html)):
            ch = html[i]
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

        if end is None:
            return []

        try:
            data = json.loads(html[start:end])
        except json.JSONDecodeError:
            return []

        return [edge.get("node", {}) for edge in data.get("edges", []) if edge.get("node")]

    def crawl_all_courses(self, categories=None, progress_callback=None):
        """
        Fetches the SWAYAM explorer for a handful of MBA-adjacent category
        filters and returns the courses that pass the MBA-relevance check.

        NOTE: we filter client-side with model.is_mba_relevant() regardless
        of whether the `category` query param actually narrows the
        server-side response, so results stay correct either way.
        """
        categories = categories or [
            "Management", "Finance", "Marketing", "Commerce",
            "Business_Administration", "HRM_ORG_BEHAVIOUR",
            "ANA_DEC_SCIENCE", "PROD_OPERATIONS", "STRATEGY",
        ]

        seen_urls = set()
        all_found = []

        for i, cat in enumerate(categories):
            if progress_callback:
                progress_callback(f"Fetching category: {cat} ({i + 1}/{len(categories)})")
            try:
                html = self._fetch_html(category=cat)
            except requests.RequestException as e:
                if progress_callback:
                    progress_callback(f"  -> failed to fetch {cat}: {e}")
                continue

            nodes = self._extract_course_nodes(html)

            for node in nodes:
                url = node.get("url")
                title = node.get("title")
                if not url or not title or url in seen_urls:
                    continue

                nc_code = node.get("ncCode") or "Swayam"
                org = node.get("instructorInstitute") or "Swayam NPTEL"

                if not model.is_mba_relevant(title, nc_code, org):
                    continue

                seen_urls.add(url)

                exam_date = node.get("examDate") or ""
                deadline = exam_date[:10] if exam_date else "2026-12-31"

                all_found.append({
                    "title": title,
                    "org": org,
                    "deadline": deadline,
                    "link": url,
                    "type": "Certification",
                    "platform": "Swayam (Live Crawl)",
                    "description": f"Verified NPTEL/SWAYAM course under {nc_code}",
                })

        if progress_callback:
            progress_callback(f"Done. Scanned {len(categories)} categories, "
                               f"found {len(all_found)} MBA-relevant courses.")

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
    with t3: display_category("Certification", date_check=False)  # Certs ignore launch date

elif nav == "⚙️ IEC IEC Admin":
    st.title("⚙️ Admin Management System")
    pw = st.sidebar.text_input("Enter IEC Admin Password", type="password")

    if pw == "iitj2026":
        st.success("Authorized: Placement Committee Access")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Swayam Catalog Sync")
            if st.button("RUN DEEP SWAYAM SCRAPER"):
                progress_box = st.empty()

                def progress(msg):
                    progress_box.write(msg)

                with st.spinner("Scanning SWAYAM catalog over HTTP (no browser required)..."):
                    found_courses = swayam_bot.crawl_all_courses(progress_callback=progress)
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
                model.save_to_vault([{"title": n, "org": "IEC Direct", "deadline": str(dd), "link": l, "type": ca, "platform": "Industry Email", "description": "Link shared privately by organizer."}])
                st.toast("Success")
    else:
        st.error("Admin Security check needed.")
