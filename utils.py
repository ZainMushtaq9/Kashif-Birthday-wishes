import pandas as pd

def search_jobs(df, query):
    if not query:
        return df
    query = query.lower()
    return df[df['title'].str.lower().str.contains(query) | df['company'].str.lower().str.contains(query)]
