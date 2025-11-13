import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re

# --- Constants ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}

# Cleaned and categorized list of websites from your PDFs
JOB_SITES = {
    "Major Job Portals (Pakistan)": [
        ("Rozee.pk", "https://www.rozee.pk"),
        ("Mustakbil.com", "https://www.mustakbil.com"),
        ("Indeed Pakistan", "https://pk.indeed.com"),
        ("LinkedIn Jobs (PK)", "https://pk.linkedin.com/jobs"),
        ("Jobz.pk", "https://www.jobz.pk"),
        ("Bayt.com (Pakistan)", "https://www.bayt.com/en/pakistan/"),
        ("Brightspyre.com", "https://www.brightspyre.com"),
        ("CareerOkay.com", "https://www.careerokay.com"),
        ("Jobee.pk", "https://www.jobee.pk"),
        ("PakPositions.com", "https://www.PakPositions.com"),
        ("JobsBirds.com", "https://www.JobsBirds.com"),
        ("Apna.co", "https://www.apna.co"),
        ("Glassdoor (Pakistan)", "https://www.glassdoor.com/Job/pakistan-jobs-SRCH_IL.0,8_IN178.htm"),
    ],
    "Government Job Portals (Federal & Provincial)": [
        ("FPSC", "https://www.fpsc.gov.pk"),
        ("PPSC", "https://www.ppsc.gop.pk"),
        ("SPSC", "https://www.spsc.gov.pk"),
        ("KPPSC", "https://www.kppsc.gov.pk"),
        ("BPSC", "https://www.bpsc.gob.pk"),
        ("AJKPSC", "https://www.ajkpsc.gov.pk"),
        ("National Job Portal (NJP)", "https://njp.gov.pk"),
        ("Overseas Employment (OEC)", "https://www.oec.gov.pk"),
        ("State Bank Careers", "https://www.sbp.org.pk/careers"),
        ("HEC Careers", "https://careers.hec.gov.pk"),
    ],
    "Newspaper & Classifieds": [
        ("Dawn Jobs", "https://www.dawn.com/jobs"),
        ("Jang Jobs", "https://www.jang.com.pk/jobs"),
        ("Tribune Careers", "https://www.tribune.com.pk/careers"),
        ("Nawaiwaqt", "https://www.nawaiwaqt.com.pk/work-for-us"),
        ("OLX Jobs", "https://www.olx.com.pk/jobs/"),
    ],
    "Major International Job Websites": [
        ("LinkedIn (Global)", "https://www.linkedin.com/jobs/"),
        ("Indeed (Global)", "https://www.indeed.com"),
        ("Glassdoor (Global)", "https://www.glassdoor.com"),
        ("Monster.com", "https://www.monster.com"),
        ("Jooble.org", "https://www.jooble.org"),
        ("FlexJobs (Remote)", "https://www.flexjobs.com"),
        ("WeWorkRemotely", "https://weworkremotely.com"),
        ("Upwork (Freelance)", "https://www.upwork.com"),
        ("Freelancer.com", "https://www.freelancer.com"),
        ("Dice.com (Tech)", "https://www.dice.com"),
        ("Wellfound (Startups)", "https://wellfound.com"),
        ("Idealist.org (Non-profit)", "https://www.idealist.org"),
        ("USAJobs.gov (US Govt)", "https://www.usajobs.gov"),
        ("Job Bank Canada", "https://www.jobbank.gc.ca"),
        ("StepStone.de (Germany)", "https://www.stepstone.de"),
        ("Reed.co.uk (UK)", "https://www.reed.co.uk"),
        ("Seek.com.au (Australia)", "https://www.seek.com.au"),
        ("Naukri.com (India)", "https://www.naukri.com"),
        ("GulfTalent.com (Middle East)", "https://www.gulftalent.com"),
        ("NaukriGulf.com", "https://www.naukrigulf.com"),
    ]
    # NOTE: Company-specific and recruiter-specific sites are omitted for brevity
    # but follow the same scraping principles.
}

# --- Helper Functions ---

@st.cache_data(ttl=3600)
def fetch_url_content(url):
    """Fetches the content of a URL with error handling."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.text, None
    except requests.exceptions.HTTPError as errh:
        return None, f"HTTP Error: {errh}"
    except requests.exceptions.ConnectionError as errc:
        return None, f"Connection Error: {errc}"
    except requests.exceptions.Timeout as errt:
        return None, f"Timeout Error: {errt}"
    except requests.exceptions.RequestException as err:
        return None, f"An Error Occurred: {err}"

def get_base_url(url):
    """Extracts the base URL (scheme + netloc) from a URL."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"

