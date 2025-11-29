class Alert {
  final String id;
  final String symbol;
  final String type; // 'PRICE', 'INDICATOR', 'PATTERN', 'NEWS'
  final String condition; // 'ABOVE', 'BELOW', 'CROSSES'
  final double? targetValue;
  final String? indicator;
  final String? pattern;
  final bool isActive;
  final DateTime createdAt;
  final DateTime? triggeredAt;
  final String? message;

  Alert({
    required this.id,
    required this.symbol,
    required this.type,
    required this.condition,
    this.targetValue,
    this.indicator,
    this.pattern,
    this.isActive = true,
    required this.createdAt,
    this.triggeredAt,
    this.message,
  });

  factory Alert.fromJson(Map<String, dynamic> json) {
    return Alert(
      id: json['id'] ?? '',
      symbol: json['symbol'] ?? '',
      type: json['type'] ?? 'PRICE',
      condition: json['condition'] ?? 'ABOVE',
      targetValue: json['target_value']?.toDouble(),
      indicator: json['indicator'],
      pattern: json['pattern'],
      isActive: json['is_active'] ?? true,
      createdAt: DateTime.parse(json['created_at'] ?? DateTime.now().toIso8601String()),
      triggeredAt: json['triggered_at'] != null
          ? DateTime.parse(json['triggered_at'])
          : null,
      message: json['message'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'symbol': symbol,
      'type': type,
      'condition': condition,
      'target_value': targetValue,
      'indicator': indicator,
      'pattern': pattern,
      'is_active': isActive,
      'created_at': createdAt.toIso8601String(),
      'triggered_at': triggeredAt?.toIso8601String(),
      'message': message,
    };
  }
}
