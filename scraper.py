import time
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options


def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    service = Service("/usr/bin/chromedriver")
    return webdriver.Chrome(service=service, options=chrome_options)


def get_job_links_from_github(raw_url: str):
    """Fetch list of job site URLs from a raw GitHub txt file."""
    response = requests.get(raw_url)
    response.raise_for_status()
    links = [line.strip() for line in response.text.splitlines() if line.strip()]
    return links


def generic_scraper(driver, url):
    """Try to scrape jobs generically for static sites."""
    jobs = []
    try:
        driver.get(url)
        time.sleep(3)
        # Try common patterns
        possible_selectors = [
            ".job", ".job-list-item", ".job-box", "tr", "li", "article"
        ]
        for sel in possible_selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            for e in elements:
                text = e.text.strip()
                if len(text) > 25 and ("apply" not in text.lower()):
                    jobs.append({
                        "title": text.split("\n")[0][:80],
                        "company": url.split("//")[-1].split("/")[0],
                        "link": url,
                        "source": url
                    })
            if len(jobs) > 10:
                break
    except Exception as e:
        print(f"Error scraping {url}: {e}")
    return jobs


def scrape_from_github(raw_txt_url):
    """Scrape all sites listed in job_links.txt hosted on GitHub."""
    links = get_job_links_from_github(raw_txt_url)
    driver = init_driver()
    all_jobs = []
    for site in links:
        site_jobs = generic_scraper(driver, site)
        all_jobs.extend(site_jobs)
    driver.quit()
    return pd.DataFrame(all_jobs)
