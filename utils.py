import pandas as pd

def search_jobs(df, query):
    """Filter jobs by search query."""
    if not query:
        return df
    query = query.lower()
    return df[
        df["title"].str.lower().str.contains(query, na=False)
        | df["company"].str.lower().str.contains(query, na=False)
    ]
