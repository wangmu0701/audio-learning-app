import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story.dart';
import '../data/fake_stories.dart';

// Provider for the complete story list
final storyListProvider = Provider<List<Story>>((ref) {
  return fakeStories;
});

// Provider for selected difficulty filter
final selectedDifficultyProvider = StateProvider<String>((ref) {
  return 'All';
});

// Provider for selected topics filter
final selectedTopicsProvider = StateProvider<Set<String>>((ref) {
  return {};
});

// Provider for filtered stories based on difficulty and topics
final filteredStoriesProvider = Provider<List<Story>>((ref) {
  final stories = ref.watch(storyListProvider);
  final difficulty = ref.watch(selectedDifficultyProvider);
  final selectedTopics = ref.watch(selectedTopicsProvider);

  var filtered = stories;

  // Filter by difficulty
  if (difficulty != 'All') {
    filtered = filtered.where((story) => story.difficulty == difficulty).toList();
  }

  // Filter by topics (if any topics are selected)
  if (selectedTopics.isNotEmpty) {
    filtered = filtered.where((story) {
      // Check if story has at least one of the selected topics
      return story.topics.any((topic) => selectedTopics.contains(topic));
    }).toList();
  }

  // Sort by date descending (newest first)
  filtered.sort((a, b) => b.date.compareTo(a.date));

  return filtered;
});