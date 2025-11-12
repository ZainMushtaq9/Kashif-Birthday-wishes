import streamlit as st
import google.generativeai as genai
import json
import re
import uuid
import requests
from datetime import datetime
from bs4 import BeautifulSoup

# --- Configuration ---
PAGE_TITLE = "Pak Job Finder"
PAGE_ICON = "🇵🇰"

# --- Page Setup ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="wide")

st.title(f"{PAGE_ICON} Pak Job Finder")
st.markdown("Your AI-powered guide to jobs in Pakistan and beyond.")

# --- Gemini API Key Management ---
if "api_key" not in st.session_state:
    st.session_state.api_key = ""

if not st.session_state.api_key:
    try:
        # Try to get from st.secrets (for deployment)
        st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
    except (KeyError, AttributeError):
        # Fallback to sidebar input
        with st.sidebar:
            st.warning("Please add your Gemini API Key to proceed.")
            st.session_state.api_key = st.text_input("Enter your Gemini API Key:", type="password", key="api_key_input")

if st.session_state.api_key:
    try:
        genai.configure(api_key=st.session_state.api_key)
    except Exception as e:
        st.error(f"Failed to configure Gemini API: {e}")
        st.stop()
else:
    st.info("Please enter your Gemini API Key in the sidebar to enable AI features.")
    if 'page' not in st.session_state or st.session_state.page != "View Job Sources":
        st.stop()


# --- Utility Functions ---

def safe_html(html_content):
    """Render HTML content safely in Streamlit."""
    if not html_content:
        return
    soup = BeautifulSoup(html_content, 'html.parser')
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
    st.markdown(soup.prettify(), unsafe_allow_html=True)

def get_gemini_response(prompt_text, job_context=None, is_json=False):
    """Calls the Gemini API to get a response."""
    if not st.session_state.api_key:
        return "Please provide a Gemini API Key to use this feature."
    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        full_prompt = f"{prompt_text}\n\nHere is the full list of available jobs:\n{job_context}" if job_context else prompt_text
        generation_config = {"response_mime_type": "application/json"} if is_json else {}
        response = model.generate_content(full_prompt, generation_config=generation_config)
        return response.text
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return f"Error: Could not get response from AI. {e}"

def clean_text(text):
    """Basic text cleaning for search."""
    if not text:
        return ""
    return text.lower().strip()

def create_search_text(job):
    """Creates a single searchable string from job details."""
    return (
        f"{clean_text(job.get('title'))} "
        f"{clean_text(job.get('organization'))} "
        f"{clean_text(job.get('description'))}"
    )

# --- Data Loading Functions ---