def find_sitemap(robots_txt_content):
    """Finds sitemap URLs in robots.txt content."""
    sitemaps = re.findall(r'Sitemap:\s*(.*)', robots_txt_content, re.IGNORECASE)
    return [s.strip() for s in sitemaps]

def generate_scraper_code(url, base_url, container_tag, container_class, title_tag, title_class, link_tag, link_class):
    """Generates boilerplate Python scraper code."""
    
    # Handle cases where user might not provide tags
    find_all_str = f"soup.find_all('{container_tag}', class_='{container_class}')" if container_tag and container_class else "soup.find_all('div')" # Default to 'div'
    find_title_str = f"listing.find('{title_tag}', class_='{title_class}')" if title_tag else "listing.find('h2')" # Default to 'h2'
    find_link_str = f"listing.find('{link_tag}', class_='{link_class}')" if link_tag else f"{find_title_str}.find('a') if {find_title_str} else None" # Default to 'a' inside title

    # Provide defaults if inputs are empty for the code snippet
    ct_str = container_tag if container_tag else "div"
    cc_str = container_class if container_class else "job-listing-container"
    tt_str = title_tag if title_tag else "h2"
    tc_str = title_class if title_class else "job-title"
    lt_str = link_tag if link_tag else "a"
    lc_str = link_class if link_class else "job-link"


    code = f"""
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import pandas as pd

# --- Configuration ---
TARGET_URL = "{url}"
BASE_URL = "{base_url}"
HEADERS = {{
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9'
}}

def fetch_page(url):
    """Fetches the content of a single page."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {{url}}: {{e}}")
        return None

def parse_jobs(html):
    """Parses the job listings from the HTML content."""
    soup = BeautifulSoup(html, 'html.parser')
    job_listings = []
    
    # --- THIS IS THE PART YOU MUST CUSTOMIZE ---
    # Inspect the website's HTML to find the correct tags and classes.
    # The values below are placeholders based on your input.
    
    container_selector = ("{ct_str}", "{cc_str}") # (tag, class)
    title_selector = ("{tt_str}", "{tc_str}")     # (tag, class)
    link_selector = ("{lt_str}", "{lc_str}")       # (tag, class)
    
    # Example: soup.find_all('div', class_='job-card')
    for listing in {find_all_str}:
        
        # Example: listing.find('h2', class_='job-title')
        title_element = {find_title_str}
        title = title_element.text.strip() if title_element else 'N/A'
        
        # Example: listing.find('a', class_='job-link')
        link_element = {find_link_str}
        link = link_element['href'] if link_element and link_element.has_attr('href') else 'N/A'
        
        # Clean up the link
        if link != 'N/A' and not link.startswith('http'):
            link = urljoin(BASE_URL, link)
            
        job_listings.append({{
            'title': title,
            'link': link
            # TODO: Add more fields like company, location, etc.
            # e.g., company_element = listing.find('span', class_='company-name')
            # 'company': company_element.text.strip() if company_element else 'N/A'
        }})
        
    return job_listings

def main():
    """Main function to run the scraper."""
    print(f"Scraping jobs from: {{TARGET_URL}}")
    html_content = fetch_page(TARGET_URL)
    
    if html_content:
        jobs = parse_jobs(html_content)
        
        if jobs:
            print(f"Found {{len(jobs)}} jobs.")
            # Convert to DataFrame for easy viewing/saving
            df = pd.DataFrame(jobs)
            print(df)
            # You can save this to a CSV file
            # df.to_csv('jobs.csv', index=False)
        else:
            print("No jobs found. Check your selectors (tags and classes).")
            print("To help, here is the start of the HTML:")
            print(html_content[:2000])

if __name__ == "__main__":
    main()
