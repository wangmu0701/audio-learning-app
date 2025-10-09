import '../models/story.dart';

final List<Story> fakeStories = [
  Story(
    storyId: 'tech_story_001',
    date: '2025-10-07',
    title: '新しいスマートフォン',
    difficulty: 'N5',
    topics: ['科技 Technology', '日常生活 Daily Life'],
    durationSeconds: 125,
  ),
  Story(
    storyId: 'food_story_001',
    date: '2025-10-06',
    title: 'ラーメン屋で',
    difficulty: 'N4',
    topics: ['食べ物 Food', '日常生活 Daily Life'],
    durationSeconds: 150,
  ),
  Story(
    storyId: 'travel_story_001',
    date: '2025-10-05',
    title: '京都旅行',
    difficulty: 'N3',
    topics: ['旅行 Travel', '文化 Culture'],
    durationSeconds: 180,
  ),
  Story(
    storyId: 'business_story_001',
    date: '2025-10-04',
    title: '会議の準備',
    difficulty: 'N2',
    topics: ['ビジネス Business', '職場 Workplace'],
    durationSeconds: 210,
  ),
  Story(
    storyId: 'news_story_001',
    date: '2025-10-03',
    title: '環境問題について',
    difficulty: 'N1',
    topics: ['ニュース News', '社会 Society'],
    durationSeconds: 270,
  ),
  Story(
    storyId: 'daily_story_001',
    date: '2025-10-02',
    title: '朝のルーティン',
    difficulty: 'N5',
    topics: ['日常生活 Daily Life'],
    durationSeconds: 90,
  ),
  Story(
    storyId: 'hobby_story_001',
    date: '2025-10-01',
    title: '週末の趣味',
    difficulty: 'N4',
    topics: ['趣味 Hobbies', '日常生活 Daily Life'],
    durationSeconds: 140,
  ),
  Story(
    storyId: 'shopping_story_001',
    date: '2025-09-30',
    title: 'スーパーで買い物',
    difficulty: 'N5',
    topics: ['買い物 Shopping', '日常生活 Daily Life'],
    durationSeconds: 100,
  ),
  Story(
    storyId: 'tech_story_002',
    date: '2025-09-29',
    title: 'AIの未来',
    difficulty: 'N2',
    topics: ['科技 Technology', 'テクノロジー Tech'],
    durationSeconds: 220,
  ),
  Story(
    storyId: 'culture_story_001',
    date: '2025-09-28',
    title: '日本の祭り',
    difficulty: 'N3',
    topics: ['文化 Culture', '伝統 Tradition'],
    durationSeconds: 195,
  ),
];

// Get all unique topics for filtering
final List<String> allTopics = [
  '科技 Technology',
  '日常生活 Daily Life',
  '食べ物 Food',
  '旅行 Travel',
  '文化 Culture',
  'ビジネス Business',
  '職場 Workplace',
  'ニュース News',
  '社会 Society',
  '趣味 Hobbies',
  '買い物 Shopping',
  'テクノロジー Tech',
  '伝統 Tradition',
];

// All difficulty levels
final List<String> allDifficulties = ['All', 'N5', 'N4', 'N3', 'N2', 'N1'];