import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/story_provider.dart';
import '../models/story.dart';
import '../data/fake_stories.dart';
import 'player_screen.dart';  

class LibraryScreen extends ConsumerWidget {
  const LibraryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final stories = ref.watch(filteredStoriesProvider);
    final selectedDifficulty = ref.watch(selectedDifficultyProvider);
    final selectedTopics = ref.watch(selectedTopicsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Japanese Audio Stories'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Column(
        children: [
          // Compact filter section
          Container(
            padding: const EdgeInsets.all(16.0),
            child: Column(
              children: [
                Row(
                  children: [
                    // Difficulty dropdown
                    Expanded(
                      child: _DifficultyDropdown(
                        selectedDifficulty: selectedDifficulty,
                        onChanged: (value) {
                          if (value != null) {
                            ref.read(selectedDifficultyProvider.notifier).state = value;
                          }
                        },
                      ),
                    ),
                    const SizedBox(width: 12),
                    // Topics dropdown
                    Expanded(
                      child: _TopicsDropdown(
                        selectedTopics: selectedTopics,
                        onChanged: (newTopics) {
                          ref.read(selectedTopicsProvider.notifier).state = newTopics;
                        },
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                // Results count and clear button
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      '${stories.length} stories',
                      style: TextStyle(
                        color: Colors.grey[600],
                        fontSize: 14,
                      ),
                    ),
                    if (selectedDifficulty != 'All' || selectedTopics.isNotEmpty)
                      TextButton.icon(
                        onPressed: () {
                          ref.read(selectedDifficultyProvider.notifier).state = 'All';
                          ref.read(selectedTopicsProvider.notifier).state = {};
                        },
                        icon: const Icon(Icons.clear, size: 16),
                        label: const Text('Clear'),
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(horizontal: 8),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // Story list
          Expanded(
            child: stories.isEmpty
                ? const Center(
                    child: Text('No stories found'),
                  )
                : ListView.builder(
                    itemCount: stories.length,
                    padding: const EdgeInsets.all(8.0),
                    itemBuilder: (context, index) {
                      final story = stories[index];
                      return StoryListItem(story: story);
                    },
                  ),
          ),
        ],
      ),
    );
  }
}

// Difficulty Dropdown Widget
class _DifficultyDropdown extends StatelessWidget {
  final String selectedDifficulty;
  final ValueChanged<String?> onChanged;

  const _DifficultyDropdown({
    required this.selectedDifficulty,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return DropdownButtonFormField<String>(
      value: selectedDifficulty,
      decoration: InputDecoration(
        labelText: 'Difficulty',
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      ),
      isExpanded: true,
      items: allDifficulties.map((difficulty) {
        return DropdownMenuItem(
          value: difficulty,
          child: Text(difficulty),
        );
      }).toList(),
      onChanged: onChanged,
    );
  }
}

// Topics Multi-select Dropdown Widget
class _TopicsDropdown extends StatelessWidget {
  final Set<String> selectedTopics;
  final ValueChanged<Set<String>> onChanged;

  const _TopicsDropdown({
    required this.selectedTopics,
    required this.onChanged,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: () async {
        final result = await showDialog<Set<String>>(
          context: context,
          builder: (context) => _TopicsDialog(selectedTopics: selectedTopics),
        );
        if (result != null) {
          onChanged(result);
        }
      },
      child: InputDecorator(
        decoration: InputDecoration(
          labelText: 'Topics',
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(8),
          ),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          suffixIcon: const Icon(Icons.arrow_drop_down),
        ),
        child: Text(
          selectedTopics.isEmpty
              ? 'All Topics'
              : '${selectedTopics.length} selected',
          style: const TextStyle(fontSize: 14),
          overflow: TextOverflow.ellipsis,
        ),
      ),
    );
  }
}

// Topics Selection Dialog
class _TopicsDialog extends StatefulWidget {
  final Set<String> selectedTopics;

  const _TopicsDialog({required this.selectedTopics});

  @override
  State<_TopicsDialog> createState() => _TopicsDialogState();
}

class _TopicsDialogState extends State<_TopicsDialog> {
  late Set<String> _tempSelected;

  @override
  void initState() {
    super.initState();
    _tempSelected = Set.from(widget.selectedTopics);
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('Select Topics'),
      content: SizedBox(
        width: double.maxFinite,
        child: ListView(
          shrinkWrap: true,
          children: allTopics.map((topic) {
            final isSelected = _tempSelected.contains(topic);
            return CheckboxListTile(
              title: Text(
                topic,
                style: const TextStyle(fontSize: 13),
              ),
              value: isSelected,
              onChanged: (checked) {
                setState(() {
                  if (checked == true) {
                    _tempSelected.add(topic);
                  } else {
                    _tempSelected.remove(topic);
                  }
                });
              },
              dense: true,
            );
          }).toList(),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () {
            Navigator.of(context).pop(widget.selectedTopics);
          },
          child: const Text('Cancel'),
        ),
        TextButton(
          onPressed: () {
            setState(() {
              _tempSelected.clear();
            });
          },
          child: const Text('Clear All'),
        ),
        FilledButton(
          onPressed: () {
            Navigator.of(context).pop(_tempSelected);
          },
          child: const Text('Apply'),
        ),
      ],
    );
  }
}

class StoryListItem extends StatelessWidget {
  final Story story;

  const StoryListItem({super.key, required this.story});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 4.0),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16.0),
        title: Text(
          story.title,
          style: const TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 8),
            // Topics
            Wrap(
              spacing: 4.0,
              runSpacing: 4.0,
              children: story.topics.map((topic) {
                return Chip(
                  label: Text(
                    topic,
                    style: const TextStyle(fontSize: 11),
                  ),
                  materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                  visualDensity: VisualDensity.compact,
                );
              }).toList(),
            ),
            const SizedBox(height: 8),
            // Difficulty and duration
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 8.0,
                    vertical: 4.0,
                  ),
                  decoration: BoxDecoration(
                    color: _getDifficultyColor(story.difficulty),
                    borderRadius: BorderRadius.circular(4.0),
                  ),
                  child: Text(
                    story.difficulty,
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
                  story.formattedDuration,
                  style: TextStyle(
                    color: Colors.grey[600],
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ],
        ),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (context) => PlayerScreen(story: story),
            ),
          );
        },
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