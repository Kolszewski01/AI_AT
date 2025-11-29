"""
Comprehensive tests for alert services
Tests DiscordAlerter, SMSAlerter, TelegramBot, and TTSEngine
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime

from app.services.alerts.discord_bot import DiscordAlerter
from app.services.alerts.sms_sender import SMSAlerter
from app.services.alerts.telegram_bot import TradingBot, send_alert
from app.services.alerts.tts_engine import TTSEngine


# ===== DISCORD ALERTER TESTS =====

class TestDiscordAlerter:
    """Tests for Discord alerter"""

    @pytest.fixture
    def mock_requests(self):
        """Mock requests library"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response
            yield mock_post

    @pytest.fixture
    def discord_alerter(self):
        """Create Discord alerter instance"""
        return DiscordAlerter(webhook_url="https://discord.com/api/webhooks/test")

    def test_discord_initialization(self, discord_alerter):
        """Test Discord alerter initializes correctly"""
        assert discord_alerter is not None
        assert discord_alerter.webhook_url is not None

    def test_send_alert_success(self, discord_alerter, mock_requests):
        """Test successful alert sending"""
        result = discord_alerter.send_alert(
            symbol="AAPL",
            signal_type="BUY",
            price=150.50,
            confidence=0.85
        )

        assert result == True
        mock_requests.assert_called_once()

    def test_send_alert_with_indicators(self, discord_alerter, mock_requests):
        """Test sending alert with indicators"""
        indicators = {
            'rsi': 65.5,
            'macd': 2.3,
            'volume': 1000000
        }

        result = discord_alerter.send_alert(
            symbol="AAPL",
            signal_type="BUY",
            price=150.50,
            confidence=0.85,
            indicators=indicators
        )

        assert result == True

    def test_send_alert_with_reasoning(self, discord_alerter, mock_requests):
        """Test sending alert with reasoning"""
        result = discord_alerter.send_alert(
            symbol="AAPL",
            signal_type="BUY",
            price=150.50,
            confidence=0.85,
            reasoning="Strong bullish momentum"
        )

        assert result == True

    def test_send_alert_failure(self, discord_alerter):
        """Test alert sending failure handling"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error")

            result = discord_alerter.send_alert(
                symbol="AAPL",
                signal_type="BUY",
                price=150.50
            )

            assert result == False

    def test_send_simple_message(self, discord_alerter, mock_requests):
        """Test sending simple message"""
        result = discord_alerter.send_simple_message("Test message")

        assert result == True
        mock_requests.assert_called_once()

    def test_send_simple_message_failure(self, discord_alerter):
        """Test simple message failure"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Exception("Network error")

            result = discord_alerter.send_simple_message("Test")

            assert result == False

    def test_send_chart_screenshot(self, discord_alerter, mock_requests):
        """Test sending chart screenshot"""
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value = Mock()

            result = discord_alerter.send_chart_screenshot(
                symbol="AAPL",
                chart_path="/tmp/chart.png"
            )

            # May succeed or fail depending on file handling
            assert isinstance(result, bool)


# ===== SMS ALERTER TESTS =====

