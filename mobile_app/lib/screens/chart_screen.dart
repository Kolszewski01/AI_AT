import 'package:flutter/material.dart';
import 'package:candlesticks/candlesticks.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/market_data.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../widgets/drawing_tools_panel.dart';
import '../utils/theme.dart';

class ChartScreen extends StatefulWidget {
  final String symbol;
  final String? initialTimeframe;

  const ChartScreen({
    super.key,
    required this.symbol,
    this.initialTimeframe,
  });

  @override
  State<ChartScreen> createState() => _ChartScreenState();
}

class _ChartScreenState extends State<ChartScreen> {
  final ApiService _apiService = ApiService();
  final WebSocketService _wsService = WebSocketService();

  List<Candle> _candles = [];
  String _selectedTimeframe = '1h';
  bool _isLoading = true;
  bool _showVolume = true;
  bool _showEMA = true;
  bool _showSMA = true;
  bool _showRSI = false;
  bool _showMACD = false;
  bool _drawingMode = false;

  Map<String, dynamic>? _indicators;
  Map<String, dynamic>? _supportResistance;

  @override
  void initState() {
    super.initState();
    _selectedTimeframe = widget.initialTimeframe ?? '1h';
    _loadChartData();
    _loadIndicators();
    _loadSupportResistance();
    _subscribeToUpdates();
  }

  Future<void> _loadChartData() async {
    setState(() => _isLoading = true);

    try {
      final data = await _apiService.getHistoricalData(
        widget.symbol,
        _selectedTimeframe,
        200,
      );

      setState(() {
        _candles = data.map((ohlcv) {
          return Candle(
            date: ohlcv.timestamp,
            high: ohlcv.high,
            low: ohlcv.low,
            open: ohlcv.open,
            close: ohlcv.close,
            volume: ohlcv.volume,
          );
        }).toList();
        _isLoading = false;
      });
    } catch (e) {
      print('Error loading chart data: $e');
      setState(() => _isLoading = false);
    }
  }

  Future<void> _loadIndicators() async {
    try {
      final indicators = await _apiService.getTechnicalAnalysis(
        widget.symbol,
        _selectedTimeframe,
      );
      setState(() => _indicators = indicators);
    } catch (e) {
      print('Error loading indicators: $e');
    }
  }

  Future<void> _loadSupportResistance() async {
    try {
      final sr = await _apiService.getSupportResistance(
        widget.symbol,
        _selectedTimeframe,
      );
      setState(() => _supportResistance = sr);
    } catch (e) {
      print('Error loading S/R levels: $e');
    }
  }

  void _subscribeToUpdates() {
    _wsService.subscribe(widget.symbol);
    _wsService.stream.listen((data) {
      if (data['symbol'] == widget.symbol && data['type'] == 'candle') {
        _updateCandle(data);
      }
    });
  }

