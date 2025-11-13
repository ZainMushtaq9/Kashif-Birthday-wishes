import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from scraper import scrape_all_sources, save_jobs_cache, load_jobs_cache

# GitHub RAW URL - Update this with your actual GitHub username and repo name
GITHUB_RAW_URL = "https://raw.githubusercontent.com/ZainMushtaq9/Kashif-Birthday-wishes/main/job_links.txt"

# Page Configuration
st.set_page_config(
    page_title="JobFinder Pakistan | Find Your Dream Job",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
    }
    .job-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .job-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
    }
    .job-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    .job-detail {
        color: #7f8c8d;
        font-size: 0.9rem;
        margin: 0.3rem 0;
    }
    .apply-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 5px;
        font-weight: bold;
        text-decoration: none;
        display: inline-block;
        margin-top: 0.5rem;
    }
    .stats-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>💼 JobFinder Pakistan</h1>
    <p>Your Gateway to Thousands of Job Opportunities | Updated Daily at 12 AM</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "jobs" not in st.session_state:
    st.session_state["jobs"] = pd.DataFrame()
if "last_scrape" not in st.session_state:
    st.session_state["last_scrape"] = None

# Auto-scrape check (runs at 12 AM daily)
def check_and_auto_scrape():
    """Check if we need to auto-scrape (once daily at midnight)"""
    cache_file = "jobs_cache.csv"
    
    # Check if cache exists and get its modification time
    if os.path.exists(cache_file):
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        current_time = datetime.now()
        
        # If cache is older than 24 hours OR it's past midnight and we haven't scraped today
        if (current_time - cache_time > timedelta(hours=24)) or \
           (current_time.hour == 0 and cache_time.date() < current_time.date()):
            return True
    else:
        return True
    
    return False

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("🔍 Search & Filter")
    
    # Search box
    search_query = st.text_input("🔎 Search jobs...", placeholder="e.g., Software Engineer")
    
    # Filters
    st.subheader("Filters")
    
    # Location filter
    locations = ["All Locations", "Karachi", "Lahore", "Islamabad", "Rawalpindi", 
                 "Faisalabad", "Multan", "Peshawar", "Quetta", "Bahawalpur", "Remote"]
    location_filter = st.selectbox("📍 Location", locations)
    
    # Job source filter
    if not st.session_state["jobs"].empty:
        sources = ["All Sources"] + sorted(st.session_state["jobs"]["source"].unique().tolist())
        source_filter = st.selectbox("🌐 Source", sources)
    else:
        source_filter = "All Sources"
    
    # Date filter
    date_options = ["All Time", "Today", "Last 7 Days", "Last 30 Days"]
    date_filter = st.selectbox("📅 Posted", date_options)
    
    st.markdown("---")
    
    # Manual refresh button
    if st.button("🔄 Refresh Jobs Now", use_container_width=True):
        with st.spinner("🔍 Fetching latest jobs from 200+ websites... This may take 5-10 minutes."):
            df = scrape_all_sources(GITHUB_RAW_URL)
            if not df.empty:
                save_jobs_cache(df)
                st.session_state["jobs"] = df
                st.session_state["last_scrape"] = datetime.now().isoformat()
                st.success(f"✅ Successfully loaded {len(df)} fresh jobs!")
                st.rerun()
            else:
                st.error("❌ No jobs found. Please check your internet connection.")
    
    st.info("💡 Jobs auto-update daily at 12 AM. Click 'Refresh' to update manually.")
    
    # Download options
    st.markdown("---")
    st.subheader("📥 Download Results")
    
    if not st.session_state["jobs"].empty:
        csv_data = st.session_state["jobs"].to_csv(index=False)
        st.download_button(
            "📄 Download CSV",
            csv_data,
            "jobfinder_pakistan_jobs.csv",
            "text/csv",
            use_container_width=True
        )

# Main content - Auto-load jobs
if st.session_state["jobs"].empty:
    # Try loading from cache first
    cached_df = load_jobs_cache()
    
    if not cached_df.empty:
        st.session_state["jobs"] = cached_df
        cache_time = datetime.fromtimestamp(os.path.getmtime("jobs_cache.csv"))
        st.session_state["last_scrape"] = cache_time.isoformat()
        
        # Check if we need to auto-scrape
        if check_and_auto_scrape():
            st.info("🔄 Jobs are being updated in the background. Showing cached results for now.")
    else:
        # No cache exists - first time setup
        st.warning("⚠️ No cached jobs found. This is your first time using the portal!")
        
        if st.button("🚀 Start Scraping Jobs", type="primary"):
            with st.spinner("🔍 Scraping jobs from 200+ websites for the first time... This will take 10-15 minutes."):
                df = scrape_all_sources(GITHUB_RAW_URL)
                if not df.empty:
                    save_jobs_cache(df)
                    st.session_state["jobs"] = df
                    st.session_state["last_scrape"] = datetime.now().isoformat()
                    st.success(f"✅ Successfully loaded {len(df)} jobs!")
                    st.rerun()
                else:
                    st.error("❌ Could not fetch jobs. Please try again later.")
        
        st.info("👆 Click the button above to start loading jobs from 200+ websites!")
        st.stop()