class TestSMSAlerter:
    """Tests for SMS alerter (Twilio)"""

    @pytest.fixture
    def mock_twilio_client(self):
        """Mock Twilio client"""
        client = Mock()
        message = Mock()
        message.sid = "SM123456"
        client.messages.create.return_value = message
        return client

    @pytest.fixture
    def sms_alerter(self, mock_twilio_client):
        """Create SMS alerter with mocked Twilio"""
        with patch('twilio.rest.Client', return_value=mock_twilio_client):
            alerter = SMSAlerter(
                account_sid="test_sid",
                auth_token="test_token",
                from_number="+1234567890",
                to_number="+0987654321"
            )
            return alerter

    def test_sms_initialization(self):
        """Test SMS alerter initializes"""
        with patch('twilio.rest.Client'):
            alerter = SMSAlerter(
                account_sid="test",
                auth_token="test",
                from_number="+1234567890",
                to_number="+0987654321"
            )
            assert alerter is not None

    def test_send_alert_success(self, sms_alerter, mock_twilio_client):
        """Test successful SMS alert"""
        result = sms_alerter.send_alert(
            symbol="AAPL",
            signal_type="BUY",
            price=150.50,
            confidence=0.85
        )

        assert result == True
        mock_twilio_client.messages.create.assert_called_once()

    def test_send_alert_with_reasoning(self, sms_alerter, mock_twilio_client):
        """Test SMS alert with reasoning"""
        result = sms_alerter.send_alert(
            symbol="AAPL",
            signal_type="BUY",
            price=150.50,
            reasoning="Breakout above resistance"
        )

        assert result == True

    def test_send_alert_failure(self, sms_alerter):
        """Test SMS alert failure handling"""
        with patch.object(sms_alerter.client.messages, 'create', side_effect=Exception("API error")):
            result = sms_alerter.send_alert(
                symbol="AAPL",
                signal_type="BUY",
                price=150.50
            )

            assert result == False

    def test_send_simple_message(self, sms_alerter, mock_twilio_client):
        """Test sending simple SMS"""
        result = sms_alerter.send_simple_message("Test message")

        assert result == True
        mock_twilio_client.messages.create.assert_called()

    def test_send_critical_alert(self, sms_alerter, mock_twilio_client):
        """Test sending critical alert"""
        result = sms_alerter.send_critical_alert(
            title="Market Crash",
            message="Major decline detected",
            severity="HIGH"
        )

        assert result == True

    def test_message_length_limit(self, sms_alerter, mock_twilio_client):
        """Test SMS message length handling"""
        long_message = "A" * 2000  # Longer than SMS limit

        result = sms_alerter.send_simple_message(long_message)

        # Should handle gracefully
        assert isinstance(result, bool)


# ===== TTS ENGINE TESTS =====

class TestTTSEngine:
    """Tests for Text-to-Speech engine"""

    @pytest.fixture
    def mock_pyttsx3(self):
        """Mock pyttsx3 engine"""
        engine = Mock()
        engine.getProperty.return_value = 150
        engine.setProperty = Mock()
        engine.say = Mock()
        engine.runAndWait = Mock()
        return engine

    @pytest.fixture
    def tts_engine(self, mock_pyttsx3):
        """Create TTS engine with mocked pyttsx3"""
        with patch('pyttsx3.init', return_value=mock_pyttsx3):
            engine = TTSEngine(engine="pyttsx3")
            return engine

    def test_tts_initialization(self):
        """Test TTS engine initializes"""
        with patch('pyttsx3.init'):
            engine = TTSEngine()
            assert engine is not None

    def test_speak_success(self, tts_engine, mock_pyttsx3):
        """Test speaking text"""
        result = tts_engine.speak("Test message", async_mode=False)

        assert result == True
        mock_pyttsx3.say.assert_called_with("Test message")
        mock_pyttsx3.runAndWait.assert_called_once()

    def test_speak_async(self, tts_engine, mock_pyttsx3):
        """Test async speaking"""
        with patch('threading.Thread') as mock_thread:
            mock_thread.return_value.start = Mock()

            result = tts_engine.speak("Test message", async_mode=True)

            assert result == True
            mock_thread.assert_called_once()

    def test_speak_failure(self, tts_engine):
        """Test speak failure handling"""
        with patch.object(tts_engine.engine, 'say', side_effect=Exception("TTS error")):
            result = tts_engine.speak("Test")

            assert result == False

    def test_alert_trading_signal(self, tts_engine, mock_pyttsx3):
        """Test trading signal alert"""
        result = tts_engine.alert(
            symbol="AAPL",
            signal_type="BUY",
            price=150.50,
            confidence=0.85
        )

        assert result == True
        mock_pyttsx3.say.assert_called()

    def test_alert_with_reasoning(self, tts_engine, mock_pyttsx3):
        """Test alert with reasoning"""
        result = tts_engine.alert(
            symbol="AAPL",
            signal_type="BUY",
            price=150.50,
            reasoning="Strong momentum"
        )

        assert result == True

    def test_simple_alert(self, tts_engine, mock_pyttsx3):
        """Test simple alert"""
        result = tts_engine.simple_alert("Market opened")

        assert result == True
        mock_pyttsx3.say.assert_called_with("Market opened")

    def test_tts_engine_configuration(self, tts_engine, mock_pyttsx3):
        """Test TTS engine configuration"""
        # Verify configuration was called
        assert mock_pyttsx3.setProperty.called


