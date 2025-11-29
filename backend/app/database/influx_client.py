"""
InfluxDB client for time series market data storage
"""
from influxdb_client import InfluxDBClient as InfluxClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


class InfluxDBClient:
    """
    InfluxDB client for storing and querying time series market data
    """

    def __init__(
        self,
        url: str = None,
        token: str = None,
        org: str = None,
        bucket: str = None
    ):
        """
        Initialize InfluxDB client

        Args:
            url: InfluxDB URL
            token: InfluxDB authentication token
            org: InfluxDB organization
            bucket: InfluxDB bucket name
        """
        self.url = url or os.getenv("INFLUX_URL", "http://localhost:8086")
        self.token = token or os.getenv("INFLUX_TOKEN", "trading_token")
        self.org = org or os.getenv("INFLUX_ORG", "trading_org")
        self.bucket = bucket or os.getenv("INFLUX_BUCKET", "market_data")

        try:
            self.client = InfluxClient(
                url=self.url,
                token=self.token,
                org=self.org,
                timeout=30000
            )
            self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
            self.query_api = self.client.query_api()
            logger.info(f"InfluxDB connection established: {self.url}")
        except Exception as e:
            logger.error(f"InfluxDB connection failed: {str(e)}")
            self.client = None
            self.write_api = None
            self.query_api = None

    def is_connected(self) -> bool:
        """
        Check if InfluxDB is connected

        Returns:
            True if connected, False otherwise
        """
        if not self.client:
            return False

        try:
            # Try to ping the server
            health = self.client.health()
            return health.status == "pass"
        except Exception:
            return False

    def write_ohlcv(
        self,
        symbol: str,
        timestamp: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        exchange: str = None,
        timeframe: str = None
    ) -> bool:
        """
        Write OHLCV data point to InfluxDB

        Args:
            symbol: Trading symbol
            timestamp: Timestamp of the candle
            open_price: Opening price
            high: High price
            low: Low price
            close: Close price
            volume: Trading volume
            exchange: Exchange name
            timeframe: Timeframe (e.g., 1h, 1d)

        Returns:
            True if successful, False otherwise
        """
        if not self.write_api:
            return False

        try:
            point = Point("ohlcv")\
                .tag("symbol", symbol)\
                .tag("exchange", exchange or "unknown")\
                .tag("timeframe", timeframe or "unknown")\
                .field("open", float(open_price))\
                .field("high", float(high))\
                .field("low", float(low))\
                .field("close", float(close))\
                .field("volume", float(volume))\
                .time(timestamp, WritePrecision.NS)

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True

        except Exception as e:
            logger.error(f"Error writing OHLCV data: {str(e)}")
            return False

    def write_ohlcv_batch(
        self,
        symbol: str,
        df: pd.DataFrame,
        exchange: str = None,
        timeframe: str = None
    ) -> bool:
        """
        Write batch of OHLCV data to InfluxDB

        Args:
            symbol: Trading symbol
            df: DataFrame with OHLCV data (columns: timestamp, open, high, low, close, volume)
            exchange: Exchange name
            timeframe: Timeframe

        Returns:
            True if successful, False otherwise
        """
        if not self.write_api:
            return False

        try:
            points = []

            for idx, row in df.iterrows():
                timestamp = row.get('timestamp', idx)
                if not isinstance(timestamp, datetime):
                    timestamp = pd.to_datetime(timestamp)

                point = Point("ohlcv")\
                    .tag("symbol", symbol)\
                    .tag("exchange", exchange or "unknown")\
                    .tag("timeframe", timeframe or "unknown")\
                    .field("open", float(row['open']))\
                    .field("high", float(row['high']))\
                    .field("low", float(row['low']))\
                    .field("close", float(row['close']))\
                    .field("volume", float(row.get('volume', 0)))\
                    .time(timestamp, WritePrecision.NS)

                points.append(point)

            self.write_api.write(bucket=self.bucket, org=self.org, record=points)
            logger.info(f"Written {len(points)} OHLCV points for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Error writing OHLCV batch: {str(e)}")
            return False

    def write_indicator(
        self,
        symbol: str,
        timestamp: datetime,
        indicator_name: str,
        value: float,
        exchange: str = None,
        timeframe: str = None,
        additional_fields: dict = None
    ) -> bool:
        """
        Write technical indicator data point

        Args:
            symbol: Trading symbol
            timestamp: Timestamp
            indicator_name: Name of the indicator (e.g., RSI, MACD)
            value: Indicator value
            exchange: Exchange name
            timeframe: Timeframe
            additional_fields: Additional fields to write

        Returns:
            True if successful, False otherwise
        """
        if not self.write_api:
            return False

        try:
            point = Point("indicators")\
                .tag("symbol", symbol)\
                .tag("exchange", exchange or "unknown")\
                .tag("timeframe", timeframe or "unknown")\
                .tag("indicator", indicator_name)\
                .field("value", float(value))\
                .time(timestamp, WritePrecision.NS)

            # Add additional fields if provided
            if additional_fields:
                for key, val in additional_fields.items():
                    point = point.field(key, float(val))

            self.write_api.write(bucket=self.bucket, org=self.org, record=point)
            return True

        except Exception as e:
            logger.error(f"Error writing indicator data: {str(e)}")
            return False

    def query_ohlcv(
        self,
        symbol: str,
        start: datetime,
        end: datetime = None,
        exchange: str = None,
        timeframe: str = None
    ) -> pd.DataFrame:
        """
        Query OHLCV data from InfluxDB

        Args:
            symbol: Trading symbol
            start: Start time
            end: End time (default: now)
            exchange: Exchange name filter
            timeframe: Timeframe filter

        Returns:
            DataFrame with OHLCV data
        """
        if not self.query_api:
            return pd.DataFrame()

        try:
            if end is None:
                end = datetime.utcnow()

            # Build Flux query
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                |> filter(fn: (r) => r["_measurement"] == "ohlcv")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
            '''

            if exchange:
                query += f'|> filter(fn: (r) => r["exchange"] == "{exchange}")\n'

            if timeframe:
                query += f'|> filter(fn: (r) => r["timeframe"] == "{timeframe}")\n'

            query += '|> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")'

            # Execute query
            result = self.query_api.query(org=self.org, query=query)

            # Convert to DataFrame
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'timestamp': record.get_time(),
                        'open': record.values.get('open'),
                        'high': record.values.get('high'),
                        'low': record.values.get('low'),
                        'close': record.values.get('close'),
                        'volume': record.values.get('volume'),
                    })

            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error querying OHLCV data: {str(e)}")
            return pd.DataFrame()

    def query_indicator(
        self,
        symbol: str,
        indicator_name: str,
        start: datetime,
        end: datetime = None,
        exchange: str = None,
        timeframe: str = None
    ) -> pd.DataFrame:
        """
        Query indicator data from InfluxDB

        Args:
            symbol: Trading symbol
            indicator_name: Indicator name
            start: Start time
            end: End time
            exchange: Exchange name filter
            timeframe: Timeframe filter

        Returns:
            DataFrame with indicator data
        """
        if not self.query_api:
            return pd.DataFrame()

        try:
            if end is None:
                end = datetime.utcnow()

            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {start.isoformat()}Z, stop: {end.isoformat()}Z)
                |> filter(fn: (r) => r["_measurement"] == "indicators")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
                |> filter(fn: (r) => r["indicator"] == "{indicator_name}")
            '''

            if exchange:
                query += f'|> filter(fn: (r) => r["exchange"] == "{exchange}")\n'

            if timeframe:
                query += f'|> filter(fn: (r) => r["timeframe"] == "{timeframe}")\n'

            result = self.query_api.query(org=self.org, query=query)

            # Convert to DataFrame
            data = []
            for table in result:
                for record in table.records:
                    data.append({
                        'timestamp': record.get_time(),
                        'indicator': record.values.get('indicator'),
                        'value': record.values.get('_value'),
                    })

            df = pd.DataFrame(data)
            if not df.empty:
                df.set_index('timestamp', inplace=True)
                df.sort_index(inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error querying indicator data: {str(e)}")
            return pd.DataFrame()

    def get_latest_candle(
        self,
        symbol: str,
        exchange: str = None,
        timeframe: str = None
    ) -> Optional[Dict]:
        """
        Get the latest candle for a symbol

        Args:
            symbol: Trading symbol
            exchange: Exchange name
            timeframe: Timeframe

        Returns:
            Dictionary with latest candle data
        """
        if not self.query_api:
            return None

        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -7d)
                |> filter(fn: (r) => r["_measurement"] == "ohlcv")
                |> filter(fn: (r) => r["symbol"] == "{symbol}")
            '''

            if exchange:
                query += f'|> filter(fn: (r) => r["exchange"] == "{exchange}")\n'

            if timeframe:
                query += f'|> filter(fn: (r) => r["timeframe"] == "{timeframe}")\n'

            query += '''
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> last()
            '''

            result = self.query_api.query(org=self.org, query=query)

            for table in result:
                for record in table.records:
                    return {
                        'timestamp': record.get_time(),
                        'open': record.values.get('open'),
                        'high': record.values.get('high'),
                        'low': record.values.get('low'),
                        'close': record.values.get('close'),
                        'volume': record.values.get('volume'),
                    }

            return None

        except Exception as e:
            logger.error(f"Error getting latest candle: {str(e)}")
            return None

    def delete_old_data(self, days: int = 90) -> bool:
        """
        Delete data older than specified days

        Args:
            days: Number of days to keep

        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            return False

        try:
            delete_api = self.client.delete_api()
            start = datetime(1970, 1, 1)
            stop = datetime.utcnow() - timedelta(days=days)

            delete_api.delete(
                start=start,
                stop=stop,
                predicate='_measurement="ohlcv" OR _measurement="indicators"',
                bucket=self.bucket,
                org=self.org
            )

            logger.info(f"Deleted data older than {days} days")
            return True

        except Exception as e:
            logger.error(f"Error deleting old data: {str(e)}")
            return False

    def close(self):
        """Close InfluxDB connection"""
        if self.client:
            self.client.close()
            logger.info("InfluxDB connection closed")
