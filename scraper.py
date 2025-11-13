import time
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def init_driver():
    """Initialize headless Chromium for Streamlit Cloud."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)


def get_job_links_from_github(raw_url: str):
    """Fetch list of job site URLs from a raw GitHub txt file, with fallback."""
    try:
        response = requests.get(raw_url, timeout=10)
        response.raise_for_status()
        links = [line.strip() for line in response.text.splitlines() if line.strip()]
        if not links:
            raise ValueError("Empty file or invalid links.")
        print(f"[INFO] Loaded {len(links)} job websites from GitHub.")
        return links
    except Exception as e:
        print(f"[WARN] Could not fetch from GitHub: {e}")
        # fallback default websites
        return [
            "https://www.rozee.pk",
            "https://www.brightspyre.com",
            "https://www.mustakbil.com",
            "https://www.careerokay.com",
            "https://www.jobee.pk"
        ]


def generic_scraper(driver, url):
    """Basic scraper that extracts visible job titles from known HTML patterns."""
    jobs = []
    try:
        driver.get(url)
        time.sleep(3)
        selectors = [".job", ".job-list-item", ".job-box", "tr", "li", "article"]
        for sel in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elements:
                text = e.text.strip()
                if len(text) > 25 and "apply" not in text.lower():
                    jobs.append({
                        "title": text.split("\n")[0][:100],
                        "company": url.split("//")[-1].split("/")[0],
                        "link": url,
                        "source": url
                    })
            if len(jobs) > 10:
                break
    except Exception as e:
        print(f"[ERROR] scraping {url}: {e}")
    return jobs


def scrape_from_github(raw_txt_url):
    """Scrape all websites listed in job_links.txt."""
    links = get_job_links_from_github(raw_txt_url)
    driver = init_driver()
    all_jobs = []
    for site in links:
        print(f"[SCRAPE] Fetching from {site}")
        site_jobs = generic_scraper(driver, site)
        all_jobs.extend(site_jobs)
    driver.quit()
    df = pd.DataFrame(all_jobs)
    if df.empty:
        print("[WARN] No jobs found.")
    else:
        print(f"[DONE] Scraped {len(df)} jobs total.")
    return df
