class TradingSignal {
  final String id;
  final String symbol;
  final String timeframe;
  final String direction; // 'BUY', 'SELL', 'NEUTRAL'
  final double strength; // 0.0 to 1.0
  final double currentPrice;
  final double? entryPrice;
  final double? stopLoss;
  final double? takeProfit;
  final String strategy;
  final List<String> indicators;
  final String? pattern;
  final double? sentiment;
  final String description;
  final DateTime timestamp;
  final bool isActive;

  TradingSignal({
    required this.id,
    required this.symbol,
    required this.timeframe,
    required this.direction,
    required this.strength,
    required this.currentPrice,
    this.entryPrice,
    this.stopLoss,
    this.takeProfit,
    required this.strategy,
    required this.indicators,
    this.pattern,
    this.sentiment,
    required this.description,
    required this.timestamp,
    this.isActive = true,
  });

  factory TradingSignal.fromJson(Map<String, dynamic> json) {
    return TradingSignal(
      id: json['id'] ?? '',
      symbol: json['symbol'] ?? '',
      timeframe: json['timeframe'] ?? '1h',
      direction: json['direction'] ?? 'NEUTRAL',
      strength: (json['strength'] ?? 0.5).toDouble(),
      currentPrice: (json['current_price'] ?? 0).toDouble(),
      entryPrice: json['entry_price']?.toDouble(),
      stopLoss: json['stop_loss']?.toDouble(),
      takeProfit: json['take_profit']?.toDouble(),
      strategy: json['strategy'] ?? '',
      indicators: List<String>.from(json['indicators'] ?? []),
      pattern: json['pattern'],
      sentiment: json['sentiment']?.toDouble(),
      description: json['description'] ?? '',
      timestamp: DateTime.parse(json['timestamp'] ?? DateTime.now().toIso8601String()),
      isActive: json['is_active'] ?? true,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'symbol': symbol,
      'timeframe': timeframe,
      'direction': direction,
      'strength': strength,
      'current_price': currentPrice,
      'entry_price': entryPrice,
      'stop_loss': stopLoss,
      'take_profit': takeProfit,
      'strategy': strategy,
      'indicators': indicators,
      'pattern': pattern,
      'sentiment': sentiment,
      'description': description,
      'timestamp': timestamp.toIso8601String(),
      'is_active': isActive,
    };
  }
}