"""
    return code

# --- Streamlit App UI ---
st.set_page_config(layout="wide", page_title="Job Scraper Assistant")
st.title("Job Scraper Assistant 🤖")

st.info("""
**Welcome!** This tool helps you start the process of web scraping for job details.
Web scraping is complex and site-specific. A single script **cannot** scrape all sites.
This app generates a **boilerplate template** that you **must edit and refine**.
""")

st.warning("""
**Disclaimer:** Always check a website's `robots.txt` and Terms of Service before scraping.
Be respectful: don't send too many requests too quickly. This tool is for educational purposes.
Sites like LinkedIn, Indeed, and Rozee have strong anti-bot measures and may not work with this basic script.
""", icon="⚖️")

# --- Step 1: Select Website ---
st.header("Step 1: Select a Website to Analyze")

col1, col2 = st.columns(2)
with col1:
    category = st.selectbox("Choose a category", list(JOB_SITES.keys()))
with col2:
    selected_site_tuple = st.selectbox(
        "Choose a site",
        JOB_SITES[category],
        format_func=lambda x: x[0] # Display the name (x[0])
    )

base_url = get_base_url(selected_site_tuple[1])
jobs_page_url = st.text_input("Enter the specific jobs page URL (or leave as is)", selected_site_tuple[1])

# --- Step 2: Analyze Site ---
st.header("Step 2: Basic Site Analysis")
if st.button(f"Analyze {selected_site_tuple[0]}"):
    st.subheader(f"Analysis for: {jobs_page_url}")
    
    with st.spinner("Fetching robots.txt..."):
        robots_url = urljoin(base_url, "/robots.txt")
        robots_txt, error = fetch_url_content(robots_url)
        
        with st.expander(f"robots.txt Analysis (from {robots_url})"):
            if robots_txt:
                st.code(robots_txt, language="text")
                st.markdown("---")
                st.markdown("`Disallow:` directives indicate paths that web crawlers *should* avoid. Check for paths like `/jobs/` or `/search/`.")
                
                # Try to find sitemap
                sitemaps = find_sitemap(robots_txt)
                if sitemaps:
                    st.markdown("**Sitemap(s) found in robots.txt:**")
                    for s in sitemaps:
                        st.code(s, language="text")
                else:
                    st.info("No sitemap URL found in robots.txt.")
            else:
                st.error(f"Could not fetch robots.txt: {error}")

    with st.spinner(f"Fetching HTML from {jobs_page_url}..."):
        html_content, error = fetch_url_content(jobs_page_url)
        
        with st.expander("Initial Page HTML (Snippet)"):
            if html_content:
                st.info("Success! Below is the first 2000 characters of the page's HTML. Use this to find the tags and classes for the job listings.")
                st.code(html_content[:2000], language="html")
            else:
                st.error(f"Failed to fetch page HTML: {error}")
                st.warning("This site may be blocking simple scripts. You might need more advanced tools like Selenium (browser automation), which cannot be run from this app.")

# --- Step 3: Generate Boilerplate ---
st.header("Step 3: Generate Boilerplate Scraper Code")
st.markdown("""
Based on the HTML snippet from Step 2 (or by using your browser's "Inspect Element" tool),
find the tags and classes that wrap each job listing.
""")

st.info("**How to find tags/classes:**\n1. Right-click on a job title on the website and select 'Inspect'.\n2. Look at the HTML. Find the tag that contains the whole job item (e.g., `<div class='job-card'>`).\n3. Find the tag inside it that has the job title (e.g., `<h2 class='job-title'>`).\n4. Find the tag that has the link (e.g., `<a class='job-link'>`).")

col3, col4 = st.columns(2)
with col3:
    container_tag = st.text_input("Job **Container** Tag (e.g., div)", "div")
    container_class = st.text_input("Job **Container** Class (e.g., job-listing or card)", "job-card")
    link_tag = st.text_input("Job **Link** Tag (e.g., a)", "a")
with col4:
    title_tag = st.text_input("Job **Title** Tag (e.g., h2 or span)", "h2")
    title_class = st.text_input("Job **Title** Class (e.g., job-title or job-name)")
    link_class = st.text_input("Job **Link** Class (e.g., job-title or read-more)")

if st.button("Generate Python Scraper"):
    generated_code = generate_scraper_code(
        jobs_page_url, 
        base_url,
        container_tag, 
        container_class, 
        title_tag, 
        title_class, 
        link_tag, 
        link_class
    )
    
    st.error("""
    **This is a template!** You **will** need to edit this code. 
    The tags and classes are just guesses. You must inspect the website's HTML to find the correct ones.
    """, icon="⚠️")
    st.code(generated_code, language="python")
