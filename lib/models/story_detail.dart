import 'sentence.dart';
import 'audio_timeline.dart';

class StoryPlaybackTimeline {
  final int sentenceIndex;
  final double start;
  final double end;

  StoryPlaybackTimeline({
    required this.sentenceIndex,
    required this.start,
    required this.end,
  });

  factory StoryPlaybackTimeline.fromJson(Map<String, dynamic> json) {
    return StoryPlaybackTimeline(
      sentenceIndex: json['sentence_index'] ?? 0,
      start: (json['start'] ?? 0).toDouble(),
      end: (json['end'] ?? 0).toDouble(),
    );
  }

  bool contains(double time) {
    return time >= start && time <= end;
  }
}

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
  final List<StoryPlaybackTimeline> storyPlaybackTimelineJa;
  final List<StoryPlaybackTimeline> storyPlaybackTimelineEn;
  final List<FastModeSentence> sentences;

  FastModeTimeline({
    required this.storyPlaybackTimelineJa,
    required this.storyPlaybackTimelineEn,
    required this.sentences,
  });

  factory FastModeTimeline.fromJson(Map<String, dynamic> json) {
    final jaList =
        (json['story_playback_timeline_ja'] as List<dynamic>?)
            ?.map((s) => StoryPlaybackTimeline.fromJson(s))
            .toList() ??
        [];

    final enList =
        (json['story_playback_timeline_en'] as List<dynamic>?)
            ?.map((s) => StoryPlaybackTimeline.fromJson(s))
            .toList() ??
        [];

    final sentencesList =
        (json['sentences'] as List<dynamic>?)
            ?.map((s) => FastModeSentence.fromJson(s))
            .toList() ??
        [];

    return FastModeTimeline(
      storyPlaybackTimelineJa: jaList,
      storyPlaybackTimelineEn: enList,
      sentences: sentencesList,
    );
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
  final FastModeAudio? fastModeAudio;

  StoryDetail({
    required this.storyId,
    required this.title,
    required this.titleJa,
    required this.difficulty,
    required this.grammarGroup,
    required this.grammarPoints,
    required this.sentenceCount,
    required this.sentences,
    this.fastModeAudio,
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
          : null,
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
