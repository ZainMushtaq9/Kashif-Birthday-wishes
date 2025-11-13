import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
import json

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

def analyze_html_strategy(html_content):
    """
    Analyzes the HTML to determine the best scraping strategy.
    Returns: (strategy_type, data)
    strategy_type: 'json-ld', 'dynamic', 'static', 'empty'
    data: The parsed JSON-LD data if found
    """
    if not html_content:
        return 'empty', None
        
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Strategy 1: Look for JSON-LD structured data (Gold Standard)
    try:
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            if script.string:
                data = json.loads(script.string)
                # Check if it's a list of items or a single item
                if isinstance(data, dict) and data.get('@type') == 'JobPosting':
                    return 'json-ld', data
                if isinstance(data, list) and len(data) > 0 and data[0].get('@type') == 'JobPosting':
                     return 'json-ld', data
                # Check for graph structures
                if isinstance(data, dict) and '@graph' in data:
                    for item in data['@graph']:
                         if item.get('@type') == 'JobPosting':
                             return 'json-ld', data
    except Exception:
        pass  # Ignore JSON parsing errors

    # Strategy 2: Look for signs of a dynamic/JS-heavy site
    body_text = soup.body.get_text(strip=True) if soup.body else ""
    if len(body_text) < 1000 and (
        'loading...' in html_content or 
        'data-reactroot' in html_content or
        'id="app"' in html_content or 
        'id="__next"' in html_content):
        return 'dynamic', None

    # Strategy 3: Default to static HTML
    return 'static', None

def generate_bs4_scraper(url, base_url):
    """Generates boilerplate Python scraper code for standard BeautifulSoup."""
    
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
    # Fetches the content of a single page.
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {{url}}: {{e}}")
        return None

def parse_jobs(html):
    # Parses the job listings from the HTML content.
    soup = BeautifulSoup(html, 'html.parser')
    job_listings = []
    
    # --- THIS IS THE PART YOU MUST CUSTOMIZE ---
    # Inspect the website's HTML to find the correct tags and classes.
    # The values below are BEST GUESSES and are probably WRONG.
    
    container_tag = "div"
    container_class = "job-listing" # GUESS: Try 'job-card', 'listing', 'job-item'
    
    title_tag = "h2"
    title_class = "job-title"       # GUESS: Try 'title', 'job-name'
    
    link_tag = "a"
    
    # Find all job listing containers
    for listing in soup.find_all(container_tag, class_=container_class):
        
        title_element = listing.find(title_tag, class_=title_class)
        title = title_element.text.strip() if title_element else 'N/A'
        
        # Try to find link inside title, or on the container
        link_element = listing.find(link_tag) 
        if title_element and not link_element:
             link_element = title_element.find(link_tag)
             
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
    # Main function to run the scraper.
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

