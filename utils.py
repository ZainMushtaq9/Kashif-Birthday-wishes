import pandas as pd
from fpdf import FPDF

def save_to_csv(df, filename="jobs.csv"):
    df.to_csv(filename, index=False)
    return filename

def save_to_pdf(df, filename="jobs.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Job Listings", ln=True, align="C")

    for _, row in df.iterrows():
        pdf.multi_cell(0, 8, f"{row['title']} - {row['company']}\n{row['link']}\n", border=0)
        pdf.ln(2)
    pdf.output(filename)
    return filename
