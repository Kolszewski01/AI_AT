"""
Telegram Bot for trading alerts and commands
"""
import asyncio
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from datetime import datetime
import yfinance as yf

from app.core.config import settings

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class TradingBot:
    """Telegram bot for trading system"""

    def __init__(self, token: str):
        self.token = token
        self.application = None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        welcome_message = """
🤖 **AI Trading System Bot**

Witaj! Jestem Twoim asystentem tradingowym.

**Dostępne komendy:**
/help - Pokaż tę pomoc
/price <symbol> - Aktualna cena (np. /price ^GDAXI)
/analysis <symbol> - Analiza techniczna
/signal <symbol> - Sygnał tradingowy
/watchlist - Twoja lista obserwowanych
/alerts - Aktywne alerty
/subscribe <symbol> - Subskrybuj alerty
/unsubscribe <symbol> - Odsubskrybuj alerty

**Przykłady symboli:**
• ^GDAXI - DAX
• ^GSPC - S&P 500
• BTC-USD - Bitcoin
• EURUSD=X - EUR/USD

Gotowy do tradingu! 📊
        """
        await update.message.reply_text(
            welcome_message,
            parse_mode='Markdown'
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.start_command(update, context)

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price <symbol> command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Użyj: /price <symbol>\nPrzykład: /price ^GDAXI"
            )
            return

        symbol = context.args[0].upper()
        await update.message.reply_text(f"⏳ Pobieram dane dla {symbol}...")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            price = info.get("currentPrice") or info.get("regularMarketPrice")
            change = info.get("regularMarketChange", 0)
            change_pct = info.get("regularMarketChangePercent", 0)
            volume = info.get("volume") or info.get("regularMarketVolume", 0)

            # Emoji based on price direction
            direction = "🟢" if change >= 0 else "🔴"

            message = f"""
{direction} **{symbol}**

💰 Cena: **{price:.2f}**
📈 Zmiana: {change:+.2f} ({change_pct:+.2f}%)
📊 Wolumen: {volume:,}

🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """

            # Create inline keyboard for quick actions
            keyboard = [
                [
                    InlineKeyboardButton("📊 Analiza", callback_data=f"analysis:{symbol}"),
                    InlineKeyboardButton("🎯 Sygnał", callback_data=f"signal:{symbol}")
                ],
                [
                    InlineKeyboardButton("🔔 Subskrybuj alerty", callback_data=f"subscribe:{symbol}")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )

        except Exception as e:
            await update.message.reply_text(
                f"❌ Błąd pobierania danych: {str(e)}"
            )

    async def analysis_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /analysis <symbol> command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Użyj: /analysis <symbol>\nPrzykład: /analysis BTC-USD"
            )
            return

        symbol = context.args[0].upper()
        await update.message.reply_text(f"⏳ Analizuję {symbol}...")

        try:
            from app.api.endpoints.analysis import calculate_rsi, calculate_macd
            import pandas as pd

            ticker = yf.Ticker(symbol)
            df = ticker.history(period="30d", interval="1h")

            if df.empty:
                await update.message.reply_text(f"❌ Brak danych dla {symbol}")
                return

            # Calculate indicators
            df['RSI'] = calculate_rsi(df['Close'])
            macd, signal_line, histogram = calculate_macd(df['Close'])

            latest = df.iloc[-1]
            price = float(latest['Close'])
            rsi = float(latest['RSI'])
            macd_val = float(macd.iloc[-1])
            signal_val = float(signal_line.iloc[-1])

            # RSI interpretation
            if rsi < 30:
                rsi_status = "🟢 **Wyprzedanie** (Bullish)"
            elif rsi > 70:
                rsi_status = "🔴 **Wykupienie** (Bearish)"
            else:
                rsi_status = "🟡 **Neutralny**"

            # MACD interpretation
            if macd_val > signal_val:
                macd_status = "🟢 **Bullish cross**"
            else:
                macd_status = "🔴 **Bearish**"

            message = f"""
📊 **Analiza Techniczna: {symbol}**

💰 Cena: **{price:.2f}**

📈 **RSI(14):** {rsi:.2f}
{rsi_status}

📉 **MACD:**
• MACD: {macd_val:.4f}
• Signal: {signal_val:.4f}
{macd_status}

🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            await update.message.reply_text(f"❌ Błąd analizy: {str(e)}")

    async def signal_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signal <symbol> command"""
        if not context.args:
            await update.message.reply_text(
                "❌ Użyj: /signal <symbol>\nPrzykład: /signal ^GDAXI"
            )
            return

        symbol = context.args[0].upper()
        await update.message.reply_text(f"⏳ Generuję sygnał dla {symbol}...")

        try:
            from app.api.endpoints.analysis import (
                calculate_rsi,
                calculate_macd,
                detect_hammer,
                detect_shooting_star
            )
            import pandas as pd

            ticker = yf.Ticker(symbol)
            df = ticker.history(period="7d", interval="1h")

            if df.empty:
                await update.message.reply_text(f"❌ Brak danych dla {symbol}")
                return

            # Calculate indicators
            df['RSI'] = calculate_rsi(df['Close'])
            macd, signal_line, _ = calculate_macd(df['Close'])

            latest = df.iloc[-1]
            price = float(latest['Close'])
            rsi = float(latest['RSI'])

            # Signal logic
            signals = []
            if rsi < 30:
                signals.append(("RSI wyprzedanie", "bullish", 2))
            elif rsi > 70:
                signals.append(("RSI wykupienie", "bearish", 2))

            if macd.iloc[-1] > signal_line.iloc[-1]:
                signals.append(("MACD bullish cross", "bullish", 1))
            else:
                signals.append(("MACD bearish", "bearish", 1))

            # Pattern detection
            if detect_hammer(latest):
                signals.append(("Hammer pattern", "bullish", 2))
            if detect_shooting_star(latest):
                signals.append(("Shooting star", "bearish", 2))

            # Calculate overall signal
            bullish_score = sum(s for _, t, s in signals if t == "bullish")
            bearish_score = sum(s for _, t, s in signals if t == "bearish")

            if bullish_score > bearish_score + 1:
                overall = "🟢 **BUY**"
                emoji = "📈"
            elif bearish_score > bullish_score + 1:
                overall = "🔴 **SELL**"
                emoji = "📉"
            else:
                overall = "🟡 **NEUTRAL**"
                emoji = "⚖️"

            reasoning = "\n".join([f"• {r} ({sig})" for r, sig, _ in signals])

            message = f"""
{emoji} **Trading Signal: {symbol}**

💰 Cena: **{price:.2f}**

🎯 **Sygnał:** {overall}
📊 **RSI:** {rsi:.2f}

**Uzasadnienie:**
{reasoning}

⚠️ **Pamiętaj o zarządzaniu ryzykiem!**

🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            """

            await update.message.reply_text(message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Error in signal: {e}")
            await update.message.reply_text(f"❌ Błąd generowania sygnału: {str(e)}")

    async def watchlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /watchlist command"""
        # In production, fetch from database
        default_watchlist = [
            ("^GDAXI", "DAX"),
            ("^GSPC", "S&P 500"),
            ("BTC-USD", "Bitcoin"),
            ("ETH-USD", "Ethereum"),
            ("EURUSD=X", "EUR/USD")
        ]

        message = "📋 **Twoja Watchlist:**\n\n"
        for symbol, name in default_watchlist:
            message += f"• {name} ({symbol})\n"

        message += "\n💡 Użyj /price <symbol> aby sprawdzić cenę"

        await update.message.reply_text(message, parse_mode='Markdown')

    async def alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /alerts command"""
        # In production, fetch active alerts from database
        message = """
🔔 **Aktywne Alerty:**

Obecnie brak aktywnych alertów.

Użyj /subscribe <symbol> aby dodać alert.
        """
        await update.message.reply_text(message, parse_mode='Markdown')

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle button callbacks"""
        query = update.callback_query
        await query.answer()

        action, symbol = query.data.split(":")

        if action == "analysis":
            context.args = [symbol]
            await self.analysis_command(update, context)
        elif action == "signal":
            context.args = [symbol]
            await self.signal_command(update, context)
        elif action == "subscribe":
            await query.message.reply_text(
                f"✅ Subskrybowano alerty dla {symbol}\n"
                f"Będziesz otrzymywać powiadomienia o istotnych sygnałach."
            )

    async def unknown_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle unknown commands"""
        await update.message.reply_text(
            "❓ Nieznana komenda. Użyj /help aby zobaczyć dostępne komendy."
        )

    def run(self):
        """Start the bot"""
        logger.info("Starting Telegram bot...")

        # Create application
        self.application = Application.builder().token(self.token).build()

        # Add handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("price", self.price_command))
        self.application.add_handler(CommandHandler("analysis", self.analysis_command))
        self.application.add_handler(CommandHandler("signal", self.signal_command))
        self.application.add_handler(CommandHandler("watchlist", self.watchlist_command))
        self.application.add_handler(CommandHandler("alerts", self.alerts_command))
        self.application.add_handler(CallbackQueryHandler(self.button_callback))
        self.application.add_handler(
            MessageHandler(filters.COMMAND, self.unknown_command)
        )

        # Start bot
        logger.info("Bot is running... Press Ctrl+C to stop")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


async def send_alert(
    bot_token: str,
    chat_id: str,
    alert_data: dict
):
    """
    Send a trading alert via Telegram

    Args:
        bot_token: Telegram bot token
        chat_id: Target chat ID
        alert_data: Alert information dictionary
    """
    from telegram import Bot

    bot = Bot(token=bot_token)

    symbol = alert_data.get("symbol", "UNKNOWN")
    pattern = alert_data.get("pattern", "")
    signal = alert_data.get("signal", "")
    rsi = alert_data.get("rsi", 0)
    price = alert_data.get("price", 0)

    # Determine emoji based on signal
    if signal.lower() == "bullish":
        emoji = "🟢"
        arrow = "📈"
    elif signal.lower() == "bearish":
        emoji = "🔴"
        arrow = "📉"
    else:
        emoji = "🟡"
        arrow = "⚖️"

    message = f"""
{emoji} **TRADING ALERT!**
━━━━━━━━━━━━━━━━━━━━

{arrow} **Symbol:** {symbol}
📊 **Pattern:** {pattern}
🎯 **Signal:** {signal.upper()}

💰 **Price:** {price:.2f}
📈 **RSI:** {rsi:.2f}

🕐 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
━━━━━━━━━━━━━━━━━━━━

⚠️ **Always manage your risk!**
    """

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=message,
            parse_mode='Markdown'
        )
        logger.info(f"Alert sent to {chat_id} for {symbol}")
    except Exception as e:
        logger.error(f"Failed to send alert: {e}")


if __name__ == "__main__":
    # Run bot if executed directly
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment")
        exit(1)

    bot = TradingBot(settings.TELEGRAM_BOT_TOKEN)
    bot.run()
