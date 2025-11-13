import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from scraper import scrape_all_sources, save_jobs_cache, load_jobs_cache

# ADMIN PASSWORD - Change this to your own secret password
ADMIN_PASSWORD = "admin123"  # Change this!

# GitHub RAW URL
GITHUB_RAW_URL = "https://raw.githubusercontent.com/ZainMushtaq9/Kashif-Birthday-wishes/main/job_links.txt"

# Page Configuration
st.set_page_config(
    page_title="JobFinder Pakistan | Find Your Dream Job",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
    .admin-section {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
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
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False
if "show_admin" not in st.session_state:
    st.session_state["show_admin"] = False

# Load jobs from cache
def load_initial_jobs():
    """Load jobs from cache file"""
    if st.session_state["jobs"].empty:
        cached_df = load_jobs_cache()
        if not cached_df.empty:
            st.session_state["jobs"] = cached_df
            if os.path.exists("jobs_cache.csv"):
                cache_time = datetime.fromtimestamp(os.path.getmtime("jobs_cache.csv"))
                st.session_state["last_scrape"] = cache_time.isoformat()

# Load jobs on startup
load_initial_jobs()

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
    st.title("🔍 Search & Filter")
    
    # Admin Access Toggle
    if st.checkbox("🔐 Admin Access", key="admin_toggle"):
        st.session_state["show_admin"] = True
    else:
        st.session_state["show_admin"] = False
        st.session_state["admin_authenticated"] = False
    
    # Admin Section
    if st.session_state["show_admin"]:
        st.markdown("""
        <div class="admin-section">
            <h4 style="margin:0; color:#856404;">👨‍💼 Admin Panel</h4>
        </div>
        """, unsafe_allow_html=True)
        
        if not st.session_state["admin_authenticated"]:
            admin_pass = st.text_input("Enter Admin Password:", type="password", key="admin_password")
            if st.button("🔓 Login", use_container_width=True):
                if admin_pass == ADMIN_PASSWORD:
                    st.session_state["admin_authenticated"] = True
                    st.success("✅ Admin authenticated!")
                    st.rerun()
                else:
                    st.error("❌ Wrong password!")
        else:
            st.success("✅ Logged in as Admin")
            
            # Show cache status
            if os.path.exists("jobs_cache.csv"):
                cache_time = datetime.fromtimestamp(os.path.getmtime("jobs_cache.csv"))
                hours_old = int((datetime.now() - cache_time).total_seconds() / 3600)
                st.info(f"📊 Cache is {hours_old} hours old")
            
            # Update Jobs Button
            if st.button("🔄 Update Jobs Now", use_container_width=True, type="primary"):
                with st.spinner("🔍 Scraping 200+ websites... This will take 10-15 minutes. You can close this and come back later."):
                    try:
                        df = scrape_all_sources(GITHUB_RAW_URL)
                        if not df.empty:
                            save_jobs_cache(df)
                            st.session_state["jobs"] = df
                            st.session_state["last_scrape"] = datetime.now().isoformat()
                            st.success(f"✅ Successfully updated {len(df)} jobs!")
                            st.balloons()
                        else:
                            st.error("❌ No jobs found. Please try again.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            
            st.warning("⚠️ Scraping takes 10-15 minutes. Users can still browse cached jobs during update.")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state["admin_authenticated"] = False
                st.rerun()
            
            st.markdown("---")
    
    # Regular User Search & Filters
    st.markdown("### 🔍 Search Jobs")
    search_query = st.text_input("Keywords", placeholder="e.g., Software Engineer")
    
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
    df = st.session_state["jobs"]
    if not df.empty:
        sources = ["All Sources"] + sorted(df["source"].unique().tolist())
        source_filter = st.selectbox("🌐 Source", sources)
    else:
        source_filter = "All Sources"
    
    st.markdown("---")
    
    # Info
    st.info("💡 **Fresh Jobs Daily**\n\nBrowse thousands of opportunities updated regularly!")
    
    # Download
    if not df.empty:
        st.markdown("---")
        st.markdown("### 📥 Download")
        csv_data = df.to_csv(index=False)
        st.download_button(
            "📄 Download All Jobs",
            csv_data,
            "jobfinder_jobs.csv",
            "text/csv",
            use_container_width=True
        )

# Main Content
df = st.session_state["jobs"]

# First time setup - show admin info
if df.empty:
    st.error("❌ **No jobs in database yet!**")
    st.markdown("""
    ### 🔧 Initial Setup Required
    
    This is your first time running the portal. To populate jobs:
    
    1. Check the **"🔐 Admin Access"** box in the sidebar
    2. Enter admin password: `admin123`
    3. Click **"🔄 Update Jobs Now"**
    4. Wait 10-15 minutes for scraping
    5. Jobs will appear!
    
    **Change the admin password in `app.py` file (line 11) for security!**
    """)
    st.stop()

# Add category column
if "category" not in df.columns:
    def categorize_job(title):
        title = str(title).lower()
        if any(word in title for word in ["engineer", "developer", "programmer", "software", "it"]):
            return "IT & Software"
        elif any(word in title for word in ["manager", "executive", "director", "head", "ceo"]):
            return "Management"
        elif any(word in title for word in ["marketing", "sales", "business"]):
            return "Sales & Marketing"
        elif any(word in title for word in ["accountant", "finance", "audit", "banking"]):
            return "Finance & Accounting"
        elif any(word in title for word in ["teacher", "professor", "education", "lecturer"]):
            return "Education"
        elif any(word in title for word in ["doctor", "nurse", "medical", "health"]):
            return "Healthcare"
        elif any(word in title for word in ["civil", "mechanical", "electrical"]):
            return "Engineering"
        else:
            return "Other"
    
    df["category"] = df["title"].apply(categorize_job)

# Apply filters
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[
        filtered_df["title"].str.contains(search_query, case=False, na=False) |
        filtered_df["company"].str.contains(search_query, case=False, na=False) |
        filtered_df["description"].str.contains(search_query, case=False, na=False)
    ]

if location_filter != "All Locations":
    filtered_df = filtered_df[
        filtered_df["location"].str.contains(location_filter, case=False, na=False)
    ]

if category_filter != "All Categories":
    filtered_df = filtered_df[filtered_df["category"] == category_filter]

if source_filter != "All Sources":
    filtered_df = filtered_df[filtered_df["source"] == source_filter]

# Statistics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="stats-box">
        <h2 style="color: #667eea; margin:0;">{len(filtered_df):,}</h2>
        <p style="margin:0; font-size: 0.9rem;">Available Jobs</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    unique_companies = filtered_df["company"].nunique()
    st.markdown(f"""
    <div class="stats-box">
        <h2 style="color: #764ba2; margin:0;">{unique_companies:,}</h2>
        <p style="margin:0; font-size: 0.9rem;">Companies</p>
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
        update_text = f"{hours_ago}h" if hours_ago < 24 else f"{hours_ago // 24}d"
        st.markdown(f"""
        <div class="stats-box">
            <h2 style="color: #4facfe; margin:0;">{update_text}</h2>
            <p style="margin:0; font-size: 0.9rem;">Last Update</p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Display jobs
if filtered_df.empty:
    st.info("🔍 **No jobs match your filters.**")
    st.markdown("""
    ### 💡 Try:
    - Remove filters
    - Use different keywords
    - Select "All Locations"
    """)
else:
    try:
        filtered_df["posted_date"] = pd.to_datetime(filtered_df["posted_date"])
        filtered_df = filtered_df.sort_values("posted_date", ascending=False)
    except:
        pass
    
    st.subheader(f"📋 {len(filtered_df):,} Jobs Found")
    
    # Pagination
    jobs_per_page = 10
    total_pages = (len(filtered_df) - 1) // jobs_per_page + 1
    
    if "page" not in st.session_state:
        st.session_state["page"] = 1
    
    if total_pages > 1:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            page = st.selectbox(
                "📄 Page",
                range(1, total_pages + 1),
                index=st.session_state["page"] - 1,
                format_func=lambda x: f"Page {x} of {total_pages}"
            )
            st.session_state["page"] = page
    else:
        page = 1
    
    start_idx = (page - 1) * jobs_per_page
    end_idx = start_idx + jobs_per_page
    page_df = filtered_df.iloc[start_idx:end_idx]
    
    for idx, job in page_df.iterrows():
        salary_display = job.get('salary', 'Not specified')
        if salary_display == 'Not specified':
            salary_display = "💰 Salary: Negotiable"
        else:
            salary_display = f"💰 {salary_display}"
        
        category = job.get('category', 'Other')
        
        st.markdown(f"""
        <div class="job-card">
            <div class="job-title">{job['title']}</div>
            <span class="category-badge">{category}</span>
            <div class="job-detail">🏢 <b>{job['company']}</b></div>
            <div class="job-detail">📍 {job['location']}</div>
            <div class="job-detail">{salary_display}</div>
            <div class="job-detail" style="margin-top: 0.8rem;">📝 {str(job['description'])[:250]}...</div>
            <div class="job-detail" style="margin-top: 0.5rem; color: #95a5a6;">
                🌐 {job['source']} | 📅 {job['posted_date']}
            </div>
            <a href="{job['link']}" target="_blank">
                <button class="apply-btn">Apply Now →</button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
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
