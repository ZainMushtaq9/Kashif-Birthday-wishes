import time
import pandas as pd
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

def init_driver():
    """Initialize headless Chromium for Streamlit Cloud."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    
    try:
        service = Service("/usr/bin/chromedriver")
        return webdriver.Chrome(service=service, options=chrome_options)
    except:
        return webdriver.Chrome(options=chrome_options)

def get_job_links_from_github(raw_url: str):
    """Fetch list of job site URLs from a raw GitHub txt file."""
    try:
        response = requests.get(raw_url, timeout=10)
        response.raise_for_status()
        links = [line.strip() for line in response.text.splitlines() if line.strip() and line.strip().startswith('http')]
        print(f"[INFO] Loaded {len(links)} job websites from GitHub.")
        return links
    except Exception as e:
        print(f"[ERROR] Could not fetch from GitHub: {e}")
        return []

def extract_job_details(element, url):
    """Extract detailed job information from element."""
    try:
        text = element.text.strip()
        lines = [l.strip() for l in text.split('\n') if l.strip()]
        
        if not lines or len(text) < 20:
            return None
        
        # Extract title (usually first line)
        title = lines[0][:150]
        
        # Try to find company name
        company = "Not specified"
        for line in lines[1:4]:
            if any(word in line.lower() for word in ['company', 'pvt', 'ltd', 'inc', 'corp']):
                company = line[:100]
                break
        
        if company == "Not specified":
            company = url.split("//")[-1].split("/")[0].replace("www.", "").split('.')[0].title()
        
        # Extract location
        location = "Pakistan"
        for line in lines:
            if any(city in line.lower() for city in ['karachi', 'lahore', 'islamabad', 'rawalpindi', 
                                                       'faisalabad', 'multan', 'peshawar', 'quetta', 
                                                       'pakistan', 'remote']):
                location = line[:100]
                break
        
        # Try to get apply link
        try:
            link_elem = element.find_element(By.TAG_NAME, "a")
            job_link = link_elem.get_attribute("href")
            if not job_link or not job_link.startswith('http'):
                job_link = url
        except:
            job_link = url
        
        # Extract description (combine middle lines)
        description = " ".join(lines[1:4])[:300] if len(lines) > 1 else "Details available on website"
        
        # Extract salary if mentioned
        salary = "Not specified"
        for line in text.split('\n'):
            if any(word in line.lower() for word in ['rs', 'pkr', 'salary', 'lakh', 'thousand', 'k per']):
                salary = line.strip()[:100]
                break
        
        return {
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "salary": salary,
            "link": job_link,
            "source": url.split("//")[-1].split("/")[0],
            "posted_date": datetime.now().strftime("%Y-%m-%d"),
            "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    except Exception as e:
        return None

def scrape_with_selenium(driver, url):
    """Scrape jobs using Selenium with multiple selectors."""
    jobs = []
    try:
        driver.get(url)
        time.sleep(4)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Multiple selector strategies
        selectors = [
            ".job-listing", ".job-item", ".job-card", ".job-box",
            ".job", ".vacancy", ".opening", ".position",
            "[class*='job']", "[class*='vacancy']",
            "article", ".card", ".listing"
        ]
        
        for selector in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for elem in elements[:20]:  # Limit to 20 per selector
                    job_data = extract_job_details(elem, url)
                    if job_data and job_data not in jobs:
                        jobs.append(job_data)
                
                if len(jobs) >= 15:
                    break
            except:
                continue
                
    except Exception as e:
        print(f"[ERROR] Selenium scraping {url}: {e}")
    
    return jobs

def scrape_with_beautifulsoup(url):
    """Fallback scraper using BeautifulSoup."""
    jobs = []
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find job containers
        job_containers = []
        for tag in ['article', 'div', 'li', 'tr']:
            for class_name in ['job', 'vacancy', 'listing', 'card', 'item']:
                job_containers.extend(soup.find_all(tag, class_=lambda x: x and class_name in x.lower()))
        
        for container in job_containers[:15]:
            text = container.get_text(strip=True)
            if len(text) > 30:
                title = text[:150].split('\n')[0]
                link_tag = container.find('a')
                job_link = link_tag.get('href') if link_tag else url
                
                if job_link and not job_link.startswith('http'):
                    job_link = requests.compat.urljoin(url, job_link)
                
                jobs.append({
                    "title": title,
                    "company": url.split("//")[-1].split("/")[0].replace("www.", "").split('.')[0].title(),
                    "location": "Pakistan",
                    "description": text[:300],
                    "salary": "Not specified",
                    "link": job_link,
                    "source": url.split("//")[-1].split("/")[0],
                    "posted_date": datetime.now().strftime("%Y-%m-%d"),
                    "scrape_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                
    except Exception as e:
        print(f"[ERROR] BeautifulSoup scraping {url}: {e}")
    
    return jobs

def scrape_all_sources(raw_txt_url):
    """Main scraping function that processes all job sources."""
    links = get_job_links_from_github(raw_txt_url)
    
    if not links:
        print("[ERROR] No links loaded from GitHub")
        return pd.DataFrame()
    
    driver = None
    all_jobs = []
    
    try:
        driver = init_driver()
        
        for i, site in enumerate(links, 1):
            print(f"[SCRAPE {i}/{len(links)}] Processing: {site}")
            
            # Try Selenium first
            site_jobs = scrape_with_selenium(driver, site)
            
            # Fallback to BeautifulSoup if Selenium fails
            if not site_jobs:
                print(f"[FALLBACK] Trying BeautifulSoup for {site}")
                site_jobs = scrape_with_beautifulsoup(site)
            
            all_jobs.extend(site_jobs)
            print(f"[INFO] Found {len(site_jobs)} jobs from {site}")
            
            time.sleep(2)  # Rate limiting
            
    except Exception as e:
        print(f"[ERROR] Main scraping error: {e}")
    finally:
        if driver:
            driver.quit()
    
    # Create DataFrame and remove duplicates
    df = pd.DataFrame(all_jobs)
    if not df.empty:
        df = df.drop_duplicates(subset=['title', 'company'], keep='first')
        print(f"[SUCCESS] Total unique jobs scraped: {len(df)}")
    else:
        print("[WARNING] No jobs found")
    
    return df

def save_jobs_cache(df, filename="jobs_cache.csv"):
    """Save scraped jobs to cache file."""
    try:
        df.to_csv(filename, index=False)
        print(f"[SAVED] Jobs cached to {filename}")
        return True
    except Exception as e:
        print(f"[ERROR] Could not save cache: {e}")
        return False

def load_jobs_cache(filename="jobs_cache.csv"):
    """Load jobs from cache file."""
    try:
        df = pd.read_csv(filename)
        print(f"[LOADED] {len(df)} jobs from cache")
        return df
    except Exception as e:
        print(f"[INFO] No cache file found: {e}")
        return pd.DataFrame()
