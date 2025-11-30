/// Platform-specific logger implementation for web (no dart:io)
library;

import 'package:flutter/foundation.dart';

/// Get device info for error reports (web)
Map<String, dynamic> getDeviceInfo() {
  return {
    'platform': 'web',
    'is_web': true,
  };
}

/// Write log entry to file - NO-OP on web (no file system access)
void writeToLogFile(
  String level,
  String module,
  String message,
  dynamic error,
  StackTrace? stackTrace,
) {
  // Web doesn't have file system access
  // Errors are still logged to console and sent to backend
  debugPrint('[$level] [$module] $message');
}

/// Dispose file logger resources - NO-OP on web
Future<void> disposeFileLogger() async {
  // Nothing to dispose on web
}