def get_mock_jobs():
    """Returns a list of mock jobs for demonstration."""
    mock_data = [
        {
            "id": "mock-1", "title": "Senior Python Developer", "organization": "Techlogix", 
            "location": "Lahore", "category": "IT", "source": "rozee.pk (Mock)",
            "url": "https://www.rozee.pk", "posted_date": "2025-11-10",
            "description": "<h3>Job Description</h3><p>We are looking for a Senior Python Developer with 5+ years of experience in Django and Flask. Must know data structures and algorithms.</p><ul><li>5+ years Python</li><li>Experience with AWS</li><li>Good communication skills</li></ul>"
        },
        {
            "id": "mock-2", "title": "Section Officer (BPS-17)", "organization": "Federal Public Service Commission", 
            "location": "Islamabad", "category": "Government", "source": "fpsc.gov.pk (Mock)",
            "url": "https://www.fpsc.gov.pk", "posted_date": "2025-11-08",
            "description": "<h3>Official Job Posting</h3><p>The FPSC invites applications for the post of Section Officer (BPS-17). Candidates must hold a Master's Degree (Second Class) and pass the CSS examination.</p>"
        },
        {
            "id": "mock-3", "title": "Marketing Manager", "organization": "Packages Limited", 
            "location": "Karachi", "category": "Marketing", "source": "dawn.com (Mock)",
            "url": "https://www.dawn.com/jobs", "posted_date": "2025-11-09",
            "description": "<p>Seeking an experienced Marketing Manager to lead our branding efforts in the southern region. MBA required.</p>"
        },
        {
            "id": "mock-4", "title": "Frontend Developer (React)", "organization": "Systems Limited", 
            "location": "Remote", "category": "IT", "source": "jobz.pk (Mock)",
            "url": "https://www.jobz.pk", "posted_date": "2025-11-11",
            "description": "<p>Join our remote team! We need a React developer with 2+ years of experience with Next.js and Tailwind CSS.</p>"
        },
        {
            "id": "mock-5", "title": "Civil Engineer", "organization": "NESPAK", 
            "location": "Lahore", "category": "Engineering", "source": "rozee.pk (Mock)",
            "url": "https://www.rozee.pk", "posted_date": "2025-11-07",
            "description": "<p>NESPAK requires a Civil Engineer for its Water Resources division. Must be registered with PEC.</p>"
        },
        {
            "id": "mock-6", "title": "Content Writer", "organization": "Express News", 
            "location": "Remote", "category": "Media", "source": "jang.com.pk (Mock)",
            "url": "https://www.jang.com.pk/jobs", "posted_date": "2025-11-10",
            "description": "<p>Urdu content writer needed for our digital platform. Must have excellent command of Urdu and knowledge of current affairs.</p>"
        },
        {
            "id": "mock-7", "title": "Data Scientist", "organization": "Afiniti", 
            "location": "Karachi", "category": "IT", "source": "linkedin.com (Mock)",
            "url": "https://pk.linkedin.com/jobs", "posted_date": "2025-11-12",
            "description": "<p>AI and Machine Learning expert wanted. PhD or Master's in Computer Science preferred. Strong Python & R skills.</p>"
        },
        {
            "id": "mock-8", "title": "Accountant", "organization": "Fauji Foundation", 
            "location": "Rawalpindi", "category": "Finance", "source": "fpsc.gov.pk (Mock)",
            "url": "https://www.fpsc.gov.pk", "posted_date": "2025-11-05",
            "description": "<p>ACCA/CMA qualified accountant with 3 years of experience in financial reporting and auditing.</p>"
        }
    ]
    for job in mock_data:
        job['search_text'] = create_search_text(job)
    return mock_data

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_real_jobs_bs4_rozee():
    """Scrapes Rozee.pk using Requests and BS4. Returns a dict."""
    URL = "https://www.rozee.pk/search-jobs-in-pakistan"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
    
    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        job_cards = soup.select("div.job.job-c")
        
        if not job_cards:
            return {'status': 'error', 'message': "No job cards found on Rozee.pk. The website's HTML structure may have changed."}

        jobs_list = []
        for card in job_cards[:20]: # Limit to 20 jobs
            title = card.select_one("h2 a")
            org = card.select_one("div.c-name")
            loc = card.select_one("div.j-loc")
            
            if title and org and loc:
                job_url = title.get('href')
                if not job_url.startswith('http'):
                    job_url = "https://www.rozee.pk" + job_url
                
                job = {
                    "id": str(uuid.uuid4()),
                    "title": title.text.strip(),
                    "organization": org.text.strip(),
                    "location": loc.text.strip(),
                    "category": "IT", # Placeholder, would need to visit details page
                    "source": "rozee.pk (Live)",
                    "url": job_url,
                    "posted_date": card.select_one(".j-posted").text.strip() if card.select_one(".j-posted") else "N/A",
                    "description": f"<p>Description only available on the website. <a href='{job_url}' target='_blank'>Click here to view</a></p>"
                }
                job['search_text'] = create_search_text(job)
                jobs_list.append(job)
        
        if not jobs_list:
            return {'status': 'error', 'message': "Found job cards but could not parse them. Selectors may be outdated."}
            
        return {'status': 'success', 'jobs': jobs_list}

    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f"Error fetching data from Rozee.pk: {e}"}

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_real_jobs_bs4_jobz():
    """Scrapes Jobz.pk using Requests and BS4. Returns a dict."""
    URL = "https://www.jobz.pk/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        job_cards = soup.select("div.job-list-default")
        
        if not job_cards:
            return {'status': 'error', 'message': "No job cards found on Jobz.pk. The website's HTML structure may have changed."}

        jobs_list = []
        for card in job_cards[:20]: # Limit to 20 jobs
            title_element = card.select_one("h4.job-title a")
            org_element = card.select_one("span.job-company a")
            loc_element = card.select_one("span.job-location")

            if title_element and org_element and loc_element:
                job_url = title_element.get('href')
                if not job_url.startswith('http'):
                    job_url = "https://www.jobz.pk" + job_url
                
                job = {
                    "id": str(uuid.uuid4()),
                    "title": title_element.text.strip(),
                    "organization": org_element.text.strip(),
                    "location": loc_element.text.strip(),
                    "category": "General", # Placeholder
                    "source": "jobz.pk (Live)",
                    "url": job_url,
                    "posted_date": "N/A", # Not easily visible on list page
                    "description": f"<p>Description only available on the website. <a href='{job_url}' target='_blank'>Click here to view</a></p>"
                }
                job['search_text'] = create_search_text(job)
                jobs_list.append(job)
        
        if not jobs_list:
            return {'status': 'error', 'message': "Found job cards but could not parse them. Selectors may be outdated."}

        return {'status': 'success', 'jobs': jobs_list}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f"Error fetching data from Jobz.pk: {e}"}

