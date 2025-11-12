import streamlit as st
import google.generativeai as genai
import json
import os
import re
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
    # Stop execution if no API key is provided, but allow viewing sources
    if 'page' in st.session_state and st.session_state.page != "View Job Sources":
        st.stop()


# --- Utility Functions ---

def safe_html(html_content):
    """Render HTML content safely in Streamlit."""
    if not html_content:
        return
    # Use BeautifulSoup to parse and clean the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style tags
    for script_or_style in soup(["script", "style"]):
        script_or_style.decompose()
        
    # Convert to string and display as markdown (which Streamlit sanitizes)
    # Using 'unsafe_allow_html=True' is necessary for rendering, 
    # but we've reduced risk by stripping scripts/styles.
    st.markdown(soup.prettify(), unsafe_allow_html=True)

def get_gemini_response(prompt_text, job_context=None, is_json=False):
    """
    Calls the Gemini API to get a response.
    
    Args:
        prompt_text (str): The main user prompt.
        job_context (str): Optional. A string (e.g., JSON) of all jobs for context.
        is_json (bool): Optional. Whether to ask for a JSON response.
    """
    if not st.session_state.api_key:
        return "Please provide a Gemini API Key to use this feature."

    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        
        # Combine prompt and context if provided
        if job_context:
            full_prompt = f"{prompt_text}\n\nHere is the full list of available jobs:\n{job_context}"
        else:
            full_prompt = prompt_text

        # Configure for JSON output if requested
        generation_config = {}
        if is_json:
            generation_config["response_mime_type"] = "application/json"

        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        return response.text
    except Exception as e:
        st.error(f"Gemini API error: {e}")
        return f"Error: Could not get response from AI. {e}"

def clean_text(text):
    """Basic text cleaning for search."""
    if not text:
        return ""
    return text.lower().strip()

# --- Data Loading ---

