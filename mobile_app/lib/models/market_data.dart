class OHLCV {
  final DateTime timestamp;
  final double open;
  final double high;
  final double low;
  final double close;
  final double volume;

  OHLCV({
    required this.timestamp,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
  });

  factory OHLCV.fromJson(Map<String, dynamic> json) {
    return OHLCV(
      timestamp: DateTime.parse(json['timestamp']),
      open: (json['open'] ?? 0).toDouble(),
      high: (json['high'] ?? 0).toDouble(),
      low: (json['low'] ?? 0).toDouble(),
      close: (json['close'] ?? 0).toDouble(),
      volume: (json['volume'] ?? 0).toDouble(),
    );
  }
}

class MarketData {
  final String symbol;
  final String name;
  final double currentPrice;
  final double change;
  final double changePercent;
  final double volume;
  final double marketCap;
  final List<OHLCV> ohlcv;
  final Map<String, dynamic>? indicators;

  MarketData({
    required this.symbol,
    required this.name,
    required this.currentPrice,
    required this.change,
    required this.changePercent,
    required this.volume,
    required this.marketCap,
    required this.ohlcv,
    this.indicators,
  });

  factory MarketData.fromJson(Map<String, dynamic> json) {
    List<OHLCV> ohlcvList = [];
    if (json['ohlcv'] != null) {
      ohlcvList = (json['ohlcv'] as List)
          .map((item) => OHLCV.fromJson(item))
          .toList();
    }

    return MarketData(
      symbol: json['symbol'] ?? '',
      name: json['name'] ?? '',
      currentPrice: (json['current_price'] ?? 0).toDouble(),
      change: (json['change'] ?? 0).toDouble(),
      changePercent: (json['change_percent'] ?? 0).toDouble(),
      volume: (json['volume'] ?? 0).toDouble(),
      marketCap: (json['market_cap'] ?? 0).toDouble(),
      ohlcv: ohlcvList,
      indicators: json['indicators'],
    );
  }
}