@st.cache_data(ttl=3600)
def get_real_jobs_bs4_dawn():
    """Scrapes Dawn.com/jobs using Requests and BS4. Returns a dict."""
    URL = "https://www.dawn.com/jobs"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}

    try:
        response = requests.get(URL, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        job_cards = soup.select("article.job")
        
        if not job_cards:
            return {'status': 'error', 'message': "No job cards found on Dawn.com/jobs. The website's HTML structure may have changed."}

        jobs_list = []
        for card in job_cards[:20]: # Limit to 20 jobs
            title_element = card.select_one("h2.job__title a")
            org_element = card.select_one("span.job__company")
            loc_element = card.select_one("span.job__location")
            cat_element = card.select_one("span.job__sector")

            if title_element and org_element and loc_element:
                job_url = title_element.get('href')
                
                job = {
                    "id": str(uuid.uuid4()),
                    "title": title_element.text.strip(),
                    "organization": org_element.text.strip(),
                    "location": loc_element.text.strip(),
                    "category": cat_element.text.strip() if cat_element else "General",
                    "source": "dawn.com (Live)",
                    "url": job_url,
                    "posted_date": card.select_one("span.job__date").text.strip() if card.select_one("span.job__date") else "N/A",
                    "description": f"<p>Description only available on the website. <a href='{job_url}' target='_blank'>Click here to view</a></p>"
                }
                job['search_text'] = create_search_text(job)
                jobs_list.append(job)
        
        if not jobs_list:
            return {'status': 'error', 'message': "Found job cards but could not parse them. Selectors may be outdated."}

        return {'status': 'success', 'jobs': jobs_list}
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f"Error fetching data from Dawn.com/jobs: {e}"}


# --- Main App Logic ---

# Initialize session state variables
if "jobs" not in st.session_state:
    st.session_state.jobs = get_mock_jobs()
    st.session_state.last_updated = "Mock Data Loaded"
    
if "page" not in st.session_state:
    st.session_state.page = "List"
    
if "selected_job_id" not in st.session_state:
    st.session_state.selected_job_id = None
    
if "saved_jobs" not in st.session_state:
    st.session_state.saved_jobs = {} # Store as a dict for quick lookup: {id: job_data}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Welcome! Ask me to find jobs, e.g., 'Find me IT jobs in Karachi' or 'Are there any remote developer jobs?'"}
    ]

# --- Page Navigation ---

def set_page(page_name, job_id=None):
    st.session_state.page = page_name
    if job_id:
        st.session_state.selected_job_id = job_id

