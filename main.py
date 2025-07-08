from fastapi import FastAPI
from brightmls import run_brightmls_scraper, scrape_all_pages
import json

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.get("/scrape")
def scrape():
    # Run the scraper and get the data
    result = run_brightmls_scraper()
    # If you want to return the actual data, you need to modify run_brightmls_scraper to return the data
    # For now, let's assume it returns a dict with 'success', 'message', and 'row_count'
    return result
