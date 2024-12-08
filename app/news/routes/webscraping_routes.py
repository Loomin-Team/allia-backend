from fastapi import APIRouter, HTTPException

from app.news.services.bings_scraper import BingNewsWebScraper
from app.news.services.google_scraper import GoogleNewsWebScraper

news = APIRouter()
tag = "News"
endpoint = "/news"

@news.get("/news/google-news/")
async def fetch_google_news(query: str, region: str = "us", max_results: int = 10):
    try:
        scraper = GoogleNewsWebScraper()
        articles = scraper.get_news(query=query, region=region, max_results=max_results)
        return {"query": query, "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@news.get("/news/bing-news/")
async def fetch_google_news(query: str, region: str = "us", max_results: int = 10):
    try:
        scraper = BingNewsWebScraper()
        articles = scraper.get_news(query=query, region=region, max_results=max_results)
        return {"query": query, "articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@news.get("/news/google-news/article/")
async def extract_article_content(url: str):
    """
    Endpoint para extraer el contenido de un artículo.
    """
    try:
        scraper = GoogleNewsWebScraper()
        content = scraper.extract_news_content(url)
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