def generate_json_ld_scraper(url):
    """Generates boilerplate Python scraper code for parsing JSON-LD."""
    
    code = f"""
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd

# --- Configuration ---
TARGET_URL = "{url}"
HEADERS = {{
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}}

def fetch_page(url):
    # Fetches the content of a single page.
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {{url}}: {{e}}")
        return None

def parse_jobs_from_json_ld(html):
    # Parses the job listings from JSON-LD script tags.
    soup = BeautifulSoup(html, 'html.parser')
    job_listings = []
    
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in json_ld_scripts:
        if not script.string:
            continue
            
        try:
            data = json.loads(script.string)
            
            # Case 1: Data is a list of JobPostings
            if isinstance(data, list):
                for item in data:
                    if item.get('@type') == 'JobPosting':
                        job_listings.append({{
                            'title': item.get('title'),
                            'description': item.get('description'),
                            'company': item.get('hiringOrganization', {{}}).get('name'),
                            'location': item.get('jobLocation', {{}}).get('address', {{}}).get('addressLocality'),
                            'date_posted': item.get('datePosted'),
                            'link': item.get('url') or TARGET_URL
                        }})
                        
            # Case 2: Data is a single JobPosting
            elif isinstance(data, dict) and data.get('@type') == 'JobPosting':
                item = data
                job_listings.append({{
                    'title': item.get('title'),
                    'description': item.get('description'),
                    'company': item.get('hiringOrganization', {{}}).get('name'),
                    'location': item.get('jobLocation', {{}}).get('address', {{}}).get('addressLocality'),
                    'date_posted': item.get('datePosted'),
                    'link': item.get('url') or TARGET_URL
                }})
            
            # Case 3: Data is in a '@graph'
            elif isinstance(data, dict) and '@graph' in data:
                for item in data['@graph']:
                    if item.get('@type') == 'JobPosting':
                        job_listings.append({{
                            'title': item.get('title'),
                            'description': item.get('description'),
                            'company': item.get('hiringOrganization', {{}}).get('name'),
                            'location': item.get('jobLocation', {{}}).get('address', {{}}).get('addressLocality'),
                            'date_posted': item.get('datePosted'),
                            'link': item.get('url') or TARGET_URL
                        }})
                        
        except json.JSONDecodeError:
            print("Found a JSON-LD script, but failed to parse it.")
            
    return job_listings

def main():
    # Main function to run the scraper.
    print(f"Scraping jobs from: {{TARGET_URL}}")
    html_content = fetch_page(TARGET_URL)
    
    if html_content:
        jobs = parse_jobs_from_json_ld(html_content)
        
        if jobs:
            print(f"Found {{len(jobs)}} jobs via JSON-LD.")
            df = pd.DataFrame(jobs)
            print(df)
            # df.to_csv('jobs_json_ld.csv', index=False)
        else:
            print("No 'JobPosting' JSON-LD data found. The site structure may have changed.")

if __name__ == "__main__":
    main()
"""
    return code

def generate_selenium_scraper(url):
    """Generates boilerplate Python scraper code for Selenium."""
    code = f"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# --- Configuration ---
TARGET_URL = "{url}"

