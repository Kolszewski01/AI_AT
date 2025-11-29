import 'package:flutter/material.dart';

class DrawingToolsPanel extends StatelessWidget {
  const DrawingToolsPanel({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 60,
      padding: const EdgeInsets.symmetric(horizontal: 8),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 4,
            offset: const Offset(0, -2),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _buildToolButton(
            context,
            icon: Icons.horizontal_rule,
            label: 'Line',
            onTap: () => _selectTool(context, 'line'),
          ),
          _buildToolButton(
            context,
            icon: Icons.trending_up,
            label: 'Trend',
            onTap: () => _selectTool(context, 'trendline'),
          ),
          _buildToolButton(
            context,
            icon: Icons.show_chart,
            label: 'Fibo',
            onTap: () => _selectTool(context, 'fibonacci'),
          ),
          _buildToolButton(
            context,
            icon: Icons.rectangle_outlined,
            label: 'Rectangle',
            onTap: () => _selectTool(context, 'rectangle'),
          ),
          _buildToolButton(
            context,
            icon: Icons.text_fields,
            label: 'Text',
            onTap: () => _selectTool(context, 'text'),
          ),
          _buildToolButton(
            context,
            icon: Icons.delete,
            label: 'Clear',
            onTap: () => _clearDrawings(context),
          ),
        ],
      ),
    );
  }

  Widget _buildToolButton(
    BuildContext context, {
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 24),
          const SizedBox(height: 4),
          Text(
            label,
            style: const TextStyle(fontSize: 10),
          ),
        ],
      ),
    );
  }

  void _selectTool(BuildContext context, String tool) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('Selected: $tool'),
        duration: const Duration(seconds: 1),
      ),
    );
    // TODO: Implement drawing tool selection
  }

  void _clearDrawings(BuildContext context) {
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Drawings cleared'),
        duration: Duration(seconds: 1),
      ),
    );
    // TODO: Implement clear drawings
  }
}
