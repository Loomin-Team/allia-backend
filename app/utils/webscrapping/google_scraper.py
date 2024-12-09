from serpapi import GoogleSearch
from app.utils.webscrapping.serpapi_web_scraper import SerpApiWebScraper

class GoogleNewsWebScraper(SerpApiWebScraper):
    """
        Fetch news articles based on a query.
        :param query: Search query string.
        :param language: Language for the results.
        :param max_results: Maximum number of results to fetch.
        :return: Concatenated string of headers and bodies.
    """

    def get_news(self, query, language="en", max_results=5):
        params = {
            "engine": "google",
            "q": query,
            "tbm": "nws",
            "hl": language,
            "api_key": self.api_key,
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
        except Exception as e:
            print(f"Error fetching news results: {e}")
            return []

        if "news_results" not in results:
            print(f"No news results found for query in Google: {query}")
            return []

        articles = results["news_results"][:max_results]
        articles_data = []

        for article in articles:
            try:
                link = article.get("link")
                if not link:
                    print(f"Missing link for article: {article}")
                    continue
                content = self.extract_news_content(link)
                if content and 'header' in content and 'body' in content:
                    articles_data.append({
                        "header": content["header"],
                        "body": content["body"],
                        "link": link
                    })
            except Exception as e:
                print(f"Error processing article: {e}")
                continue

        return articles_data