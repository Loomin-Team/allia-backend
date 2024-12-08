import os
import re
import requests
from serpapi import GoogleSearch
from bs4 import BeautifulSoup

class BingNewsWebScraper:
    
    def __init__(self, api_key=None):
        """
        Initialize the scraper with an API key.
        :param api_key: (Optional) SerpAPI key. If not provided, uses environment variable.
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key is required. Provide it as a parameter or set it in the environment variables.")
        
    def get_news(self, query, region="us", max_results=10):
        """
        Fetch news articles based on the query.
        :param query: Search term for news articles.
        :param region: Geographic location (e.g., "us" for the United States).
        :param max_results: Maximum number of results to fetch.
        :return: List of news articles as dictionaries.
        """
        params = {
            "engine": "bing_news",
            "q": query,
            "cc": region,
            "api_key": self.api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        
        if "organic_results" not in results:
            raise ValueError(f"No organic results found for query: {query}")

        return results["organic_results"][:max_results]
    
    def display_news(self, articles):
        """
        Display fetched news articles in a readable format.
        :param articles: List of news articles as dictionaries.
        """
        for i, article in enumerate(articles, 1):
            print(f"Article {i}:")
            print(f"Title: {article.get('title')}")
            print(f"Source: {article.get('source')}")
            print(f"Published: {article.get('date')}")
            print(f"Link: {article.get('link')}")
            print(f"Snippet: {article.get('snippet')}")
            print(f"Thumbnail: {article.get('thumbnail')}")
            print("-" * 40)

    def save_news_to_file(self, articles, file_path):
        """
        Save fetched news articles to a file.
        :param articles: List of news articles as dictionaries.
        :param file_path: Path to the file where articles will be saved.
        """
        with open(file_path, "w") as f:
            for article in articles:
                f.write(f"Title: {article.get('title')}\n")
                f.write(f"Source: {article.get('source')}\n")
                f.write(f"Published: {article.get('date')}\n")
                f.write(f"Link: {article.get('link')}\n")
                f.write(f"Snippet: {article.get('snippet')}\n")
                f.write(f"Thumbnail: {article.get('thumbnail')}\n")
                f.write("-" * 40 + "\n")
        print(f"News articles saved to {file_path}")

    def fetch_and_process(self, query, region="us", max_results=10, save_path=None):
        """
        Fetch, display, and optionally save news articles.
        :param query: Search term for news articles.
        :param region: Geographic location (e.g., "us" for the United States).
        :param max_results: Maximum number of results to fetch.
        :param save_path: (Optional) Path to save articles to a file.
        """
        articles = self.get_news(query, region, max_results)
        self.display_news(articles)
        if save_path:
            self.save_news_to_file(articles, save_path)
