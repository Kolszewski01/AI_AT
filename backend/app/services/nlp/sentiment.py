"""
Sentiment analysis using FinBERT
"""
import logging
from typing import Dict, List, Optional
from datetime import datetime
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

logger = logging.getLogger(__name__)


class FinBERTSentimentAnalyzer:
    """
    Sentiment analyzer using FinBERT model
    Pre-trained on financial news and reports
    """

    def __init__(self, model_name: str = "ProsusAI/finbert"):
        """
        Initialize FinBERT model

        Args:
            model_name: HuggingFace model name
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._load_model()

    def _load_model(self):
        """Load FinBERT model and tokenizer"""
        try:
            logger.info(f"Loading FinBERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"FinBERT model loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            raise

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze sentiment of a single text

        Args:
            text: Text to analyze (news headline, article, tweet)

        Returns:
            Dictionary with sentiment scores and label
        """
        if not text or not text.strip():
            return {
                "label": "neutral",
                "score": 0.0,
                "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0}
            }

        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=512
            ).to(self.device)

            # Get predictions
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)

            # FinBERT outputs: [negative, neutral, positive]
            probs = probabilities[0].cpu().numpy()

            scores = {
                "negative": float(probs[0]),
                "neutral": float(probs[1]),
                "positive": float(probs[2])
            }

            # Determine label
            max_label = max(scores, key=scores.get)

            # Calculate compound score (-1 to 1)
            compound_score = scores["positive"] - scores["negative"]

            result = {
                "label": max_label,
                "score": compound_score,
                "scores": scores,
                "confidence": float(probs.max())
            }

            return result

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {
                "label": "neutral",
                "score": 0.0,
                "scores": {"positive": 0.0, "negative": 0.0, "neutral": 1.0},
                "error": str(e)
            }

    def analyze_batch(self, texts: List[str]) -> List[Dict]:
        """
        Analyze sentiment for multiple texts

        Args:
            texts: List of texts to analyze

        Returns:
            List of sentiment dictionaries
        """
        results = []
        for text in texts:
            result = self.analyze_text(text)
            results.append(result)
        return results

    def aggregate_sentiment(self, sentiments: List[Dict]) -> Dict:
        """
        Aggregate multiple sentiment scores

        Args:
            sentiments: List of sentiment dictionaries

        Returns:
            Aggregated sentiment with average scores
        """
        if not sentiments:
            return {
                "label": "neutral",
                "score": 0.0,
                "count": 0
            }

        scores = [s["score"] for s in sentiments if "score" in s]
        avg_score = np.mean(scores) if scores else 0.0

        # Determine overall label
        if avg_score > 0.3:
            label = "positive"
        elif avg_score < -0.3:
            label = "negative"
        else:
            label = "neutral"

        return {
            "label": label,
            "score": float(avg_score),
            "count": len(sentiments),
            "individual_scores": scores
        }


# Global instance
_sentiment_analyzer: Optional[FinBERTSentimentAnalyzer] = None


def get_sentiment_analyzer() -> FinBERTSentimentAnalyzer:
    """Get or create global sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = FinBERTSentimentAnalyzer()
    return _sentiment_analyzer


def analyze_news_sentiment(news_items: List[str], symbol: str = None) -> Dict:
    """
    Analyze sentiment for a list of news items

    Args:
        news_items: List of news headlines/articles
        symbol: Optional symbol for context

    Returns:
        Aggregated sentiment analysis
    """
    analyzer = get_sentiment_analyzer()

    # Analyze each news item
    sentiments = analyzer.analyze_batch(news_items)

    # Aggregate results
    aggregated = analyzer.aggregate_sentiment(sentiments)
    aggregated["symbol"] = symbol
    aggregated["timestamp"] = datetime.utcnow().isoformat()
    aggregated["news_count"] = len(news_items)

    logger.info(
        f"Sentiment analysis complete for {symbol}: "
        f"{aggregated['label']} ({aggregated['score']:.2f})"
    )

    return aggregated


# Example usage
if __name__ == "__main__":
    # Test sentiment analyzer
    analyzer = FinBERTSentimentAnalyzer()

    test_texts = [
        "Stock market rallies to record highs on strong earnings",
        "Company faces bankruptcy amid declining sales",
        "Federal Reserve keeps interest rates unchanged",
        "Tesla announces new record deliveries",
        "Banking sector under pressure from regulatory changes"
    ]

    print("Testing FinBERT Sentiment Analyzer\n")
    print("=" * 50)

    for text in test_texts:
        result = analyzer.analyze_text(text)
        print(f"\nText: {text}")
        print(f"Label: {result['label']}")
        print(f"Score: {result['score']:.3f}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Scores: {result['scores']}")

    print("\n" + "=" * 50)
    print("\nAggregated Sentiment:")
    aggregated = analyzer.aggregate_sentiment(
        [analyzer.analyze_text(t) for t in test_texts]
    )
    print(f"Overall: {aggregated['label']}")
    print(f"Average Score: {aggregated['score']:.3f}")
