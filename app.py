import streamlit as st
import pandas as pd
import sqlite3
from scanner import init_db, add_opportunity
import PyPDF2

st.set_page_config(page_title="IITJ MBA Opportunity Hub", layout="wide")
init_db()

# --- SIDEBAR: Add New Data (For Admin/Committee) ---
st.sidebar.header("Admin: Add Opportunity")
with st.sidebar.form("add_form"):
    t = st.text_input("Title")
    o = st.text_input("Organizer")
    d = st.date_input("Deadline")
    l = st.text_input("Link")
    cat = st.selectbox("Category", ["Case Comp", "Live Project", "Fellowship"])
    desc = st.text_area("Eligibility Description")
    if st.form_submit_button("Add to Database"):
        add_opportunity(t, o, str(d), l, desc, cat)
        st.success("Added!")

# --- MAIN PAGE ---
st.title("🎓 IIT Jodhpur MBA Opportunity Hub")

tab1, tab2, tab3 = st.tabs(["✅ Eligible Opps", "❌ Not Eligible", "📄 Resume Matcher"])

def get_data(status):
    conn = sqlite3.connect('opportunities.db')
    df = pd.read_sql_query(f"SELECT * FROM opps WHERE status = '{status}'", conn)
    conn.close()
    return df

with tab1:
    st.subheader("Opportunities you can apply to today")
    df_eligible = get_data("Eligible")
    if not df_eligible.empty:
        for _, row in df_eligible.iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                col1.markdown(f"### [{row['title']}]({row['link']})")
                col1.write(f"**{row['org']}** | Category: {row['category']}")
                col2.error(f"Deadline: {row['deadline']}")
                st.divider()
    else:
        st.info("No eligible opportunities found yet.")

with tab2:
    st.subheader("Filtered Out (Not for IITJ MBA)")
    df_not = get_data("Not Eligible")
    st.table(df_not[['title', 'org', 'deadline']])

with tab3:
    st.subheader("Personalized Career Guidance")
    uploaded_file = st.file_uploader("Upload your Resume (PDF)", type="pdf")
    
    if uploaded_file:
        # Extract text from PDF
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
            
        st.success("Resume parsed successfully!")
        
        # In a real app, you'd send 'text' to OpenAI here
        st.info("Top Matches based on your profile:")
        st.write("1. **Consulting Case Comp:** Your experience in 'Operations' fits the 'Supply Chain' track.")
        st.write("2. **Live Project (Marketing):** Matches your 'Digital Marketing' certification.")
        
        st.warning("Gap Analysis: You are missing a 'Product Management' certification. Try the 'Google PM Certificate' to unlock 4 more opportunities.")