# --- Sidebar ---
with st.sidebar:
    st.button("🏠 Home (Job Listings)", on_click=set_page, args=("List",), use_container_width=True, type="primary" if st.session_state.page == "List" else "secondary")
    
    saved_count = len(st.session_state.saved_jobs)
    st.button(f"❤️ Saved Jobs ({saved_count})", on_click=set_page, args=("Saved",), use_container_width=True, type="primary" if st.session_state.page == "Saved" else "secondary")
    
    st.button("🤖 AI Job Assistant", on_click=set_page, args=("Chat",), use_container_width=True, type="primary" if st.session_state.page == "Chat" else "secondary")

    st.button("📜 View Job Sources", on_click=set_page, args=("View Job Sources",), use_container_width=True, type="primary" if st.session_state.page == "View Job Sources" else "secondary")

    st.divider()
    
    # --- Filters (Only show on List page) ---
    if st.session_state.page == "List" and st.session_state.jobs:
        st.header("🔍 Filter Jobs")
        
        # Get unique values for filters
        all_locations = sorted(list(set(j.get('location', 'N/A') for j in st.session_state.jobs if j.get('location'))))
        all_categories = sorted(list(set(j.get('category', 'N/A') for j in st.session_state.jobs if j.get('category'))))
        all_sources = sorted(list(set(j.get('source', 'N/A') for j in st.session_state.jobs if j.get('source'))))

        # Session state for filters
        if "filters" not in st.session_state:
            st.session_state.filters = {
                "keyword": "",
                "location": "All",
                "category": "All",
                "source": "All"
            }

        st.session_state.filters["keyword"] = st.text_input("Search by Keyword", st.session_state.filters["keyword"])
        st.session_state.filters["location"] = st.selectbox("Location", ["All"] + all_locations, index=all_locations.index(st.session_state.filters["location"]) + 1 if st.session_state.filters["location"] in all_locations else 0)
        st.session_state.filters["category"] = st.selectbox("Category", ["All"] + all_categories, index=all_categories.index(st.session_state.filters["category"]) + 1 if st.session_state.filters["category"] in all_categories else 0)
        st.session_state.filters["source"] = st.selectbox("Source", ["All"] + all_sources, index=all_sources.index(st.session_state.filters["source"]) + 1 if st.session_state.filters["source"] in all_sources else 0)

    st.divider()
    st.caption(f"Job data last updated:\n{st.session_state.last_updated}")


# --- Page: Job Listings (Home) ---
if st.session_state.page == "List":
    
    st.subheader("Live Data Scrapers")
    st.markdown("Load mock data or run a live (slow) scrape. Live data will replace the current job list.")
    
    c1, c2, c3, c4 = st.columns(4)
    
    if c1.button("Load Mock Data", use_container_width=True):
        st.session_state.jobs = get_mock_jobs()
        st.session_state.last_updated = "Mock Data Loaded"
        st.toast("Loaded mock data!", icon="🎉")
        st.rerun()

    if c2.button("Live Scrape: Rozee.pk", use_container_width=True):
        with st.spinner("Scraping Rozee.pk... This may take a moment."):
            result = get_real_jobs_bs4_rozee()
        if result['status'] == 'success':
            st.session_state.jobs = result['jobs']
            st.session_state.last_updated = datetime.now().strftime('%Y-%m-%d %I:%M %p')
            st.toast(f"Success! Found {len(result['jobs'])} jobs from Rozee.pk", icon="🚀")
            st.rerun()
        else:
            st.error(f"Scrape Failed: {result['message']}")

    if c3.button("Live Scrape: Jobz.pk", use_container_width=True):
        with st.spinner("Scraping Jobz.pk... This may take a moment."):
            result = get_real_jobs_bs4_jobz()
        if result['status'] == 'success':
            st.session_state.jobs = result['jobs']
            st.session_state.last_updated = datetime.now().strftime('%Y-%m-%d %I:%M %p')
            st.toast(f"Success! Found {len(result['jobs'])} jobs from Jobz.pk", icon="🚀")
            st.rerun()
        else:
            st.error(f"Scrape Failed: {result['message']}")
            
    if c4.button("Live Scrape: Dawn.com", use_container_width=True):
        with st.spinner("Scraping Dawn.com/jobs... This may take a moment."):
            result = get_real_jobs_bs4_dawn()
        if result['status'] == 'success':
            st.session_state.jobs = result['jobs']
            st.session_state.last_updated = datetime.now().strftime('%Y-%m-%d %I:%M %p')
            st.toast(f"Success! Found {len(result['jobs'])} jobs from Dawn.com", icon="🚀")
            st.rerun()
        else:
            st.error(f"Scrape Failed: {result['message']}")

    st.divider()

    # Apply filters
    filtered_jobs = st.session_state.jobs
    f = st.session_state.filters
    if f["keyword"]:
        filtered_jobs = [j for j in filtered_jobs if f["keyword"].lower() in j.get('search_text', '')]
    if f["location"] != "All":
        filtered_jobs = [j for j in filtered_jobs if j.get('location') == f["location"]]
    if f["category"] != "All":
        filtered_jobs = [j for j in filtered_jobs if j.get('category') == f["category"]]
    if f["source"] != "All":
        filtered_jobs = [j for j in filtered_jobs if j.get('source') == f["source"]]

    # Display results
    st.subheader(f"Showing {len(filtered_jobs)} of {len(st.session_state.jobs)} jobs")
    
    cols = st.columns([3, 1, 1, 1])
    cols[0].markdown("**Job Title**")
    cols[1].markdown("**Organization**")
    cols[2].markdown("**Location**")
    cols[3].markdown("**Source**")
        
    st.divider()

    if not filtered_jobs:
        st.warning("No jobs match your filter criteria.")

    for job in filtered_jobs:
        cols = st.columns([3, 1, 1, 1])
        is_saved = job.get('id') in st.session_state.saved_jobs
        
        title_display = f"❤️ {job.get('title')}" if is_saved else job.get('title')
        cols[0].button(title_display, on_click=set_page, args=("Detail", job.get('id')), key=f"title_{job.get('id')}", use_container_width=True)
        cols[1].markdown(job.get('organization', 'N/A'))
        cols[2].markdown(job.get('location', 'N/A'))
        cols[3].markdown(job.get('source', 'N/A'))


