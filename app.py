import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, unquote
import re
import json
import pandas as pd
import time
from fpdf import FPDF
import io
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import pandas as pd

# --- Constants ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
}

def clean_url_name_tuple(url_str, name_hint=""):
    """Cleans google search links and extracts a name."""
    url = url_str.strip()
    name = name_hint.strip()

    # Clean Google search links
    if url.startswith("https://www.google.com/search?q="):
        url = url.split("?q=")[1].split("&")[0]
        url = unquote(url)

    # Clean suspicious/removed links
    if "[suspicious link removed]" in url_str:
        if "National Job Portal" in name_hint:
            url = "https://njp.gov.pk"
            name = "National Job Portal"
        else:
            return None # Can't be sure, skip it
            
    if "[https://www.njp.gov.pk/]" in url_str:
        url = "https://njp.gov.pk"
        name = "National Job Portal"

    if not url.startswith("http"):
        return None # Skip invalid lines

    # Infer name if empty
    if not name:
        try:
            name = urlparse(url).netloc.replace("www.", "").split('.')[0]
            name = name.capitalize()
        except:
            name = "Unknown"
            
    # Special case for linkedin
    if "linkedin.com" in url and "pk" in url:
        name = "LinkedIn Jobs (PK)"

    return (name, url)

# --- Full Website List (Parsed from your text and typos corrected) ---
RAW_SITE_LIST = {
    "Major Job Portals (General)": [
        "https://www.rozee.pk",
        "https://www.mustakbil.com",
        "https://pk.indeed.com",
        "https://www.google.com/search?q=https://www.linkedin.com/jobs/search%3Fcountry%3Dpk",
        "https://www.jobz.pk",
        "https://www.bayt.com/en/pakistan/",
        "https://www.brightspyre.com",
        "https://www.careerokay.com",
        "https://www.google.com/search?q=https://www.jobee.pk",
        "https://www.PakPositions.com",
        "https://www.google.com/search?q=https://www.JobsBirds.com",
        "https://www.google.com/search?q=https://www.Placementam.com",
        "https://www.google.com/search?q=https://www.Jobsleed.com",
        "https://www.apna.co (Search for Pakistan)",
        "https://www.glassdoor.com (Pakistan section)",
        "https://www.guru.com (Primarily for freelance jobs)",
        "https://www.9cv9.com",
        "https://www.jobomas.com",
        "https://www.simplyhired.com (Pakistan)",
        "https://www.careerjet.com (Pakistan)",
    ],
    "Government Job Portals (Federal & Provincial)": [
        "https://www.fpsc.gov.pk (Federal Public Service Commission)",
        "https://www.ppsc.gop.pk (Punjab Public Service Commission)",
        "https://www.spsc.gov.pk (Sindh Public Service Commission)",
        "https://www.kppsc.gov.pk (Khyber Pakhtunkhwa Public Service Commission)",
        "https://www.bpsc.gob.pk (Balochistan Public Service Commission)",
        "https://www.ajkpsc.gov.pk (Azad Kashmir Public Service Commission)",
        "[suspicious link removed] (National Job Portal)",
        "[https://www.njp.gov.pk/] (National Job Portal)",
        "https://www.oec.gov.pk (Overseas Employment Corporation - Govt. Recruiter)",
        "https://www.beoe.gov.pk (Bureau of Emigration & Overseas Employment)",
        "https://www.google.com/search?q=https://www.sbp.org.pk/careers (State Bank of Pakistan)",
        "https://www.google.com/search?q=https://www.jobs.ecp.gov.pk (Election Commission of Pakistan)",
        "https://www.google.com/search?q=https://jobs.cda.gov.pk (Capital Development Authority)",
        "https://careers.hec.gov.pk (Higher Education Commission)",
        "https://gilgitbaltistan.gov.pk/pages/jobs (Gilgit-Baltistan Govt)",
        "https://www.google.com/search?q=https://www.fgei.gov.pk/jobs (Federal Government Educational Institutions)",
        "https://jobs.gov.pk",
        "https://jobs.punjab.gov.pk",
        "https://njp.gov.pk",
        "https://career.fpsc.gov.pk",
        "https://www.pta.gov.pk/en/career",
        "https://www.hec.gov.pk/english/careers",
        "https://careers.sbp.org.pk",
        "https://jobs.oec.gov.pk",
        "https://www.pakrail.gov.pk/Career.aspx",
        "https://careers.pakpost.gov.pk",
        "https://www.paknavy.gov.pk/jobs.html",
        "https://www.joinpakarmy.gov.pk",
        "https://www.joinpaf.gov.pk",
    ],
    "Newspaper & Classifieds Job Sections": [
        "https://www.dawn.com/jobs",
        "https://www.jang.com.pk/jobs",
        "https://www.google.com/search?q=https://www.tribune.com.pk/careers",
        "https://www.nawaiwaqt.com.pk/work-for-us",
        "https://www.olx.com.pk/jobs/",
        "https://www.google.com/search?q=https://www.dubizzle.com.pk (Formerly OLX, includes job listings)",
        "https://www.paperpk.com/jobs/",
        "https://www.jobsalert.pk",
    ],
    "University Career Portals": [
        "https://connect.lums.edu.pk (Lahore University of Management Sciences)",
        "https://careers.iba.edu.pk (Institute of Business Administration, Karachi)",
        "https://nust.edu.pk (National University of Sciences & Technology)",
        "https://qau.edu.pk/faculty-employee/ (Quaid-i-Azam University)",
        "https://pu.edu.pk (Punjab University)",
        "https://careers.uol.edu.pk (University of Lahore)",
        "https://nbc.nust.edu.pk/career/ (NUST Balochistan Campus)",
        "https://www.comsats.edu.pk/jobs",
        "https://www.lums.edu.pk/careers",
        "https://careers.aku.edu/",
        "https://www.gcu.edu.pk/jobs.php",
        "https://www.numl.edu.pk/jobs.php",
        "https://www.ntu.edu.pk/jobs.php",
        "https://www.iba.edu.pk/career/index.php",
    ],
    "Major Company Career Pages": [
        "https://hblasset.com/careers/job-openings/ (HBL - Bank)",
        "https://www.ubldigital.com/Careers (UBL - Bank)",
        "https://www.mcb.com.pk/careers (MCB - Bank)",
        "https://www.meezanbank.com/career-opportunities-in-islamic-banking-9/ (Meezan Bank)",
        "https://www.nbpfunds.com/job-opening/ (NBP Funds)",
        "https://www.google.com/search?q=https://www.telenor.com/career/ (Telenor)",
        "https://www.ufone.com/business/careers/ (Ufone)",
        "https://engrocorp.jobs.hr.cloud.sap/ (Engro Corporation)",
        "https://www.engrofertilizers.com/leaders (Engro Fertilizers)",
        "https://ffc.com.pk/careers/ (Fauji Fertilizer Company)",
        "https://fccl.com.pk/eng/careers/ (Fauji Cement)",
        "https://www.lucky-cement.com/careers/ (Lucky Cement)",
        "https://luckycore.com/recruitment/ (Lucky Core Industries)",
    ],
    "Recruitment Agencies & OEPs": [
        "https://www.khawajamanpower.com",
        "https://www.ditrc.com",
        "https://www.ghaffarsons.com",
        "https://www.greenlandoep.com",
        "https://www.alahadgrouppakistan.com",
        "https://www.falishamanpower.com",
        "https://www.teleportmanpower.com",
        "https://www.alsaqibrecruitmentgroup.com",
        "https://www.hrbs.com.pk",
        "https://www.ginitalent.com",
        "https://www.hrworld.org.pk",
        "https://www.fulcrum-pk.com",
        "https://www.stiryum.com",
        "https://www.talenthue.com",
        "https://www.enlyststaffing.com",
        "https://www.google.com/search?q=https://www.psbpakistan.com",
        "https://www.google.com/search?q=https://www.waraichenterprises.com",
        "https://www.baigtravels.com",
        "https://www.luna.com.pk",
        "https://www.chaudharyassociates.com",
        "https://www.premierinternational.com.pk",
        "https://www.nira-intl.agency",
        "https://www.nexgentrs.com",
        "https://www.bossoep.com",
        "https://www.reliancehr.co.uk",
        "https://www.barcamanpower.com",
        "https://www.tricommanagement.org",
        "https://www.google.com/search?q=https://www.airworldtravel.pk",
        "https://www.muzainahoverseas.com",
    ],
    "Private Sector (Other)": [
        "https://www.pakistanjobsbank.com",
        "https://www.pakjobspedia.com",
        "https://www.jobz.pk/private-jobs/",
        "https://www.pakijobs.pk",
        "https://www.jobsborse.com",
        "https://www.jobustad.com",
        "https://www.nokrijunction.com",
        "https://www.mehnat.pk",
        "https://www.latestjobsinpakistan.net",
        "https://www.jobzmall.pk",
        "https://www.careerjoin.com",
    ],
    "International & Freelance": [
        "https://www.linkedin.com (Global)",
        "https://www.indeed.com (Global aggregator)",
        "https://www.glassdoor.com (Global, includes reviews)",
        "https://www.monster.com (Global)",
        "https://www.careerbuilder.com (Strong in North America & Europe)",
        "https://www.jooble.org (Global job aggregator)",
        "https://www.ziprecruiter.com (Primarily US/Canada, but global reach)",
        "https://www.simplyhired.com (Global aggregator)",
        "https://www.adzuna.com (Strong in UK, Australia, Europe)",
        "https://www.flexjobs.com (Curated remote & flexible jobs)",
        "https://weworkremotely.com (Remote-first jobs)",
        "https://remote.co (Remote jobs & resources)",
        "https://www.remoteok.io (Tech-focused remote jobs)",
        "https://www.upwork.com (Freelance marketplace)",
        "https://www.freelancer.com (Freelance marketplace)",
        "https://www.peopleperhour.com (Freelance)",
        "https://www.toptal.com (Top freelance tech/finance talent)",
        "https://www.freelancer.com/jobs/pakistan",
        "https://www.upwork.com/nx/find-work/",
        "https://www.peopleperhour.com/freelance-jobs/location/pakistan",
        "https://www.toptal.com/freelance-jobs/pakistan",
    ],
    "Niche & Special-Interest": [
        "https://www.dice.com (Technology jobs, primarily US)",
        "https://wellfound.com (Formerly AngelList Talent - Startup jobs)",
        "https://relocate.me (Tech jobs with relocation packages)",
        "https://www.idealist.org (Non-profit & social impact jobs)",
        "https://www.gooverseas.com (Teaching & working abroad)",
        "https://www.goabroad.com (Internships & teaching abroad)",
        "https://www.theladders.com (High-earning ($100k+) jobs, primarily US)",
        "https://hrcp-web.org/hrcpweb/jobs/",
        "https://www.unjobs.org/duty_stations/pakistan",
        "https://ngojobs.pk",
        "https://www.brightermonday.pk",
        "https://pk.joblum.com",
    ],
    "Regional: North America": [
        "https://www.usajobs.gov (Official US Federal Government jobs)",
        "https://www.snagajob.com (US hourly jobs)",
        "https://www.linkup.com (US job aggregator from company sites)",
        "https://www.jobbank.gc.ca (Official Government of Canada job board)",
        "https://www.workopolis.com (Canada)",
        "https://www.google.com/search?q=https://www.eluta.ca (Canada, aggregator)",
        "https://www.jobillico.com (Canada, strong in Quebec)",
    ],
    "Regional: Europe": [
        "https://europa.eu/eures/portal/ (EURES - The European Job Mobility Portal)",
        "https://www.eurojobs.com (Pan-European)",
        "https://www.jobsinnetwork.com (English-speaking jobs in Europe)",
        "https://www.stepstone.de (Germany's leading job board)",
        "https://www.arbeitsagentur.de/jobsuche/ (German Federal Employment Agency)",
        "https://www.xing.com/jobs (Germany, Austria, Switzerland)",
        "https://www.google.com/search?q=https://www.francetravail.fr (France's official employment service)",
        "https://www.hellowork.com (France)",
        "https://www.reed.co.uk (UK)",
        "https://www.cv-library.co.uk (UK)",
        "https://www.totaljobs.com (UK)",
        "https://www.gov.uk/find-a-job (Official UK government job site)",
    ],
    "Regional: Asia & Pacific": [
        "https://www.seek.com.au (Australia)",
        "https://www.google.com/search?q=https://www.ethicaljobs.org.au (Australia, Not-for-profit)",
        "https://gradaustralia.com.au (Australia, Graduate jobs)",
        "https://au.jora.com (Australia, Aggregator)",
        "https://www.mycareersfuture.gov.sg (Singapore, Government portal)",
        "https://www.jobstreet.com.sg (Singapore)",
        "https://www.jobsdb.com.sg (Singapore)",
        "https://glints.com (Singapore & Southeast Asia)",
        "https://www.jobstreet.com.my (Malaysia)",
        "https://myfuturejobs.gov.my (Malaysia, Government portal)",
        "https://www.ricebowl.my (Malaysia)",
        "https://www.naukri.com (India)",
        "https://www.timesjobs.com (India)",
    ],
    "Regional: Middle East": [
        "https://www.gulftalent.com (Pan-Gulf)",
        "https://www.naukrigulf.com (Pan-Gulf)",
        "https://www.google.com/search?q=https://www.foundit.ae (Formerly Monster Gulf - UAE/Gulf)",
        "https://laimoon.com (UAE/Gulf, includes courses)",
        "https://sa.talent.com (Saudi Arabia)",
        "https://www.mihnati.com (Saudi Arabia)",
        "https://www.tanqeeb.com (Pan-Middle East)",
    ]
}