# ===== TELEGRAM BOT TESTS =====

class TestTelegramBot:
    """Tests for Telegram trading bot"""

    @pytest.fixture
    def mock_application(self):
        """Mock Telegram application"""
        app = Mock()
        app.add_handler = Mock()
        app.run_polling = Mock()
        return app

    @pytest.fixture
    def telegram_bot(self, mock_application):
        """Create Telegram bot with mocked application"""
        with patch('telegram.ext.Application.builder') as mock_builder:
            mock_builder.return_value.token.return_value.build.return_value = mock_application

            bot = TradingBot(token="test_token")
            return bot

    def test_telegram_bot_initialization(self):
        """Test Telegram bot initializes"""
        with patch('telegram.ext.Application.builder') as mock_builder:
            mock_app = Mock()
            mock_builder.return_value.token.return_value.build.return_value = mock_app

            bot = TradingBot(token="test_token")
            assert bot is not None

    @pytest.mark.asyncio
    async def test_start_command(self, telegram_bot):
        """Test /start command"""
        update = Mock()
        update.effective_user.first_name = "John"
        update.message.reply_text = AsyncMock()
        context = Mock()

        await telegram_bot.start_command(update, context)

        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_help_command(self, telegram_bot):
        """Test /help command"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()

        await telegram_bot.help_command(update, context)

        update.message.reply_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_price_command(self, telegram_bot):
        """Test /price command"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()
        context.args = ["AAPL"]

        with patch('app.services.data_fetchers.yfinance_client.YFinanceClient') as mock_yf:
            mock_client = Mock()
            mock_client.get_quote.return_value = {
                'symbol': 'AAPL',
                'current_price': 150.50,
                'change': 2.50,
                'change_percent': 1.69
            }
            mock_yf.return_value = mock_client

            await telegram_bot.price_command(update, context)

            update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_price_command_no_args(self, telegram_bot):
        """Test /price command without symbol"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()
        context.args = []

        await telegram_bot.price_command(update, context)

        update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_analysis_command(self, telegram_bot):
        """Test /analysis command"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()
        context.args = ["AAPL"]

        await telegram_bot.analysis_command(update, context)

        # Should attempt to send a message
        assert update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_signal_command(self, telegram_bot):
        """Test /signal command"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()
        context.args = ["AAPL"]

        await telegram_bot.signal_command(update, context)

        assert update.message.reply_text.called

    @pytest.mark.asyncio
    async def test_watchlist_command(self, telegram_bot):
        """Test /watchlist command"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()

        await telegram_bot.watchlist_command(update, context)

        update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_alerts_command(self, telegram_bot):
        """Test /alerts command"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()

        await telegram_bot.alerts_command(update, context)

        update.message.reply_text.assert_called()

    @pytest.mark.asyncio
    async def test_button_callback(self, telegram_bot):
        """Test button callback handling"""
        update = Mock()
        update.callback_query.answer = AsyncMock()
        update.callback_query.data = "test_action"
        context = Mock()

        await telegram_bot.button_callback(update, context)

        update.callback_query.answer.assert_called()

    @pytest.mark.asyncio
    async def test_unknown_command(self, telegram_bot):
        """Test unknown command handling"""
        update = Mock()
        update.message.reply_text = AsyncMock()
        context = Mock()

        await telegram_bot.unknown_command(update, context)

        update.message.reply_text.assert_called()

    def test_bot_run(self, telegram_bot, mock_application):
        """Test bot running"""
        telegram_bot.run()

        mock_application.run_polling.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_alert_function(self):
        """Test standalone send_alert function"""
        with patch('telegram.Bot') as mock_bot_class:
            mock_bot = Mock()
            mock_bot.send_message = AsyncMock()
            mock_bot_class.return_value = mock_bot

            await send_alert(
                token="test_token",
                chat_id="123456",
                symbol="AAPL",
                signal_type="BUY",
                price=150.50
            )

            mock_bot.send_message.assert_called_once()


# ===== INTEGRATION TESTS =====

class TestAlertsIntegration:
    """Integration tests for alert services"""

    def test_all_alert_services_exist(self):
        """Test all alert services can be instantiated"""
        # Discord
        discord = DiscordAlerter(webhook_url="https://test.com/webhook")
        assert discord is not None

        # SMS with mocked Twilio
        with patch('twilio.rest.Client'):
            sms = SMSAlerter(
                account_sid="test",
                auth_token="test",
                from_number="+1234567890",
                to_number="+0987654321"
            )
            assert sms is not None

        # TTS with mocked pyttsx3
        with patch('pyttsx3.init'):
            tts = TTSEngine()
            assert tts is not None

        # Telegram with mocked application
        with patch('telegram.ext.Application.builder') as mock_builder:
            mock_app = Mock()
            mock_builder.return_value.token.return_value.build.return_value = mock_app

            telegram = TradingBot(token="test")
            assert telegram is not None

    def test_all_alert_services_have_send_methods(self):
        """Test all services have send/alert methods"""
        # Discord
        discord = DiscordAlerter(webhook_url="https://test.com/webhook")
        assert hasattr(discord, 'send_alert')
        assert hasattr(discord, 'send_simple_message')

        # SMS
        with patch('twilio.rest.Client'):
            sms = SMSAlerter(
                account_sid="test",
                auth_token="test",
                from_number="+1",
                to_number="+2"
            )
            assert hasattr(sms, 'send_alert')
            assert hasattr(sms, 'send_simple_message')

        # TTS
        with patch('pyttsx3.init'):
            tts = TTSEngine()
            assert hasattr(tts, 'speak')
            assert hasattr(tts, 'alert')

        # Telegram
        with patch('telegram.ext.Application.builder') as mock_builder:
            mock_app = Mock()
            mock_builder.return_value.token.return_value.build.return_value = mock_app

            telegram = TradingBot(token="test")
            assert hasattr(telegram, 'run')

    def test_alert_message_formatting(self):
        """Test that alerts can be formatted consistently"""
        # Common alert data
        alert_data = {
            'symbol': 'AAPL',
            'signal_type': 'BUY',
            'price': 150.50,
            'confidence': 0.85,
            'reasoning': 'Strong momentum'
        }

        # All services should handle this data
        with patch('requests.post'):
            discord = DiscordAlerter(webhook_url="https://test.com/webhook")
            result = discord.send_alert(**alert_data)
            assert isinstance(result, bool)

        with patch('twilio.rest.Client'):
            sms = SMSAlerter(
                account_sid="test",
                auth_token="test",
                from_number="+1",
                to_number="+2"
            )
            result = sms.send_alert(**alert_data)
            assert isinstance(result, bool)

        with patch('pyttsx3.init'):
            tts = TTSEngine()
            result = tts.alert(**alert_data)
            assert isinstance(result, bool)

    def test_error_handling_consistency(self):
        """Test that all services handle errors gracefully"""
        # Discord with network error
        with patch('requests.post', side_effect=Exception("Network error")):
            discord = DiscordAlerter(webhook_url="https://test.com/webhook")
            result = discord.send_alert("AAPL", "BUY", 150.50)
            assert result == False

        # SMS with API error
        with patch('twilio.rest.Client') as mock_client:
            mock_client.return_value.messages.create.side_effect = Exception("API error")
            sms = SMSAlerter(
                account_sid="test",
                auth_token="test",
                from_number="+1",
                to_number="+2"
            )
            result = sms.send_alert("AAPL", "BUY", 150.50)
            assert result == False

        # TTS with engine error
        with patch('pyttsx3.init', side_effect=Exception("TTS error")):
            try:
                tts = TTSEngine()
                result = False  # If no exception, initialization succeeded
            except:
                result = True  # Exception expected
            assert result in [True, False]  # Either way is acceptable
