import 'sentence.dart';
import 'playback_mode.dart';

class StoryDetail {
  final String storyId;
  final String title;
  final String titleJa;
  final String difficulty;
  final int grammarGroup;
  final List<String> grammarPoints;
  final int durationSeconds;
  final int sentenceCount;
  final List<Sentence> sentences;

  StoryDetail({
    required this.storyId,
    required this.title,
    required this.titleJa,
    required this.difficulty,
    required this.grammarGroup,
    required this.grammarPoints,
    required this.durationSeconds,
    required this.sentenceCount,
    required this.sentences,
  });

  factory StoryDetail.fromJson(Map<String, dynamic> json) {
    return StoryDetail(
      storyId: json['story_id'] ?? '',
      title: json['title'] ?? '',
      titleJa: json['title_ja'] ?? '',
      difficulty: json['difficulty'] ?? '',
      grammarGroup: json['grammar_group'] ?? 0,
      grammarPoints: (json['grammar_points'] as List<dynamic>?)
              ?.map((g) => g.toString())
              .toList() ??
          [],
      durationSeconds: json['duration_seconds'] ?? 0,
      sentenceCount: json['sentence_count'] ?? 0,
      sentences: (json['story_breakdown'] as List<dynamic>?)
              ?.map((s) => Sentence.fromJson(s))
              .toList() ??
          [],
    );
  }

  String get formattedDuration {
    final minutes = durationSeconds ~/ 60;
    final seconds = durationSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
  
  /// Calculate duration for fast mode (Japanese + English only)
  int calculateFastModeDuration() {
    double totalSeconds = 0;
    
    for (var sentence in sentences) {
      if (sentence.packedAudio != null) {
        final timeline = sentence.packedAudio!.timeline;
        // Add sentence_ja duration
        totalSeconds += (timeline.sentenceJa.end - timeline.sentenceJa.start);
        // Add sentence_en duration
        totalSeconds += (timeline.sentenceEn.end - timeline.sentenceEn.start);
        // Add 0.5 second gap between sentences
        totalSeconds += 0.5;
      }
    }
    
    return totalSeconds.round();
  }
  
  String getFormattedDuration(PlaybackMode mode) {
    final seconds = mode == PlaybackMode.fast 
        ? calculateFastModeDuration() 
        : durationSeconds;
    final minutes = seconds ~/ 60;
    final secs = seconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${secs.toString().padLeft(2, '0')}';
  }
  
  /// Get total word count
  int get totalWordCount {
    return sentences.fold(0, (sum, sentence) => sum + sentence.words.length);
  }
}