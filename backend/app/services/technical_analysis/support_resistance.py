"""
Automatic Support and Resistance zone detection
Uses multiple methods: pivot points, fractals, volume profile, and clustering
"""
import logging
from typing import List, Dict, Tuple, Optional
import numpy as np
import pandas as pd
from scipy.signal import find_peaks, argrelextrema
from sklearn.cluster import DBSCAN

logger = logging.getLogger(__name__)


class SupportResistanceDetector:
    """
    Detect support and resistance levels automatically
    """

    def __init__(self, sensitivity: float = 0.02):
        """
        Initialize detector

        Args:
            sensitivity: Price difference threshold for merging levels (as ratio)
        """
        self.sensitivity = sensitivity

    def detect_fractals(
        self,
        df: pd.DataFrame,
        left_bars: int = 5,
        right_bars: int = 5
    ) -> Tuple[List[float], List[float]]:
        """
        Detect fractal support and resistance levels

        Args:
            df: DataFrame with OHLCV data
            left_bars: Number of bars to the left
            right_bars: Number of bars to the right

        Returns:
            Tuple of (support_levels, resistance_levels)
        """
        if len(df) < left_bars + right_bars + 1:
            return [], []

        highs = df['high'].values
        lows = df['low'].values

        # Find local maxima (resistance)
        resistance_indices = argrelextrema(
            highs,
            np.greater_equal,
            order=left_bars
        )[0]

        # Find local minima (support)
        support_indices = argrelextrema(
            lows,
            np.less_equal,
            order=left_bars
        )[0]

        resistance_levels = highs[resistance_indices].tolist()
        support_levels = lows[support_indices].tolist()

        logger.info(
            f"Detected {len(support_levels)} support and "
            f"{len(resistance_levels)} resistance fractals"
        )

        return support_levels, resistance_levels

    def detect_pivot_points(
        self,
        df: pd.DataFrame,
        method: str = 'standard'
    ) -> Dict[str, float]:
        """
        Calculate pivot points

        Args:
            df: DataFrame with OHLCV data
            method: 'standard', 'fibonacci', or 'camarilla'

        Returns:
            Dictionary with pivot levels
        """
        if len(df) == 0:
            return {}

        # Use last complete candle
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]
        close = df['close'].iloc[-1]

        pivot = (high + low + close) / 3

        if method == 'standard':
            r1 = 2 * pivot - low
            s1 = 2 * pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            r3 = high + 2 * (pivot - low)
            s3 = low - 2 * (high - pivot)

        elif method == 'fibonacci':
            r1 = pivot + 0.382 * (high - low)
            s1 = pivot - 0.382 * (high - low)
            r2 = pivot + 0.618 * (high - low)
            s2 = pivot - 0.618 * (high - low)
            r3 = pivot + (high - low)
            s3 = pivot - (high - low)

        elif method == 'camarilla':
            r1 = close + (high - low) * 1.1 / 12
            s1 = close - (high - low) * 1.1 / 12
            r2 = close + (high - low) * 1.1 / 6
            s2 = close - (high - low) * 1.1 / 6
            r3 = close + (high - low) * 1.1 / 4
            s3 = close - (high - low) * 1.1 / 4

        else:
            raise ValueError(f"Unknown pivot method: {method}")

        return {
            'pivot': pivot,
            'r1': r1, 's1': s1,
            'r2': r2, 's2': s2,
            'r3': r3, 's3': s3,
            'method': method
        }

    def detect_volume_profile(
        self,
        df: pd.DataFrame,
        num_bins: int = 50
    ) -> List[Dict]:
        """
        Detect high-volume price levels (Point of Control, Value Area)

        Args:
            df: DataFrame with OHLCV data
            num_bins: Number of price bins

        Returns:
            List of volume profile levels
        """
        if len(df) == 0:
            return []

        # Create price bins
        price_min = df['low'].min()
        price_max = df['high'].max()
        bins = np.linspace(price_min, price_max, num_bins)

        # Aggregate volume by price level
        volume_profile = []
        for i in range(len(bins) - 1):
            bin_low = bins[i]
            bin_high = bins[i + 1]

            # Find candles within this price range
            mask = (df['low'] <= bin_high) & (df['high'] >= bin_low)
            volume = df.loc[mask, 'volume'].sum()

            if volume > 0:
                volume_profile.append({
                    'price': (bin_low + bin_high) / 2,
                    'volume': volume,
                    'range': (bin_low, bin_high)
                })

        # Sort by volume
        volume_profile.sort(key=lambda x: x['volume'], reverse=True)

        # Point of Control (POC) - highest volume
        poc = volume_profile[0] if volume_profile else None

        # Value Area (70% of volume)
        total_volume = sum(v['volume'] for v in volume_profile)
        value_area_volume = 0.7 * total_volume
        current_volume = 0
        value_area_levels = []

        for level in volume_profile:
            if current_volume < value_area_volume:
                value_area_levels.append(level)
                current_volume += level['volume']
            else:
                break

        logger.info(f"Detected POC at {poc['price']:.2f} and {len(value_area_levels)} value area levels")

        return {
            'poc': poc,
            'value_area': value_area_levels[:10],  # Top 10 levels
            'total_volume': total_volume
        }

    def cluster_levels(
        self,
        levels: List[float],
        eps: Optional[float] = None
    ) -> List[float]:
        """
        Cluster nearby levels using DBSCAN

        Args:
            levels: List of price levels
            eps: Clustering distance (if None, calculated from sensitivity)

        Returns:
            List of clustered levels
        """
        if not levels or len(levels) < 2:
            return levels

        # Convert to numpy array
        levels_array = np.array(levels).reshape(-1, 1)

        # Calculate eps based on sensitivity if not provided
        if eps is None:
            price_range = levels_array.max() - levels_array.min()
            eps = price_range * self.sensitivity

        # Cluster using DBSCAN
        clustering = DBSCAN(eps=eps, min_samples=1).fit(levels_array)

        # Get cluster centers
        clustered_levels = []
        for label in set(clustering.labels_):
            cluster_points = levels_array[clustering.labels_ == label]
            cluster_center = cluster_points.mean()
            clustered_levels.append(float(cluster_center))

        return sorted(clustered_levels)

    def detect_zones(
        self,
        df: pd.DataFrame,
        current_price: float,
        lookback: int = 100
    ) -> Dict:
        """
        Detect support and resistance zones using multiple methods

        Args:
            df: DataFrame with OHLCV data
            current_price: Current market price
            lookback: Number of bars to look back

        Returns:
            Dictionary with support and resistance zones
        """
        if len(df) < lookback:
            lookback = len(df)

        df_lookback = df.tail(lookback).copy()

        # Method 1: Fractals
        support_fractals, resistance_fractals = self.detect_fractals(df_lookback)

        # Method 2: Pivot Points (multiple methods)
        pivots_standard = self.detect_pivot_points(df_lookback, 'standard')
        pivots_fib = self.detect_pivot_points(df_lookback, 'fibonacci')
        pivots_cam = self.detect_pivot_points(df_lookback, 'camarilla')

        # Method 3: Volume Profile
        volume_profile = self.detect_volume_profile(df_lookback)

        # Combine all support levels
        all_support = support_fractals + [
            pivots_standard['s1'], pivots_standard['s2'], pivots_standard['s3'],
            pivots_fib['s1'], pivots_fib['s2'], pivots_fib['s3'],
            pivots_cam['s1'], pivots_cam['s2'], pivots_cam['s3'],
        ]

        # Add volume profile support levels (below current price)
        if volume_profile.get('value_area'):
            value_area_support = [
                v['price'] for v in volume_profile['value_area']
                if v['price'] < current_price
            ]
            all_support.extend(value_area_support)

        # Combine all resistance levels
        all_resistance = resistance_fractals + [
            pivots_standard['r1'], pivots_standard['r2'], pivots_standard['r3'],
            pivots_fib['r1'], pivots_fib['r2'], pivots_fib['r3'],
            pivots_cam['r1'], pivots_cam['r2'], pivots_cam['r3'],
        ]

        # Add volume profile resistance levels (above current price)
        if volume_profile.get('value_area'):
            value_area_resistance = [
                v['price'] for v in volume_profile['value_area']
                if v['price'] > current_price
            ]
            all_resistance.extend(value_area_resistance)

        # Filter and cluster
        support_below = [s for s in all_support if s < current_price]
        resistance_above = [r for r in all_resistance if r > current_price]

        clustered_support = self.cluster_levels(support_below)
        clustered_resistance = self.cluster_levels(resistance_above)

        # Sort and take top levels
        clustered_support.sort(reverse=True)  # Closest to current price first
        clustered_resistance.sort()  # Closest to current price first

        # Calculate strength based on number of touches
        support_zones = self._calculate_zone_strength(
            clustered_support[:10], df_lookback, 'support'
        )
        resistance_zones = self._calculate_zone_strength(
            clustered_resistance[:10], df_lookback, 'resistance'
        )

        return {
            'support': support_zones,
            'resistance': resistance_zones,
            'current_price': current_price,
            'pivots': {
                'standard': pivots_standard,
                'fibonacci': pivots_fib,
                'camarilla': pivots_cam,
            },
            'volume_profile': volume_profile,
        }

    def _calculate_zone_strength(
        self,
        levels: List[float],
        df: pd.DataFrame,
        zone_type: str
    ) -> List[Dict]:
        """
        Calculate strength of each zone based on touches

        Args:
            levels: List of price levels
            df: DataFrame with OHLCV data
            zone_type: 'support' or 'resistance'

        Returns:
            List of zones with strength
        """
        zones = []
        tolerance = df['close'].mean() * self.sensitivity

        for level in levels:
            # Count touches
            if zone_type == 'support':
                touches = ((df['low'] >= level - tolerance) &
                          (df['low'] <= level + tolerance)).sum()
            else:
                touches = ((df['high'] >= level - tolerance) &
                          (df['high'] <= level + tolerance)).sum()

            # Calculate strength (0-1)
            strength = min(touches / 5, 1.0)  # Max strength at 5 touches

            zones.append({
                'level': round(level, 2),
                'touches': int(touches),
                'strength': round(strength, 2),
                'type': zone_type
            })

        return zones

    def detect_order_blocks(
        self,
        df: pd.DataFrame,
        lookback: int = 50
    ) -> List[Dict]:
        """
        Detect order blocks (institutional buying/selling zones)

        Args:
            df: DataFrame with OHLCV data
            lookback: Number of bars to look back

        Returns:
            List of order blocks
        """
        if len(df) < lookback + 5:
            return []

        df_lookback = df.tail(lookback).copy()
        order_blocks = []

        for i in range(2, len(df_lookback) - 2):
            current = df_lookback.iloc[i]
            prev = df_lookback.iloc[i - 1]
            next_candle = df_lookback.iloc[i + 1]

            # Bullish order block: strong move up after accumulation
            if (next_candle['close'] > current['close'] * 1.02 and
                current['close'] > current['open'] and
                current['volume'] > df_lookback['volume'].mean() * 1.5):

                order_blocks.append({
                    'type': 'bullish',
                    'top': current['high'],
                    'bottom': current['low'],
                    'timestamp': current.name if hasattr(current, 'name') else i,
                    'strength': min((next_candle['close'] - current['close']) / current['close'], 0.1) * 10
                })

            # Bearish order block: strong move down after distribution
            if (next_candle['close'] < current['close'] * 0.98 and
                current['close'] < current['open'] and
                current['volume'] > df_lookback['volume'].mean() * 1.5):

                order_blocks.append({
                    'type': 'bearish',
                    'top': current['high'],
                    'bottom': current['low'],
                    'timestamp': current.name if hasattr(current, 'name') else i,
                    'strength': min((current['close'] - next_candle['close']) / current['close'], 0.1) * 10
                })

        # Sort by strength
        order_blocks.sort(key=lambda x: x['strength'], reverse=True)

        logger.info(f"Detected {len(order_blocks)} order blocks")
        return order_blocks[:10]  # Return top 10