@st.cache_data(ttl=600)  # Cache for 10 minutes
def load_data(filepath="jobs.json"):
    """Loads job data from the JSON file produced by Scrapy."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            jobs = json.load(f)
        
        # Add a 'search_text' field for easier filtering
        for job in jobs:
            job['search_text'] = (
                f"{clean_text(job.get('title'))} "
                f"{clean_text(job.get('organization'))} "
                f"{clean_text(job.get('description'))}"
            )
        
        # Get last modified time
        last_mod_time = os.path.getmtime(filepath)
        last_updated = datetime.fromtimestamp(last_mod_time).strftime('%Y-%m-%d %I:%M %p')
        return jobs, last_updated
    except FileNotFoundError:
        return None, None
    except json.JSONDecodeError:
        st.error(f"Error: The file '{filepath}' is corrupted or empty.")
        return None, None
    except Exception as e:
        st.error(f"An error occurred while loading '{filepath}': {e}")
        return None, None

# --- Main App Logic ---

# Initialize session state variables
if "jobs" not in st.session_state:
    st.session_state.jobs = []
    st.session_state.last_updated = "Never"
    
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

# Load data only once
if not st.session_state.jobs:
    jobs, last_updated = load_data()
    if jobs:
        st.session_state.jobs = jobs
        st.session_state.last_updated = last_updated
    else:
        st.error("Could not load job data from 'jobs.json'.")
        st.info("""
            This app reads data from `jobs.json`.
            
            Please run your Scrapy project (`job_scraper_project`) first to generate this file.
            
            **Example commands:**
            ```bash
            cd job_scraper_project
            scrapy crawl rozee
            scrapy crawl jobz
            scrapy crawl dawn
            ```
            
            After running your spiders, refresh this page.
        """)
        # Allow viewing sources even if no data
        st.session_state.page = "View Job Sources"


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
    
    if not st.session_state.jobs:
        st.warning("No jobs loaded. See sidebar for instructions.")
    else:
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
        with cols[0]:
            st.markdown("**Job Title**")
        with cols[1]:
            st.markdown("**Organization**")
        with cols[2]:
            st.markdown("**Location**")
        with cols[3]:
            st.markdown("**Source**")
            
        st.divider()

        if not filtered_jobs:
            st.warning("No jobs match your filter criteria.")

        for job in filtered_jobs:
            cols = st.columns([3, 1, 1, 1])
            is_saved = job.get('id') in st.session_state.saved_jobs
            
            with cols[0]:
                title_display = f"❤️ {job.get('title')}" if is_saved else job.get('title')
                st.button(title_display, on_click=set_page, args=("Detail", job.get('id')), key=f"title_{job.get('id')}", use_container_width=True)
            
            with cols[1]:
                st.markdown(job.get('organization', 'N/A'))
            
            with cols[2]:
                st.markdown(job.get('location', 'N/A'))
            
            with cols[3]:
                st.markdown(job.get('source', 'N/A'))


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
        with info_cols[0]:
            st.markdown(f"**Location:**\n\n{job.get('location', 'N/A')}")
        with info_cols[1]:
            st.markdown(f"**Category:**\n\n{job.get('category', 'N/A')}")
        with info_cols[2]:
            st.markdown(f"**Source:**\n\n{job.get('source', 'N/A')}")
            st.markdown(f"**Posted:**\n\n{job.get('posted_date', 'N/A')}")

        st.divider()

        # AI Summary
        st.subheader("🤖 AI Summary")
        if "summary_cache" not in st.session_state:
            st.session_state.summary_cache = {}

        summary_key = f"summary_{job_id}"

        if summary_key not in st.session_state.summary_cache:
            if st.button("Generate AI Summary", key="gen_summary", use_container_width=True):
                with st.spinner("Summarizing job description with Gemini..."):
                    # Create a clean text version for the prompt
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
                with st.spinner("Regenerating summary with Gemini..."):
                    desc_soup = BeautifulSoup(job.get('description', ''), 'html.parser')
                    clean_desc = desc_soup.get_text(separator=" ").strip()
                    prompt = f"Please provide a new, slightly different summary (3-5 bullet points) for this job description:\n\n{clean_desc}"
                    summary = get_gemini_response(prompt)
                    st.session_state.summary_cache[summary_key] = summary
                    st.rerun()

        st.divider()
        
        # Full Description
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
            with cols[0]:
                st.button(job.get('title'), on_click=set_page, args=("Detail", job_id), key=f"saved_{job_id}", use_container_width=True)
            with cols[1]:
                st.markdown(job.get('organization', 'N/A'))
            with cols[2]:
                st.markdown(job.get('location', 'N/A'))


# --- Page: AI Chatbot ---
elif st.session_state.page == "Chat":
    st.header("🤖 AI Job Assistant")
    st.markdown("Ask me to find jobs from the current listings.")

    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Get user input
    if prompt := st.chat_input("e.g., 'Find me engineering jobs in Karachi'"):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate assistant response
        with st.chat_message("assistant"):
            with st.spinner("AI is thinking..."):
                # Create a simplified JSON of all jobs for context
                # This is crucial for the AI to answer based on *your* data
                if not st.session_state.jobs:
                    st.warning("No job data is loaded. The AI cannot find jobs.")
                    st.stop()
                    
                simplified_jobs = [
                    {
                        "id": j.get("id"),
                        "title": j.get("title"),
                        "organization": j.get("organization"),
                        "location": j.get("location"),
                        "category": j.get("category"),
                        "source": j.get("source")
                    } for j in st.session_state.jobs
                ]
                jobs_context = json.dumps(simplified_jobs)
                
                # Create a system prompt
                system_prompt = f"""
                You are a friendly and helpful AI Job Assistant for 'Pak Job Finder'.
                Your task is to answer user questions *only* based on the list of available jobs provided below.
                
                Rules:
                1.  Analyze the user's prompt: "{prompt}"
                2.  Scan the 'Here is the full list of available jobs' JSON to find matching jobs.
                3.  If you find matching jobs, list them clearly with their title, organization, and location.
                4.  If you don't find any matches, say so politely (e.g., "Sorry, I couldn't find any jobs that match...").
                5.  Do not make up jobs or information. Stick *only* to the provided list.
                6.  Be conversational and friendly.
                """
                
                response_text = get_gemini_response(system_prompt, job_context=jobs_context)
                
                # Post-process the response to make job titles clickable
                # This is a simple regex, might need refinement
                def make_links_clickable(match):
                    job_title = match.group(1)
                    # Find the job in our state
                    found_job = next((j for j in st.session_state.jobs if j.get('title') == job_title), None)
                    if found_job:
                        # This part is tricky. Streamlit can't easily embed buttons in chat.
                        # We'll just list them. A future improvement would be to return JSON.
                        return f"**{job_title}**" # Make it bold
                    return job_title

                # This regex is a placeholder. A better way is to ask the AI for JSON.
                # For now, we'll just display the text.
                # response_text = re.sub(r"\*\*(.*?)\*\*", make_links_clickable, response_text)

                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# --- Page: View Job Sources ---
elif st.session_state.page == "View Job Sources":
    st.header("📜 Job Data Sources")
    st.markdown("This app is designed to aggregate job postings from a wide variety of sources. The data is collected by a separate backend process (your Scrapy project) and read from the `jobs.json` file.")
    st.markdown("Below is the target list of websites from `job_links.txt` that the backend scraper is designed to crawl.")
    
    try:
        with open("job_links.txt", 'r') as f:
            links = f.readlines()
        
        st.subheader(f"Target Websites ({len(links)})")
        
        # Group links for better display
        st.markdown("#### Pakistani Portals")
        pk_links = [link for link in links if ".pk" in link or ".gov.pk" in link or "pakistan" in link]
        st.text_area("Pakistani Links", "\n".join(pk_links), height=300)

        st.markdown("#### International & Regional Portals")
        intl_links = [link for link in links if ".pk" not in link and ".gov.pk" not in link and "pakistan" not in link]
        st.text_area("International Links", "\n".join(intl_links), height=300)

    except FileNotFoundError:
        st.error("`job_links.txt` not found.")
        st.info("Please make sure the `job_links.txt` file is in the same directory as `app.py`.")
    except Exception as e:
        st.error(f"Could not read `job_links.txt`: {e}")
