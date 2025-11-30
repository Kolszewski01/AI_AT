/// Platform-specific logger implementation for mobile/desktop (dart:io)
library;

import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

File? _logFile;
IOSink? _sink;
bool _initialized = false;

/// Get device info for error reports (mobile/desktop)
Map<String, dynamic> getDeviceInfo() {
  return {
    'platform': Platform.operatingSystem,
    'os_version': Platform.operatingSystemVersion,
    'dart_version': Platform.version.split(' ').first,
  };
}

/// Initialize file logger
Future<void> _initFileLogger() async {
  if (_initialized) return;

  try {
    final directory = await getApplicationDocumentsDirectory();
    final logDir = Directory('${directory.path}/logs');
    if (!await logDir.exists()) {
      await logDir.create(recursive: true);
    }

    _logFile = File('${logDir.path}/errors.log');
    _sink = _logFile!.openWrite(mode: FileMode.append);
    _initialized = true;
  } catch (e) {
    debugPrint('Failed to initialize file logger: $e');
  }
}

/// Write log entry to file
void writeToLogFile(
  String level,
  String module,
  String message,
  dynamic error,
  StackTrace? stackTrace,
) {
  _initFileLogger().then((_) {
    if (_sink == null) return;

    final timestamp = DateTime.now().toIso8601String();
    _sink!.writeln('$timestamp | $level | [$module] $message');
    if (error != null) {
      _sink!.writeln('  Error: $error');
    }
    if (stackTrace != null) {
      _sink!.writeln('  Stack: $stackTrace');
    }
    _sink!.flush();
  });
}

/// Dispose file logger resources
Future<void> disposeFileLogger() async {
  await _sink?.flush();
  await _sink?.close();
  _sink = null;
  _initialized = false;
}