  void _updateCandle(Map<String, dynamic> data) {
    if (_candles.isEmpty) return;

    final newCandle = Candle(
      date: DateTime.parse(data['timestamp']),
      high: data['high'].toDouble(),
      low: data['low'].toDouble(),
      open: data['open'].toDouble(),
      close: data['close'].toDouble(),
      volume: data['volume'].toDouble(),
    );

    setState(() {
      if (_candles.last.date.isAtSameMomentAs(newCandle.date)) {
        _candles.last = newCandle;
      } else {
        _candles.add(newCandle);
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.symbol),
        actions: [
          IconButton(
            icon: Icon(_drawingMode ? Icons.check : Icons.draw),
            onPressed: () => setState(() => _drawingMode = !_drawingMode),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              _loadChartData();
              _loadIndicators();
              _loadSupportResistance();
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings),
            onPressed: _showIndicatorSettings,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : Column(
              children: [
                _buildTimeframeSelector(),
                Expanded(
                  child: _candles.isEmpty
                      ? const Center(child: Text('No data available'))
                      : Candlesticks(
                          candles: _candles,
                          actions: [
                            ToolBarAction(
                              onPressed: () => setState(() => _showVolume = !_showVolume),
                              child: Icon(
                                Icons.bar_chart,
                                color: _showVolume ? AppTheme.bullishGreen : Colors.grey,
                              ),
                            ),
                            ToolBarAction(
                              onPressed: () => setState(() => _showEMA = !_showEMA),
                              child: Text(
                                'EMA',
                                style: TextStyle(
                                  color: _showEMA ? AppTheme.bullishGreen : Colors.grey,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            ToolBarAction(
                              onPressed: () => setState(() => _showSMA = !_showSMA),
                              child: Text(
                                'SMA',
                                style: TextStyle(
                                  color: _showSMA ? Colors.blue : Colors.grey,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            ToolBarAction(
                              onPressed: () => setState(() => _showRSI = !_showRSI),
                              child: Text(
                                'RSI',
                                style: TextStyle(
                                  color: _showRSI ? Colors.purple : Colors.grey,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            ToolBarAction(
                              onPressed: () => setState(() => _showMACD = !_showMACD),
                              child: Text(
                                'MACD',
                                style: TextStyle(
                                  color: _showMACD ? Colors.orange : Colors.grey,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ],
                        ),
                ),
                if (_supportResistance != null) _buildSupportResistancePanel(),
                if (_indicators != null) _buildIndicatorsPanel(),
                if (_drawingMode) const DrawingToolsPanel(),
              ],
            ),
    );
  }

  Widget _buildTimeframeSelector() {
    final timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w'];

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: timeframes.map((tf) {
            final isSelected = tf == _selectedTimeframe;
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 4),
              child: ChoiceChip(
                label: Text(tf),
                selected: isSelected,
                onSelected: (selected) {
                  if (selected) {
                    setState(() => _selectedTimeframe = tf);
                    _loadChartData();
                    _loadIndicators();
                  }
                },
              ),
            );
          }).toList(),
        ),
      ),
    );
  }

  Widget _buildSupportResistancePanel() {
    final supports = _supportResistance!['support'] as List? ?? [];
    final resistances = _supportResistance!['resistance'] as List? ?? [];

    return Container(
      padding: const EdgeInsets.all(8),
      color: Theme.of(context).cardColor,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Support & Resistance', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Support:', style: TextStyle(color: AppTheme.bullishGreen)),
                    ...supports.take(3).map((s) => Text(
                          s.toStringAsFixed(2),
                          style: const TextStyle(fontSize: 12),
                        )),
                  ],
                ),
              ),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Resistance:', style: TextStyle(color: AppTheme.bearishRed)),
                    ...resistances.take(3).map((r) => Text(
                          r.toStringAsFixed(2),
                          style: const TextStyle(fontSize: 12),
                        )),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildIndicatorsPanel() {
    return Container(
      padding: const EdgeInsets.all(8),
      color: Theme.of(context).cardColor,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            if (_indicators!['rsi'] != null)
              _buildIndicatorChip('RSI', _indicators!['rsi'].toStringAsFixed(2)),
            if (_indicators!['macd'] != null)
              _buildIndicatorChip('MACD', _indicators!['macd'].toStringAsFixed(4)),
            if (_indicators!['adx'] != null)
              _buildIndicatorChip('ADX', _indicators!['adx'].toStringAsFixed(2)),
            if (_indicators!['stochastic'] != null)
              _buildIndicatorChip('Stoch', _indicators!['stochastic'].toStringAsFixed(2)),
          ],
        ),
      ),
    );
  }

  Widget _buildIndicatorChip(String name, String value) {
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: Chip(
        label: Text('$name: $value'),
        backgroundColor: Theme.of(context).colorScheme.primaryContainer,
      ),
    );
  }

  void _showIndicatorSettings() {
    showModalBottomSheet(
      context: context,
      builder: (context) => Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('Indicator Settings', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 16),
            SwitchListTile(
              title: const Text('Volume'),
              value: _showVolume,
              onChanged: (value) => setState(() => _showVolume = value),
            ),
            SwitchListTile(
              title: const Text('EMA'),
              value: _showEMA,
              onChanged: (value) => setState(() => _showEMA = value),
            ),
            SwitchListTile(
              title: const Text('SMA'),
              value: _showSMA,
              onChanged: (value) => setState(() => _showSMA = value),
            ),
            SwitchListTile(
              title: const Text('RSI'),
              value: _showRSI,
              onChanged: (value) => setState(() => _showRSI = value),
            ),
            SwitchListTile(
              title: const Text('MACD'),
              value: _showMACD,
              onChanged: (value) => setState(() => _showMACD = value),
            ),
          ],
        ),
      ),
    );
  }

  @override
  void dispose() {
    _wsService.unsubscribe(widget.symbol);
    super.dispose();
  }
}
