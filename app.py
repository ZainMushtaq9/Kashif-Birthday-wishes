import streamlit as st
import pandas as pd
from scraper import scrape_from_github
from utils import search_jobs

# 🔗 GitHub raw link to your job_links.txt
GITHUB_RAW_URL = "https://raw.githubusercontent.com/<YOUR_USERNAME>/<YOUR_REPO>/main/job_links.txt"

st.set_page_config(page_title="JobFinder Portal", layout="wide")

st.markdown("""
    <h1 style='text-align:center; color:#2c3e50;'>💼 JobFinder Portal</h1>
    <p style='text-align:center;'>Search jobs from multiple websites (auto-loaded from GitHub).</p>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("🔍 Search & Fetch")
query = st.sidebar.text_input("Search Job Title or Company")
fetch_now = st.sidebar.button("Fetch Latest Jobs")

# Data Load / Scraping
if fetch_now:
    with st.spinner("Fetching job sites from GitHub and scraping listings..."):
        df = scrape_from_github(GITHUB_RAW_URL)
        st.session_state["jobs"] = df
        st.success(f"✅ Scraped {len(df)} jobs successfully!")
else:
    df = st.session_state.get("jobs", pd.DataFrame())

# Display
if df.empty:
    st.info("No jobs loaded yet. Click 'Fetch Latest Jobs' to start scraping.")
else:
    filtered = search_jobs(df, query)
    st.subheader(f"Showing {len(filtered)} Job Results")

    for _, row in filtered.iterrows():
        st.markdown(f"""
        <div style='border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;'>
            <h4 style='margin:0;'>{row['title']}</h4>
            <p><b>Company:</b> {row['company']}</p>
            <a href="{row['link']}" target="_blank">
                <button style='background-color:#4CAF50; color:white; border:none; padding:8px 16px; border-radius:5px; cursor:pointer;'>
                    Apply Now
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
