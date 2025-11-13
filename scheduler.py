
import schedule
import time
from datetime import datetime
from scraper import scrape_all_sources, save_jobs_cache
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

GITHUB_RAW_URL = "https://raw.githubusercontent.com/ZainMushtaq9/Kashif-Birthday-wishes/main/job_links.txt"

def daily_scrape_job():
    """Function to run daily scraping."""
    logging.info("="*50)
    logging.info("Starting daily job scraping...")
    
    try:
        # Scrape all sources
        df = scrape_all_sources(GITHUB_RAW_URL)
        
        if df.empty:
            logging.warning("No jobs found during scraping!")
            return
        
        # Save to cache
        save_jobs_cache(df, "jobs_cache.csv")
        
        logging.info(f"Successfully scraped {len(df)} jobs")
        logging.info(f"Unique companies: {df['company'].nunique()}")
        logging.info(f"Unique locations: {df['location'].nunique()}")
        
        # Optional: Save backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"jobs_backup_{timestamp}.csv"
        df.to_csv(backup_filename, index=False)
        logging.info(f"Backup saved: {backup_filename}")
        
    except Exception as e:
        logging.error(f"Error during scraping: {e}", exc_info=True)

def run_scheduler():
    """Run the scheduler continuously."""
    # Schedule daily at 12:00 AM
    schedule.every().day.at("00:00").do(daily_scrape_job)
    
    # Also run immediately on start
    logging.info("Running initial scrape...")
    daily_scrape_job()
    
    logging.info("Scheduler started. Jobs will run daily at 12:00 AM")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    try:
        run_scheduler()
    except KeyboardInterrupt:
        logging.info("Scheduler stopped by user")
    except Exception as e:
        logging.error(f"Scheduler error: {e}", exc_info=True)
