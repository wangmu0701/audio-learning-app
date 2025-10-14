import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/services.dart';
import 'package:japanese/services/story_repository.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  test('StoryRepository should load stories from index.json', () async {
    final repository = StoryRepository();
    
    // Clear cache first
    repository.clearCache();
    
    // Load stories
    final stories = await repository.loadStories();
    
    // Verify
    expect(stories.isNotEmpty, true);
    expect(stories.first.storyId, 'N5_G0_001');
    expect(stories.first.title, "The Lost Cat's Adventure");
    expect(stories.first.difficulty, 'N5');
    expect(stories.first.durationSeconds, 1161);
    
    print('✅ Loaded ${stories.length} stories from index.json');
  });

  test('StoryRepository should load story detail', () async {
    final repository = StoryRepository();
    repository.clearCache();
    
    // Load story detail
    final storyDetail = await repository.loadStoryDetail('N5_G0_001');
    
    // Verify
    expect(storyDetail, isNotNull);
    expect(storyDetail!.storyId, 'N5_G0_001');
    expect(storyDetail.titleJa, '迷子の猫の冒険 (Maigo no Neko no Bōken)');
    expect(storyDetail.sentences.length, 10);
    expect(storyDetail.sentences.first.sentenceJa, 'ふわふわの小さな猫がいました。');
    
    print('✅ Successfully loaded story detail with ${storyDetail.sentences.length} sentences');
  });

  test('Audio asset path should be correct', () {
    final repository = StoryRepository();
    final audioPath = repository.getAudioAssetPath('N5_G0_001', 'audio/packed/s1.mp3');
    
    expect(audioPath, 'assets/stories/N5_G0_001/audio/packed/s1.mp3');
    print('✅ Audio path generated correctly: $audioPath');
  });
}