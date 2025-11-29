import 'package:flutter/material.dart';
import '../models/alert.dart';
import '../services/api_service.dart';
import '../services/websocket_service.dart';
import '../utils/theme.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  final ApiService _apiService = ApiService();
  final WebSocketService _wsService = WebSocketService();

  List<Alert> _alerts = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadAlerts();
    _subscribeToAlerts();
  }

  Future<void> _loadAlerts() async {
    setState(() => _isLoading = true);

    try {
      final alerts = await _apiService.getAlerts();
      setState(() {
        _alerts = alerts;
        _isLoading = false;
      });
    } catch (e) {
      print('Error loading alerts: $e');
      setState(() => _isLoading = false);
    }
  }

  void _subscribeToAlerts() {
    _wsService.subscribeToAlerts();
    _wsService.stream.listen((data) {
      if (data['type'] == 'alert_triggered') {
        _showAlertNotification(data);
        _loadAlerts();
      }
    });
  }

  void _showAlertNotification(Map<String, dynamic> data) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Alert triggered: ${data['message']}'),
        backgroundColor: AppTheme.warningYellow,
        duration: const Duration(seconds: 5),
        action: SnackBarAction(
          label: 'View',
          onPressed: () {},
        ),
      ),
    );
  }

  void _createAlert() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => const CreateAlertSheet(),
    ).then((created) {
      if (created == true) {
        _loadAlerts();
      }
    });
  }

  Future<void> _deleteAlert(String id) async {
    try {
      await _apiService.deleteAlert(id);
      _loadAlerts();
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Alert deleted')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  Future<void> _toggleAlert(String id, bool isActive) async {
    try {
      await _apiService.toggleAlert(id, isActive);
      _loadAlerts();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Alerts'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadAlerts,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _alerts.isEmpty
              ? _buildEmptyState()
              : RefreshIndicator(
                  onRefresh: _loadAlerts,
                  child: ListView.builder(
                    itemCount: _alerts.length,
                    itemBuilder: (context, index) {
                      return _buildAlertCard(_alerts[index]);
                    },
                  ),
                ),
      floatingActionButton: FloatingActionButton(
        onPressed: _createAlert,
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildAlertCard(Alert alert) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        leading: Icon(
          _getAlertIcon(alert.type),
          color: alert.isActive ? AppTheme.bullishGreen : Colors.grey,
        ),
        title: Text(alert.symbol),
        subtitle: Text(_getAlertDescription(alert)),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Switch(
              value: alert.isActive,
              onChanged: (value) => _toggleAlert(alert.id, value),
            ),
            IconButton(
              icon: const Icon(Icons.delete),
              color: AppTheme.bearishRed,
              onPressed: () => _deleteAlert(alert.id),
            ),
          ],
        ),
      ),
    );
  }

  IconData _getAlertIcon(String type) {
    switch (type) {
      case 'PRICE':
        return Icons.attach_money;
      case 'INDICATOR':
        return Icons.analytics;
      case 'PATTERN':
        return Icons.pattern;
      case 'NEWS':
        return Icons.article;
      default:
        return Icons.notifications;
    }
  }

  String _getAlertDescription(Alert alert) {
    switch (alert.type) {
      case 'PRICE':
        return 'Price ${alert.condition.toLowerCase()} ${alert.targetValue?.toStringAsFixed(2) ?? ''}';
      case 'INDICATOR':
        return '${alert.indicator} ${alert.condition.toLowerCase()} ${alert.targetValue?.toStringAsFixed(2) ?? ''}';
      case 'PATTERN':
        return 'Pattern: ${alert.pattern}';
      default:
        return alert.message ?? 'Custom alert';
    }
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.notifications_off, size: 64, color: Colors.grey[400]),
          const SizedBox(height: 16),
          Text(
            'No alerts set',
            style: TextStyle(fontSize: 18, color: Colors.grey[600]),
          ),
          const SizedBox(height: 8),
          ElevatedButton.icon(
            onPressed: _createAlert,
            icon: const Icon(Icons.add),
            label: const Text('Create Alert'),
          ),
        ],
      ),
    );
  }
}

class CreateAlertSheet extends StatefulWidget {
  const CreateAlertSheet({super.key});

  @override
  State<CreateAlertSheet> createState() => _CreateAlertSheetState();
}

class _CreateAlertSheetState extends State<CreateAlertSheet> {
  final _formKey = GlobalKey<FormState>();
  final ApiService _apiService = ApiService();

  final TextEditingController _symbolController = TextEditingController();
  final TextEditingController _targetValueController = TextEditingController();

  String _alertType = 'PRICE';
  String _condition = 'ABOVE';

  Future<void> _createAlert() async {
    if (!_formKey.currentState!.validate()) return;

    try {
      final alert = Alert(
        id: '',
        symbol: _symbolController.text.toUpperCase(),
        type: _alertType,
        condition: _condition,
        targetValue: double.tryParse(_targetValueController.text),
        createdAt: DateTime.now(),
      );

      await _apiService.createAlert(alert);
      Navigator.pop(context, true);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 16,
        right: 16,
        top: 16,
      ),
      child: Form(
        key: _formKey,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Create New Alert',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _symbolController,
              decoration: const InputDecoration(
                labelText: 'Symbol',
                border: OutlineInputBorder(),
              ),
              textCapitalization: TextCapitalization.characters,
              validator: (value) {
                if (value == null || value.isEmpty) return 'Required';
                return null;
              },
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _alertType,
              decoration: const InputDecoration(
                labelText: 'Alert Type',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'PRICE', child: Text('Price')),
                DropdownMenuItem(value: 'INDICATOR', child: Text('Indicator')),
                DropdownMenuItem(value: 'PATTERN', child: Text('Pattern')),
              ],
              onChanged: (value) => setState(() => _alertType = value!),
            ),
            const SizedBox(height: 16),
            DropdownButtonFormField<String>(
              value: _condition,
              decoration: const InputDecoration(
                labelText: 'Condition',
                border: OutlineInputBorder(),
              ),
              items: const [
                DropdownMenuItem(value: 'ABOVE', child: Text('Above')),
                DropdownMenuItem(value: 'BELOW', child: Text('Below')),
                DropdownMenuItem(value: 'CROSSES', child: Text('Crosses')),
              ],
              onChanged: (value) => setState(() => _condition = value!),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _targetValueController,
              decoration: const InputDecoration(
                labelText: 'Target Value',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
              validator: (value) {
                if (value == null || value.isEmpty) return 'Required';
                if (double.tryParse(value) == null) return 'Invalid number';
                return null;
              },
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: _createAlert,
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
              child: const Text('Create Alert'),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }
}
