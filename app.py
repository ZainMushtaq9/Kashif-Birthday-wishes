import streamlit as st
import google.generativeai as genai
import time
import json
from datetime import datetime
from textwrap import dedent
import requests
from bs4 import BeautifulSoup
import uuid # To create unique IDs for scraped items
import re # <-- Import regular expressions

# --- Configuration ---
st.set_page_config(
    page_title="Pak Job Finder",
    page_icon="🇵🇰",
    layout="wide"
)

# --- Mock Data (UPDATED) ---
def get_mock_jobs():
    """
    Simulates fetching jobs from a data source.
    UPDATED: Now includes more diverse examples based on the provided PDF lists.
    """
    return [
        {
            "id": "j1",
            "title": "Senior Python Developer",
            "organization": "Tech Solutions Ltd.",
            "location": "Karachi",
            "category": "IT",
            "source": "rozee.pk",
            "url": "https://www.rozee.pk",
            "posted_date": "2025-11-10",
            "description": dedent("""
                **Job Description:**
                We are looking for an experienced Senior Python Developer to join our dynamic team. The ideal candidate will be responsible for developing, testing, and maintaining high-quality software solutions. You will work on a variety of projects, from backend services to data processing pipelines.

                **Responsibilities:**
                - Write reusable, testable, and efficient code.
                - Design and implement low-latency, high-availability, and performant applications.
                - Integrate user-facing elements developed by front-end developers with server-side logic.
                - Implement security and data protection solutions.
                - Optimize applications for maximum speed and scalability.

                **Qualifications:**
                - 5+ years of experience with Python.
                - Strong understanding of frameworks like Django or Flask.
                - Experience with databases (e.g., PostgreSQL, MySQL, MongoDB).
                - Familiarity with front-end technologies (e.g., React, Vue.js) is a plus.
                - Excellent problem-solving skills and attention to detail.
            """)
        },
        {
            "id": "j2",
            "title": "Assistant Director (IT)",
            "organization": "Federal Public Service Commission (FPSC)",
            "location": "Islamabad",
            "category": "Government",
            "source": "fpsc.gov.pk",
            "url": "https://www.fpsc.gov.pk",
            "posted_date": "2025-11-08",
            "description": dedent("""
                **Case No. F.4-150/2025-R (11/2025)**
                **Position:** Assistant Director (IT) (BS-17)
                **Department:** Ministry of Information Technology & Telecommunication

                **Job Duties:**
                - To assist in the formulation and implementation of IT policies.
                - Management of network infrastructure and data centers.
                - Oversee cybersecurity protocols and ensure data integrity.
                - Liaise with other government departments for IT-related projects.

                **Qualifications:**
                - Master's Degree in Computer Science, IT, or equivalent from a recognized university.
                - OR Bachelor's Degree in Engineering (Software, IT, Computer) from a recognized university.
                - Minimum 3 years of post-qualification experience in IT infrastructure management.
                - Age Limit: 22-30 years plus five (5) years general relaxation in upper age limit.
            """)
        },
        {
            "id": "j3",
            "title": "Registered Nurse (RN)",
            "organization": "Aga Khan University Hospital",
            "location": "Karachi",
            "category": "Healthcare",
            "source": "jang.com.pk",
            "url": "https://www.jang.com.pk/jobs",
            "posted_date": "2025-11-11",
            "description": dedent("""
                **Join Our Team of Compassionate Professionals!**
                Aga Khan University Hospital (AKUH) is seeking qualified and dedicated Registered Nurses to join our team. We are committed to providing the highest quality of patient care.

                **Responsibilities:**
                - Provide direct patient care, including assessment, planning, implementation, and evaluation of patient needs.
                - Administer medications and treatments as prescribed by physicians.
                - Collaborate with healthcare team members to provide comprehensive care.
                - Maintain accurate and detailed patient records.
                - Educate patients and their families on health management and disease prevention.

                **Requirements:**
                - BScN or Diploma in General Nursing.
                - Valid registration with the Pakistan Nursing Council (PNC).
                - Minimum 2 years of clinical experience preferred.
                - Excellent communication and interpersonal skills.
                - Ability to work in a fast-paced environment.
            """)
        },
        {
            "id": "j4",
            "title": "Remote React Developer",
            "organization": "Startup Co.",
            "location": "Remote",
            "category": "IT",
            "source": "linkedin.com",
            "url": "https://www.linkedin.com/jobs",
            "posted_date": "2025-11-12",
            "description": dedent("""
                **About Us:**
                We are a fast-growing tech startup building the next generation of productivity tools. We are a fully remote team spread across the globe.

                **The Role:**
                We are seeking a talented React Developer to build and maintain our user-facing applications. You will work closely with our designers and backend engineers to create a seamless and intuitive user experience.

                **What You'll Do:**
                - Develop new user-facing features using React.js.
                - Build reusable components and front-end libraries for future use.
                - Translate designs and wireframes into high-quality code.
                - Optimize components for maximum performance across a vast array of web-capable devices and browsers.

                **What We're Looking For:**
                - 3+ years of professional experience with React.js.
                - Strong proficiency in JavaScript, including DOM manipulation and the JavaScript object model.
                - Familiarity with modern front-end build pipelines and tools (e.g., Webpack, Babel, NPM).
                - Experience with state management libraries (e.g., Redux, Zustand).
                - A passion for remote work and asynchronous communication.
            """)
        },
        {
            "id": "j5",
            "title": "Marketing Manager",
            "organization": "FMCG Giant",
            "location": "Lahore",
            "category": "Marketing",
            "source": "rozee.pk",
            "url": "https://www.rozee.pk",
            "posted_date": "2025-11-09",
            "description": dedent("""
                **Job Summary:**
                We are seeking an innovative Marketing Manager to lead our brand strategy for a key product line. You will be responsible for developing and executing marketing campaigns that drive brand awareness, engagement, and sales.

                **Key Responsibilities:**
                - Develop and implement comprehensive marketing plans and strategies.
                - Conduct market research to identify trends and opportunities.
                - Manage the marketing budget and allocate resources effectively.
                - Oversee digital marketing efforts, including social media, SEO/SEM, and email marketing.
                - Collaborate with sales and product development teams.

                **Qualifications:**
                - Bachelor's degree in Marketing, Business, or related field (MBA preferred).
                - 5+ years of brand management or marketing experience in the FMCG sector.
                - Proven track of successful marketing campaigns.
                - Strong analytical and leadership skills.
            """)
        },
        {
            "id": "j6",
            "title": "Lecturer in English (BPS-18)",
            "organization": "Punjab Public Service Commission (PPSC)",
            "location": "Lahore",
            "category": "Government",
            "source": "ppsc.gop.pk",
            "url": "https://www.ppsc.gop.pk",
            "posted_date": "2025-11-07",
            "description": dedent("""
                **Case No. 42-RF/2025**
                **Position:** Lecturer in English (Female) (BPS-18)
                **Department:** Punjab Higher Education Department
                **Qualifications:**
                - Master's Degree (at least 2nd Division) in English.
                - OR Equivalent qualification from a recognized university.
                **Note:** Candidates must pass a written examination and interview.
            """)
        },
        {
            "id": "j7",
            "title": "Finance Manager",
            "organization": "A Leading Multinational",
            "location": "Dubai, UAE",
            "category": "Finance",
            "source": "gulftalent.com",
            "url": "https://www.gulftalent.com",
            "posted_date": "2025-11-05",
            "description": dedent("""
                **Role:**
                Our client, a leading multinational corporation, is looking to hire a Finance Manager to be based in their Dubai regional headquarters. The candidate will be responsible for overseeing all financial operations, managing budgets, and providing strategic financial guidance.

                **Requirements:**
                - Bachelor's degree in Finance or Accounting.
                - Professional certification (e.g., CPA, ACCA, CMA) is highly preferred.
                - 7-10 years of experience in a senior financial role.
                - Experience in the GCC region is a strong plus.
                - Strong knowledge of IFRS.
            """)
        },
        {
            "id": "j8",
            "title": "Content Writer - Urdu",
            "organization": "Digital Media Group",
            "location": "Karachi",
            "category": "Media",
            "source": "dawn.com/jobs",
            "url": "https://www.dawn.com/jobs",
            "posted_date": "2025-11-12",
            "description": dedent("""
                **Job Opening: Content Writer (Urdu)**
                A reputable digital media group requires a Content Writer for its Urdu news portal.
                - Candidate must have excellent Urdu writing, typing, and editing skills.
                - Must be aware of current affairs, social media trends.
                - Minimum 2 years of experience in a similar role.
                - Location: Karachi
                - Send your CV and work samples to [email protected]
            """)
        },
    ]

