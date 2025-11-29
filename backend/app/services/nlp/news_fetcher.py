"""
News fetcher - collects news from various sources
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import feedparser

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetch financial news from multiple sources"""

    def __init__(self):
        self.sources = {
            "yahoo_finance": "https://finance.yahoo.com/rss/",
            "reuters": "https://www.reuters.com/finance",
            "bloomberg": "https://www.bloomberg.com/feeds/",
        }

    def fetch_rss_feed(self, feed_url: str, max_items: int = 10) -> List[Dict]:
        """
        Fetch news from RSS feed

        Args:
            feed_url: RSS feed URL
            max_items: Maximum number of items to fetch

        Returns:
            List of news items with title, link, published date
        """
        try:
            feed = feedparser.parse(feed_url)
            news_items = []

            for entry in feed.entries[:max_items]:
                item = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                    "source": feed_url
                }
                news_items.append(item)

            logger.info(f"Fetched {len(news_items)} items from {feed_url}")
            return news_items

        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []

    def fetch_yahoo_finance_news(self, symbol: str, max_items: int = 10) -> List[Dict]:
        """
        Fetch news for a specific symbol from Yahoo Finance

        Args:
            symbol: Ticker symbol
            max_items: Maximum number of news items

        Returns:
            List of news items
        """
        try:
            # Yahoo Finance RSS for specific symbol
            # Note: This is a simplified version, actual implementation may vary
            url = f"https://finance.yahoo.com/rss/headline?s={symbol}"
            return self.fetch_rss_feed(url, max_items)

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance news for {symbol}: {e}")
            return []

    def fetch_general_market_news(self, max_items: int = 20) -> List[Dict]:
        """
        Fetch general market news

        Returns:
            List of news items
        """
        all_news = []

        # Try multiple RSS feeds
        rss_feeds = [
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^DJI&region=US&lang=en-US",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US",
        ]

        for feed_url in rss_feeds:
            news = self.fetch_rss_feed(feed_url, max_items=10)
            all_news.extend(news)

        # Remove duplicates based on title
        seen_titles = set()
        unique_news = []
        for item in all_news:
            if item["title"] not in seen_titles:
                seen_titles.add(item["title"])
                unique_news.append(item)

        return unique_news[:max_items]

    def search_news_by_keyword(self, keyword: str, days: int = 7) -> List[Dict]:
        """
        Search news by keyword

        Args:
            keyword: Search keyword (e.g., company name, symbol)
            days: Number of days to look back

        Returns:
            List of news items
        """
        # This is a placeholder - in production, use News API or similar service
        logger.info(f"Searching news for keyword: {keyword}")

        # Example using Google News RSS
        try:
            url = f"https://news.google.com/rss/search?q={keyword}+when:{days}d&hl=en-US&gl=US&ceid=US:en"
            return self.fetch_rss_feed(url, max_items=20)
        except Exception as e:
            logger.error(f"Error searching news: {e}")
            return []

    def get_news_for_symbol(
        self,
        symbol: str,
        days: int = 7,
        max_items: int = 20
    ) -> List[Dict]:
        """
        Get all relevant news for a symbol

        Args:
            symbol: Ticker symbol
            days: Number of days to look back
            max_items: Maximum number of items

        Returns:
            List of news items
        """
        all_news = []

        # Fetch from Yahoo Finance
        yahoo_news = self.fetch_yahoo_finance_news(symbol, max_items=10)
        all_news.extend(yahoo_news)

        # Search by symbol as keyword
        search_news = self.search_news_by_keyword(symbol, days=days)
        all_news.extend(search_news)

        # Remove duplicates
        seen_titles = set()
        unique_news = []
        for item in all_news:
            if item["title"] not in seen_titles:
                seen_titles.add(item["title"])
                unique_news.append(item)

        return unique_news[:max_items]


# Example integration with sentiment analysis
def get_news_with_sentiment(symbol: str, days: int = 7) -> Dict:
    """
    Get news for a symbol with sentiment analysis

    Args:
        symbol: Ticker symbol
        days: Number of days to look back

    Returns:
        Dictionary with news and sentiment
    """
    from app.services.nlp.sentiment import analyze_news_sentiment

    fetcher = NewsFetcher()

    # Fetch news
    news_items = fetcher.get_news_for_symbol(symbol, days=days)

    if not news_items:
        return {
            "symbol": symbol,
            "news_count": 0,
            "sentiment": {
                "label": "neutral",
                "score": 0.0
            },
            "news": []
        }

    # Extract headlines for sentiment analysis
    headlines = [item["title"] for item in news_items]

    # Analyze sentiment
    sentiment = analyze_news_sentiment(headlines, symbol=symbol)

    return {
        "symbol": symbol,
        "news_count": len(news_items),
        "sentiment": sentiment,
        "news": news_items[:10]  # Return top 10 news items
    }


# Example usage
if __name__ == "__main__":
    fetcher = NewsFetcher()

    print("Fetching general market news...")
    news = fetcher.fetch_general_market_news(max_items=5)

    for i, item in enumerate(news, 1):
        print(f"\n{i}. {item['title']}")
        print(f"   Link: {item['link']}")
        print(f"   Published: {item['published']}")

    print("\n" + "=" * 50)
    print("\nFetching news for AAPL...")
    aapl_news = fetcher.get_news_for_symbol("AAPL", days=3)

    for i, item in enumerate(aapl_news[:5], 1):
        print(f"\n{i}. {item['title']}")
