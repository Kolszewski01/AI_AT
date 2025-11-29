"""
Database connection manager for PostgreSQL
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging
import os

from .models.base import Base, engine, SessionLocal
from .models.models import (
    User, Watchlist, WatchlistSymbol, Signal, Alert,
    Strategy, Trade, MarketData, News, SocialSentiment,
    BacktestResult, SystemLog, APIKey
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database manager for PostgreSQL operations
    """

    def __init__(self, database_url: str = None):
        """
        Initialize database manager

        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or os.getenv(
            "DATABASE_URL",
            "postgresql://trading_user:trading_pass@localhost:5432/trading_db"
        )

        self.engine = engine
        self.SessionLocal = SessionLocal

    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session with context manager

        Yields:
            Database session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()

    def init_database(self):
        """Initialize database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {str(e)}")
            raise

    def drop_all_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Error dropping tables: {str(e)}")
            raise

    def reset_database(self):
        """Reset database (drop and recreate all tables)"""
        self.drop_all_tables()
        self.init_database()
        logger.info("Database reset complete")

    def test_connection(self) -> bool:
        """
        Test database connection

        Returns:
            True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            return False

    def create_user(
        self,
        username: str,
        email: str,
        password_hash: str,
        first_name: str = None,
        last_name: str = None
    ) -> User:
        """
        Create a new user

        Args:
            username: Username
            email: Email address
            password_hash: Hashed password
            first_name: First name
            last_name: Last name

        Returns:
            Created user object
        """
        with self.get_session() as session:
            user = User(
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            session.flush()
            session.refresh(user)
            return user

    def get_user_by_username(self, username: str) -> User:
        """Get user by username"""
        with self.get_session() as session:
            return session.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        with self.get_session() as session:
            return session.query(User).filter(User.email == email).first()

    def create_watchlist(
        self,
        user_id: int,
        name: str,
        description: str = None,
        is_default: bool = False
    ) -> Watchlist:
        """Create a new watchlist"""
        with self.get_session() as session:
            watchlist = Watchlist(
                user_id=user_id,
                name=name,
                description=description,
                is_default=is_default
            )
            session.add(watchlist)
            session.flush()
            session.refresh(watchlist)
            return watchlist

    def add_symbol_to_watchlist(
        self,
        watchlist_id: int,
        symbol: str,
        exchange: str = None,
        notes: str = None
    ) -> WatchlistSymbol:
        """Add symbol to watchlist"""
        with self.get_session() as session:
            watchlist_symbol = WatchlistSymbol(
                watchlist_id=watchlist_id,
                symbol=symbol,
                exchange=exchange,
                notes=notes
            )
            session.add(watchlist_symbol)
            session.flush()
            session.refresh(watchlist_symbol)
            return watchlist_symbol

    def create_signal(
        self,
        symbol: str,
        signal_type: str,
        strength: float,
        confidence: float,
        entry_price: float,
        stop_loss: float = None,
        take_profit: float = None,
        reasoning: str = None,
        indicators: dict = None,
        patterns: dict = None,
        timeframe: str = None,
        exchange: str = None
    ) -> Signal:
        """Create a new trading signal"""
        with self.get_session() as session:
            signal = Signal(
                symbol=symbol,
                exchange=exchange,
                signal_type=signal_type,
                strength=strength,
                confidence=confidence,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                indicators=indicators,
                patterns=patterns,
                timeframe=timeframe
            )
            session.add(signal)
            session.flush()
            session.refresh(signal)
            return signal

    def get_active_signals(self, limit: int = 50):
        """Get recent active signals"""
        with self.get_session() as session:
            return session.query(Signal)\
                .order_by(Signal.created_at.desc())\
                .limit(limit)\
                .all()

    def create_alert(
        self,
        user_id: int,
        symbol: str,
        alert_type: str,
        condition: dict,
        message: str = None,
        channels: list = None,
        exchange: str = None
    ) -> Alert:
        """Create a new alert"""
        with self.get_session() as session:
            alert = Alert(
                user_id=user_id,
                symbol=symbol,
                exchange=exchange,
                alert_type=alert_type,
                condition=condition,
                message=message,
                channels=channels
            )
            session.add(alert)
            session.flush()
            session.refresh(alert)
            return alert

    def get_user_alerts(self, user_id: int, status: str = None):
        """Get alerts for a user"""
        with self.get_session() as session:
            query = session.query(Alert).filter(Alert.user_id == user_id)

            if status:
                query = query.filter(Alert.status == status)

            return query.order_by(Alert.created_at.desc()).all()

    def log_message(
        self,
        level: str,
        module: str,
        message: str,
        details: dict = None
    ):
        """Log a system message"""
        with self.get_session() as session:
            log = SystemLog(
                level=level,
                module=module,
                message=message,
                details=details
            )
            session.add(log)

    def get_recent_logs(self, limit: int = 100, level: str = None):
        """Get recent system logs"""
        with self.get_session() as session:
            query = session.query(SystemLog)

            if level:
                query = query.filter(SystemLog.level == level)

            return query.order_by(SystemLog.created_at.desc()).limit(limit).all()
