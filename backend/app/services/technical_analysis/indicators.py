"""
Complete Technical Indicators Library
Wszystkie wskaźniki techniczne wymagane w systemie
"""
import pandas as pd
import numpy as np
import talib as ta
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Klasa zawierająca wszystkie wskaźniki techniczne
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with OHLCV dataframe

        Args:
            df: DataFrame z kolumnami: open, high, low, close, volume
        """
        self.df = df.copy()
        # Normalize column names
        self.df.columns = [col.lower() for col in self.df.columns]

    # ===== MOMENTUM INDICATORS =====

    def rsi(self, period: int = 14) -> pd.Series:
        """RSI - Relative Strength Index"""
        return ta.RSI(self.df['close'], timeperiod=period)

    def stochastic(
        self,
        fastk_period: int = 14,
        slowk_period: int = 3,
        slowd_period: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator (K%D)"""
        slowk, slowd = ta.STOCH(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            fastk_period=fastk_period,
            slowk_period=slowk_period,
            slowd_period=slowd_period
        )
        return slowk, slowd

    def cci(self, period: int = 20) -> pd.Series:
        """CCI - Commodity Channel Index"""
        return ta.CCI(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            timeperiod=period
        )

    def williams_r(self, period: int = 14) -> pd.Series:
        """Williams %R"""
        return ta.WILLR(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            timeperiod=period
        )

    def mfi(self, period: int = 14) -> pd.Series:
        """MFI - Money Flow Index"""
        return ta.MFI(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            self.df['volume'],
            timeperiod=period
        )

    # ===== TREND INDICATORS =====

    def macd(
        self,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD - Moving Average Convergence Divergence"""
        macd_line, signal_line, histogram = ta.MACD(
            self.df['close'],
            fastperiod=fast,
            slowperiod=slow,
            signalperiod=signal
        )
        return macd_line, signal_line, histogram

    def adx(self, period: int = 14) -> pd.Series:
        """ADX - Average Directional Index"""
        return ta.ADX(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            timeperiod=period
        )

    def sma(self, period: int = 20) -> pd.Series:
        """SMA - Simple Moving Average"""
        return ta.SMA(self.df['close'], timeperiod=period)

    def ema(self, period: int = 20) -> pd.Series:
        """EMA - Exponential Moving Average"""
        return ta.EMA(self.df['close'], timeperiod=period)

    def wma(self, period: int = 20) -> pd.Series:
        """WMA - Weighted Moving Average"""
        return ta.WMA(self.df['close'], timeperiod=period)

    def ichimoku(self) -> Dict[str, pd.Series]:
        """
        Ichimoku Cloud components
        Returns: tenkan, kijun, senkou_a, senkou_b, chikou
        """
        high = self.df['high']
        low = self.df['low']
        close = self.df['close']

        # Tenkan-sen (Conversion Line): (9-period high + 9-period low)/2
        nine_period_high = high.rolling(window=9).max()
        nine_period_low = low.rolling(window=9).min()
        tenkan = (nine_period_high + nine_period_low) / 2

        # Kijun-sen (Base Line): (26-period high + 26-period low)/2
        period26_high = high.rolling(window=26).max()
        period26_low = low.rolling(window=26).min()
        kijun = (period26_high + period26_low) / 2

        # Senkou Span A (Leading Span A): (Conversion Line + Base Line)/2
        senkou_a = ((tenkan + kijun) / 2).shift(26)

        # Senkou Span B (Leading Span B): (52-period high + 52-period low)/2
        period52_high = high.rolling(window=52).max()
        period52_low = low.rolling(window=52).min()
        senkou_b = ((period52_high + period52_low) / 2).shift(26)

        # Chikou Span (Lagging Span): Close plotted 26 days in the past
        chikou = close.shift(-26)

        return {
            'tenkan': tenkan,
            'kijun': kijun,
            'senkou_a': senkou_a,
            'senkou_b': senkou_b,
            'chikou': chikou
        }

    # ===== VOLATILITY INDICATORS =====

    def bollinger_bands(
        self,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands (Upper, Middle, Lower)"""
        upper, middle, lower = ta.BBANDS(
            self.df['close'],
            timeperiod=period,
            nbdevup=std_dev,
            nbdevdn=std_dev
        )
        return upper, middle, lower

    def atr(self, period: int = 14) -> pd.Series:
        """ATR - Average True Range"""
        return ta.ATR(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            timeperiod=period
        )

    def keltner_channel(
        self,
        ema_period: int = 20,
        atr_period: int = 10,
        multiplier: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Keltner Channel (Upper, Middle, Lower)"""
        middle = self.ema(ema_period)
        atr_values = self.atr(atr_period)

        upper = middle + (multiplier * atr_values)
        lower = middle - (multiplier * atr_values)

        return upper, middle, lower

    # ===== VOLUME INDICATORS =====

    def obv(self) -> pd.Series:
        """OBV - On-Balance Volume"""
        return ta.OBV(self.df['close'], self.df['volume'])

    def vwap(self) -> pd.Series:
        """VWAP - Volume Weighted Average Price"""
        typical_price = (self.df['high'] + self.df['low'] + self.df['close']) / 3
        return (typical_price * self.df['volume']).cumsum() / self.df['volume'].cumsum()

    # ===== COMPLETE ANALYSIS =====

    def calculate_all(self) -> Dict:
        """
        Calculate all indicators at once

        Returns:
            Dictionary with all indicator values
        """
        try:
            # Momentum
            rsi_val = self.rsi()
            stoch_k, stoch_d = self.stochastic()
            cci_val = self.cci()
            williams_val = self.williams_r()
            mfi_val = self.mfi()

            # Trend
            macd_line, macd_signal, macd_hist = self.macd()
            adx_val = self.adx()
            sma_20 = self.sma(20)
            sma_50 = self.sma(50)
            sma_200 = self.sma(200)
            ema_12 = self.ema(12)
            ema_26 = self.ema(26)

            # Volatility
            bb_upper, bb_middle, bb_lower = self.bollinger_bands()
            atr_val = self.atr()

            # Volume
            obv_val = self.obv()
            vwap_val = self.vwap()

            # Ichimoku
            ichimoku_data = self.ichimoku()

            # Keltner
            kc_upper, kc_middle, kc_lower = self.keltner_channel()

            # Get latest values
            latest = {
                # Momentum
                'rsi': float(rsi_val.iloc[-1]) if not pd.isna(rsi_val.iloc[-1]) else None,
                'stochastic_k': float(stoch_k.iloc[-1]) if not pd.isna(stoch_k.iloc[-1]) else None,
                'stochastic_d': float(stoch_d.iloc[-1]) if not pd.isna(stoch_d.iloc[-1]) else None,
                'cci': float(cci_val.iloc[-1]) if not pd.isna(cci_val.iloc[-1]) else None,
                'williams_r': float(williams_val.iloc[-1]) if not pd.isna(williams_val.iloc[-1]) else None,
                'mfi': float(mfi_val.iloc[-1]) if not pd.isna(mfi_val.iloc[-1]) else None,

                # Trend
                'macd': float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None,
                'macd_signal': float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else None,
                'macd_histogram': float(macd_hist.iloc[-1]) if not pd.isna(macd_hist.iloc[-1]) else None,
                'adx': float(adx_val.iloc[-1]) if not pd.isna(adx_val.iloc[-1]) else None,
                'sma_20': float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None,
                'sma_50': float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None,
                'sma_200': float(sma_200.iloc[-1]) if not pd.isna(sma_200.iloc[-1]) else None,
                'ema_12': float(ema_12.iloc[-1]) if not pd.isna(ema_12.iloc[-1]) else None,
                'ema_26': float(ema_26.iloc[-1]) if not pd.isna(ema_26.iloc[-1]) else None,

                # Volatility
                'bollinger_upper': float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None,
                'bollinger_middle': float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else None,
                'bollinger_lower': float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None,
                'atr': float(atr_val.iloc[-1]) if not pd.isna(atr_val.iloc[-1]) else None,
                'keltner_upper': float(kc_upper.iloc[-1]) if not pd.isna(kc_upper.iloc[-1]) else None,
                'keltner_middle': float(kc_middle.iloc[-1]) if not pd.isna(kc_middle.iloc[-1]) else None,
                'keltner_lower': float(kc_lower.iloc[-1]) if not pd.isna(kc_lower.iloc[-1]) else None,

                # Volume
                'obv': float(obv_val.iloc[-1]) if not pd.isna(obv_val.iloc[-1]) else None,
                'vwap': float(vwap_val.iloc[-1]) if not pd.isna(vwap_val.iloc[-1]) else None,

                # Ichimoku
                'ichimoku_tenkan': float(ichimoku_data['tenkan'].iloc[-1]) if not pd.isna(ichimoku_data['tenkan'].iloc[-1]) else None,
                'ichimoku_kijun': float(ichimoku_data['kijun'].iloc[-1]) if not pd.isna(ichimoku_data['kijun'].iloc[-1]) else None,
                'ichimoku_senkou_a': float(ichimoku_data['senkou_a'].iloc[-1]) if not pd.isna(ichimoku_data['senkou_a'].iloc[-1]) else None,
                'ichimoku_senkou_b': float(ichimoku_data['senkou_b'].iloc[-1]) if not pd.isna(ichimoku_data['senkou_b'].iloc[-1]) else None,
            }

            return latest

        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
            return {}

    def get_signal_summary(self) -> Dict:
        """
        Get trading signals based on all indicators

        Returns:
            Dictionary with bullish/bearish counts and overall signal
        """
        indicators = self.calculate_all()
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        # RSI signals
        if indicators.get('rsi'):
            if indicators['rsi'] < 30:
                bullish_count += 2
            elif indicators['rsi'] > 70:
                bearish_count += 2
            else:
                neutral_count += 1

        # Stochastic signals
        if indicators.get('stochastic_k'):
            if indicators['stochastic_k'] < 20:
                bullish_count += 1
            elif indicators['stochastic_k'] > 80:
                bearish_count += 1

        # MACD signal
        if indicators.get('macd') and indicators.get('macd_signal'):
            if indicators['macd'] > indicators['macd_signal']:
                bullish_count += 2
            else:
                bearish_count += 2

        # ADX (trend strength)
        if indicators.get('adx'):
            if indicators['adx'] > 25:
                # Strong trend - amplify other signals
                pass
            elif indicators['adx'] < 20:
                # Weak trend - consider neutral
                neutral_count += 1

        # Moving Average crosses
        if indicators.get('sma_20') and indicators.get('sma_50'):
            current_price = self.df['close'].iloc[-1]
            if current_price > indicators['sma_20'] > indicators['sma_50']:
                bullish_count += 1
            elif current_price < indicators['sma_20'] < indicators['sma_50']:
                bearish_count += 1

        # Bollinger Bands
        if indicators.get('bollinger_lower') and indicators.get('bollinger_upper'):
            current_price = self.df['close'].iloc[-1]
            if current_price < indicators['bollinger_lower']:
                bullish_count += 1
            elif current_price > indicators['bollinger_upper']:
                bearish_count += 1

        total = bullish_count + bearish_count + neutral_count
        if total == 0:
            return {'signal': 'NEUTRAL', 'strength': 50, 'bullish_count': 0, 'bearish_count': 0}

        bullish_percent = (bullish_count / total) * 100
        bearish_percent = (bearish_count / total) * 100

        if bullish_percent > bearish_percent + 20:
            signal = 'BUY'
            strength = int(bullish_percent)
        elif bearish_percent > bullish_percent + 20:
            signal = 'SELL'
            strength = int(bearish_percent)
        else:
            signal = 'NEUTRAL'
            strength = 50

        return {
            'signal': signal,
            'strength': strength,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count
        }
