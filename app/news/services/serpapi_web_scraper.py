import os
import requests
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup


class SerpApiWebScraper(ABC):
    """
    Abstract base class for web scrapers using SerpAPI.
    """

    def __init__(self, api_key=None):
        """
        Initialize the scraper with an API key.
        :param api_key: (Optional) SerpAPI key. If not provided, uses environment variable.
        """
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            raise ValueError("API Key is required. Provide it as a parameter or set it in the environment variables.")

    @abstractmethod
    def get_news(self, query, language="en"):
        """
        Fetch news articles based on a query.
        :param query: Search query string.
        :param language: Language for the results.
        :return: Concatenated string of headers and bodies.
        """
        pass

    @staticmethod
    def extract_news_content(url):
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

