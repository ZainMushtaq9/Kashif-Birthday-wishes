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
        cursor: pointer;
    }
    .apply-btn:hover {
        opacity: 0.9;
    }
    .stats-box {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .category-badge {
        display: inline-block;
        background: #e8f4f8;
        color: #2980b9;
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.85rem;
        margin-right: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>💼 JobFinder Pakistan</h1>
    <p>Your Gateway to Thousands of Job Opportunities | Updated Daily</p>
    <p style="font-size: 0.9rem; margin-top: 0.5rem;">🔍 Search • 📍 Filter • 📝 Apply</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if "jobs" not in st.session_state:
    st.session_state["jobs"] = pd.DataFrame()
if "last_scrape" not in st.session_state:
    st.session_state["last_scrape"] = None
if "auto_scrape_running" not in st.session_state:
    st.session_state["auto_scrape_running"] = False

# Function to check if scraping is needed (background process)
def should_auto_scrape():
    """Check if we need to auto-scrape (once daily)"""
    cache_file = "jobs_cache.csv"
    
    if os.path.exists(cache_file):
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        current_time = datetime.now()
        
        # If cache is older than 24 hours
        if current_time - cache_time > timedelta(hours=24):
            return True
    else:
        return True
    
    return False

# Background auto-scraping (only runs once per day automatically)
def auto_scrape_background():
    """Automatically scrape in background if needed"""
    if should_auto_scrape() and not st.session_state["auto_scrape_running"]:
        st.session_state["auto_scrape_running"] = True
        
        with st.spinner("🔄 Updating job listings in background... Please wait."):
            try:
                df = scrape_all_sources(GITHUB_RAW_URL)
                if not df.empty:
                    save_jobs_cache(df)
                    st.session_state["jobs"] = df
                    st.session_state["last_scrape"] = datetime.now().isoformat()
                    st.success("✅ Jobs updated successfully!")
            except Exception as e:
                st.error(f"❌ Update failed: {str(e)}")
            
        st.session_state["auto_scrape_running"] = False

# Sidebar - User Search & Filters ONLY
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("🔍 Search & Filter")
    
    # Search box
    search_query = st.text_input("🔎 Search jobs...", placeholder="e.g., Software Engineer, Manager")
    
    # Filters
    st.markdown("### 📋 Filters")
    
    # Location filter
    locations = ["All Locations", "Karachi", "Lahore", "Islamabad", "Rawalpindi", 
                 "Faisalabad", "Multan", "Peshawar", "Quetta", "Bahawalpur", 
                 "Hyderabad", "Gujranwala", "Sialkot", "Remote"]
    location_filter = st.selectbox("📍 Location", locations)
    
    # Category filter
    categories = ["All Categories", "IT & Software", "Management", "Sales & Marketing",
                  "Finance & Accounting", "Education", "Healthcare", "Engineering", "Other"]
    category_filter = st.selectbox("📂 Category", categories)
    
    # Job source filter
    if not st.session_state["jobs"].empty:
        sources = ["All Sources"] + sorted(st.session_state["jobs"]["source"].unique().tolist())
        source_filter = st.selectbox("🌐 Source Website", sources)
    else:
        source_filter = "All Sources"
    
    # Date filter
    date_options = ["All Time", "Today", "Last 7 Days", "Last 30 Days"]
    date_filter = st.selectbox("📅 Posted Date", date_options)
    
    st.markdown("---")
    
    # Info about updates
    st.info("💡 **Jobs update automatically daily at 12 AM**\n\nNo action needed from you!")
    
    # Download section
    st.markdown("---")
    st.markdown("### 📥 Download")
    
    if not st.session_state["jobs"].empty:
        # Get filtered data for download
        filtered_for_download = st.session_state["jobs"].copy()
        
        if search_query:
            filtered_for_download = filtered_for_download[
                filtered_for_download["title"].str.contains(search_query, case=False, na=False) |
                filtered_for_download["company"].str.contains(search_query, case=False, na=False) |
                filtered_for_download["description"].str.contains(search_query, case=False, na=False)
            ]
        
        if location_filter != "All Locations":
            filtered_for_download = filtered_for_download[
                filtered_for_download["location"].str.contains(location_filter, case=False, na=False)
            ]
        
        csv_data = filtered_for_download.to_csv(index=False)
        st.download_button(
            "📄 Download Results (CSV)",
            csv_data,
            "jobfinder_pakistan_jobs.csv",
            "text/csv",
            use_container_width=True,
            help="Download filtered job results"
        )

# Load jobs on first visit or auto-scrape if needed
if st.session_state["jobs"].empty:
    # Try loading from cache first
    cached_df = load_jobs_cache()
    
    if not cached_df.empty:
        st.session_state["jobs"] = cached_df
        if os.path.exists("jobs_cache.csv"):
            cache_time = datetime.fromtimestamp(os.path.getmtime("jobs_cache.csv"))
            st.session_state["last_scrape"] = cache_time.isoformat()
    else:
        # First time - scrape automatically
        st.info("🔄 Loading jobs for the first time... Please wait 10-15 minutes.")
        auto_scrape_background()

# Check if we need to auto-update (background)
if not st.session_state["jobs"].empty and should_auto_scrape():
    auto_scrape_background()

# Main Content - Display Jobs
df = st.session_state["jobs"]

if df.empty:
    st.warning("⚠️ No jobs available at the moment. Please check back later.")
    st.info("📧 Contact us at support@jobfinder.pk if this issue persists.")
    st.stop()

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

# Category filter (add category column if not exists)
if "category" not in filtered_df.columns:
    def categorize_job(title):
        title = title.lower()
        if any(word in title for word in ["engineer", "developer", "programmer", "software", "it"]):
            return "IT & Software"
        elif any(word in title for word in ["manager", "executive", "director", "head"]):
            return "Management"
        elif any(word in title for word in ["marketing", "sales", "business"]):
            return "Sales & Marketing"
        elif any(word in title for word in ["accountant", "finance", "audit"]):
            return "Finance & Accounting"
        elif any(word in title for word in ["teacher", "professor", "education", "lecturer"]):
            return "Education"
        elif any(word in title for word in ["doctor", "nurse", "medical", "health"]):
            return "Healthcare"
        elif any(word in title for word in ["civil", "mechanical", "electrical"]):
            return "Engineering"
        else:
            return "Other"
    
    filtered_df["category"] = filtered_df["title"].apply(categorize_job)

if category_filter != "All Categories":
    filtered_df = filtered_df[filtered_df["category"] == category_filter]

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

# Statistics Dashboard
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stats-box">
        <h2 style="color: #667eea; margin:0;">{len(filtered_df)}</h2>
        <p style="margin:0; font-size: 0.9rem;">Available Jobs</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    unique_companies = filtered_df["company"].nunique()
    st.markdown(f"""
    <div class="stats-box">
        <h2 style="color: #764ba2; margin:0;">{unique_companies}</h2>
        <p style="margin:0; font-size: 0.9rem;">Companies Hiring</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    unique_locations = filtered_df["location"].nunique()
    st.markdown(f"""
    <div class="stats-box">
        <h2 style="color: #f093fb; margin:0;">{unique_locations}</h2>
        <p style="margin:0; font-size: 0.9rem;">Locations</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if st.session_state["last_scrape"]:
        last_update = datetime.fromisoformat(st.session_state["last_scrape"])
        hours_ago = int((datetime.now() - last_update).total_seconds() / 3600)
        update_text = f"{hours_ago}h ago" if hours_ago < 24 else f"{hours_ago // 24}d ago"
        st.markdown(f"""
        <div class="stats-box">
            <h2 style="color: #4facfe; margin:0;">{update_text}</h2>
            <p style="margin:0; font-size: 0.9rem;">Last Updated</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Display jobs or empty state
if filtered_df.empty:
    st.info("🔍 **No jobs match your search criteria.**")
    st.markdown("""
    ### 💡 Try these tips:
    - Remove some filters
    - Use different keywords
    - Select "All Locations" or "All Categories"
    - Check back later for new listings
    """)
else:
    # Sort by date (newest first)
    try:
        filtered_df["posted_date"] = pd.to_datetime(filtered_df["posted_date"])
        filtered_df = filtered_df.sort_values("posted_date", ascending=False)
    except:
        pass
    
    st.subheader(f"📋 {len(filtered_df)} Jobs Found")
    
    # Pagination
    jobs_per_page = 10
    total_pages = (len(filtered_df) - 1) // jobs_per_page + 1
    
    if "page" not in st.session_state:
        st.session_state["page"] = 1
    
    # Pagination controls at top
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                f"📄 Page",
                range(1, total_pages + 1),
                index=st.session_state["page"] - 1,
                format_func=lambda x: f"Page {x} of {total_pages}"
            )
            st.session_state["page"] = page
    else:
        page = 1
    
    # Display current page jobs
    start_idx = (page - 1) * jobs_per_page
    end_idx = start_idx + jobs_per_page
    page_df = filtered_df.iloc[start_idx:end_idx]
    
    for idx, job in page_df.iterrows():
        # Format salary display
        salary_display = job.get('salary', 'Not specified')
        if salary_display == 'Not specified':
            salary_display = "💰 Salary: Negotiable"
        else:
            salary_display = f"💰 {salary_display}"
        
        # Get category
        category = job.get('category', 'Other')
        
        st.markdown(f"""
        <div class="job-card">
            <div class="job-title">{job['title']}</div>
            <span class="category-badge">{category}</span>
            <div class="job-detail">🏢 <b>{job['company']}</b></div>
            <div class="job-detail">📍 {job['location']}</div>
            <div class="job-detail">{salary_display}</div>
            <div class="job-detail" style="margin-top: 0.8rem;">📝 {job['description'][:250]}...</div>
            <div class="job-detail" style="margin-top: 0.5rem; color: #95a5a6;">
                🌐 Source: {job['source']} | 📅 Posted: {job['posted_date']}
            </div>
            <a href="{job['link']}" target="_blank">
                <button class="apply-btn">Apply Now →</button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # Pagination controls at bottom
    if total_pages > 1:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown(f"<p style='text-align: center;'>Page {page} of {total_pages}</p>", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #7f8c8d; padding: 2rem; background: #f8f9fa; border-radius: 10px;'>
    <h3 style="color: #2c3e50;">🇵🇰 JobFinder Pakistan</h3>
    <p><b>Pakistan's Leading Job Portal</b></p>
    <p style="font-size: 0.95rem; margin: 1rem 0;">
        🎯 200+ Job Sources | 🔄 Daily Updates | 🚀 10,000+ Active Jobs
    </p>
    <p style="font-size: 0.9rem; margin: 1rem 0;">
        📧 <b>Contact:</b> support@jobfinder.pk | 
        💼 <b>For Companies:</b> hr@jobfinder.pk | 
        🌟 <b>Premium Listings:</b> ads@jobfinder.pk
    </p>
    <div style="margin-top: 1.5rem; padding: 1rem; background: white; border-radius: 8px;">
        <p style="font-size: 0.85rem; color: #7f8c8d; margin: 0;">
            <b>For Employers:</b> Post your jobs and reach thousands of qualified candidates.<br>
            Premium packages available starting from PKR 5,000/month.
        </p>
    </div>
    <p style="font-size: 0.8rem; color: #95a5a6; margin-top: 1.5rem;">
        © 2025 JobFinder Pakistan. All Rights Reserved.<br>
        Helping build careers across Pakistan 🚀
    </p>
</div>
""", unsafe_allow_html=True)
