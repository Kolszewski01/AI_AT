"""
Local LLM integration using Ollama
Supports Mistral, LLaMA, Phi-3 for offline AI analysis
"""
import logging
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

# Try to import langchain and ollama
try:
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available. LLM features will be limited.")


class LocalLLM:
    """
    Local LLM integration for trading analysis
    Uses Ollama to run Mistral/LLaMA locally
    """

    def __init__(
        self,
        model: str = "mistral:7b",
        temperature: float = 0.7,
        ollama_base_url: str = "http://localhost:11434"
    ):
        """
        Initialize local LLM

        Args:
            model: Model name (mistral:7b, llama3:8b, phi3:mini)
            temperature: Response randomness (0.0-1.0)
            ollama_base_url: Ollama API base URL
        """
        if not LANGCHAIN_AVAILABLE:
            raise ValueError("LangChain not available. Install with: pip install langchain langchain-community")

        self.model = model
        self.llm = Ollama(
            model=model,
            temperature=temperature,
            base_url=ollama_base_url
        )

        logger.info(f"Initialized local LLM: {model}")

    def analyze_news(self, news_text: str, symbol: Optional[str] = None) -> Dict:
        """
        Analyze financial news using LLM

        Args:
            news_text: News article or headline
            symbol: Optional trading symbol for context

        Returns:
            Dictionary with sentiment, key points, impact
        """
        try:
            prompt = f"""
Analyze the following financial news and provide:
1. Sentiment (bullish/bearish/neutral)
2. Key points (bullet points)
3. Potential market impact (short-term and long-term)

Symbol: {symbol if symbol else 'General Market'}
News: {news_text}

Response format (JSON):
{{
    "sentiment": "bullish/bearish/neutral",
    "sentiment_score": 0.0 to 1.0,
    "key_points": ["point1", "point2", "point3"],
    "market_impact": {{
        "short_term": "description",
        "long_term": "description"
    }},
    "summary": "one-sentence summary"
}}
"""
            response = self.llm.invoke(prompt)

            # Try to parse JSON response
            try:
                result = json.loads(response)
            except json.JSONDecodeError:
                # If not JSON, return raw response
                result = {
                    "sentiment": "neutral",
                    "sentiment_score": 0.5,
                    "raw_response": response
                }

            logger.info(f"LLM news analysis complete for {symbol}")
            return result

        except Exception as e:
            logger.error(f"LLM news analysis error: {e}")
            return {"error": str(e)}

    def generate_alert_description(
        self,
        symbol: str,
        signal: str,
        technical_data: Dict
    ) -> str:
        """
        Generate natural language alert description

        Args:
            symbol: Trading symbol
            signal: BUY/SELL/NEUTRAL
            technical_data: Dict with RSI, MACD, pattern, etc.

        Returns:
            Natural language description
        """
        try:
            prompt = f"""
Create a concise trading alert description (2-3 sentences) based on:

Symbol: {symbol}
Signal: {signal}
Technical Data: {json.dumps(technical_data, indent=2)}

Format: Professional, actionable, include key technical levels.
Focus on WHY the signal was generated, not just WHAT it is.
"""
            response = self.llm.invoke(prompt)

            logger.info(f"LLM alert description generated for {symbol}")
            return response.strip()

        except Exception as e:
            logger.error(f"LLM alert generation error: {e}")
            return f"{signal} signal detected for {symbol}"

    def explain_indicators(
        self,
        symbol: str,
        indicators: Dict
    ) -> str:
        """
        Explain what indicators are telling us

        Args:
            symbol: Trading symbol
            indicators: Dictionary of indicator values

        Returns:
            Natural language explanation
        """
        try:
            prompt = f"""
Explain what these technical indicators are telling us about {symbol} in simple terms:

{json.dumps(indicators, indent=2)}

Provide:
1. Overall market condition (trending/ranging/volatile)
2. Momentum assessment
3. Key levels to watch
4. Potential trading opportunities

Keep it concise (4-5 sentences).
"""
            response = self.llm.invoke(prompt)

            logger.info(f"LLM indicator explanation generated for {symbol}")
            return response.strip()

        except Exception as e:
            logger.error(f"LLM explanation error: {e}")
            return "Unable to generate explanation"

    def chat_assistant(
        self,
        user_question: str,
        context: Optional[Dict] = None
    ) -> str:
        """
        Chat assistant for trading questions

        Args:
            user_question: User's question
            context: Optional context (current positions, watchlist, etc.)

        Returns:
            Assistant's response
        """
        try:
            context_str = ""
            if context:
                context_str = f"\nContext: {json.dumps(context, indent=2)}\n"

            prompt = f"""
You are a professional trading assistant. Answer the user's question clearly and concisely.
{context_str}
User Question: {user_question}

Response (be helpful, professional, and concise):
"""
            response = self.llm.invoke(prompt)

            logger.info("LLM chat response generated")
            return response.strip()

        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return "I'm unable to answer that question right now."

    def summarize_multiple_news(self, news_items: List[str]) -> str:
        """
        Summarize multiple news articles

        Args:
            news_items: List of news headlines/articles

        Returns:
            Summary of overall sentiment and key themes
        """
        try:
            news_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(news_items)])

            prompt = f"""
Summarize these financial news items and provide:
1. Overall market sentiment
2. Key themes
3. Important events

News items:
{news_text}

Summary (3-4 sentences):
"""
            response = self.llm.invoke(prompt)

            logger.info("LLM news summary generated")
            return response.strip()

        except Exception as e:
            logger.error(f"LLM summarization error: {e}")
            return "Unable to summarize news"


# Example usage
if __name__ == "__main__":
    if LANGCHAIN_AVAILABLE:
        print("Testing Local LLM (Mistral via Ollama)...")

        llm = LocalLLM(model="mistral:7b")

        # Test news analysis
        print("\n1. Testing news analysis:")
        news = "Federal Reserve hints at potential rate cuts in Q2 2025 amid cooling inflation"
        result = llm.analyze_news(news, symbol="SPX")
        print(json.dumps(result, indent=2))

        # Test alert generation
        print("\n2. Testing alert description:")
        technical_data = {
            "pattern": "Shooting Star",
            "rsi": 68.5,
            "macd": "Bearish divergence",
            "support": 16000,
            "resistance": 16250
        }
        alert = llm.generate_alert_description("DAX", "SELL", technical_data)
        print(alert)

        # Test chat assistant
        print("\n3. Testing chat assistant:")
        question = "What does RSI above 70 mean?"
        answer = llm.chat_assistant(question)
        print(answer)

    else:
        print("LangChain not available. Install dependencies first.")
        print("pip install langchain langchain-community")
        print("\nAlso install Ollama: https://ollama.ai/download")
        print("Then run: ollama pull mistral:7b")
