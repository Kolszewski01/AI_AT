import 'package:flutter/material.dart';
import '../models/signal.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../utils/theme.dart';
import 'chart_screen.dart';

class SignalsScreen extends StatefulWidget {
  const SignalsScreen({super.key});

  @override
  State<SignalsScreen> createState() => _SignalsScreenState();
}

class _SignalsScreenState extends State<SignalsScreen> {
  final ApiService _apiService = ApiService();
  final WebSocketService _wsService = WebSocketService();

  List<TradingSignal> _signals = [];
  bool _isLoading = true;
  String _filterDirection = 'ALL';
  String _sortBy = 'timestamp'; // timestamp, strength, symbol

  @override
  void initState() {
    super.initState();
    _loadSignals();
    _subscribeToSignals();
  }

  Future<void> _loadSignals() async {
    setState(() => _isLoading = true);

    try {
      final signals = await _apiService.getSignals(
        direction: _filterDirection == 'ALL' ? null : _filterDirection,
        limit: 100, // Load ALL signals, not just 3!
      );

      setState(() {
        _signals = signals;
        _sortSignals();
        _isLoading = false;
      });
    } catch (e) {
      print('Error loading signals: $e');
      setState(() => _isLoading = false);
    }
  }

  void _subscribeToSignals() {
    _wsService.subscribeToSignals();
    _wsService.stream.listen((data) {
      if (data['type'] == 'signal') {
        _addNewSignal(TradingSignal.fromJson(data['signal']));
      }
    });
  }

  void _addNewSignal(TradingSignal signal) {
    setState(() {
      _signals.insert(0, signal);
      _sortSignals();
    });
  }

