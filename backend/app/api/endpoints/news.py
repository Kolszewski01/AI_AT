"""
News and sentiment analysis endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime

router = APIRouter()


@router.get("/{symbol}")
async def get_news(
    symbol: str,
    days: int = Query(default=7, description="Number of days to look back"),
    max_items: int = Query(default=20, description="Maximum number of news items")
):
    """
    Get news for a symbol

    Args:
        symbol: Ticker symbol
        days: Number of days to look back
        max_items: Maximum number of news items

    Returns:
        List of news items
    """
    try:
        from app.services.nlp.news_fetcher import NewsFetcher

        fetcher = NewsFetcher()
        news_items = fetcher.get_news_for_symbol(symbol, days=days, max_items=max_items)

        return {
            "symbol": symbol,
            "count": len(news_items),
            "news": news_items
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@router.get("/sentiment/{symbol}")
async def get_sentiment(
    symbol: str,
    days: int = Query(default=7, description="Number of days to look back")
):
    """
    Get news sentiment for a symbol

    Args:
        symbol: Ticker symbol
        days: Number of days to look back

    Returns:
        News with sentiment analysis
    """
    try:
        from app.services.nlp.news_fetcher import get_news_with_sentiment

        result = get_news_with_sentiment(symbol, days=days)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing sentiment: {str(e)}"
        )


@router.post("/analyze")
async def analyze_text(text: str):
    """
    Analyze sentiment of arbitrary text

    Args:
        text: Text to analyze

    Returns:
        Sentiment analysis result
    """
    try:
        from app.services.nlp.sentiment import get_sentiment_analyzer

        analyzer = get_sentiment_analyzer()
        result = analyzer.analyze_text(text)

        return {
            "text": text,
            "sentiment": result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing text: {str(e)}"
        )


@router.get("/twitter/{symbol}")
async def get_twitter_sentiment(
    symbol: str,
    days: int = Query(default=3, description="Number of days to look back"),
    max_tweets: int = Query(default=100, description="Maximum tweets to analyze")
):
    """
    Get Twitter/X sentiment for a symbol

    Args:
        symbol: Ticker/crypto symbol
        days: Number of days to look back
        max_tweets: Maximum number of tweets to analyze

    Returns:
        Twitter sentiment analysis with FinBERT + keyword analysis
    """
    try:
        from app.services.nlp.twitter_scraper import get_twitter_sentiment

        result = get_twitter_sentiment(
            symbol=symbol,
            days=days,
            max_tweets=max_tweets
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing Twitter sentiment: {str(e)}"
        )


@router.get("/combined-sentiment/{symbol}")
async def get_combined_sentiment(
    symbol: str,
    days: int = Query(default=3, description="Number of days to look back")
):
    """
    Get combined sentiment from news + Twitter

    Args:
        symbol: Ticker symbol
        days: Number of days to look back

    Returns:
        Combined sentiment analysis from multiple sources
    """
    try:
        from app.services.nlp.news_fetcher import get_news_with_sentiment
        from app.services.nlp.twitter_scraper import get_twitter_sentiment

        # Get news sentiment
        news_sentiment = get_news_with_sentiment(symbol, days=days)

        # Get Twitter sentiment
        twitter_sentiment = get_twitter_sentiment(
            symbol=symbol,
            days=days,
            max_tweets=100
        )

        # Combine scores (weighted average)
        news_score = news_sentiment['sentiment'].get('score', 0)
        twitter_score = twitter_sentiment['sentiment'].get('score', 0)

        # Weight: 60% news, 40% Twitter
        combined_score = (news_score * 0.6) + (twitter_score * 0.4)

        # Determine overall sentiment
        if combined_score > 0.3:
            overall_sentiment = 'bullish'
        elif combined_score < -0.3:
            overall_sentiment = 'bearish'
        else:
            overall_sentiment = 'neutral'

        return {
            "symbol": symbol,
            "combined_sentiment": {
                "label": overall_sentiment,
                "score": combined_score,
                "confidence": (abs(combined_score) + 0.5) / 1.5  # 0-1 scale
            },
            "news_sentiment": news_sentiment,
            "twitter_sentiment": twitter_sentiment,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analyzing combined sentiment: {str(e)}"
        )
