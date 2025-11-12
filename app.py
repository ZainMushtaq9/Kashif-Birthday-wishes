import streamlit as st
import google.generativeai as genai
import json
import uuid
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import time
from urllib.parse import urlparse
import concurrent.futures

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
        st.session_state.api_key = st.secrets["GEMINI_API_KEY"]
    except (KeyError, AttributeError):
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

def load_job_links():
    """Load job website links from job_links.txt file."""
    try:
        with open('job_links.txt', 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return links
    except FileNotFoundError:
        st.warning("job_links.txt not found. Using default links.")
        return [
            "https://www.rozee.pk",
            "https://www.jobz.pk",
            "https://www.dawn.com/jobs",
            "https://pk.indeed.com"
        ]

def extract_domain(url):
    """Extract domain name from URL for identification."""
    try:
        domain = urlparse(url).netloc
        return domain.replace('www.', '')
    except:
        return "unknown"

def generic_job_scraper(url, timeout=10):
    """
    Generic job scraper that attempts to find job listings on any website.
    Uses common HTML patterns for job listings.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        domain = extract_domain(url)
        jobs_list = []
        
        # Common job card selectors (try multiple patterns)
        job_selectors = [
            'div.job', 'article.job', 'li.job',
            'div[class*="job"]', 'div[class*="vacancy"]',
            'div[class*="position"]', 'div[class*="listing"]',
            'article', 'div.card', 'li[class*="job"]'
        ]
        
        job_cards = []
        for selector in job_selectors:
            cards = soup.select(selector)
            if len(cards) > 3:  # If we find more than 3, likely correct
                job_cards = cards
                break
        
        if not job_cards:
            # Try finding any repeated structure
            all_divs = soup.find_all('div', limit=100)
            class_counts = {}
            for div in all_divs:
                classes = div.get('class', [])
                if classes:
                    class_str = ' '.join(classes)
                    class_counts[class_str] = class_counts.get(class_str, 0) + 1
            
            # Find most common class (likely job cards)
            if class_counts:
                most_common = max(class_counts, key=class_counts.get)
                if class_counts[most_common] > 3:
                    job_cards = soup.find_all('div', class_=most_common.split())
        
        # Extract job information
        for idx, card in enumerate(job_cards[:30]):  # Limit to 30 jobs per site
            try:
                # Try to find title
                title = None
                for tag in ['h1', 'h2', 'h3', 'h4', 'a']:
                    title_elem = card.find(tag)
                    if title_elem and len(title_elem.get_text(strip=True)) > 5:
                        title = title_elem.get_text(strip=True)
                        break
                
                if not title:
                    continue
                
                # Try to find link
                link_elem = card.find('a', href=True)
                job_url = link_elem['href'] if link_elem else url
                if not job_url.startswith('http'):
                    base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
                    job_url = base_url + job_url
                
                # Try to find organization/company
                org = None
                org_keywords = ['company', 'organization', 'employer', 'org', 'firm']
                for keyword in org_keywords:
                    org_elem = card.find(class_=lambda x: x and keyword in x.lower())
                    if org_elem:
                        org = org_elem.get_text(strip=True)
                        break
                
                if not org:
                    # Try to find any text that looks like a company
                    spans = card.find_all(['span', 'div', 'p'])
                    for span in spans:
                        text = span.get_text(strip=True)
                        if 10 < len(text) < 50 and text != title:
                            org = text
                            break
                
                # Try to find location
                location = None
                loc_keywords = ['location', 'loc', 'city', 'place', 'area']
                for keyword in loc_keywords:
                    loc_elem = card.find(class_=lambda x: x and keyword in x.lower())
                    if loc_elem:
                        location = loc_elem.get_text(strip=True)
                        break
                
                # Create job entry
                job = {
                    "id": str(uuid.uuid4()),
                    "title": title[:200],  # Limit length
                    "organization": org[:100] if org else domain,
                    "location": location[:100] if location else "Pakistan",
                    "category": "General",
                    "source": f"{domain} (Live)",
                    "url": job_url,
                    "posted_date": datetime.now().strftime('%Y-%m-%d'),
                    "description": f"<p>View full details on the website. <a href='{job_url}' target='_blank'>Click here</a></p>"
                }
                job['search_text'] = create_search_text(job)
                jobs_list.append(job)
                
            except Exception as e:
                continue
        
        return {'status': 'success', 'jobs': jobs_list, 'count': len(jobs_list)}
        
    except requests.exceptions.RequestException as e:
        return {'status': 'error', 'message': f"Error: {str(e)[:100]}"}
    except Exception as e:
        return {'status': 'error', 'message': f"Parsing error: {str(e)[:100]}"}

def scrape_multiple_sites(urls, max_workers=5, progress_bar=None):
    """
    Scrape multiple job sites concurrently.
    """
    all_jobs = []
    results_summary = {
        'successful': 0,
        'failed': 0,
        'total_jobs': 0,
        'details': []
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(generic_job_scraper, url): url for url in urls}
        
        for idx, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            domain = extract_domain(url)
            
            try:
                result = future.result()
                
                if result['status'] == 'success':
                    jobs = result.get('jobs', [])
                    all_jobs.extend(jobs)
                    results_summary['successful'] += 1
                    results_summary['total_jobs'] += len(jobs)
                    results_summary['details'].append({
                        'domain': domain,
                        'status': 'success',
                        'jobs_found': len(jobs)
                    })
                else:
                    results_summary['failed'] += 1
                    results_summary['details'].append({
                        'domain': domain,
                        'status': 'failed',
                        'error': result.get('message', 'Unknown error')
                    })
                    
            except Exception as e:
                results_summary['failed'] += 1
                results_summary['details'].append({
                    'domain': domain,
                    'status': 'error',
                    'error': str(e)[:100]
                })
            
            # Update progress
            if progress_bar:
                progress_bar.progress((idx + 1) / len(urls))
    
    return all_jobs, results_summary

# --- Initialize Session State ---
if "jobs" not in st.session_state:
    st.session_state.jobs = []
    st.session_state.last_updated = "No data loaded"
    
if "page" not in st.session_state:
    st.session_state.page = "List"
    
if "selected_job_id" not in st.session_state:
    st.session_state.selected_job_id = None
    
if "saved_jobs" not in st.session_state:
    st.session_state.saved_jobs = {}

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "Welcome! Ask me to find jobs, e.g., 'Find me IT jobs in Karachi' or 'Are there any remote developer jobs?'"}
    ]

if "scrape_results" not in st.session_state:
    st.session_state.scrape_results = None

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
    
    # --- Filters ---
    if st.session_state.page == "List" and st.session_state.jobs:
        st.header("🔍 Filter Jobs")
        
        all_locations = sorted(list(set(j.get('location', 'N/A') for j in st.session_state.jobs if j.get('location'))))
        all_categories = sorted(list(set(j.get('category', 'N/A') for j in st.session_state.jobs if j.get('category'))))
        all_sources = sorted(list(set(j.get('source', 'N/A') for j in st.session_state.jobs if j.get('source'))))

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
    if st.session_state.jobs:
        st.caption(f"Total jobs loaded: {len(st.session_state.jobs)}")

# --- Page: Job Listings (Home) ---
if st.session_state.page == "List":
    
    st.subheader("🚀 Job Data Scraper")
    st.markdown("Load jobs from all websites listed in `job_links.txt`")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        num_sites = st.number_input("Number of sites to scrape (from job_links.txt)", min_value=1, max_value=500, value=10, step=5)
    
    with col2:
        max_workers = st.number_input("Concurrent workers", min_value=1, max_value=20, value=5)
    
    if st.button("🔥 Scrape All Sites from job_links.txt", use_container_width=True, type="primary"):
        job_links = load_job_links()
        
        if not job_links:
            st.error("No job links found in job_links.txt")
        else:
            st.info(f"Found {len(job_links)} links in job_links.txt. Scraping first {num_sites} sites...")
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner(f"Scraping {num_sites} websites... This may take a few minutes."):
                selected_links = job_links[:num_sites]
                all_jobs, summary = scrape_multiple_sites(selected_links, max_workers=max_workers, progress_bar=progress_bar)
                
                st.session_state.jobs = all_jobs
                st.session_state.last_updated = datetime.now().strftime('%Y-%m-%d %I:%M %p')
                st.session_state.scrape_results = summary
                
                progress_bar.empty()
                st.success(f"✅ Scraping complete! Found {summary['total_jobs']} jobs from {summary['successful']} sites")
                st.rerun()
    
    # Show scrape results
    if st.session_state.scrape_results:
        with st.expander("📊 Scraping Results Summary"):
            summary = st.session_state.scrape_results
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Successful Sites", summary['successful'])
            col2.metric("Failed Sites", summary['failed'])
            col3.metric("Total Jobs Found", summary['total_jobs'])
            
            st.subheader("Site-by-Site Results")
            for detail in summary['details']:
                if detail['status'] == 'success':
                    st.success(f"✅ {detail['domain']}: {detail['jobs_found']} jobs")
                else:
                    st.error(f"❌ {detail['domain']}: {detail.get('error', 'Failed')}")

    st.divider()

    # Apply filters
    filtered_jobs = st.session_state.jobs
    if st.session_state.jobs and "filters" in st.session_state:
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
    if st.session_state.jobs:
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
    else:
        st.info("No jobs loaded yet. Click the 'Scrape All Sites' button above to start.")

# --- Page: Job Detail ---
elif st.session_state.page == "Detail":
    job = next((j for j in st.session_state.jobs if j.get('id') == st.session_state.selected_job_id), None)
    
    if not job:
        st.error("Job not found.")
        st.button("← Back to list", on_click=set_page, args=("List",))
    else:
        st.button("← Back to list", on_click=set_page, args=("List",))
        
        st.header(job.get('title', 'No Title'))
        st.subheader(job.get('organization', 'No Organization'))
        
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

        info_cols = st.columns(3)
        info_cols[0].markdown(f"**Location:**\n\n{job.get('location', 'N/A')}")
        info_cols[1].markdown(f"**Category:**\n\n{job.get('category', 'N/A')}")
        info_cols[2].markdown(f"**Source:**\n\n{job.get('source', 'N/A')}")
        st.divider()

        st.subheader("🤖 AI Summary")
        if "summary_cache" not in st.session_state:
            st.session_state.summary_cache = {}
        summary_key = f"summary_{job_id}"

        if summary_key not in st.session_state.summary_cache:
            if st.button("Generate AI Summary", key="gen_summary", use_container_width=True):
                with st.spinner("Summarizing job with Gemini..."):
                    desc_soup = BeautifulSoup(job.get('description', ''), 'html.parser')
                    clean_desc = desc_soup.get_text(separator=" ").strip()
                    prompt = f"Summarize this job in 3-5 bullet points: {clean_desc}"
                    summary = get_gemini_response(prompt)
                    st.session_state.summary_cache[summary_key] = summary
                    st.rerun()
        else:
            st.markdown(st.session_state.summary_cache[summary_key])
            if st.button("Regenerate Summary", key="regen_summary", use_container_width=True):
                st.session_state.summary_cache.pop(summary_key, None)
                st.rerun()

        st.divider()
        st.subheader("Full Job Description")
        safe_html(job.get('description', 'No description provided.'))

# --- Page: Saved Jobs ---
elif st.session_state.page == "Saved":
    st.header(f"❤️ My Saved Jobs ({len(st.session_state.saved_jobs)})")
    
    if not st.session_state.saved_jobs:
        st.info("You haven't saved any jobs yet.")
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
                    response_text = "No job data is loaded. Please go to the Home page and scrape some websites first."
                else:
                    simplified_jobs = [{"id": j.get("id"), "title": j.get("title"), "organization": j.get("organization"), "location": j.get("location"), "category": j.get("category"), "source": j.get("source")} for j in st.session_state.jobs]
                    jobs_context = json.dumps(simplified_jobs)
                    
                    system_prompt = f"""You are a friendly AI Job Assistant. Answer based only on the provided jobs list.
Rules:
1. Analyze: "{prompt}"
2. Find matching jobs from the JSON
3. List them with title, organization, and location
4. If no matches, say so politely
5. Be conversational"""
                    
                    response_text = get_gemini_response(system_prompt, job_context=jobs_context)
                
                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})

# --- Page: View Job Sources ---
elif st.session_state.page == "View Job Sources":
    st.header("📜 Job Data Sources")
    st.markdown("This app scrapes jobs from all websites listed in `job_links.txt`")
    
    job_links = load_job_links()
    
    st.subheader(f"Total Sources: {len(job_links)}")
    st.markdown("**First 50 sources from job_links.txt:**")
    
    for i, link in enumerate(job_links[:50], 1):
        st.text(f"{i}. {link}")
    
    if len(job_links) > 50:
        st.info(f"... and {len(job_links) - 50} more sources in job_links.txt")
    
    st.divider()
    st.markdown("**To add more sources:**")
    st.code("Edit job_links.txt and add one URL per line", language="text")