JOB_SITES = {}
for category, lines in RAW_SITE_LIST.items():
    cleaned_tuples = []
    for line in lines:
        # Extract name hint if present
        name_hint = ""
        line = line.replace("https_//", "https://").replace("https_", "https://") # Fix typos in source
        line = line.replace("httpss_", "https://").replace("httpswww", "https://www")
        
        if "(" in line:
            parts = line.split("(", 1)
            line = parts[0].strip()
            name_hint = parts[1].replace(")", "").strip()
            
        cleaned = clean_url_name_tuple(line, name_hint)
        if cleaned:
            cleaned_tuples.append(cleaned)
    
    # Add to main dict, removing duplicates
    JOB_SITES[category] = sorted(list(set(cleaned_tuples)))


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
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    except Exception:
        return url # fallback

def find_sitemap(robots_txt_content):
    """Finds sitemap URLs in robots.txt content."""
    sitemaps = re.findall(r'Sitemap:\s*(.*)', robots_txt_content, re.IGNORECASE)
    return [s.strip() for s in sitemaps]

def check_robots_disallow(robots_txt_content, url):
    """
    Checks if a specific URL path is disallowed by robots.txt.
    Returns: "Allowed", "Disallowed", or "Unknown"
    """
    if not robots_txt_content:
        return "Unknown (No robots.txt)"

    try:
        path = urlparse(url).path or "/"
        
        # Simple parser for Disallow rules
        disallowed_paths = []
        user_agent_applies = False
        saw_global_agent = False

        for line in robots_txt_content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            try:
                # Use regex to handle potential missing space after colon
                match = re.match(r'([^:]+):\s*(.*)', line, re.IGNORECASE)
                if not match:
                    continue
                
                key = match.group(1).strip().lower()
                value = match.group(2).strip()

                if key == "user-agent":
                    if value == "*":
                        user_agent_applies = True
                        saw_global_agent = True
                    elif value == "bot" and not saw_global_agent: # Simple check
                        user_agent_applies = True
                    else:
                        user_agent_applies = False # Rule is for different agent
                
                if key == "disallow" and user_agent_applies:
                    if value: # Only add if there is a path
                        disallowed_paths.append(value)
            except Exception:
                pass # Ignore malformed lines

        # Check path against disallowed paths
        for dis_path in disallowed_paths:
            if dis_path == "/":
                return "Disallowed (All)" # Site disallows all
            if path.startswith(dis_path):
                return f"Disallowed (Rule: {dis_path})"
        
        return "Allowed"

    except Exception:
        return "Unknown (Parse Error)"


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

