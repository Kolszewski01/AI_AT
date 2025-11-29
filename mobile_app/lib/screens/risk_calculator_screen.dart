import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/api_service.dart';
import '../utils/theme.dart';

class RiskCalculatorScreen extends StatefulWidget {
  const RiskCalculatorScreen({super.key});

  @override
  State<RiskCalculatorScreen> createState() => _RiskCalculatorScreenState();
}

class _RiskCalculatorScreenState extends State<RiskCalculatorScreen> {
  final ApiService _apiService = ApiService();
  final _formKey = GlobalKey<FormState>();

  final TextEditingController _accountSizeController = TextEditingController();
  final TextEditingController _entryPriceController = TextEditingController();
  final TextEditingController _stopLossController = TextEditingController();
  final TextEditingController _takeProfitController = TextEditingController();
  final TextEditingController _riskPercentController = TextEditingController(text: '1');

  String _symbol = 'BTCUSDT';
  Map<String, dynamic>? _calculationResult;
  bool _isCalculating = false;

  @override
  void initState() {
    super.initState();
    _accountSizeController.text = '10000';
    _riskPercentController.text = '1';
  }

  Future<void> _calculateRisk() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isCalculating = true);

    try {
      final result = await _apiService.calculateRisk(
        accountSize: double.parse(_accountSizeController.text),
        entryPrice: double.parse(_entryPriceController.text),
        stopLoss: double.parse(_stopLossController.text),
        riskPercent: double.parse(_riskPercentController.text),
        symbol: _symbol,
      );

      setState(() {
        _calculationResult = result;
        _isCalculating = false;
      });
    } catch (e) {
      setState(() => _isCalculating = false);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  void _autoCalculateTakeProfit(double riskRewardRatio) {
    if (_entryPriceController.text.isEmpty || _stopLossController.text.isEmpty) {
      return;
    }

    final entryPrice = double.parse(_entryPriceController.text);
    final stopLoss = double.parse(_stopLossController.text);
    final isLong = entryPrice > stopLoss;

    final stopDistance = (entryPrice - stopLoss).abs();
    final tpDistance = stopDistance * riskRewardRatio;

    final takeProfit = isLong
        ? entryPrice + tpDistance
        : entryPrice - tpDistance;

    setState(() {
      _takeProfitController.text = takeProfit.toStringAsFixed(2);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Risk Calculator'),
        actions: [
          IconButton(
            icon: const Icon(Icons.info_outline),
            onPressed: _showHelp,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _buildInfoCard(),
              const SizedBox(height: 16),
              _buildInputSection(),
              const SizedBox(height: 16),
              _buildRiskRewardButtons(),
              const SizedBox(height: 24),
              ElevatedButton(
                onPressed: _isCalculating ? null : _calculateRisk,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                ),
                child: _isCalculating
                    ? const CircularProgressIndicator()
                    : const Text('Calculate Risk', style: TextStyle(fontSize: 16)),
              ),
              if (_calculationResult != null) ...[
                const SizedBox(height: 24),
                _buildResultsSection(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoCard() {
    return Card(
      color: Theme.of(context).colorScheme.primaryContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.lightbulb, color: Theme.of(context).colorScheme.primary),
                const SizedBox(width: 8),
                const Text(
                  'Risk Management',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            const SizedBox(height: 8),
            const Text(
              'Calculate position size based on your account size and risk tolerance. '
              'Never risk more than 1-2% per trade!',
              style: TextStyle(fontSize: 14),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInputSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextFormField(
          controller: _accountSizeController,
          decoration: const InputDecoration(
            labelText: 'Account Size (\$)',
            prefixIcon: Icon(Icons.account_balance_wallet),
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
          validator: (value) {
            if (value == null || value.isEmpty) return 'Required';
            if (double.tryParse(value) == null) return 'Invalid number';
            return null;
          },
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _riskPercentController,
          decoration: const InputDecoration(
            labelText: 'Risk Per Trade (%)',
            prefixIcon: Icon(Icons.percent),
            border: OutlineInputBorder(),
            helperText: 'Recommended: 1-2%',
          ),
          keyboardType: TextInputType.number,
          validator: (value) {
            if (value == null || value.isEmpty) return 'Required';
            final percent = double.tryParse(value);
            if (percent == null) return 'Invalid number';
            if (percent > 5) return 'Too risky! Max 5%';
            return null;
          },
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _entryPriceController,
          decoration: const InputDecoration(
            labelText: 'Entry Price',
            prefixIcon: Icon(Icons.arrow_downward),
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
          validator: (value) {
            if (value == null || value.isEmpty) return 'Required';
            if (double.tryParse(value) == null) return 'Invalid number';
            return null;
          },
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _stopLossController,
          decoration: const InputDecoration(
            labelText: 'Stop Loss',
            prefixIcon: Icon(Icons.close),
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
          validator: (value) {
            if (value == null || value.isEmpty) return 'Required';
            if (double.tryParse(value) == null) return 'Invalid number';
            return null;
          },
          onChanged: (_) => _autoCalculateTakeProfit(2.0), // Auto-calculate with 1:2 R:R
        ),
        const SizedBox(height: 16),
        TextFormField(
          controller: _takeProfitController,
          decoration: const InputDecoration(
            labelText: 'Take Profit (Optional)',
            prefixIcon: Icon(Icons.check),
            border: OutlineInputBorder(),
          ),
          keyboardType: TextInputType.number,
        ),
      ],
    );
  }

  Widget _buildRiskRewardButtons() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Quick Risk:Reward Ratio',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 8),
        Wrap(
          spacing: 8,
          children: [
            ActionChip(
              label: const Text('1:1'),
              onPressed: () => _autoCalculateTakeProfit(1.0),
            ),
            ActionChip(
              label: const Text('1:2'),
              onPressed: () => _autoCalculateTakeProfit(2.0),
            ),
            ActionChip(
              label: const Text('1:3'),
              onPressed: () => _autoCalculateTakeProfit(3.0),
            ),
            ActionChip(
              label: const Text('1:4'),
              onPressed: () => _autoCalculateTakeProfit(4.0),
            ),
            ActionChip(
              label: const Text('1:5'),
              onPressed: () => _autoCalculateTakeProfit(5.0),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildResultsSection() {
    return Card(
      elevation: 4,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Calculation Results',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const Divider(height: 24),
            _buildResultRow(
              'Position Size',
              _calculationResult!['position_size']?.toStringAsFixed(4) ?? 'N/A',
              Icons.shopping_cart,
              Colors.blue,
            ),
            _buildResultRow(
              'Risk Amount',
              '\$${_calculationResult!['risk_amount']?.toStringAsFixed(2) ?? 'N/A'}',
              Icons.warning,
              AppTheme.bearishRed,
            ),
            _buildResultRow(
              'Potential Loss',
              '\$${_calculationResult!['potential_loss']?.toStringAsFixed(2) ?? 'N/A'}',
              Icons.trending_down,
              AppTheme.bearishRed,
            ),
            if (_calculationResult!['potential_profit'] != null)
              _buildResultRow(
                'Potential Profit',
                '\$${_calculationResult!['potential_profit']?.toStringAsFixed(2) ?? 'N/A'}',
                Icons.trending_up,
                AppTheme.bullishGreen,
              ),
            if (_calculationResult!['risk_reward_ratio'] != null)
              _buildResultRow(
                'Risk:Reward Ratio',
                '1:${_calculationResult!['risk_reward_ratio']?.toStringAsFixed(2) ?? 'N/A'}',
                Icons.balance,
                Colors.orange,
              ),
            const Divider(height: 24),
            _buildWarningSection(),
          ],
        ),
      ),
    );
  }

  Widget _buildResultRow(String label, String value, IconData icon, Color color) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          Icon(icon, color: color, size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: Text(
              label,
              style: const TextStyle(fontSize: 16),
            ),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWarningSection() {
    final riskPercent = double.tryParse(_riskPercentController.text) ?? 0;
    if (riskPercent > 2) {
      return Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: AppTheme.warningYellow.withOpacity(0.2),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            const Icon(Icons.warning, color: AppTheme.warningYellow),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                'Warning: Risking more than 2% per trade is dangerous!',
                style: TextStyle(
                  color: AppTheme.warningYellow.withOpacity(0.9),
                  fontWeight: FontWeight.bold,
                ),
              ),
            ),
          ],
        ),
      );
    }
    return const SizedBox.shrink();
  }

  void _showHelp() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Risk Calculator Help'),
        content: const SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'How to use:',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              SizedBox(height: 8),
              Text('1. Enter your account size'),
              Text('2. Set risk percentage (1-2% recommended)'),
              Text('3. Enter entry price and stop loss'),
              Text('4. Optionally set take profit or use quick R:R buttons'),
              Text('5. Click Calculate to see position size and risk'),
              SizedBox(height: 16),
              Text(
                'Risk Management Rules:',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
              ),
              SizedBox(height: 8),
              Text('• Never risk more than 1-2% per trade'),
              Text('• Always use stop loss'),
              Text('• Aim for 1:2 or better risk:reward ratio'),
              Text('• Calculate position size before entering'),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _accountSizeController.dispose();
    _entryPriceController.dispose();
    _stopLossController.dispose();
    _takeProfitController.dispose();
    _riskPercentController.dispose();
    super.dispose();
  }
}
