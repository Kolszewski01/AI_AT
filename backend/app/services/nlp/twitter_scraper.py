"""
Twitter/X sentiment scraper for financial topics
Uses snscrape for scraping without API limits
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

# Try to import snscrape, fallback gracefully
try:
    import snscrape.modules.twitter as sntwitter
    SNSCRAPE_AVAILABLE = True
except ImportError:
    SNSCRAPE_AVAILABLE = False
    logger.warning("snscrape not available. Twitter scraping will be limited.")


class TwitterSentimentScraper:
    """
    Scrape tweets for sentiment analysis without API keys
    Uses snscrape library for unlimited scraping
    """

    def __init__(self):
        if not SNSCRAPE_AVAILABLE:
            logger.warning("Twitter scraping functionality is limited without snscrape")

    def clean_tweet(self, text: str) -> str:
        """
        Clean tweet text for analysis

        Args:
            text: Raw tweet text

        Returns:
            Cleaned text
        """
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        # Remove user mentions
        text = re.sub(r'@\w+', '', text)
        # Remove hashtags (keep the text)
        text = re.sub(r'#(\w+)', r'\1', text)
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text.strip()

    def scrape_tweets(
        self,
        query: str,
        max_tweets: int = 100,
        days: int = 7,
        language: str = "en"
    ) -> List[Dict]:
        """
        Scrape tweets for a given query

        Args:
            query: Search query (e.g., "$BTC", "bitcoin", "#crypto")
            max_tweets: Maximum number of tweets to fetch
            days: Number of days to look back
            language: Tweet language filter

        Returns:
            List of tweet dictionaries
        """
        if not SNSCRAPE_AVAILABLE:
            logger.error("snscrape not available. Cannot scrape tweets.")
            return []

        try:
            # Calculate date range
            since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            until = datetime.now().strftime('%Y-%m-%d')

            # Build query with filters
            search_query = f"{query} lang:{language} since:{since} until:{until}"

            tweets = []
            for i, tweet in enumerate(sntwitter.TwitterSearchScraper(search_query).get_items()):
                if i >= max_tweets:
                    break

                tweets.append({
                    'id': tweet.id,
                    'date': tweet.date.isoformat() if tweet.date else None,
                    'text': self.clean_tweet(tweet.content),
                    'raw_text': tweet.content,
                    'username': tweet.user.username if tweet.user else None,
                    'likes': tweet.likeCount or 0,
                    'retweets': tweet.retweetCount or 0,
                    'replies': tweet.replyCount or 0,
                    'url': tweet.url,
                })

            logger.info(f"Scraped {len(tweets)} tweets for query: {query}")
            return tweets

        except Exception as e:
            logger.error(f"Error scraping tweets: {e}")
            return []

    def scrape_symbol_tweets(
        self,
        symbol: str,
        max_tweets: int = 100,
        days: int = 3
    ) -> List[Dict]:
        """
        Scrape tweets for a specific financial symbol

        Args:
            symbol: Stock/crypto symbol (e.g., "AAPL", "BTC")
            max_tweets: Maximum number of tweets
            days: Number of days to look back

        Returns:
            List of tweets
        """
        # Build queries for different formats
        queries = [
            f"${symbol}",  # Cashtag
            f"#{symbol}",  # Hashtag
            symbol,        # Plain symbol
        ]

        all_tweets = []
        tweets_per_query = max_tweets // len(queries)

        for query in queries:
            tweets = self.scrape_tweets(
                query=query,
                max_tweets=tweets_per_query,
                days=days
            )
            all_tweets.extend(tweets)

        # Remove duplicates by tweet ID
        seen_ids = set()
        unique_tweets = []
        for tweet in all_tweets:
            if tweet['id'] not in seen_ids:
                seen_ids.add(tweet['id'])
                unique_tweets.append(tweet)

        # Sort by engagement (likes + retweets)
        unique_tweets.sort(
            key=lambda t: t['likes'] + t['retweets'],
            reverse=True
        )

        return unique_tweets[:max_tweets]

    def get_sentiment_keywords(self, tweets: List[Dict]) -> Dict:
        """
        Extract common sentiment keywords from tweets

        Args:
            tweets: List of tweet dictionaries

        Returns:
            Dictionary with positive and negative keywords
        """
        positive_keywords = [
            'bullish', 'moon', 'rally', 'pump', 'up', 'gains', 'profit',
            'buy', 'long', 'breakout', 'surge', 'soar', 'rocket', '🚀',
            'green', 'bull', 'ath', 'highs'
        ]

        negative_keywords = [
            'bearish', 'dump', 'crash', 'down', 'losses', 'sell', 'short',
            'breakdown', 'drop', 'fall', 'red', 'bear', 'panic', 'fear',
            'liquidation', 'rekt'
        ]

        positive_count = 0
        negative_count = 0

        for tweet in tweets:
            text = tweet['text'].lower()
            for keyword in positive_keywords:
                if keyword in text:
                    positive_count += 1

            for keyword in negative_keywords:
                if keyword in text:
                    negative_count += 1

        total = positive_count + negative_count
        if total == 0:
            return {
                'positive_ratio': 0.5,
                'negative_ratio': 0.5,
                'sentiment': 'neutral'
            }

        pos_ratio = positive_count / total
        neg_ratio = negative_count / total

        if pos_ratio > neg_ratio * 1.5:
            sentiment = 'bullish'
        elif neg_ratio > pos_ratio * 1.5:
            sentiment = 'bearish'
        else:
            sentiment = 'neutral'

        return {
            'positive_ratio': pos_ratio,
            'negative_ratio': neg_ratio,
            'sentiment': sentiment,
            'total_keywords': total
        }


def get_twitter_sentiment(symbol: str, days: int = 3, max_tweets: int = 100) -> Dict:
    """
    Get comprehensive Twitter sentiment for a symbol

    Args:
        symbol: Stock/crypto symbol
        days: Number of days to look back
        max_tweets: Maximum tweets to analyze

    Returns:
        Dictionary with tweets and sentiment analysis
    """
    from app.services.nlp.sentiment import analyze_news_sentiment

    scraper = TwitterSentimentScraper()

    # Scrape tweets
    tweets = scraper.scrape_symbol_tweets(symbol, max_tweets=max_tweets, days=days)

    if not tweets:
        return {
            'symbol': symbol,
            'tweet_count': 0,
            'sentiment': {
                'label': 'neutral',
                'score': 0.0
            },
            'tweets': [],
            'keyword_analysis': None
        }

    # Extract tweet texts for sentiment analysis
    tweet_texts = [tweet['text'] for tweet in tweets if tweet['text']]

    # Analyze sentiment using FinBERT
    sentiment = analyze_news_sentiment(tweet_texts, symbol=symbol)

    # Get keyword-based sentiment
    keyword_analysis = scraper.get_sentiment_keywords(tweets)

    # Calculate engagement metrics
    total_likes = sum(t['likes'] for t in tweets)
    total_retweets = sum(t['retweets'] for t in tweets)
    avg_engagement = (total_likes + total_retweets) / len(tweets) if tweets else 0

    return {
        'symbol': symbol,
        'tweet_count': len(tweets),
        'sentiment': sentiment,
        'keyword_analysis': keyword_analysis,
        'engagement': {
            'total_likes': total_likes,
            'total_retweets': total_retweets,
            'avg_engagement': avg_engagement
        },
        'tweets': tweets[:20],  # Return top 20 most engaged tweets
        'timeframe': f'{days} days',
        'timestamp': datetime.utcnow().isoformat()
    }


# Alternative: Use Twitter API v2 (requires API keys)
class TwitterAPIClient:
    """
    Official Twitter API client (requires API keys)
    More reliable but has rate limits
    """

    def __init__(self, bearer_token: str):
        """
        Initialize Twitter API client

        Args:
            bearer_token: Twitter API v2 Bearer Token
        """
        self.bearer_token = bearer_token
        self.base_url = "https://api.twitter.com/2"

    def search_tweets(
        self,
        query: str,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search tweets using Twitter API v2

        Args:
            query: Search query
            max_results: Maximum results (10-100)

        Returns:
            List of tweets
        """
        import requests

        headers = {"Authorization": f"Bearer {self.bearer_token}"}
        params = {
            "query": query,
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at,public_metrics,lang"
        }

        try:
            response = requests.get(
                f"{self.base_url}/tweets/search/recent",
                headers=headers,
                params=params
            )
            response.raise_for_status()

            data = response.json()
            tweets = []

            for tweet in data.get('data', []):
                tweets.append({
                    'id': tweet['id'],
                    'text': tweet['text'],
                    'date': tweet.get('created_at'),
                    'likes': tweet['public_metrics']['like_count'],
                    'retweets': tweet['public_metrics']['retweet_count'],
                    'replies': tweet['public_metrics']['reply_count'],
                })

            return tweets

        except Exception as e:
            logger.error(f"Error calling Twitter API: {e}")
            return []


# Example usage
if __name__ == "__main__":
    scraper = TwitterSentimentScraper()

    if SNSCRAPE_AVAILABLE:
        print("Testing Twitter sentiment scraper\n")
        print("=" * 50)

        # Test scraping for Bitcoin
        symbol = "BTC"
        print(f"\nScraping tweets for ${symbol}...")

        tweets = scraper.scrape_symbol_tweets(symbol, max_tweets=20, days=1)
        print(f"Found {len(tweets)} tweets")

        if tweets:
            print("\nTop 5 tweets by engagement:")
            for i, tweet in enumerate(tweets[:5], 1):
                print(f"\n{i}. @{tweet['username']}")
                print(f"   {tweet['text'][:100]}...")
                print(f"   Likes: {tweet['likes']}, Retweets: {tweet['retweets']}")

            # Analyze sentiment
            keyword_sentiment = scraper.get_sentiment_keywords(tweets)
            print(f"\nKeyword sentiment: {keyword_sentiment['sentiment']}")
            print(f"Positive ratio: {keyword_sentiment['positive_ratio']:.2%}")
            print(f"Negative ratio: {keyword_sentiment['negative_ratio']:.2%}")
    else:
        print("snscrape not installed. Install with: pip install snscrape")
