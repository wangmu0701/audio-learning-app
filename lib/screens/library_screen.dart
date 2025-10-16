import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_providers.dart';
import '../models/story.dart';
import 'player_screen.dart';

class LibraryScreen extends ConsumerWidget {
  const LibraryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final storiesAsync = ref.watch(storiesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Japanese Audio Stories'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: storiesAsync.when(
        data: (stories) {
          if (stories.isEmpty) {
            return const Center(child: Text('No stories available'));
          }

          return ListView.builder(
            itemCount: stories.length,
            padding: const EdgeInsets.all(8.0),
            itemBuilder: (context, index) {
              final story = stories[index];
              return StoryCard(story: story);
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error loading stories: $error'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () {
                  ref.invalidate(storiesProvider);
                },
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class StoryCard extends ConsumerStatefulWidget {
  final Story story;

  const StoryCard({super.key, required this.story});

  @override
  ConsumerState<StoryCard> createState() => _StoryCardState();
}

class _StoryCardState extends ConsumerState<StoryCard> {
  bool _isExpanded = false;

  @override
  Widget build(BuildContext context) {
    final storyDetailAsync = ref.watch(
      storyDetailProvider(widget.story.storyId),
    );

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: Column(
        children: [
          // Main story info
          ListTile(
            contentPadding: const EdgeInsets.all(16.0),
            title: Text(
              widget.story.title,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            subtitle: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const SizedBox(height: 8),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8.0,
                        vertical: 4.0,
                      ),
                      decoration: BoxDecoration(
                        color: _getDifficultyColor(widget.story.difficulty),
                        borderRadius: BorderRadius.circular(4.0),
                      ),
                      child: Text(
                        widget.story.difficulty,
                        style: const TextStyle(
                          color: Colors.white,
                          fontWeight: FontWeight.bold,
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Icon(Icons.access_time, size: 16, color: Colors.grey[600]),
                    const SizedBox(width: 4),
                    Text(
                      widget.story.formattedDuration,
                      style: TextStyle(color: Colors.grey[600], fontSize: 14),
                    ),
                  ],
                ),
              ],
            ),
            trailing: IconButton(
              icon: Icon(_isExpanded ? Icons.expand_less : Icons.expand_more),
              onPressed: () {
                setState(() {
                  _isExpanded = !_isExpanded;
                });
              },
            ),
          ),

          // Expanded content
          if (_isExpanded)
            storyDetailAsync.when(
              data: (storyDetail) {
                if (storyDetail == null) return const SizedBox.shrink();

                return Padding(
                  padding: const EdgeInsets.fromLTRB(16.0, 0, 16.0, 16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Divider(),
                      const SizedBox(height: 8),

                      // Japanese title
                      Text(
                        storyDetail.titleJa,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 16),

                      // Stats
                      Row(
                        children: [
                          _buildStatChip(
                            Icons.format_list_numbered,
                            '${storyDetail.sentenceCount} sentences',
                          ),
                          const SizedBox(width: 8),
                          _buildStatChip(
                            Icons.abc,
                            '${storyDetail.totalWordCount} words',
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),

                      // Grammar points
                      const Text(
                        'Grammar Points:',
                        style: TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8.0,
                        runSpacing: 4.0,
                        children: storyDetail.grammarPoints.map((point) {
                          return Chip(
                            label: Text(
                              point,
                              style: const TextStyle(fontSize: 12),
                            ),
                            backgroundColor: Colors.blue[50],
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8.0,
                            ),
                          );
                        }).toList(),
                      ),
                      const SizedBox(height: 16),

                      // Play button (simplified - no mode selection)
                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () {
                            Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (context) =>
                                    PlayerScreen(story: widget.story),
                              ),
                            );
                          },
                          icon: const Icon(Icons.play_arrow),
                          label: Text(
                            'Start Learning (${storyDetail.formattedDuration})',
                          ),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.blue,
                            foregroundColor: Colors.white,
                            padding: const EdgeInsets.all(16.0),
                          ),
                        ),
                      ),
                    ],
                  ),
                );
              },
              loading: () => const Padding(
                padding: EdgeInsets.all(16.0),
                child: Center(child: CircularProgressIndicator()),
              ),
              error: (error, stack) => Padding(
                padding: const EdgeInsets.all(16.0),
                child: Text('Error loading details: $error'),
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildStatChip(IconData icon, String label) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12.0, vertical: 6.0),
      decoration: BoxDecoration(
        color: Colors.grey[200],
        borderRadius: BorderRadius.circular(16.0),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.grey[700]),
          const SizedBox(width: 4),
          Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[700])),
        ],
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
}