def clean_text_for_pdf(text):
    """Removes non-latin-1 characters to avoid FPDF errors."""
    if not isinstance(text, str):
        text = str(text)
    return text.encode('latin-1', 'replace').decode('latin-1')

def create_pdf_report(df):
    """Creates a PDF report from a DataFrame."""
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font('Arial', '', 8)
    
    # Calculate column widths
    # A4 Landscape width is 297mm. Margins 10mm each side = 277mm usable.
    # 6 columns: Cat, Site, Strategy, Robots, Page Status, URL
    # Give URL more space
    col_widths = {
        "Category": 40,
        "Site Name": 40,
        "Strategy": 30,
        "Robots Rule": 30,
        "Page Status": 67, # Allow space for error messages
        "URL": 70
    }
    
    # Add Header
    pdf.set_font('Arial', 'B', 8)
    pdf.set_fill_color(240, 240, 240)
    for col in df.columns:
        pdf.cell(col_widths[col], 10, col, 1, 0, 'C', fill=True)
    pdf.ln()

    # Add Rows
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        # Truncate long text to fit in cells
        for col in df.columns:
            text = clean_text_for_pdf(row[col])
            # Check if text is wider than cell, truncate if necessary
            if pdf.get_string_width(text) > col_widths[col] - 2: # 2mm padding
                # Simple truncate
                text = text[:int(col_widths[col] / 1.5)] + '...'
            
            pdf.cell(col_widths[col], 10, text, 1, 0, 'L')
        pdf.ln()
    
    # Return PDF data as bytes
    return pdf.output(dest='S') # <- FIXED: Removed .encode('latin-1')


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
import pandas as pd