  void _sortSignals() {
    switch (_sortBy) {
      case 'timestamp':
        _signals.sort((a, b) => b.timestamp.compareTo(a.timestamp));
        break;
      case 'strength':
        _signals.sort((a, b) => b.strength.compareTo(a.strength));
        break;
      case 'symbol':
        _signals.sort((a, b) => a.symbol.compareTo(b.symbol));
        break;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Trading Signals'),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.sort),
            onSelected: (value) {
              setState(() {
                _sortBy = value;
                _sortSignals();
              });
            },
            itemBuilder: (context) => [
              const PopupMenuItem(value: 'timestamp', child: Text('Sort by Time')),
              const PopupMenuItem(value: 'strength', child: Text('Sort by Strength')),
              const PopupMenuItem(value: 'symbol', child: Text('Sort by Symbol')),
            ],
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadSignals,
          ),
        ],
      ),
      body: Column(
        children: [
          _buildFilterChips(),
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : _signals.isEmpty
                    ? _buildEmptyState()
                    : RefreshIndicator(
                        onRefresh: _loadSignals,
                        child: ListView.builder(
                          itemCount: _signals.length,
                          itemBuilder: (context, index) {
                            return _buildSignalCard(_signals[index]);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChips() {
    final filters = ['ALL', 'BUY', 'SELL', 'NEUTRAL'];

    return Container(
      padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: Row(
        children: filters.map((filter) {
          final isSelected = filter == _filterDirection;
          return Padding(
            padding: const EdgeInsets.only(right: 8),
            child: FilterChip(
              label: Text(filter),
              selected: isSelected,
              onSelected: (selected) {
                if (selected) {
                  setState(() => _filterDirection = filter);
                  _loadSignals();
                }
              },
              selectedColor: _getDirectionColor(filter),
            ),
          );
        }).toList(),
      ),
    );
  }

  Widget _buildSignalCard(TradingSignal signal) {
    final directionColor = _getDirectionColor(signal.direction);

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: () => _showSignalDetails(signal),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: directionColor.withOpacity(0.2),
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          signal.direction,
                          style: TextStyle(
                            color: directionColor,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        signal.symbol,
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  _buildStrengthIndicator(signal.strength),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                signal.description,
                style: TextStyle(color: Colors.grey[600]),
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Icon(Icons.schedule, size: 14, color: Colors.grey[600]),
                  const SizedBox(width: 4),
                  Text(
                    _formatTimestamp(signal.timestamp),
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                  const SizedBox(width: 16),
                  Icon(Icons.layers, size: 14, color: Colors.grey[600]),
                  const SizedBox(width: 4),
                  Text(
                    signal.timeframe,
                    style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                  ),
                ],
              ),
              if (signal.indicators.isNotEmpty) ...[
                const SizedBox(height: 8),
                Wrap(
                  spacing: 4,
                  children: signal.indicators.take(5).map((indicator) {
                    return Chip(
                      label: Text(
                        indicator,
                        style: const TextStyle(fontSize: 10),
                      ),
                      padding: const EdgeInsets.all(2),
                      materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                    );
                  }).toList(),
                ),
              ],
              if (signal.entryPrice != null ||
                  signal.stopLoss != null ||
                  signal.takeProfit != null) ...[
                const Divider(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceAround,
                  children: [
                    if (signal.entryPrice != null)
                      _buildPriceInfo('Entry', signal.entryPrice!, Colors.blue),
                    if (signal.stopLoss != null)
                      _buildPriceInfo('SL', signal.stopLoss!, AppTheme.bearishRed),
                    if (signal.takeProfit != null)
                      _buildPriceInfo('TP', signal.takeProfit!, AppTheme.bullishGreen),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildStrengthIndicator(double strength) {
    final color = strength > 0.7
        ? AppTheme.bullishGreen
        : strength > 0.4
            ? Colors.orange
            : AppTheme.bearishRed;

    return Row(
      children: [
        Text(
          '${(strength * 100).toInt()}%',
          style: TextStyle(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(width: 4),
        SizedBox(
          width: 50,
          child: LinearProgressIndicator(
            value: strength,
            backgroundColor: Colors.grey[300],
            valueColor: AlwaysStoppedAnimation<Color>(color),
          ),
        ),
      ],
    );
  }

  Widget _buildPriceInfo(String label, double price, Color color) {
    return Column(
      children: [
        Text(
          label,
          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
        ),
        Text(
          price.toStringAsFixed(2),
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
            color: color,
          ),
        ),
      ],
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.show_chart, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'No signals available',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          TextButton(
            onPressed: _loadSignals,
            child: const Text('Refresh'),
          ),
        ],
      ),
    );
  }

  Color _getDirectionColor(String direction) {
    switch (direction.toUpperCase()) {
      case 'BUY':
        return AppTheme.bullishGreen;
      case 'SELL':
        return AppTheme.bearishRed;
      default:
        return AppTheme.neutralGray;
    }
  }

  String _formatTimestamp(DateTime timestamp) {
    final now = DateTime.now();
    final difference = now.difference(timestamp);

    if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else {
      return '${difference.inDays}d ago';
    }
  }

  void _showSignalDetails(TradingSignal signal) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        minChildSize: 0.5,
        maxChildSize: 0.95,
        expand: false,
        builder: (context, scrollController) {
          return Container(
            padding: const EdgeInsets.all(16),
            child: ListView(
              controller: scrollController,
              children: [
                Text(
                  signal.symbol,
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                const SizedBox(height: 8),
                Text(
                  signal.description,
                  style: const TextStyle(fontSize: 16),
                ),
                const Divider(height: 32),
                if (signal.pattern != null) ...[
                  _buildDetailRow('Pattern', signal.pattern!),
                ],
                _buildDetailRow('Strategy', signal.strategy),
                _buildDetailRow('Timeframe', signal.timeframe),
                _buildDetailRow('Strength', '${(signal.strength * 100).toInt()}%'),
                if (signal.sentiment != null) ...[
                  _buildDetailRow(
                    'Sentiment',
                    signal.sentiment! > 0 ? 'Positive' : 'Negative',
                  ),
                ],
                const Divider(height: 32),
                ElevatedButton.icon(
                  onPressed: () {
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => ChartScreen(
                          symbol: signal.symbol,
                          initialTimeframe: signal.timeframe,
                        ),
                      ),
                    );
                  },
                  icon: const Icon(Icons.show_chart),
                  label: const Text('View Chart'),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(color: Colors.grey[600]),
          ),
          Text(
            value,
            style: const TextStyle(fontWeight: FontWeight.bold),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    super.dispose();
  }
}
