import os
import requests
from serpapi import GoogleSearch
from bs4 import BeautifulSoup


class GoogleNewsWebScraper:
    """
    A class to fetch, process, and extract detailed news content using the SerpAPI Google News Engine.
    """

    def __init__(self, api_key=None):
        """
        Initialize the scraper with an API key.
        :param api_key: (Optional) SerpAPI key. If not provided, uses environment variable.
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key is required. Provide it as a parameter or set it in the environment variables.")

    def get_news(self, query, region="us", max_results=10):
        #print(f"Fetching news for query: {query}, region: {region}, max_results: {max_results}")
        params = {
            "engine": "google",
            "q": query,
            "tbm": "nws",
            "gl": region,
            "api_key": self.api_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()

        if "news_results" not in results:
            raise ValueError(f"No news results found for query: {query}")

        return results["news_results"][:max_results]


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
                f.write("-" * 40 + "\n")
        print(f"News articles saved to {file_path}")

    def extract_news_content(self, url):
        """
        Extract the header and body content from a news article page.
        :param url: URL of the news article.
        :return: Dictionary containing header and body content.
        """
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Attempt to extract the title (header) and body
            header = soup.find('h1')  # Most news pages use <h1> for the main title
            body = soup.find_all('p')  # Body paragraphs are usually in <p> tags
            
            # Convert extracted content to strings
            header_text = header.get_text(strip=True) if header else "No title found"
            body_text = "\n".join(p.get_text(strip=True) for p in body if p.get_text(strip=True))
            
            return {"header": header_text, "body": body_text}

        except requests.RequestException as e:
            print(f"Failed to fetch the article: {e}")
            return {"header": "Error fetching article", "body": ""}
        except Exception as e:
            print(f"An error occurred during content extraction: {e}")
            return {"header": "Error extracting content", "body": ""}

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
        
        # Example: Extract content for the first article
        if articles:
            print("\nFetching content for the first article...")
            article_content = self.extract_news_content(articles[0].get('link'))
            print(f"Header: {article_content['header']}")
            print(f"Body: {article_content['body'][:500]}...")  # Print first 500 characters for brevity

