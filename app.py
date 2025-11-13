import streamlit as st
import pandas as pd
from scraper import scrape_all_sites
from utils import save_to_csv, save_to_pdf

st.set_page_config(page_title="Job Scraper", layout="wide")
st.title("💼 Job Scraper Dashboard")

if st.button("Scrape Jobs Now"):
    with st.spinner("Scraping jobs from multiple sites..."):
        df = scrape_all_sites()
        if not df.empty:
            st.success(f"Scraped {len(df)} jobs successfully!")
            st.dataframe(df)

            csv_file = save_to_csv(df)
            pdf_file = save_to_pdf(df)

            st.download_button("📥 Download CSV", open(csv_file, "rb"), file_name="jobs.csv")
            st.download_button("📄 Download PDF", open(pdf_file, "rb"), file_name="jobs.pdf")
        else:
            st.warning("No jobs found. Try again later.")
else:
    st.info("Click the button above to fetch fresh job data.")