# --- Page: Job Detail ---
elif st.session_state.page == "Detail":
    
    # Find the selected job
    job = next((j for j in st.session_state.jobs if j.get('id') == st.session_state.selected_job_id), None)
    
    if not job:
        st.error("Job not found or ID is missing.")
        st.button("← Back to list", on_click=set_page, args=("List",))
    else:
        st.button("← Back to list", on_click=set_page, args=("List",))
        
        st.header(job.get('title', 'No Title'))
        st.subheader(job.get('organization', 'No Organization'))
        
        # Save/Unsave button
        job_id = job.get('id')
        if job_id in st.session_state.saved_jobs:
            if st.button("❤️ Unsave Job", use_container_width=True, type="primary"):
                del st.session_state.saved_jobs[job_id]
                st.rerun()
        else:
            if st.button("Save Job", use_container_width=True):
                st.session_state.saved_jobs[job_id] = job
                st.rerun()

        st.link_button("🚀 Apply Now (External Link)", job.get('url', '#'), use_container_width=True)
        st.divider()

        # Job Info
        info_cols = st.columns(3)
        info_cols[0].markdown(f"**Location:**\n\n{job.get('location', 'N/A')}")
        info_cols[1].markdown(f"**Category:**\n\n{job.get('category', 'N/A')}")
        info_cols[2].markdown(f"**Source:**\n\n{job.get('source', 'N/A')}")
        info_cols[2].markdown(f"**Posted:**\n\n{job.get('posted_date', 'N/A')}")
        st.divider()

        # AI Summary
        st.subheader("🤖 AI Summary")
        if "summary_cache" not in st.session_state:
            st.session_state.summary_cache = {}
        summary_key = f"summary_{job_id}"

        if summary_key not in st.session_state.summary_cache:
            if st.button("Generate AI Summary", key="gen_summary", use_container_width=True):
                with st.spinner("Summarizing job description with Gemini..."):
                    desc_soup = BeautifulSoup(job.get('description', ''), 'html.parser')
                    clean_desc = desc_soup.get_text(separator=" ").strip()
                    prompt = f"""
                    Please summarize the following job description in 3-5 bullet points.
                    Focus on:
                    1. The core role/responsibility.
                    2. Key qualifications or required skills (e.g., '5+ years Java', 'Master's Degree').
                    3. Any mentioned benefits or salary.
                    Here is the job description:
                    ---
                    {clean_desc}
                    ---
                    """
                    summary = get_gemini_response(prompt)
                    st.session_state.summary_cache[summary_key] = summary
                    st.rerun()
        else:
            st.markdown(st.session_state.summary_cache[summary_key])
            if st.button("Regenerate Summary", key="regen_summary", use_container_width=True):
                # This button will clear the cache and rerun, triggering the 'if' block above
                st.session_state.summary_cache.pop(summary_key, None)
                st.rerun()

        st.divider()
        st.subheader("Full Job Description")
        safe_html(job.get('description', 'No description provided.'))


