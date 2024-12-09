import os
from serpapi import GoogleSearch
from app.utils.webscrapping.serpapi_web_scraper import SerpApiWebScraper


class BingNewsWebScraper(SerpApiWebScraper):
    """
    A class to fetch and process Bing News content using the SerpAPI Bing News Engine.
    """

    def get_news(self, query, language="en", max_results=10):
        """
        Fetch news articles based on the query.
        :param query: Search term for news articles.
        :param language: Language for the results.
        :param max_results: Maximum number of results to fetch.
        :return: Concatenated string of headers and bodies.
        """
        params = {
            "engine": "bing_news",
            "q": query,
            "cc": language,  # Language or region code
            "api_key": self.api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        if "organic_results" not in results:
            print(f"No organic results found for query: {query}")
            return ""

        articles = results["organic_results"][:max_results]

        # Fetch and concatenate headers and bodies
        concatenated_content = ""
        for article in articles:
            link = article.get("link")
            content = self.extract_news_content(link)
            concatenated_content += f"{content['header']} {content['body']} "

        return concatenated_content.strip()