# --- Configuration ---
TARGET_URL = "{url}"

def setup_driver():
    # Sets up the Chrome WebDriver for Streamlit Cloud
    # This assumes 'chromedriver' and 'google-chrome-stable' are in packages.txt
    try:
        service = Service() # Finds the driver installed in the system PATH
        options = webdriver.ChromeOptions()
        options.add_argument('--headless') # Run without opening a browser window
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        driver = webdriver.Chrome(service=service, options=options)
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {{e}}")
        print("This app must be deployed on Streamlit Cloud with packages.txt for Selenium to work.")
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

# --- Step 1: Full Site Analysis ---
st.header("Step 1: Full Site Analysis")

total_sites_count = sum(len(v) for v in JOB_SITES.values())
st.warning(f"""
**Heads Up:** This will analyze **all {total_sites_count}+ sites** in the list.
This process will take **several minutes** to complete. Please be patient.
Running this many requests at once may also get your IP address rate-limited by some sites.
""", icon="⏱️")

if st.button("Analyse websites"):
    # Flatten the JOB_SITES dictionary into a list of tuples
    sites_to_analyze = []
    for category, sites in JOB_SITES.items():
        for site_name, url in sites:
            sites_to_analyze.append((category, site_name, url))
    
    total_sites = len(sites_to_analyze)
    report_data = []
    
    progress_bar = st.progress(0.0, text=f"Starting analysis for {total_sites} sites...")
    status_text = st.empty()

    for i, (category, site_name, url) in enumerate(sites_to_analyze):
        status_text.text(f"Analyzing ({i+1}/{total_sites}): {site_name}...")
        
        base_url = get_base_url(url)
        robots_url = urljoin(base_url, "/robots.txt")
        
        # 1. Fetch robots.txt
        robots_txt, robots_error = fetch_url_content(robots_url)
        
        # 2. Check Robots Rule
        robots_rule = check_robots_disallow(robots_txt, url)

        # 3. Fetch Page HTML
        html_content, html_error = fetch_url_content(url) # <-- Fixed bug here
        page_status = "OK" if html_content else (str(html_error) or "Fetch Failed")
        
        # 4. Determine Strategy
        strategy_rec = "Unknown"
        if html_content:
            strategy, _ = analyze_html_strategy(html_content)
            if strategy == 'json-ld':
                strategy_rec = "JSON-LD (Easy)"
            elif strategy == 'dynamic':
                strategy_rec = "Dynamic (Hard)"
            elif strategy == 'static':
                strategy_rec = "Static HTML (Medium)"
            else:
                strategy_rec = "Empty HTML (Check URL)"
        else:
            strategy_rec = f"Blocked ({page_status})"
            
        report_data.append({
            "Category": category,
            "Site Name": site_name,
            "URL": url,
            "Page Status": page_status,
            "Robots Rule": robots_rule,
            "Strategy": strategy_rec
        })
        
        # Update progress bar
        progress_bar.progress((i + 1) / total_sites, text=f"Analyzing ({i+1}/{total_sites}): {site_name}...")
        
        # Small delay to be polite to servers
        time.sleep(0.05) 

    status_text.success(f"Analysis complete! Processed {total_sites} sites.")
    
    # Create and display DataFrame
    df = pd.DataFrame(report_data, columns=["Category", "Site Name", "Strategy", "Robots Rule", "Page Status", "URL"])
    st.session_state['analysis_report'] = df