# Display jobs
df = st.session_state["jobs"]

if df.empty:
    st.warning("⚠️ No jobs available. Please click 'Refresh Jobs Now' in the sidebar.")
else:
    # Apply filters
    filtered_df = df.copy()
    
    # Search filter
    if search_query:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_query, case=False, na=False) |
            filtered_df["company"].str.contains(search_query, case=False, na=False) |
            filtered_df["description"].str.contains(search_query, case=False, na=False)
        ]
    
    # Location filter
    if location_filter != "All Locations":
        filtered_df = filtered_df[
            filtered_df["location"].str.contains(location_filter, case=False, na=False)
        ]
    
    # Source filter
    if source_filter != "All Sources":
        filtered_df = filtered_df[filtered_df["source"] == source_filter]
    
    # Date filter
    if date_filter != "All Time":
        try:
            filtered_df["posted_date"] = pd.to_datetime(filtered_df["posted_date"])
            today = datetime.now()
            
            if date_filter == "Today":
                filtered_df = filtered_df[filtered_df["posted_date"].dt.date == today.date()]
            elif date_filter == "Last 7 Days":
                week_ago = today - timedelta(days=7)
                filtered_df = filtered_df[filtered_df["posted_date"] >= week_ago]
            elif date_filter == "Last 30 Days":
                month_ago = today - timedelta(days=30)
                filtered_df = filtered_df[filtered_df["posted_date"] >= month_ago]
        except:
            pass
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-box">
            <h2 style="color: #667eea; margin:0;">{len(filtered_df)}</h2>
            <p style="margin:0;">Total Jobs</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        unique_companies = filtered_df["company"].nunique()
        st.markdown(f"""
        <div class="stats-box">
            <h2 style="color: #764ba2; margin:0;">{unique_companies}</h2>
            <p style="margin:0;">Companies</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        unique_locations = filtered_df["location"].nunique()
        st.markdown(f"""
        <div class="stats-box">
            <h2 style="color: #f093fb; margin:0;">{unique_locations}</h2>
            <p style="margin:0;">Locations</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if st.session_state["last_scrape"]:
            last_update = datetime.fromisoformat(st.session_state["last_scrape"])
            hours_ago = int((datetime.now() - last_update).total_seconds() / 3600)
            st.markdown(f"""
            <div class="stats-box">
                <h2 style="color: #4facfe; margin:0;">{hours_ago}h</h2>
                <p style="margin:0;">Last Update</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display jobs
    if filtered_df.empty:
        st.info("🔍 No jobs match your filters. Try adjusting your search criteria.")
    else:
        st.subheader(f"📋 Showing {len(filtered_df)} Jobs")
        
        # Pagination
        jobs_per_page = 10
        total_pages = (len(filtered_df) - 1) // jobs_per_page + 1
        
        if "page" not in st.session_state:
            st.session_state["page"] = 1
        
        # Pagination controls
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                f"Page (Total: {total_pages})",
                range(1, total_pages + 1),
                index=st.session_state["page"] - 1
            )
            st.session_state["page"] = page
        
        # Display current page jobs
        start_idx = (page - 1) * jobs_per_page
        end_idx = start_idx + jobs_per_page
        page_df = filtered_df.iloc[start_idx:end_idx]
        
        for _, job in page_df.iterrows():
            st.markdown(f"""
            <div class="job-card">
                <div class="job-title">{job['title']}</div>
                <div class="job-detail">🏢 <b>{job['company']}</b></div>
                <div class="job-detail">📍 {job['location']}</div>
                <div class="job-detail">💰 {job['salary']}</div>
                <div class="job-detail">📝 {job['description'][:200]}...</div>
                <div class="job-detail">🌐 Source: {job['source']}</div>
                <div class="job-detail">📅 Posted: {job['posted_date']}</div>
                <a href="{job['link']}" target="_blank" class="apply-btn">Apply Now →</a>
            </div>
            """, unsafe_allow_html=True)

# Footer with monetization
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
    <h3 style="color: #2c3e50;">JobFinder Pakistan</h3>
    <p><b>🎯 Premium Job Portal</b> | 200+ Job Sources | Daily Updates</p>
    <p>© 2025 All Rights Reserved | Automated Daily Scraping at 12:00 AM</p>
    <p style="font-size: 0.9rem;">
        📧 Contact: support@jobfinder.pk | 
        💼 Advertise: ads@jobfinder.pk | 
        🌟 Premium Listings Available
    </p>
    <p style="font-size: 0.8rem; color: #95a5a6; margin-top: 1rem;">
        Helping job seekers find their dream careers in Pakistan 🇵🇰
    </p>
</div>
""", unsafe_allow_html=True)
