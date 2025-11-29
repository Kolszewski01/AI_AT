import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/signal.dart';
import '../models/market_data.dart';
import '../models/alert.dart';

class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';

  // Singleton pattern
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final http.Client _client = http.Client();

  // Market Data endpoints
  Future<MarketData> getMarketData(String symbol, String timeframe) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/market-data/$symbol?timeframe=$timeframe'),
    );

    if (response.statusCode == 200) {
      return MarketData.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to load market data');
    }
  }

  Future<List<OHLCV>> getHistoricalData(
    String symbol,
    String timeframe,
    int limit,
  ) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/market-data/$symbol/history?timeframe=$timeframe&limit=$limit'),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((item) => OHLCV.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load historical data');
    }
  }

  // Technical Analysis endpoints
  Future<Map<String, dynamic>> getTechnicalAnalysis(
    String symbol,
    String timeframe,
  ) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/analysis/technical/$symbol?timeframe=$timeframe'),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to load technical analysis');
    }
  }

  Future<List<String>> detectPatterns(String symbol, String timeframe) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/analysis/patterns/$symbol?timeframe=$timeframe'),
    );

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      return List<String>.from(data['patterns'] ?? []);
    } else {
      throw Exception('Failed to detect patterns');
    }
  }

  // Signals endpoints
  Future<List<TradingSignal>> getSignals({
    String? symbol,
    String? direction,
    int limit = 50,
  }) async {
    String url = '$baseUrl/signals?limit=$limit';
    if (symbol != null) url += '&symbol=$symbol';
    if (direction != null) url += '&direction=$direction';

    final response = await _client.get(Uri.parse(url));

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((item) => TradingSignal.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load signals');
    }
  }

  Future<TradingSignal> getSignalById(String id) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/signals/$id'),
    );

    if (response.statusCode == 200) {
      return TradingSignal.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to load signal');
    }
  }

  // Alerts endpoints
  Future<List<Alert>> getAlerts() async {
    final response = await _client.get(
      Uri.parse('$baseUrl/alerts'),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((item) => Alert.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load alerts');
    }
  }

  Future<Alert> createAlert(Alert alert) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/alerts'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode(alert.toJson()),
    );

    if (response.statusCode == 201) {
      return Alert.fromJson(json.decode(response.body));
    } else {
      throw Exception('Failed to create alert');
    }
  }

  Future<void> deleteAlert(String id) async {
    final response = await _client.delete(
      Uri.parse('$baseUrl/alerts/$id'),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to delete alert');
    }
  }

  Future<void> toggleAlert(String id, bool isActive) async {
    final response = await _client.patch(
      Uri.parse('$baseUrl/alerts/$id'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'is_active': isActive}),
    );

    if (response.statusCode != 200) {
      throw Exception('Failed to toggle alert');
    }
  }

  // News & Sentiment endpoints
  Future<Map<String, dynamic>> getNewsSentiment(String symbol) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/news/sentiment/$symbol'),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to load news sentiment');
    }
  }

  Future<List<Map<String, dynamic>>> getNews(String symbol, int limit) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/news/$symbol?limit=$limit'),
    );

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.cast<Map<String, dynamic>>();
    } else {
      throw Exception('Failed to load news');
    }
  }

  // Risk Management endpoints
  Future<Map<String, dynamic>> calculateRisk({
    required double accountSize,
    required double entryPrice,
    required double stopLoss,
    required double riskPercent,
    required String symbol,
  }) async {
    final response = await _client.post(
      Uri.parse('$baseUrl/risk/calculate'),
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'account_size': accountSize,
        'entry_price': entryPrice,
        'stop_loss': stopLoss,
        'risk_percent': riskPercent,
        'symbol': symbol,
      }),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to calculate risk');
    }
  }

  // Support & Resistance endpoints
  Future<Map<String, dynamic>> getSupportResistance(
    String symbol,
    String timeframe,
  ) async {
    final response = await _client.get(
      Uri.parse('$baseUrl/analysis/support-resistance/$symbol?timeframe=$timeframe'),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body);
    } else {
      throw Exception('Failed to load support/resistance levels');
    }
  }

  void dispose() {
    _client.close();
  }
}
