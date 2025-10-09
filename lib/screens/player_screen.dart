import 'package:flutter/material.dart';
import '../models/story.dart';

class PlayerScreen extends StatefulWidget {
  final Story story;

  const PlayerScreen({super.key, required this.story});

  @override
  State<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends State<PlayerScreen> {
  bool isPlaying = false;
  double progress = 0.0;

  // Mock current sentence data
  String currentJapanese = '新しいスマートフォンを買いました。';
  String currentRomaji = 'Atarashii sumaatofon o kaimashita.';
  String currentEnglish = 'I bought a new smartphone.';

  void _togglePlayPause() {
    setState(() {
      isPlaying = !isPlaying;
      // In real implementation, this will control audio playback
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.story.title),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Story metadata
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 12.0,
                    vertical: 6.0,
                  ),
                  decoration: BoxDecoration(
                    color: _getDifficultyColor(widget.story.difficulty),
                    borderRadius: BorderRadius.circular(6.0),
                  ),
                  child: Text(
                    widget.story.difficulty,
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Icon(Icons.access_time, size: 18, color: Colors.grey[600]),
                const SizedBox(width: 6),
                Text(
                  widget.story.formattedDuration,
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 16,
                  ),
                ),
              ],
            ),

            const Spacer(),

            // Large play/pause button
            Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Theme.of(context).colorScheme.primary,
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withOpacity(0.2),
                    blurRadius: 15,
                    offset: const Offset(0, 5),
                  ),
                ],
              ),
              child: IconButton(
                icon: Icon(
                  isPlaying ? Icons.pause : Icons.play_arrow,
                  size: 60,
                ),
                color: Colors.white,
                onPressed: _togglePlayPause,
              ),
            ),

            const Spacer(),

            // Progress bar
            Column(
              children: [
                LinearProgressIndicator(
                  value: progress,
                  minHeight: 6,
                  backgroundColor: Colors.grey[300],
                  valueColor: AlwaysStoppedAnimation<Color>(
                    Theme.of(context).colorScheme.primary,
                  ),
                ),
                const SizedBox(height: 8),
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _formatTime(progress * widget.story.durationSeconds),
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 12,
                      ),
                    ),
                    Text(
                      widget.story.formattedDuration,
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ],
            ),

            const SizedBox(height: 32),

            // Current sentence display
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20.0),
              decoration: BoxDecoration(
                color: Colors.grey[100],
                borderRadius: BorderRadius.circular(12.0),
                border: Border.all(
                  color: Colors.grey[300]!,
                  width: 1,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Current Sentence:',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.bold,
                      color: Colors.grey,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Text(
                    currentJapanese,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    currentRomaji,
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[700],
                      fontStyle: FontStyle.italic,
                      height: 1.4,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    currentEnglish,
                    style: TextStyle(
                      fontSize: 16,
                      color: Colors.grey[600],
                      height: 1.4,
                    ),
                  ),
                ],
              ),
            ),

            const SizedBox(height: 24),

            // Topics
            Wrap(
              spacing: 8.0,
              runSpacing: 8.0,
              alignment: WrapAlignment.center,
              children: widget.story.topics.map((topic) {
                return Chip(
                  label: Text(
                    topic,
                    style: const TextStyle(fontSize: 12),
                  ),
                );
              }).toList(),
            ),

            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Color _getDifficultyColor(String difficulty) {
    switch (difficulty) {
      case 'N5':
        return Colors.green;
      case 'N4':
        return Colors.lightGreen;
      case 'N3':
        return Colors.orange;
      case 'N2':
        return Colors.deepOrange;
      case 'N1':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _formatTime(double seconds) {
    final minutes = seconds ~/ 60;
    final secs = (seconds % 60).toInt();
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }
}