# --- Download Reports & Display Data ---
if 'analysis_report' in st.session_state:
    df = st.session_state['analysis_report']
    
    st.subheader("Download Reports")
    
    # Create CSV data
    csv_data = df.to_csv(index=False).encode('utf-8')
    
    # Create PDF data
    pdf_data = create_pdf_report(df)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="Download Report as CSV",
            data=csv_data,
            file_name="website_analysis_report.csv",
            mime="text/csv",
        )
    with col2:
        st.download_button(
            label="Download Report as PDF",
            data=pdf_data,
            file_name="website_analysis_report.pdf",
            mime="application/pdf",
        )
        
    st.subheader("Analysis Report")
    st.dataframe(df, use_container_width=True)


# --- Step 2: Generate Boilerplate Script ---
st.header("Step 2: Generate Boilerplate Script")

if 'analysis_report' in st.session_state:
    df = st.session_state['analysis_report']
    
    # Create a user-friendly list for the selectbox
    site_options = df.apply(
        lambda row: f"{row['Site Name']} ({row['Strategy']})", 
        axis=1
    ).tolist()
    
    st.info("Select a site from the report below to generate a starter script.")
    selected_site_str = st.selectbox(
        "Choose a site to generate code for:",
        site_options,
        index=None,
        placeholder="Select a site..."
    )

    if selected_site_str:
        # Find the corresponding row in the DataFrame
        selected_row = df[df.apply(lambda row: f"{row['Site Name']} ({row['Strategy']})", axis=1) == selected_site_str].iloc[0]
        
        url = selected_row['URL']
        base_url = get_base_url(url)
        strategy = selected_row['Strategy']
        
        st.subheader(f"Generated Script for: {selected_row['Site Name']}")
        
        generated_code = None
        if "JSON-LD" in strategy:
            st.success("This script is configured to parse JSON-LD. It should be highly reliable.")
            generated_code = generate_json_ld_scraper(url)
        elif "Dynamic" in strategy:
            st.warning("This is a Selenium script for dynamic sites. You must inspect the page and update the selectors (e.g., `div.job-listing`).")
            generated_code = generate_selenium_scraper(url)
        elif "Static" in strategy:
            st.warning("This is a BeautifulSoup script. You **must** inspect the page and update the selectors (e.g., `container_class`, `title_class`).")
            generated_code = generate_bs4_scraper(url, base_url)
        elif "Blocked" in strategy:
            st.error(f"Cannot generate script. The site blocked the analysis request ({selected_row['Page Status']}). A simple scraper will not work.")
        
        if generated_code:
            st.code(generated_code, language="python")

else:
    st.info("Run the analysis in Step 1 to generate a report and enable code generation.")
