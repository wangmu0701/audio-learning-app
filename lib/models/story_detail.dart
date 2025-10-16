import 'sentence.dart';
import 'audio_timeline.dart';

class FastModeAudio {
  final String url;
  final double duration;
  final FastModeTimeline timeline;

  FastModeAudio({
    required this.url,
    required this.duration,
    required this.timeline,
  });

  factory FastModeAudio.fromJson(Map<String, dynamic> json) {
    return FastModeAudio(
      url: json['audio_url'] ?? '',
      duration: (json['duration'] ?? 0).toDouble(),
      timeline: FastModeTimeline.fromJson(json['timeline'] ?? {}),
    );
  }
}

class FastModeTimeline {
  final List<FastModeSentence> sentences;

  FastModeTimeline({required this.sentences});

  factory FastModeTimeline.fromJson(Map<String, dynamic> json) {
    final sentencesList =
        (json['sentences'] as List<dynamic>?)
            ?.map((s) => FastModeSentence.fromJson(s))
            .toList() ??
        [];
    return FastModeTimeline(sentences: sentencesList);
  }
}

class FastModeSentence {
  final int sentenceIndex;
  final TimeRange sentenceJa;
  final TimeRange sentenceEn;
  final List<WordTimeRange> words;

  FastModeSentence({
    required this.sentenceIndex,
    required this.sentenceJa,
    required this.sentenceEn,
    required this.words,
  });

  factory FastModeSentence.fromJson(Map<String, dynamic> json) {
    return FastModeSentence(
      sentenceIndex: json['sentence_index'] ?? 0,
      sentenceJa: TimeRange.fromJson(json['sentence_ja'] ?? {}),
      sentenceEn: TimeRange.fromJson(json['sentence_en'] ?? {}),
      words:
          (json['words'] as List<dynamic>?)
              ?.map((w) => WordTimeRange.fromJson(w))
              .toList() ??
          [],
    );
  }
}

class StoryDetail {
  final String storyId;
  final String title;
  final String titleJa;
  final String difficulty;
  final int grammarGroup;
  final List<String> grammarPoints;
  final int sentenceCount;
  final List<Sentence> sentences;
  final FastModeAudio? fastModeAudio; // 新增

  StoryDetail({
    required this.storyId,
    required this.title,
    required this.titleJa,
    required this.difficulty,
    required this.grammarGroup,
    required this.grammarPoints,
    required this.sentenceCount,
    required this.sentences,
    this.fastModeAudio, // 新增
  });

  factory StoryDetail.fromJson(Map<String, dynamic> json) {
    return StoryDetail(
      storyId: json['story_id'] ?? '',
      title: json['title'] ?? '',
      titleJa: json['title_ja'] ?? '',
      difficulty: json['difficulty'] ?? '',
      grammarGroup: json['grammar_group'] ?? 0,
      grammarPoints:
          (json['grammar_points'] as List<dynamic>?)
              ?.map((g) => g.toString())
              .toList() ??
          [],
      sentenceCount: json['sentence_count'] ?? 0,
      sentences:
          (json['story_breakdown'] as List<dynamic>?)
              ?.map((s) => Sentence.fromJson(s))
              .toList() ??
          [],
      fastModeAudio: json['fast_mode'] != null
          ? FastModeAudio.fromJson(json['fast_mode'])
          : null, // 新增
    );
  }

  String get formattedDuration {
    if (fastModeAudio != null) {
      final seconds = fastModeAudio!.duration.round();
      final minutes = seconds ~/ 60;
      final secs = seconds % 60;
      return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
    }
    return '00:00';
  }

  int get totalWordCount {
    return sentences.fold(0, (sum, sentence) => sum + sentence.words.length);
  }
}