# --- NEW: Job Sources Function (Reads from .txt file) ---
@st.cache_data # Cache this file read
def get_links_from_txt(file_path="job_links.txt"):
    """Reads a .txt file and returns a list of links."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip()]
        return links
    except FileNotFoundError:
        st.error(f"Error: {file_path} not found.")
        return []
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return []


# --- Scraping Function 1 (rozee.pk) ---
@st.cache_data(ttl=600) # Cache for 10 minutes to avoid re-scraping
def get_real_jobs_rozee_pk():
    """
    Scrapes rozee.pk using Requests and BeautifulSoup.
    Returns a dictionary: {"status": "success", "data": []} or {"status": "error", "message": "..."}
    """
    scraped_jobs = []
    try:
        url = "https://www.rozee.pk/search-jobs-in-pakistan"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise error for bad responses

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- IMPORTANT ---
        # These selectors are *examples* based on the HTML of rozee.pk
        # at the time of writing. They WILL break.
        job_cards = soup.find_all("div", class_=["job", "job-c"]) # Find all job card containers

        for card in job_cards:
            title_element = card.find("h2")
            org_element = card.find("div", class_="c-name")
            loc_element = card.find("div", class_="j-loc")
            
            if title_element and org_element and loc_element:
                job_url = title_element.find("a")["href"] if title_element.find("a") else "https://www.rozee.pk"
                job = {
                    "id": str(uuid.uuid4()), # Generate a unique ID
                    "title": title_element.get_text(strip=True),
                    "organization": org_element.get_text(strip=True),
                    "location": loc_element.get_text(strip=True),
                    "category": "Scraped", # Category is hard to guess, hardcoding
                    "source": "rozee.pk (Live)",
                    "url": job_url,
                    "posted_date": datetime.now().strftime('%Y-%m-%d'),
                    "description": f"This is a live-scraped job. Full description available at the source URL. {title_element.get_text(strip=True)} at {org_element.get_text(strip=True)}."
                }
                scraped_jobs.append(job)

        if not scraped_jobs:
            return {"status": "error", "message": "Could not find any jobs with the current selectors (rozee.pk). The website's HTML has likely changed."}
            
        return {"status": "success", "data": scraped_jobs}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Error fetching data (rozee.pk): {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Error parsing data (rozee.pk): {e}. The website's HTML has likely changed."}

# --- NEW: Scraping Function 2 (jobz.pk) ---
@st.cache_data(ttl=600) # Cache for 10 minutes
def get_real_jobs_jobz_pk():
    """
    Scrapes jobz.pk using Requests and BeautifulSoup.
    Returns a dictionary: {"status": "success", "data": []} or {"status": "error", "message": "..."}
    """
    scraped_jobs = []
    try:
        url = "https://www.jobz.pk/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # --- IMPORTANT ---
        # These selectors are *guesses* based on the HTML of jobz.pk.
        # They are very likely to break when the site's HTML changes.
        job_cards = soup.find_all("div", class_="job")

        for card in job_cards:
            title_element = card.find("h2")
            p_elements = card.find_all("p")
            
            if title_element and len(p_elements) > 0:
                title_link = title_element.find("a")
                if not title_link:
                    continue

                title = title_link.get_text(strip=True)
                job_url = title_link.get("href", "https://www.jobz.pk")
                
                # Guessing company and location from <p> tags
                organization = p_elements[0].find("strong").get_text(strip=True) if p_elements[0].find("strong") else "N/A"
                location = p_elements[0].find_all("strong")[1].get_text(strip=True) if len(p_elements[0].find_all("strong")) > 1 else "N/A"
                
                job = {
                    "id": str(uuid.uuid4()),
                    "title": title,
                    "organization": organization,
                    "location": location,
                    "category": "Scraped",
                    "source": "jobz.pk (Live)",
                    "url": job_url,
                    "posted_date": datetime.now().strftime('%Y-%m-%d'),
                    "description": f"This is a live-scraped job from jobz.pk. Full description available at the source URL. {title} at {organization}."
                }
                scraped_jobs.append(job)

        if not scraped_jobs:
            return {"status": "error", "message": "Could not find any jobs with the current selectors (jobz.pk). The website's HTML has likely changed."}
        
        return {"status": "success", "data": scraped_jobs}

    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": f"Error fetching data (jobz.pk): {e}"}
    except Exception as e:
        return {"status": "error", "message": f"Error parsing data (jobz.pk): {e}. The website's HTML has likely changed."}


# --- Gemini API Service (Replaces geminiService.ts) ---

def get_gemini_model(api_key):
    """Initializes and returns a Gemini model."""
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash-preview-09-2025')
        return model
    except Exception as e:
        st.error(f"Error initializing Gemini model: {e}")
        return None

def summarize_job_description(api_key, description):
    """Calls Gemini API to summarize a job description."""
    model = get_gemini_model(api_key)
    if not model:
        return "Error: Could not initialize AI model."

    prompt = dedent(f"""
        Please summarize the following job description for a job seeker. 
        Focus on the key responsibilities and qualifications. 
        Format the output as 3-4 concise bullet points.

        **Job Description:**
        {description}
    """)
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating summary: {e}"

def get_chatbot_response(api_key, chat_history, all_jobs, user_query):
    """Calls Gemini API for the chatbot, providing job list as context."""
    model = get_gemini_model(api_key)
    if not model:
        return "Error: Could not initialize AI model."

    # Convert all jobs to a JSON string to pass as context
    jobs_context = json.dumps(all_jobs)

    # System instruction to guide the model
    system_instruction = dedent(f"""
        You are an AI Job Assistant. Your goal is to answer the user's questions about available jobs.
        You MUST base your answers ONLY on the following list of available jobs provided in JSON format.
        Do not make up jobs or information. If no job matches the user's request, say so.
        Be friendly and helpful.

        **Available Jobs:**
        {jobs_context}
    """)
    
    # Format chat history for the API
    messages = [{"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]} for msg in chat_history]

    try:
        # Start a chat with the system instruction
        chat = model.start_chat(history=messages)
        response = chat.send_message(user_query, system_instruction=system_instruction)
        return response.text
    except Exception as e:
        return f"Error getting chatbot response: {e}"

# --- Session State Initialization (Replaces React Hooks) ---

if 'page' not in st.session_state:
    st.session_state.page = 'list'  # 'list', 'detail', 'saved', or 'sources'
if 'selected_job_id' not in st.session_state:
    st.session_state.selected_job_id = None
if 'saved_jobs' not in st.session_state:
    st.session_state.saved_jobs = []  # Replaces localStorage
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'jobs' not in st.session_state:
    # Fetch jobs once and store in session state
    st.session_state.jobs = get_mock_jobs()
if 'ai_summary' not in st.session_state:
    st.session_state.ai_summary = None

# --- API Key Management ---
api_key = ""
try:
    # Try to get API key from Streamlit secrets
    api_key = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # If not found, ask user in the sidebar
    st.sidebar.warning("Please add your Gemini API Key to proceed.")
    api_key = st.sidebar.text_input("Enter your Gemini API Key:", type="password")

if not api_key:
    st.error("A Gemini API Key is required to use the AI features.")

# --- Helper Functions (for navigation and actions) ---

def navigate_to_detail(job_id):
    """Callback to switch to the detail view."""
    st.session_state.page = 'detail'
    st.session_state.selected_job_id = job_id

def navigate_to_list():
    """Callback to switch to the list view."""
    st.session_state.page = 'list'
    st.session_state.selected_job_id = None
    st.session_state.ai_summary = None # Clear summary on nav

def navigate_to_saved():
    """Callback to switch to the saved jobs view."""
    st.session_state.page = 'saved'
    st.session_state.selected_job_id = None

# --- NEW: Navigation for Job Sources page ---
def navigate_to_sources():
    """Callback to switch to the job sources view."""
    st.session_state.page = 'sources'
    st.session_state.selected_job_id = None

def toggle_save_job(job_id):
    """Callback to save or unsave a job."""
    if job_id in st.session_state.saved_jobs:
        st.session_state.saved_jobs.remove(job_id)
    else:
        st.session_state.saved_jobs.append(job_id)

# --- Sidebar (Replaces SearchBar.tsx) ---
st.sidebar.title("🇵🇰 Pak Job Finder")
st.sidebar.divider()

# Navigation
st.sidebar.button("Mock Job List", on_click=navigate_to_list, use_container_width=True)
saved_job_count = len(st.session_state.saved_jobs)
st.sidebar.button(f"Saved Jobs ({saved_job_count})", on_click=navigate_to_saved, use_container_width=True)
st.sidebar.button("View Job Sources", on_click=navigate_to_sources, use_container_width=True) # NEW BUTTON

st.sidebar.divider()
st.sidebar.subheader("Live Scraping Demos")

# --- UPDATED: Button logic for multiple scrapers ---
if st.sidebar.button("Fetch Live (rozee.pk)", use_container_width=True):
    with st.spinner("Scraping rozee.pk... This is slow!"):
        result = get_real_jobs_rozee_pk()
        
        if result["status"] == "success":
            st.session_state.jobs = result["data"]
            st.session_state.page = 'list'
            st.session_state.selected_job_id = None
            st.session_state.ai_summary = None
            st.toast("Live jobs fetched from rozee.pk!", icon="✅")
            st.rerun()
        else:
            st.error(result["message"])

# --- NEW: Button for jobz.pk scraper ---
if st.sidebar.button("Fetch Live (jobz.pk)", use_container_width=True):
    with st.spinner("Scraping jobz.pk... This is slow!"):
        result = get_real_jobs_jobz_pk()
        
        if result["status"] == "success":
            st.session_state.jobs = result["data"]
            st.session_state.page = 'list'
            st.session_state.selected_job_id = None
            st.session_state.ai_summary = None
            st.toast("Live jobs fetched from jobz.pk!", icon="✅")
            st.rerun()
        else:
            st.error(result["message"])

st.sidebar.divider()
st.sidebar.header("Filter Jobs")

# Get unique filter options from the job data
all_jobs = st.session_state.jobs
locations = sorted(list(set([job['location'] for job in all_jobs])))
categories = sorted(list(set([job['category'] for job in all_jobs])))
sources = sorted(list(set([job['source'] for job in all_jobs])))

# Create filter widgets
keyword = st.sidebar.text_input("Keyword Search", placeholder="e.g., Python, Manager")
location = st.sidebar.selectbox("Location", ["All"] + locations)
category = st.sidebar.selectbox("Category", ["All"] + categories)
source = st.sidebar.selectbox("Source", ["All"] + sources)


# --- Main App Body (View Controller) ---

if st.session_state.page in ['list', 'saved']:
    
    # --- Job List View (Replaces JobCard.tsx grid) ---
    
    if st.session_state.page == 'list':
        st.title("All Job Listings")
        jobs_to_display = st.session_state.jobs
    else:
        st.title("Your Saved Jobs")
        jobs_to_display = [job for job in st.session_state.jobs if job['id'] in st.session_state.saved_jobs]

    # Display simulated "Last Updated" timestamp
    st.markdown(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}")

    # --- Filtering Logic ---
    filtered_jobs = jobs_to_display

    if keyword:
        filtered_jobs = [job for job in filtered_jobs if keyword.lower() in job['title'].lower() or keyword.lower() in job['description'].lower()]
    if location != "All":
        filtered_jobs = [job for job in filtered_jobs if job['location'] == location]
    if category != "All":
        filtered_jobs = [job for job in filtered_jobs if job['category'] == category]
    if source != "All":
        filtered_jobs = [job for job in filtered_jobs if job['source'] == source]

    # --- Loading Simulation (Replaces JobListingsLoading.tsx) ---
    if st.session_state.page == 'list' and st.session_state.jobs == get_mock_jobs(): # Only show loading spinner on mock list
        with st.spinner("Simulating fetch of new job data..."):
            time.sleep(1) # Deliberate 1-second delay

    # --- Job Grid Display ---
    st.subheader(f"Showing {len(filtered_jobs)} jobs")
    st.divider()

    if not filtered_jobs:
        st.info("No jobs found matching your criteria.")
    else:
        # Create a grid of 3 columns
        cols = st.columns(3)
        for i, job in enumerate(filtered_jobs):
            col = cols[i % 3]
            with col:
                # Use a container for each "Job Card"
                with st.container(border=True):
                    st.subheader(job['title'])
                    st.markdown(f"**{job['organization']}**")
                    st.markdown(f"📍 {job['location']} | 📁 {job['category']}")
                    st.caption(f"Source: {job['source']} | Posted: {job['posted_date']}")
                    st.button(
                        "View Details", 
                        key=f"view_{job['id']}", 
                        on_click=navigate_to_detail, 
                        args=(job['id'],),
                        use_container_width=True
                    )

elif st.session_state.page == 'detail':
    
    # --- Job Detail View (Replaces JobDetail.tsx) ---
    
    # Find the selected job
    selected_job = next((job for job in st.session_state.jobs if job['id'] == st.session_state.selected_job_id), None)

    if selected_job:
        st.button("← Back to List", on_click=navigate_to_list)
        st.title(selected_job['title'])
        st.subheader(selected_job['organization'])

        # Key details
        c1, c2, c3 = st.columns(3)
        c1.metric("Location", selected_job['location'])
        c2.metric("Category", selected_job['category'])
        c3.metric("Source", selected_job['source'])

        # Action Buttons
        b1, b2, b3 = st.columns(3)
        b1.link_button("Apply Now ↗", selected_job['url'], use_container_width=True)
        
        # Save/Unsave Button
        is_saved = selected_job['id'] in st.session_state.saved_jobs
        save_button_text = "Unsave Job" if is_saved else "Save Job"
        save_button_type = "secondary" if is_saved else "primary"
        b2.button(
            save_button_text, 
            on_click=toggle_save_job, 
            args=(selected_job['id'],), 
            use_container_width=True,
            type=save_button_type
        )
        
        # AI Summary Button
        with b3:
            if st.button("Summarize with AI ✨", use_container_width=True, disabled=not api_key):
                with st.spinner("Generating AI summary..."):
                    summary = summarize_job_description(api_key, selected_job['description'])
                    st.session_state.ai_summary = summary # Store summary in state
        
        # Display AI summary if it exists in state
        if st.session_state.ai_summary and st.session_state.get('last_summarized_id') == selected_job['id']:
             st.info(st.session_state.ai_summary)
        else:
            # Clear summary if it's for a different job
            st.session_state.ai_summary = None
        
        # Store the ID of the job we just summarized
        if 'summary' in locals():
            st.session_state.last_summarized_id = selected_job['id']

        st.divider()
        st.markdown(selected_job['description'], unsafe_allow_html=True) # Allow HTML for scraped data

    else:
        st.error("Job not found. Returning to list.")
        st.session_state.page = 'list'
        st.session_state.selected_job_id = None
        st.rerun()

# --- UPDATED: Job Sources Page (Reads from .txt file) ---
elif st.session_state.page == 'sources':
    st.title("Our Job Sources")
    st.markdown("This is the full list of job portals we (simulately) scrape, loaded directly from `job_links.txt`.")
    st.info("The 'Live Scraping Demos' in the sidebar use real, but brittle, scrapers for demonstration.")
    
    links = get_links_from_txt() # Call the new function
    
    if links:
        st.markdown(f"**Found {len(links)} total links.**")
        
        # Create a simple, scrollable text area for the links
        links_text = "\n".join(links)
        st.text_area("Source Links", links_text, height=400)
    else:
        st.error("No links were loaded. Make sure `job_links.txt` is in the same folder as `app.py`.")


# --- AI Chatbot (Replaces Chatbot.tsx) ---
# Placed in the sidebar to be "available on every page"
with st.sidebar.expander("🤖 AI Job Assistant", expanded=False):
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about jobs...", disabled=not api_key):
        # Add user message to history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = get_chatbot_response(
                    api_key,
                    st.session_state.chat_history,
                    st.session_state.jobs, # Provide all jobs as context
                    prompt
                )
                st.markdown(response)
        
        # Add assistant response to history
        st.session_state.chat_history.append({"role": "assistant", "content": response})
