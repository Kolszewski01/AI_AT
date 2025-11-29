import 'package:flutter/material.dart';
import '../models/signal.dart';
import '../models/market_data.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../utils/theme.dart';
import 'chart_screen.dart';
import 'risk_calculator_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService _apiService = ApiService();
  final WebSocketService _wsService = WebSocketService();

  List<TradingSignal> _recentSignals = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
    _connectWebSocket();
  }

  Future<void> _loadData() async {
    setState(() => _isLoading = true);

    try {
      final signals = await _apiService.getSignals(limit: 5);
      setState(() {
        _recentSignals = signals;
        _isLoading = false;
      });
    } catch (e) {
      print('Error loading data: $e');
      setState(() => _isLoading = false);
    }
  }

  void _connectWebSocket() {
    if (!_wsService.isConnected) {
      _wsService.connect();
    }
    _wsService.subscribeToSignals();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AI Trading System'),
        actions: [
          IconButton(
            icon: const Icon(Icons.calculate),
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (context) => const RiskCalculatorScreen()),
            ),
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _loadData,
        child: _isLoading
            ? const Center(child: CircularProgressIndicator())
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  _buildWelcomeCard(),
                  const SizedBox(height: 16),
                  _buildQuickActions(),
                  const SizedBox(height: 24),
                  _buildSectionHeader('Recent Signals', () {}),
                  const SizedBox(height: 8),
                  ..._recentSignals.map((signal) => _buildSignalCard(signal)),
                ],
              ),
      ),
    );
  }

  Widget _buildWelcomeCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.waving_hand, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                const Text(
                  'Welcome back!',
                  style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Monitor markets, analyze charts, and manage risk with AI-powered insights.',
              style: TextStyle(color: Colors.grey[600]),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildQuickActions() {
    return Row(
      children: [
        Expanded(
          child: _buildActionCard(
            'Charts',
            Icons.show_chart,
            AppTheme.bullishGreen,
            () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const ChartScreen(symbol: 'BTCUSDT'),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _buildActionCard(
            'Risk Calc',
            Icons.calculate,
            Colors.orange,
            () => Navigator.push(
              context,
              MaterialPageRoute(
                builder: (context) => const RiskCalculatorScreen(),
              ),
            ),
          ),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: _buildActionCard(
            'Signals',
            Icons.notifications_active,
            Colors.blue,
            () => DefaultTabController.of(context)?.animateTo(2),
          ),
        ),
      ],
    );
  }

  Widget _buildActionCard(String title, IconData icon, Color color, VoidCallback onTap) {
    return Card(
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Icon(icon, size: 32, color: color),
              const SizedBox(height: 8),
              Text(
                title,
                style: const TextStyle(fontWeight: FontWeight.bold),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildSectionHeader(String title, VoidCallback onViewAll) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
        ),
        TextButton(
          onPressed: onViewAll,
          child: const Text('View All'),
        ),
      ],
    );
  }

  Widget _buildSignalCard(TradingSignal signal) {
    final directionColor = signal.direction == 'BUY'
        ? AppTheme.bullishGreen
        : signal.direction == 'SELL'
            ? AppTheme.bearishRed
            : AppTheme.neutralGray;

    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        leading: CircleAvatar(
          backgroundColor: directionColor.withOpacity(0.2),
          child: Icon(
            signal.direction == 'BUY'
                ? Icons.trending_up
                : signal.direction == 'SELL'
                    ? Icons.trending_down
                    : Icons.remove,
            color: directionColor,
          ),
        ),
        title: Text(signal.symbol),
        subtitle: Text(signal.description),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              signal.direction,
              style: TextStyle(
                color: directionColor,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              '${(signal.strength * 100).toInt()}%',
              style: const TextStyle(fontSize: 12),
            ),
          ],
        ),
        onTap: () => Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => ChartScreen(
              symbol: signal.symbol,
              initialTimeframe: signal.timeframe,
            ),
          ),
        ),
      ),
    );
  }
}
