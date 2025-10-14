import 'package:flutter_test/flutter_test.dart';
import 'dart:convert';
import 'package:japanese/models/story_detail.dart';

void main() {
  test('StoryDetail model should parse JSON correctly', () {
    // 这是从你的 story.json 中摘取的简化数据
    final jsonString = '''
    {
      "story_id": "N5_G0_001",
      "title": "The Lost Cat's Adventure",
      "title_ja": "迷子の猫の冒険 (Maigo no Neko no Bōken)",
      "difficulty": "N5",
      "grammar_group": 0,
      "grammar_points": ["います(imasu)", "か(ka)"],
      "duration_seconds": 1161,
      "sentence_count": 10,
      "story_breakdown": [
        {
          "id": "s1",
          "sentence_ja": "ふわふわの小さな猫がいました。",
          "sentence_en": "There was a small, fluffy cat.",
          "words": [
            {
              "word_ja": "ふわふわ",
              "word_romaji": "fuwafuwa",
              "word_en": "fluffy",
              "explanation": "This word describes something soft...",
              "position": 0
            }
          ],
          "sentence_packed_audio": {
            "url": "audio/packed/s1.mp3",
            "duration": 94.428,
            "timeline": {
              "sentence_ja": {"start": 0.0, "end": 3.168},
              "sentence_en": {"start": 3.668, "end": 5.732},
              "words": [
                {"word_index": 0, "start": 6.732, "end": 20.28}
              ],
              "sentence_ja_repeat": {"start": 91.26, "end": 94.428}
            }
          }
        }
      ]
    }
    ''';

    final json = jsonDecode(jsonString);
    final story = StoryDetail.fromJson(json);

    // 验证顶层字段
    expect(story.storyId, 'N5_G0_001');
    expect(story.title, "The Lost Cat's Adventure");
    expect(story.titleJa, '迷子の猫の冒険 (Maigo no Neko no Bōken)');
    expect(story.difficulty, 'N5');
    expect(story.grammarGroup, 0);
    expect(story.durationSeconds, 1161);
    expect(story.sentenceCount, 10);
    expect(story.formattedDuration, '19:21');

    // 验证句子
    expect(story.sentences.length, 1);
    final sentence = story.sentences[0];
    expect(sentence.id, 's1');
    expect(sentence.sentenceJa, 'ふわふわの小さな猫がいました。');
    expect(sentence.sentenceEn, 'There was a small, fluffy cat.');

    // 验证单词
    expect(sentence.words.length, 1);
    final word = sentence.words[0];
    expect(word.wordJa, 'ふわふわ');
    expect(word.wordRomaji, 'fuwafuwa');
    expect(word.wordEn, 'fluffy');
    expect(word.position, 0);

    // 验证音频时间轴
    expect(sentence.packedAudio, isNotNull);
    final audio = sentence.packedAudio!;
    expect(audio.url, 'audio/packed/s1.mp3');
    expect(audio.duration, 94.428);
    expect(audio.timeline.sentenceJa.start, 0.0);
    expect(audio.timeline.sentenceJa.end, 3.168);
    expect(audio.timeline.words.length, 1);
    expect(audio.timeline.words[0].wordIndex, 0);

    // 验证时间轴查询功能
    expect(audio.timeline.getCurrentWordIndex(10.0), 0);
    expect(audio.timeline.getCurrentWordIndex(1.0), null);

    print('✅ All tests passed!');
  });
}