# --- Page: Saved Jobs ---
elif st.session_state.page == "Saved":
    st.header(f"❤️ My Saved Jobs ({len(st.session_state.saved_jobs)})")
    
    if not st.session_state.saved_jobs:
        st.info("You haven't saved any jobs yet. Click 'Save Job' on a job's detail page.")
    else:
        st.divider()
        for job_id, job in st.session_state.saved_jobs.items():
            cols = st.columns([3, 2, 1])
            cols[0].button(job.get('title'), on_click=set_page, args=("Detail", job_id), key=f"saved_{job_id}", use_container_width=True)
            cols[1].markdown(job.get('organization', 'N/A'))
            cols[2].markdown(job.get('location', 'N/A'))


# --- Page: AI Chatbot ---
elif st.session_state.page == "Chat":
    st.header("🤖 AI Job Assistant")
    st.markdown("Ask me to find jobs from the current listings.")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("e.g., 'Find me engineering jobs in Karachi'"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                if not st.session_state.jobs:
                    st.warning("No job data is loaded. The AI cannot find jobs.")
                    st.stop()
                    
                simplified_jobs = [{"id": j.get("id"), "title": j.get("title"), "organization": j.get("organization"), "location": j.get("location"), "category": j.get("category"), "source": j.get("source")} for j in st.session_state.jobs]
                jobs_context = json.dumps(simplified_jobs)
                
                system_prompt = f"""
                You are a friendly and helpful AI Job Assistant for 'Pak Job Finder'.
                Your task is to answer user questions *only* based on the list of available jobs provided below.
                Rules:
                1. Analyze the user's prompt: "{prompt}"
                2. Scan the 'Here is the full list of available jobs' JSON to find matching jobs.
                3. If you find matching jobs, list them clearly with their title, organization, and location.
                4. If you don't find any matches, say so politely.
                5. Do not make up jobs. Stick *only* to the provided list.
                6. Be conversational and friendly.
                """
                
                response_text = get_gemini_response(system_prompt, job_context=jobs_context)
                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# --- Page: View Job Sources ---
elif st.session_state.page == "View Job Sources":
    st.header("📜 Job Data Sources")
    st.markdown("This app is designed to aggregate job postings from a wide variety of sources. The mock data and live scrapers pull from sites like these, based on the lists you provided.")
    
    st.subheader("Example Target Websites")
    
    st.markdown("#### Pakistani Portals")
    st.text_area("Pakistani Links", 
"""https://www.rozee.pk
https://www.jobz.pk
https://pk.indeed.com
https://pk.linkedin.com/jobs
https://www.mustakbil.com
https://www.bayt.com/en/pakistan/
https://www.brightspyre.com
https://www.paperpk.com/jobs/
https://www.jobsalert.pk""", height=200)

    st.markdown("#### Government & Newspaper Portals")
    st.text_area("Government/News Links",
"""https://www.fpsc.gov.pk
https://www.ppsc.gop.pk
https://www.spsc.gov.pk
https://njp.gov.pk/
https://www.dawn.com/jobs
https://www.jang.com.pk/jobs""", height=150)

    st.markdown("#### International & Regional Portals")
    st.text_area("International Links",
"""https://www.bayt.com
https://www.naukrigulf.com
https://www.linkedin.com/jobs
https://www.glassdoor.com
https://weworkremotely.com
https://www.flexjobs.com
https://www.usajobs.gov
https://www.gov.uk/find-a-job""", height=200)
