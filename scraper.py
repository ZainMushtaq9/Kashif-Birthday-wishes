import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

# ---------- Setup Selenium ----------
def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service("/usr/bin/chromedriver")  # Streamlit Cloud path
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# ---------- Scraper for each site ----------
def scrape_9cv9(driver):
    driver.get("https://www.9cv9.com")
    time.sleep(2)
    jobs = []
    for job in driver.find_elements(By.CSS_SELECTOR, ".job-list-item"):
        title = job.find_element(By.CSS_SELECTOR, ".job-title").text.strip()
        company = job.find_element(By.CSS_SELECTOR, ".company-name").text.strip()
        link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
        jobs.append({"title": title, "company": company, "link": link, "source": "9cv9"})
    return jobs

def scrape_brightspyre(driver):
    driver.get("https://www.brightspyre.com")
    time.sleep(2)
    jobs = []
    for job in driver.find_elements(By.CSS_SELECTOR, ".job_list tbody tr"):
        title = job.find_element(By.CSS_SELECTOR, "td a").text.strip()
        link = job.find_element(By.CSS_SELECTOR, "td a").get_attribute("href")
        company = "N/A"
        jobs.append({"title": title, "company": company, "link": link, "source": "Brightspyre"})
    return jobs

def scrape_careerokay(driver):
    driver.get("https://www.careerokay.com")
    time.sleep(2)
    jobs = []
    for job in driver.find_elements(By.CSS_SELECTOR, ".jobs-list-item"):
        title = job.find_element(By.CSS_SELECTOR, ".title").text.strip()
        company = job.find_element(By.CSS_SELECTOR, ".company").text.strip()
        link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
        jobs.append({"title": title, "company": company, "link": link, "source": "Careerokay"})
    return jobs

def scrape_jobomas(driver):
    driver.get("https://www.jobomas.com/en/jobs")
    time.sleep(2)
    jobs = []
    for job in driver.find_elements(By.CSS_SELECTOR, ".job-list .job"):
        title = job.find_element(By.CSS_SELECTOR, ".title").text.strip()
        company = job.find_element(By.CSS_SELECTOR, ".company").text.strip()
        link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
        jobs.append({"title": title, "company": company, "link": link, "source": "Jobomas"})
    return jobs

def scrape_jobsbirds(driver):
    driver.get("https://www.jobsbirds.com")
    time.sleep(2)
    jobs = []
    for job in driver.find_elements(By.CSS_SELECTOR, ".job-box"):
        title = job.find_element(By.CSS_SELECTOR, "h3").text.strip()
        company = job.find_element(By.CSS_SELECTOR, ".job-company").text.strip()
        link = job.find_element(By.TAG_NAME, "a").get_attribute("href")
        jobs.append({"title": title, "company": company, "link": link, "source": "JobsBirds"})
    return jobs


# ---------- Master function ----------
def scrape_all_sites():
    driver = init_driver()
    all_jobs = []

    for fn in [scrape_9cv9, scrape_brightspyre, scrape_careerokay, scrape_jobomas, scrape_jobsbirds]:
        try:
            jobs = fn(driver)
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"Error scraping {fn.__name__}: {e}")

    driver.quit()
    return pd.DataFrame(all_jobs)
