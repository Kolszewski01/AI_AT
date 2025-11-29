import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/market_data.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../utils/theme.dart';
import 'chart_screen.dart';

class WatchlistScreen extends StatefulWidget {
  const WatchlistScreen({super.key});

  @override
  State<WatchlistScreen> createState() => _WatchlistScreenState();
}

class _WatchlistScreenState extends State<WatchlistScreen> {
  final ApiService _apiService = ApiService();
  final WebSocketService _wsService = WebSocketService();

  List<String> _watchlistSymbols = [];
  Map<String, MarketData> _marketDataMap = {};
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadWatchlist();
  }

  Future<void> _loadWatchlist() async {
    setState(() => _isLoading = true);

    final prefs = await SharedPreferences.getInstance();
    final symbols = prefs.getStringList('watchlist') ?? ['BTCUSDT', 'ETHUSD', 'AAPL'];

    setState(() => _watchlistSymbols = symbols);

    // Load market data for each symbol
    for (var symbol in symbols) {
      try {
        final data = await _apiService.getMarketData(symbol, '1h');
        setState(() => _marketDataMap[symbol] = data);
        _wsService.subscribe(symbol);
      } catch (e) {
        print('Error loading $symbol: $e');
      }
    }

    _subscribeToUpdates();
    setState(() => _isLoading = false);
  }

  void _subscribeToUpdates() {
    _wsService.stream.listen((data) {
      if (data['type'] == 'price_update' && _watchlistSymbols.contains(data['symbol'])) {
        _updateMarketData(data['symbol'], data);
      }
    });
  }

  void _updateMarketData(String symbol, Map<String, dynamic> data) {
    if (_marketDataMap.containsKey(symbol)) {
      final currentData = _marketDataMap[symbol]!;
      setState(() {
        _marketDataMap[symbol] = MarketData(
          symbol: symbol,
          name: currentData.name,
          currentPrice: data['price'].toDouble(),
          change: data['change']?.toDouble() ?? currentData.change,
          changePercent: data['change_percent']?.toDouble() ?? currentData.changePercent,
          volume: data['volume']?.toDouble() ?? currentData.volume,
          marketCap: currentData.marketCap,
          ohlcv: currentData.ohlcv,
        );
      });
    }
  }

  Future<void> _saveWatchlist() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setStringList('watchlist', _watchlistSymbols);
  }

  void _addSymbol() {
    final controller = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Symbol'),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'Enter symbol (e.g., BTCUSDT)',
            border: OutlineInputBorder(),
          ),
          textCapitalization: TextCapitalization.characters,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              final symbol = controller.text.trim().toUpperCase();
              if (symbol.isNotEmpty && !_watchlistSymbols.contains(symbol)) {
                setState(() => _watchlistSymbols.add(symbol));
                await _saveWatchlist();
                _loadWatchlist();
              }
              Navigator.pop(context);
            },
            child: const Text('Add'),
          ),
        ],
      ),
    );
  }

  void _removeSymbol(String symbol) {
    setState(() => _watchlistSymbols.remove(symbol));
    _saveWatchlist();
    _wsService.unsubscribe(symbol);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Watchlist'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            onPressed: _addSymbol,
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadWatchlist,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _watchlistSymbols.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: _loadWatchlist,
                  child: ListView.builder(
                    itemCount: _watchlistSymbols.length,
                    itemBuilder: (context, index) {
                      final symbol = _watchlistSymbols[index];
                      final marketData = _marketDataMap[symbol];

                      return _buildSymbolCard(symbol, marketData);
                    },
                  ),
                ),
    );
  }

  Widget _buildSymbolCard(String symbol, MarketData? data) {
    if (data == null) {
      return Card(
        margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: ListTile(
          title: Text(symbol),
          subtitle: const Text('Loading...'),
        ),
      );
    }

    final isPositive = data.changePercent >= 0;
    final changeColor = isPositive ? AppTheme.bullishGreen : AppTheme.bearishRed;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Dismissible(
        key: Key(symbol),
        direction: DismissDirection.endToStart,
        onDismissed: (_) => _removeSymbol(symbol),
        background: Container(
          alignment: Alignment.centerRight,
          padding: const EdgeInsets.only(right: 16),
          color: AppTheme.bearishRed,
          child: const Icon(Icons.delete, color: Colors.white),
        ),
        child: ListTile(
          onTap: () => Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => ChartScreen(symbol: symbol),
            ),
          ),
          title: Text(
            symbol,
            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
          ),
          subtitle: Text(data.name),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                '\$${data.currentPrice.toStringAsFixed(2)}',
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                ),
              ),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    isPositive ? Icons.arrow_upward : Icons.arrow_downward,
                    size: 14,
                    color: changeColor,
                  ),
                  Text(
                    '${data.changePercent.toStringAsFixed(2)}%',
                    style: TextStyle(
                      color: changeColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.list, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'No symbols in watchlist',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            onPressed: _addSymbol,
            icon: const Icon(Icons.add),
            label: const Text('Add Symbol'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    for (var symbol in _watchlistSymbols) {
      _wsService.unsubscribe(symbol);
    }
    super.dispose();
  }
}
