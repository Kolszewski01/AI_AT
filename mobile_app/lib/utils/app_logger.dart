/// Centralized logging for AI Trading Mobile App.
///
/// Features:
/// - Console logging with pretty formatting
/// - File logging for errors (persistent) - mobile/desktop only
/// - Remote error reporting to backend
///
/// Usage:
/// ```dart
/// import 'package:ai_trading_app/utils/app_logger.dart';
///
/// final logger = AppLogger('MyScreen');
/// logger.info('User opened screen');
/// logger.error('Failed to load data', error: e, stackTrace: s);
/// ```
library;

import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:logger/logger.dart';

// Conditional imports for platform-specific code
import 'app_logger_io.dart' if (dart.library.html) 'app_logger_web.dart' as platform;

/// App version for error reports
const String appVersion = '1.0.0';

/// Backend API URL for error reporting
const String errorReportUrl = 'http://localhost:8000/api/v1/errors/report';

/// Global logger instance
final Logger _prettyLogger = Logger(
  printer: PrettyPrinter(
    methodCount: 2,
    errorMethodCount: 8,
    lineLength: 120,
    colors: !kIsWeb, // Colors don't work in web console
    printEmojis: true,
    dateTimeFormat: DateTimeFormat.onlyTimeAndSinceStart,
  ),
  level: kDebugMode ? Level.debug : Level.info,
);

/// Remote error reporter - sends errors to backend
class _RemoteErrorReporter {
  static final _RemoteErrorReporter _instance = _RemoteErrorReporter._internal();
  factory _RemoteErrorReporter() => _instance;
  _RemoteErrorReporter._internal();

  final _errorQueue = <Map<String, dynamic>>[];
  bool _isProcessing = false;
  Timer? _processTimer;

  void reportError({
    required String module,
    required String message,
    String? errorType,
    String? stackTrace,
    String? function,
    Map<String, dynamic>? context,
    String level = 'ERROR',
  }) {
    final errorData = {
      'client_type': 'mobile',
      'client_version': appVersion,
      'error_level': level,
      'error_message': message,
      'error_type': errorType,
      'stack_trace': stackTrace,
      'module': module,
      'function': function,
      'timestamp': DateTime.now().toUtc().toIso8601String(),
      'device_info': platform.getDeviceInfo(),
      'user_context': context,
    };

    _errorQueue.add(errorData);
    _scheduleProcessing();
  }

  void _scheduleProcessing() {
    _processTimer?.cancel();
    _processTimer = Timer(const Duration(milliseconds: 500), _processQueue);
  }

  Future<void> _processQueue() async {
    if (_isProcessing || _errorQueue.isEmpty) return;
    _isProcessing = true;

    while (_errorQueue.isNotEmpty) {
      final error = _errorQueue.removeAt(0);

      try {
        await http.post(
          Uri.parse(errorReportUrl),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(error),
        ).timeout(const Duration(seconds: 5));
      } catch (e) {
        // Silently fail - don't log errors about logging
        debugPrint('Failed to report error to backend: $e');
      }
    }

    _isProcessing = false;
  }
}

/// Main application logger class
class AppLogger {
  final String module;
  static final _remoteReporter = _RemoteErrorReporter();

  AppLogger(this.module);

  /// Log debug message (only in debug mode)
  void debug(String message, [dynamic data]) {
    _prettyLogger.d('[$module] $message${data != null ? ': $data' : ''}');
  }

  /// Log info message
  void info(String message, [dynamic data]) {
    _prettyLogger.i('[$module] $message${data != null ? ': $data' : ''}');
  }

  /// Log warning message
  void warning(String message, [dynamic data]) {
    _prettyLogger.w('[$module] $message${data != null ? ': $data' : ''}');
  }

  /// Log error with optional exception and stack trace
  void error(
    String message, {
    dynamic error,
    StackTrace? stackTrace,
    String? function,
    Map<String, dynamic>? context,
  }) {
    // Log to console
    _prettyLogger.e(
      '[$module] $message',
      error: error,
      stackTrace: stackTrace,
    );

    // Write to file (mobile/desktop only)
    platform.writeToLogFile('ERROR', module, message, error, stackTrace);

    // Send to backend
    _remoteReporter.reportError(
      module: module,
      message: message,
      errorType: error?.runtimeType.toString(),
      stackTrace: stackTrace?.toString(),
      function: function,
      context: context,
      level: 'ERROR',
    );
  }

  /// Log critical error (app-breaking issues)
  void critical(
    String message, {
    dynamic error,
    StackTrace? stackTrace,
    String? function,
    Map<String, dynamic>? context,
  }) {
    // Log to console with fatal level
    _prettyLogger.f(
      '[$module] CRITICAL: $message',
      error: error,
      stackTrace: stackTrace,
    );

    // Write to file (mobile/desktop only)
    platform.writeToLogFile('CRITICAL', module, message, error, stackTrace);

    // Send to backend
    _remoteReporter.reportError(
      module: module,
      message: message,
      errorType: error?.runtimeType.toString(),
      stackTrace: stackTrace?.toString(),
      function: function,
      context: context,
      level: 'CRITICAL',
    );
  }

  /// Log API call for debugging
  void apiCall(String method, String url, {int? statusCode, String? error}) {
    if (error != null) {
      this.error(
        'API $method $url failed',
        error: error,
        context: {'status_code': statusCode},
      );
    } else {
      debug('API $method $url -> $statusCode');
    }
  }

  /// Clean up resources
  static Future<void> dispose() async {
    await platform.disposeFileLogger();
  }
}

/// Global error handler for uncaught Flutter errors
void setupGlobalErrorHandling() {
  final logger = AppLogger('GlobalErrorHandler');

  // Handle Flutter framework errors
  FlutterError.onError = (FlutterErrorDetails details) {
    logger.critical(
      'Flutter error: ${details.exceptionAsString()}',
      error: details.exception,
      stackTrace: details.stack,
      context: {'library': details.library},
    );
  };

  // Handle async errors
  PlatformDispatcher.instance.onError = (error, stack) {
    logger.critical(
      'Async error: $error',
      error: error,
      stackTrace: stack,
    );
    return true;
  };
}
