import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/story.dart';
import '../models/story_detail.dart';

class StoryRepository {
  // Singleton pattern
  static final StoryRepository _instance = StoryRepository._internal();
  factory StoryRepository() => _instance;
  StoryRepository._internal();

  // Cache
  List<Story>? _storiesCache;
  final Map<String, StoryDetail> _storyDetailsCache = {};

  /// Load the index.json file to get list of stories
  Future<List<Story>> loadStories() async {
    // Return cached data if available
    if (_storiesCache != null) {
      return _storiesCache!;
    }

    try {
      final String jsonString = await rootBundle.loadString(
        'assets/index.json',
      );
      final Map<String, dynamic> jsonData = json.decode(jsonString);
      final List<dynamic> storiesJson = jsonData['stories'] ?? [];

      _storiesCache = storiesJson.map((storyJson) {
        return Story(
          storyId: storyJson['id'] ?? '',
          date: '', // Not in index.json, can leave empty for now
          title: storyJson['title'] ?? '',
          difficulty: storyJson['difficulty'] ?? '',
          topics: [], // Not in index.json
          durationSeconds: storyJson['fast_mode_duration_seconds'] ?? 0,
        );
      }).toList();

      return _storiesCache!;
    } catch (e) {
      print('Error loading stories: $e');
      return [];
    }
  }

  /// Load a specific story's detail by storyId
  Future<StoryDetail?> loadStoryDetail(String storyId) async {
    // Return cached data if available
    if (_storyDetailsCache.containsKey(storyId)) {
      return _storyDetailsCache[storyId];
    }

    try {
      // Find the story folder from index
      final stories = await loadStories();
      final story = stories.firstWhere(
        (s) => s.storyId == storyId,
        orElse: () => throw Exception('Story not found: $storyId'),
      );

      // Load the story.json from the story's folder
      final String folderPath = _getStoryFolderPath(storyId);
      final String jsonString = await rootBundle.loadString(
        '$folderPath/story.json',
      );
      final Map<String, dynamic> jsonData = json.decode(jsonString);

      final storyDetail = StoryDetail.fromJson(jsonData);
      _storyDetailsCache[storyId] = storyDetail;

      return storyDetail;
    } catch (e) {
      print('Error loading story detail for $storyId: $e');
      return null;
    }
  }

  /// Get the folder path for a story based on its ID
  String _getStoryFolderPath(String storyId) {
    return 'assets/stories/$storyId';
  }

  /// Get the full asset path for an audio file
  String getAudioAssetPath(String storyId, String relativeAudioPath) {
    return 'assets/stories/$storyId/$relativeAudioPath';
  }

  /// Clear cache (useful for testing)
  void clearCache() {
    _storiesCache = null;
    _storyDetailsCache.clear();
  }
}
