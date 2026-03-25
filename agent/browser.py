"""
browser.py - Web browsing and scraping module
Autonomously searches and extracts content from web pages
"""

import time
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin, urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


class WebBrowser:
    """Autonomous web browser that searches and extracts structured content."""

    def __init__(self, delay: float = 1.5):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.visited_urls: list[str] = []

    def search(self, query: str, num_results: int = 6) -> list[dict]:
        """Search DuckDuckGo and return list of {title, url, snippet}."""
        print(f"  🔎 Searching: {query}")
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        try:
            resp = self.session.get(search_url, timeout=10)
            soup = BeautifulSoup(resp.text, "html.parser")
            results = []

            for result in soup.select(".result")[:num_results]:
                title_tag = result.select_one(".result__title a")
                snippet_tag = result.select_one(".result__snippet")
                url_tag = result.select_one(".result__url")

                if not title_tag:
                    continue

                href = title_tag.get("href", "")
                # DuckDuckGo wraps URLs — extract actual URL
                if "uddg=" in href:
                    from urllib.parse import parse_qs, urlparse as _up
                    qs = parse_qs(_up(href).query)
                    href = qs.get("uddg", [href])[0]

                results.append({
                    "title": title_tag.get_text(strip=True),
                    "url": href,
                    "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "",
                })

            time.sleep(self.delay + random.uniform(0, 0.5))
            return results

        except Exception as e:
            print(f"    ⚠️  Search error: {e}")
            return []

    def fetch_page(self, url: str, max_chars: int = 4000) -> dict:
        """Fetch a page and extract clean text content."""
        if not url or not url.startswith("http"):
            return {"url": url, "text": "", "error": "Invalid URL"}

        print(f"  🌐 Fetching: {url[:70]}...")
        try:
            resp = self.session.get(url, timeout=12)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            # Remove noise
            for tag in soup(["script", "style", "nav", "footer",
                              "header", "aside", "form", "iframe"]):
                tag.decompose()

            # Extract main content
            main = (
                soup.find("main")
                or soup.find("article")
                or soup.find(id="content")
                or soup.find(class_="content")
                or soup.body
            )
            text = (main or soup).get_text(separator="\n", strip=True)

            # Collapse blank lines
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            clean_text = "\n".join(lines)[:max_chars]

            self.visited_urls.append(url)
            time.sleep(self.delay)

            return {"url": url, "text": clean_text, "error": None}

        except Exception as e:
            print(f"    ⚠️  Fetch error: {e}")
            return {"url": url, "text": "", "error": str(e)}

    def multi_search(self, queries: list[str]) -> list[dict]:
        """Run multiple searches and deduplicate results."""
        seen_urls = set()
        all_results = []
        for q in queries:
            for r in self.search(q):
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    all_results.append(r)
        return all_results