# Example usage
if __name__ == "__main__":
    import yfinance as yf

    # Download sample data
    symbol = "AAPL"
    df = yf.download(symbol, period="3mo", interval="1d")

    detector = SupportResistanceDetector(sensitivity=0.02)

    # Detect zones
    current_price = df['close'].iloc[-1]
    zones = detector.detect_zones(df, current_price)

    print(f"\nSupport/Resistance Analysis for {symbol}")
    print(f"Current Price: ${current_price:.2f}")
    print("=" * 50)

    print("\nSupport Zones:")
    for zone in zones['support']:
        print(f"  ${zone['level']:.2f} - Touches: {zone['touches']}, "
              f"Strength: {zone['strength']:.2f}")

    print("\nResistance Zones:")
    for zone in zones['resistance']:
        print(f"  ${zone['level']:.2f} - Touches: {zone['touches']}, "
              f"Strength: {zone['strength']:.2f}")

    # Detect order blocks
    order_blocks = detector.detect_order_blocks(df)
    print(f"\nTop 5 Order Blocks:")
    for i, block in enumerate(order_blocks[:5], 1):
        print(f"  {i}. {block['type'].upper()} - "
              f"${block['bottom']:.2f} to ${block['top']:.2f} "
              f"(Strength: {block['strength']:.2f})")
