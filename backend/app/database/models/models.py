"""
Database models for the trading system
"""
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .base import Base


class SignalType(str, enum.Enum):
    """Signal types"""
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


class AlertStatus(str, enum.Enum):
    """Alert status"""
    ACTIVE = "ACTIVE"
    TRIGGERED = "TRIGGERED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(50))
    last_name = Column(String(50))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    watchlists = relationship("Watchlist", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="user", cascade="all, delete-orphan")


class Watchlist(Base):
    """Watchlist model"""
    __tablename__ = "watchlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="watchlists")
    symbols = relationship("WatchlistSymbol", back_populates="watchlist", cascade="all, delete-orphan")


class WatchlistSymbol(Base):
    """Watchlist symbol model"""
    __tablename__ = "watchlist_symbols"

    id = Column(Integer, primary_key=True, index=True)
    watchlist_id = Column(Integer, ForeignKey("watchlists.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(50))
    notes = Column(Text)
    added_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    watchlist = relationship("Watchlist", back_populates="symbols")


class Signal(Base):
    """Trading signal model"""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(50))
    signal_type = Column(SQLEnum(SignalType), nullable=False)
    strength = Column(Float)  # 0-100
    confidence = Column(Float)  # 0-1
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    reasoning = Column(Text)
    indicators = Column(JSON)
    patterns = Column(JSON)
    timeframe = Column(String(10))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime)


class Alert(Base):
    """Alert model"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(50))
    alert_type = Column(String(50), nullable=False)  # PRICE, INDICATOR, PATTERN
    condition = Column(JSON, nullable=False)  # Alert condition details
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.ACTIVE, index=True)
    message = Column(Text)
    channels = Column(JSON)  # List of notification channels
    triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alerts")


class Strategy(Base):
    """Trading strategy model"""
    __tablename__ = "strategies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)  # Strategy code (Python)
    parameters = Column(JSON)  # Strategy parameters
    is_active = Column(Boolean, default=False)
    performance = Column(JSON)  # Backtest results
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="strategies")


class Trade(Base):
    """Trade history model"""
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(50))
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    pnl = Column(Float)
    pnl_percentage = Column(Float)
    opened_at = Column(DateTime, default=datetime.utcnow, index=True)
    closed_at = Column(DateTime)
    notes = Column(Text)
    strategy_id = Column(Integer, ForeignKey("strategies.id"))


class MarketData(Base):
    """Market data cache model"""
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    exchange = Column(String(50))
    timeframe = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class News(Base):
    """News articles model"""
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    url = Column(String(1000))
    source = Column(String(100))
    sentiment = Column(Float)  # -1 to 1
    published_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SocialSentiment(Base):
    """Social media sentiment model"""
    __tablename__ = "social_sentiment"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    platform = Column(String(50), nullable=False)  # TWITTER, REDDIT, etc.
    content = Column(Text)
    sentiment = Column(Float)  # -1 to 1
    engagement = Column(Integer)  # likes, retweets, etc.
    author = Column(String(100))
    posted_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestResult(Base):
    """Backtest results model"""
    __tablename__ = "backtest_results"

    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float)
    total_return_pct = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    avg_win = Column(Float)
    avg_loss = Column(Float)
    metrics = Column(JSON)  # Additional metrics
    trades_data = Column(JSON)  # Trade-by-trade data
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemLog(Base):
    """System logs model"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String(20), nullable=False, index=True)  # INFO, WARNING, ERROR
    module = Column(String(100), index=True)
    message = Column(Text, nullable=False)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class APIKey(Base):
    """API keys model"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    key = Column(String(255), nullable=False, unique=True, index=True)
    permissions = Column(JSON)  # List of allowed operations
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