def setup_driver():
    # Sets up the Chrome WebDriver.
    # This uses webdriver_manager to automatically download the correct driver.
    try:
        service = Service(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument('--headless') # Run without opening a browser window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {{e}}")
        print("Please ensure you have Google Chrome installed.")
        return None

def parse_jobs_with_selenium(driver):
    # Parses the job listings from a dynamic page.
    job_listings = []
    
    # --- THIS IS THE PART YOU MUST CUSTOMIZE ---
    # Inspect the website's HTML to find the correct selectors.
    # These are BEST GUESSES and are probably WRONG.
    
    # Use By.CSS_SELECTOR or By.CLASS_NAME for better performance
    container_selector = "div.job-listing"  # GUESS: Try 'div.job-card', 'li.job-item'
    title_selector = "h2.job-title"       # GUESS: Try 'span.title', 'a.job-link'
    link_selector = "a.job-link"          # GUESS: Try 'a'
    
    try:
        # Find all job listing containers
        # Adjust the selector as needed
        listings = driver.find_elements(By.CSS_SELECTOR, container_selector)
        
        if not listings:
            print("No listings found with that selector. Trying another common selector...")
            listings = driver.find_elements(By.CSS_SELECTOR, "div.job-card") # Second guess
            
        print(f"Found {{len(listings)}} potential job elements.")

        for listing in listings:
            try:
                title_element = listing.find_element(By.CSS_SELECTOR, title_selector)
                title = title_element.text.strip()
            except:
                title = 'N/A'
                
            try:
                link_element = listing.find_element(By.CSS_SELECTOR, link_selector)
                link = link_element.get_attribute('href')
            except:
                try:
                    # Fallback: find any 'a' tag
                    link_element = listing.find_element(By.TAG_NAME, 'a')
                    link = link_element.get_attribute('href')
                except:
                    link = 'N/A'
            
            job_listings.append({{
                'title': title,
                'link': link
                # TODO: Add more fields like company, location
                # e.g., 'company': listing.find_element(By.CSS_SELECTOR, 'span.company-name').text.strip()
            }})
            
    except Exception as e:
        print(f"Error during parsing: {{e}}")
        
    return job_listings

def main():
    # Main function to run the scraper.
    print("Setting up WebDriver...")
    driver = setup_driver()
    
    if driver:
        print(f"Scraping jobs from: {{TARGET_URL}}")
        driver.get(TARGET_URL)
        
        # Wait for the dynamic content to load
        # You MUST adjust this wait time.
        # A better way is to use WebDriverWait (see Selenium docs)
        print("Waiting 5 seconds for page to load...")
        time.sleep(5) 
        
        jobs = parse_jobs_with_selenium(driver)
        
        if jobs:
            print(f"Found {{len(jobs)}} jobs.")
            df = pd.DataFrame(jobs)
            print(df)
            # df.to_csv('jobs_selenium.csv', index=False)
        else:
            print("No jobs found. Check your selectors or wait time.")
            # Save page source for debugging
            # with open('page_source.html', 'w', encoding='utf-8') as f:
            #    f.write(driver.page_source)
            # print("Saved page_source.html for debugging.")
            
        driver.quit()

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
This app analyzes a site and generates a **boilerplate template** that you **must edit and refine**.
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

# --- Step 2: Generate Analysis & Scraper ---
st.header("Step 2: Generate Analysis & Scraper")

if st.button(f"Analyze & Generate Code for {selected_site_tuple[0]}"):
    st.subheader(f"Analysis for: {jobs_page_url}")
    generated_code = None
    
    with st.spinner("Analyzing site... this may take a moment."):
        # 1. Fetch robots.txt
        robots_url = urljoin(base_url, "/robots.txt")
        robots_txt, robots_error = fetch_url_content(robots_url)
        
        # 2. Fetch Page HTML
        html_content, html_error = fetch_url_content(jobs_page_url)
        
        # 3. Start Analysis Report
        with st.expander("Analysis Report", expanded=True):
            
            # Report on robots.txt
            st.markdown("#### `robots.txt` Analysis")
            if robots_txt:
                st.code(robots_txt, language="text")
                st.markdown("`Disallow:` directives indicate paths web crawlers *should* avoid. Check for paths like `/jobs/`, `/search/`, or `/api/`.")
                sitemaps = find_sitemap(robots_txt)
                if sitemaps:
                    st.markdown("**Sitemap(s) found:**")
                    for s in sitemaps: st.code(s, language="text")
            else:
                st.error(f"Could not fetch robots.txt: {robots_error}")
            
            st.markdown("---")
            st.markdown("#### Page Analysis & Scraping Strategy")

            # Report on HTML & Strategy
            if html_content:
                strategy, data = analyze_html_strategy(html_content)
                
                if strategy == 'json-ld':
                    st.success("**Strategy: JSON-LD Data (Gold Standard)**")
                    st.markdown("This site provides structured `JobPosting` data. This is the most reliable way to scrape. The script below is configured to parse this data directly.")
                    generated_code = generate_json_ld_scraper(jobs_page_url)
                
                elif strategy == 'dynamic':
                    st.warning("**Strategy: Dynamic JavaScript Site**")
                    st.markdown("The page's HTML is very light and seems to load content using JavaScript. A simple `requests` script will **fail**.")
                    st.markdown("**Recommendation:** Use a browser automation tool like `Selenium`. A boilerplate script for Selenium is provided below. You will need to install `selenium` and `webdriver-manager-chrome`.")
                    generated_code = generate_selenium_scraper(jobs_page_url)
                
                else: # 'static'
                    st.info("**Strategy: Static HTML Site**")
                    st.markdown("This site appears to be standard HTML. A `BeautifulSoup` script is provided below. **You will almost certainly need to edit the script's selectors (tags and classes)** to match the site's structure.")
                    st.markdown("Use your browser's 'Inspect Element' tool to find the correct selectors.")
                    generated_code = generate_bs4_scraper(jobs_page_url, base_url)
            
            else:
                st.error(f"**Strategy: Blocked**")
                st.markdown(f"Failed to fetch page HTML: **{html_error}**")
                st.warning("This site is likely blocking simple scripts (e.g., 403 Forbidden, 503 Service Unavailable). A basic scraper will not work. This requires advanced techniques like rotating proxies or Selenium with anti-bot detection measures, which are beyond the scope of this tool.")

    # 4. Display the generated code
    if generated_code:
        st.subheader("Generated Boilerplate Script")
        st.code(generated_code, language="python")
    else:
        st.error("Could not generate a script for this site due to the errors above.")
