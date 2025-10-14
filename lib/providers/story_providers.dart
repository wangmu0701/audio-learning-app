import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/story.dart';
import '../models/story_detail.dart';
import '../services/story_repository.dart';

// Repository provider
final storyRepositoryProvider = Provider<StoryRepository>((ref) {
  return StoryRepository();
});

// Stories list provider
final storiesProvider = FutureProvider<List<Story>>((ref) async {
  final repository = ref.watch(storyRepositoryProvider);
  return await repository.loadStories();
});

// Story detail provider (takes storyId as parameter)
final storyDetailProvider = FutureProvider.family<StoryDetail?, String>((ref, storyId) async {
  final repository = ref.watch(storyRepositoryProvider);
  return await repository.loadStoryDetail(storyId);
});