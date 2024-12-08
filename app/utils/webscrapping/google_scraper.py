from serpapi import GoogleSearch
from app.news.services.serpapi_web_scraper import SerpApiWebScraper

class GoogleNewsWebScraper(SerpApiWebScraper):
    """
    A class to fetch, process, and extract detailed news content using the SerpAPI Google News Engine.
    """

    def get_news(self, query, language="en", max_results=3):
        """
        Fetch news articles based on a query.
        :param query: Search query string.
        :param language: Language for the results.
        :param max_results: Maximum number of results to fetch.
        :return: Concatenated string of headers and bodies.
        """

        params = {
            "engine": "google",
            "q": query,
            "tbm": "nws",
            "hl": language,
            "api_key": self.api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        if "news_results" not in results:
            print(f"No news results found for query in Google: {query}")
            return ""

        articles = results["news_results"][:max_results]

        # Fetch and concatenate headers and bodies
        concatenated_content = ""
        for article in articles:
            link = article.get("link")
            content = self.extract_news_content(link)
            concatenated_content += f"{content['header']} {content['body']} "

        return concatenated_content.strip()