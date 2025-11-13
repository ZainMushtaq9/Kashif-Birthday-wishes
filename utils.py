import pandas as pd
from fpdf import FPDF
from datetime import datetime

def save_to_csv(df, filename="jobs.csv"):
    """Save DataFrame to CSV file."""
    try:
        df.to_csv(filename, index=False)
        return filename
    except Exception as e:
        print(f"Error saving CSV: {e}")
        return None

def save_to_pdf(df, filename="jobs.pdf"):
    """Save jobs to PDF file."""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "JobFinder Pakistan - Job Listings", ln=True, align="C")
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 10, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_font("Arial", '', 9)
        for idx, row in df.iterrows():
            if idx > 100:  # Limit to 100 jobs in PDF
                break
                
            pdf.set_font("Arial", 'B', 11)
            pdf.multi_cell(0, 6, f"{row['title']}", border=0)
            
            pdf.set_font("Arial", '', 9)
            pdf.multi_cell(0, 5, f"Company: {row['company']}", border=0)
            pdf.multi_cell(0, 5, f"Location: {row['location']}", border=0)
            
            if row['salary'] != "Not specified":
                pdf.multi_cell(0, 5, f"Salary: {row['salary']}", border=0)
            
            pdf.multi_cell(0, 5, f"Link: {row['link']}", border=0)
            pdf.ln(3)
        
        pdf.output(filename)
        return filename
    except Exception as e:
        print(f"Error saving PDF: {e}")
        return None

def search_jobs(df, query):
    """Search jobs by query string."""
    if df.empty or not query:
        return df
    
    query = query.lower()
    mask = (
        df["title"].str.lower().str.contains(query, na=False) |
        df["company"].str.lower().str.contains(query, na=False) |
        df["description"].str.lower().str.contains(query, na=False) |
        df["location"].str.lower().str.contains(query, na=False)
    )
    return df[mask]

def filter_by_location(df, location):
    """Filter jobs by location."""
    if df.empty or location == "All Locations":
        return df
    
    return df[df["location"].str.contains(location, case=False, na=False)]

def filter_by_company(df, company):
    """Filter jobs by company name."""
    if df.empty or not company:
        return df
    
    return df[df["company"].str.contains(company, case=False, na=False)]

def filter_by_salary(df, min_salary=None, max_salary=None):
    """Filter jobs by salary range (if available)."""
    if df.empty:
        return df
    
    # This is a basic implementation - you may need to parse salary strings
    filtered_df = df.copy()
    
    if min_salary or max_salary:
        # Add your salary parsing logic here
        pass
    
    return filtered_df

def get_job_statistics(df):
    """Get statistics about jobs."""
    if df.empty:
        return {
            "total_jobs": 0,
            "total_companies": 0,
            "total_locations": 0,
            "top_companies": [],
            "top_locations": []
        }
    
    stats = {
        "total_jobs": len(df),
        "total_companies": df["company"].nunique(),
        "total_locations": df["location"].nunique(),
        "top_companies": df["company"].value_counts().head(10).to_dict(),
        "top_locations": df["location"].value_counts().head(10).to_dict(),
        "jobs_by_source": df["source"].value_counts().to_dict()
    }
    
    return stats

def format_job_for_display(job):
    """Format a single job record for display."""
    return {
        "title": job.get("title", "N/A"),
        "company": job.get("company", "N/A"),
        "location": job.get("location", "N/A"),
        "description": job.get("description", "N/A")[:200] + "...",
        "salary": job.get("salary", "Not specified"),
        "link": job.get("link", "#"),
        "posted_date": job.get("posted_date", "N/A")
    }

def validate_job_data(job):
    """Validate job data before adding to database."""
    required_fields = ["title", "company", "link"]
    
    for field in required_fields:
        if not job.get(field):
            return False
    
    # Check minimum title length
    if len(job["title"]) < 10:
        return False
    
    return True

def deduplicate_jobs(df):
    """Remove duplicate jobs based on title and company."""
    if df.empty:
        return df
    
    return df.drop_duplicates(subset=["title", "company"], keep="first")

def enrich_job_data(df):
    """Add additional computed fields to job data."""
    if df.empty:
        return df
    
    df = df.copy()
    
    # Add days since posting (if date is available)
    try:
        df["posted_date"] = pd.to_datetime(df["posted_date"])
        df["days_old"] = (datetime.now() - df["posted_date"]).dt.days
    except:
        df["days_old"] = 0
    
    # Add job category based on title keywords
    def categorize_job(title):
        title = title.lower()
        if any(word in title for word in ["engineer", "developer", "programmer"]):
            return "IT & Software"
        elif any(word in title for word in ["manager", "executive", "director"]):
            return "Management"
        elif any(word in title for word in ["marketing", "sales"]):
            return "Sales & Marketing"
        elif any(word in title for word in ["accountant", "finance"]):
            return "Finance & Accounting"
        elif any(word in title for word in ["teacher", "professor", "education"]):
            return "Education"
        elif any(word in title for word in ["doctor", "nurse", "medical"]):
            return "Healthcare"
        else:
            return "Other"
    
    df["category"] = df["title"].apply(categorize_job)
    
    return df
