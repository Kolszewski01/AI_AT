import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

class WebSocketService {
  static const String wsUrl = 'ws://localhost:8000/ws';

  WebSocketChannel? _channel;
  final StreamController<Map<String, dynamic>> _controller =
      StreamController<Map<String, dynamic>>.broadcast();

  bool _isConnected = false;
  Timer? _reconnectTimer;
  List<String> _subscribedSymbols = [];

  // Singleton pattern
  static final WebSocketService _instance = WebSocketService._internal();
  factory WebSocketService() => _instance;
  WebSocketService._internal();

  Stream<Map<String, dynamic>> get stream => _controller.stream;
  bool get isConnected => _isConnected;

  void connect() {
    try {
      _channel = WebSocketChannel.connect(Uri.parse(wsUrl));
      _isConnected = true;

      _channel!.stream.listen(
        (message) {
          try {
            final data = json.decode(message);
            _controller.add(data);
          } catch (e) {
            print('Error parsing WebSocket message: $e');
          }
        },
        onError: (error) {
          print('WebSocket error: $error');
          _handleDisconnect();
        },
        onDone: () {
          print('WebSocket connection closed');
          _handleDisconnect();
        },
      );

      // Resubscribe to symbols
      for (var symbol in _subscribedSymbols) {
        subscribe(symbol);
      }
    } catch (e) {
      print('Failed to connect WebSocket: $e');
      _handleDisconnect();
    }
  }

  void _handleDisconnect() {
    _isConnected = false;
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), () {
      print('Attempting to reconnect WebSocket...');
      connect();
    });
  }

  void subscribe(String symbol) {
    if (!_subscribedSymbols.contains(symbol)) {
      _subscribedSymbols.add(symbol);
    }

    if (_isConnected && _channel != null) {
      final message = json.encode({
        'action': 'subscribe',
        'symbol': symbol,
      });
      _channel!.sink.add(message);
    }
  }

  void unsubscribe(String symbol) {
    _subscribedSymbols.remove(symbol);

    if (_isConnected && _channel != null) {
      final message = json.encode({
        'action': 'unsubscribe',
        'symbol': symbol,
      });
      _channel!.sink.add(message);
    }
  }

  void subscribeToSignals() {
    if (_isConnected && _channel != null) {
      final message = json.encode({
        'action': 'subscribe',
        'channel': 'signals',
      });
      _channel!.sink.add(message);
    }
  }

  void subscribeToAlerts() {
    if (_isConnected && _channel != null) {
      final message = json.encode({
        'action': 'subscribe',
        'channel': 'alerts',
      });
      _channel!.sink.add(message);
    }
  }

  void disconnect() {
    _reconnectTimer?.cancel();
    _channel?.sink.close();
    _isConnected = false;
  }

  void dispose() {
    disconnect();
    _controller.close();
  }
}
