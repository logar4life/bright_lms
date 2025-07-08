from fastapi import FastAPI
from brightmls import run_brightmls_scraper
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/run-scraper")
def run_scraper():
    result = run_brightmls_scraper()
    return JSONResponse(content=result)
