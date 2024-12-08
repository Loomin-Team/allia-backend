from fastapi import APIRouter, HTTPException

from app.utils.webscrapping.bing_scraper import BingNewsWebScraper
from app.utils.webscrapping.google_scraper import GoogleNewsWebScraper

news = APIRouter()
tag = "News"
endpoint = "/news"


@news.get("/news/serpapi")
async def fetch_serapi_news(query: str, language: str = "us", max_results: int = 10):
    try:
        google_scraper = GoogleNewsWebScraper()
        concatenatedGoogle = google_scraper.get_news(query=query, language=language, max_results=max_results)
        print("Google News Articles: ", concatenatedGoogle)
        
        bing_scraper = BingNewsWebScraper()
        concatenatedBing = bing_scraper.get_news(query=query, language=language, max_results=max_results)
        print("Bing News Articles: ", concatenatedBing)
        
        return {"concatenated": concatenatedBing + concatenatedGoogle}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))