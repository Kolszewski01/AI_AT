"""
Candlestick Pattern Detection
Wszystkie formacje świecowe opisane w architekturze
"""
import pandas as pd
import talib as ta
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class CandlestickPatterns:
    """
    Klasa do wykrywania wszystkich formacji świecowych
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

    def _get_pattern_result(self, result: pd.Series, pattern_name: str, signal_type: str) -> List[Dict]:
        """
        Helper to convert ta-lib pattern result to list of detections

        Args:
            result: Series with pattern detections
            pattern_name: Name of the pattern
            signal_type: 'bullish', 'bearish', or 'neutral'

        Returns:
            List of pattern dictionaries
        """
        patterns = []
        for idx in range(len(result)):
            if result.iloc[idx] != 0:
                patterns.append({
                    'timestamp': str(self.df.index[idx]),
                    'pattern': pattern_name,
                    'signal': signal_type,
                    'strength': abs(result.iloc[idx]) / 100,  # Normalize to 0-1
                    'index': idx
                })
        return patterns

    # ===== REVERSAL PATTERNS (BULLISH) =====

    def hammer(self) -> List[Dict]:
        """Hammer - bullish reversal"""
        result = ta.CDLHAMMER(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Hammer', 'bullish')

    def inverted_hammer(self) -> List[Dict]:
        """Inverted Hammer - bullish reversal"""
        result = ta.CDLINVERTEDHAMMER(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Inverted Hammer', 'bullish')

    def bullish_engulfing(self) -> List[Dict]:
        """Bullish Engulfing - bullish reversal"""
        result = ta.CDLENGULFING(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        # Filter for bullish only (positive values)
        bullish = result[result > 0]
        patterns = []
        for idx in bullish.index:
            patterns.append({
                'timestamp': str(idx),
                'pattern': 'Bullish Engulfing',
                'signal': 'bullish',
                'strength': abs(bullish[idx]) / 100,
                'index': self.df.index.get_loc(idx)
            })
        return patterns

    def morning_star(self) -> List[Dict]:
        """Morning Star - bullish reversal"""
        result = ta.CDLMORNINGSTAR(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Morning Star', 'bullish')

    def bullish_harami(self) -> List[Dict]:
        """Bullish Harami - bullish reversal"""
        result = ta.CDLHARAMI(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        # Filter for bullish only
        bullish = result[result > 0]
        patterns = []
        for idx in bullish.index:
            patterns.append({
                'timestamp': str(idx),
                'pattern': 'Bullish Harami',
                'signal': 'bullish',
                'strength': abs(bullish[idx]) / 100,
                'index': self.df.index.get_loc(idx)
            })
        return patterns

    def three_white_soldiers(self) -> List[Dict]:
        """Three White Soldiers - bullish continuation"""
        result = ta.CDL3WHITESOLDIERS(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Three White Soldiers', 'bullish')

    def piercing_pattern(self) -> List[Dict]:
        """Piercing Pattern - bullish reversal"""
        result = ta.CDLPIERCING(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Piercing Pattern', 'bullish')

    # ===== REVERSAL PATTERNS (BEARISH) =====

    def shooting_star(self) -> List[Dict]:
        """Shooting Star - bearish reversal"""
        result = ta.CDLSHOOTINGSTAR(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Shooting Star', 'bearish')

    def hanging_man(self) -> List[Dict]:
        """Hanging Man - bearish reversal"""
        result = ta.CDLHANGINGMAN(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Hanging Man', 'bearish')

    def bearish_engulfing(self) -> List[Dict]:
        """Bearish Engulfing - bearish reversal"""
        result = ta.CDLENGULFING(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        # Filter for bearish only (negative values)
        bearish = result[result < 0]
        patterns = []
        for idx in bearish.index:
            patterns.append({
                'timestamp': str(idx),
                'pattern': 'Bearish Engulfing',
                'signal': 'bearish',
                'strength': abs(bearish[idx]) / 100,
                'index': self.df.index.get_loc(idx)
            })
        return patterns

    def evening_star(self) -> List[Dict]:
        """Evening Star - bearish reversal"""
        result = ta.CDLEVENINGSTAR(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Evening Star', 'bearish')

    def bearish_harami(self) -> List[Dict]:
        """Bearish Harami - bearish reversal"""
        result = ta.CDLHARAMI(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        # Filter for bearish only
        bearish = result[result < 0]
        patterns = []
        for idx in bearish.index:
            patterns.append({
                'timestamp': str(idx),
                'pattern': 'Bearish Harami',
                'signal': 'bearish',
                'strength': abs(bearish[idx]) / 100,
                'index': self.df.index.get_loc(idx)
            })
        return patterns

    def three_black_crows(self) -> List[Dict]:
        """Three Black Crows - bearish continuation"""
        result = ta.CDL3BLACKCROWS(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Three Black Crows', 'bearish')

    def dark_cloud_cover(self) -> List[Dict]:
        """Dark Cloud Cover - bearish reversal"""
        result = ta.CDLDARKCLOUDCOVER(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Dark Cloud Cover', 'bearish')

    # ===== NEUTRAL / INDECISION PATTERNS =====

    def doji(self) -> List[Dict]:
        """Doji - indecision"""
        result = ta.CDLDOJI(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Doji', 'neutral')

    def dragonfly_doji(self) -> List[Dict]:
        """Dragonfly Doji - potential bullish reversal"""
        result = ta.CDLDRAGONFLYDOJI(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Dragonfly Doji', 'bullish')

    def gravestone_doji(self) -> List[Dict]:
        """Gravestone Doji - potential bearish reversal"""
        result = ta.CDLGRAVESTONEDOJI(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Gravestone Doji', 'bearish')

    def spinning_top(self) -> List[Dict]:
        """Spinning Top - indecision"""
        result = ta.CDLSPINNINGTOP(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        return self._get_pattern_result(result, 'Spinning Top', 'neutral')

    def marubozu(self) -> List[Dict]:
        """Marubozu - strong trend continuation"""
        result = ta.CDLMARUBOZU(
            self.df['open'],
            self.df['high'],
            self.df['low'],
            self.df['close']
        )
        # Marubozu can be bullish or bearish
        patterns = []
        for idx in range(len(result)):
            if result.iloc[idx] > 0:
                patterns.append({
                    'timestamp': str(self.df.index[idx]),
                    'pattern': 'Bullish Marubozu',
                    'signal': 'bullish',
                    'strength': abs(result.iloc[idx]) / 100,
                    'index': idx
                })
            elif result.iloc[idx] < 0:
                patterns.append({
                    'timestamp': str(self.df.index[idx]),
                    'pattern': 'Bearish Marubozu',
                    'signal': 'bearish',
                    'strength': abs(result.iloc[idx]) / 100,
                    'index': idx
                })
        return patterns

    # ===== DETECT ALL =====

    def detect_all(self, lookback: int = 10) -> List[Dict]:
        """
        Detect all candlestick patterns in the last N candles

        Args:
            lookback: Number of recent candles to check

        Returns:
            List of all detected patterns with details
        """
        all_patterns = []

        # Bullish patterns
        all_patterns.extend(self.hammer())
        all_patterns.extend(self.inverted_hammer())
        all_patterns.extend(self.bullish_engulfing())
        all_patterns.extend(self.morning_star())
        all_patterns.extend(self.bullish_harami())
        all_patterns.extend(self.three_white_soldiers())
        all_patterns.extend(self.piercing_pattern())
        all_patterns.extend(self.dragonfly_doji())

        # Bearish patterns
        all_patterns.extend(self.shooting_star())
        all_patterns.extend(self.hanging_man())
        all_patterns.extend(self.bearish_engulfing())
        all_patterns.extend(self.evening_star())
        all_patterns.extend(self.bearish_harami())
        all_patterns.extend(self.three_black_crows())
        all_patterns.extend(self.dark_cloud_cover())
        all_patterns.extend(self.gravestone_doji())

        # Neutral patterns
        all_patterns.extend(self.doji())
        all_patterns.extend(self.spinning_top())
        all_patterns.extend(self.marubozu())

        # Filter to last N candles
        total_candles = len(self.df)
        recent_patterns = [
            p for p in all_patterns
            if p['index'] >= (total_candles - lookback)
        ]

        # Sort by timestamp (most recent first)
        recent_patterns.sort(key=lambda x: x['timestamp'], reverse=True)

        logger.info(f"Detected {len(recent_patterns)} patterns in last {lookback} candles")

        return recent_patterns

    def get_pattern_summary(self) -> Dict:
        """
        Get summary of patterns detected

        Returns:
            Dictionary with pattern counts and signals
        """
        patterns = self.detect_all(lookback=20)

        bullish_count = sum(1 for p in patterns if p['signal'] == 'bullish')
        bearish_count = sum(1 for p in patterns if p['signal'] == 'bearish')
        neutral_count = sum(1 for p in patterns if p['signal'] == 'neutral')

        total = len(patterns)
        if total == 0:
            overall_signal = 'NEUTRAL'
            confidence = 0
        elif bullish_count > bearish_count * 1.5:
            overall_signal = 'BULLISH'
            confidence = (bullish_count / total) * 100
        elif bearish_count > bullish_count * 1.5:
            overall_signal = 'BEARISH'
            confidence = (bearish_count / total) * 100
        else:
            overall_signal = 'NEUTRAL'
            confidence = 50

        return {
            'total_patterns': total,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'neutral_count': neutral_count,
            'overall_signal': overall_signal,
            'confidence': round(confidence, 2),
            'patterns': patterns[:5]  # Return top 5 most recent
        }
