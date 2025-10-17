import 'dart:async'; // 添加这个 import
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_providers.dart';
import '../providers/audio_providers.dart';
import '../models/story.dart';
import 'player_screen.dart';

class LibraryScreen extends ConsumerStatefulWidget {
  // 改为 StatefulWidget
  const LibraryScreen({super.key});

  @override
  ConsumerState<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends ConsumerState<LibraryScreen> {
  StreamSubscription? _playerStateSubscription;

  @override
  void initState() {
    super.initState();
    _setupPlayerStateListener();
  }

  void _setupPlayerStateListener() {
    final audioService = ref.read(audioServiceProvider);

    // 监听播放状态并更新 provider
    _playerStateSubscription = audioService.player.playerStateStream.listen((
      state,
    ) {
      if (!mounted) return;
      ref.read(isPlayingProvider.notifier).state = state.playing;
    });
  }

  @override
  void dispose() {
    _playerStateSubscription?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
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

// StoryCard 保持不变
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
    final currentPlayingStoryId = ref.watch(currentPlayingStoryIdProvider);
    final isPlaying = ref.watch(isPlayingProvider);
    final audioService = ref.watch(audioServiceProvider);

    // 判断当前故事是否正在播放
    final isCurrentStory = currentPlayingStoryId == widget.story.storyId;
    final isCurrentStoryPlaying = isCurrentStory && isPlaying;

    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: Column(
        children: [
          // Main story info
          ListTile(
            contentPadding: const EdgeInsets.symmetric(
              horizontal: 16.0,
              vertical: 8.0,
            ),
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
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                // 播放/暂停按钮（后台控制）
                IconButton(
                  icon: Icon(
                    isCurrentStoryPlaying
                        ? Icons.pause_circle_filled
                        : Icons.play_circle_filled,
                  ),
                  iconSize: 40,
                  color: isCurrentStory ? Colors.blue : Colors.grey[700],
                  onPressed: () async {
                    if (isCurrentStory) {
                      // 如果是当前故事，切换播放/暂停
                      if (isPlaying) {
                        await audioService.pause();
                      } else {
                        await audioService.play();
                      }
                    } else {
                      // 如果不是当前故事，加载并在后台播放
                      await audioService.loadStory(widget.story.storyId);
                      ref.read(currentPlayingStoryIdProvider.notifier).state =
                          widget.story.storyId;
                      await audioService.play();
                    }
                  },
                ),

                // 打开 Player Screen 按钮
                IconButton(
                  icon: const Icon(Icons.open_in_full),
                  iconSize: 28,
                  color: Colors.grey[700],
                  onPressed: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => PlayerScreen(story: widget.story),
                      ),
                    );
                  },
                ),

                // 展开/收起按钮
                IconButton(
                  icon: Icon(
                    _isExpanded ? Icons.expand_less : Icons.expand_more,
                  ),
                  onPressed: () {
                    setState(() {
                      _isExpanded = !_isExpanded;
                    });
                  },
                ),
              ],
            ),
            onTap: () {
              // 点击卡片也打开播放界面
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => PlayerScreen(story: widget.story),
                ),
              );
            },
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
