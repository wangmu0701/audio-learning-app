class TimeRange {
  final double start;
  final double end;

  TimeRange({required this.start, required this.end});

  factory TimeRange.fromJson(Map<String, dynamic> json) {
    return TimeRange(
      start: (json['start'] ?? 0).toDouble(),
      end: (json['end'] ?? 0).toDouble(),
    );
  }

  bool contains(double time) {
    return time >= start && time <= end;
  }
}

class WordTimeRange {
  final int wordIndex;
  final double start;
  final double end;

  WordTimeRange({
    required this.wordIndex,
    required this.start,
    required this.end,
  });

  factory WordTimeRange.fromJson(Map<String, dynamic> json) {
    return WordTimeRange(
      wordIndex: json['word_index'] ?? 0,
      start: (json['start'] ?? 0).toDouble(),
      end: (json['end'] ?? 0).toDouble(),
    );
  }

  bool contains(double time) {
    return time >= start && time <= end;
  }
}

class AudioTimeline {
  final TimeRange sentenceJa;
  final TimeRange sentenceEn;
  final List<WordTimeRange> words;
  final TimeRange sentenceJaRepeat;

  AudioTimeline({
    required this.sentenceJa,
    required this.sentenceEn,
    required this.words,
    required this.sentenceJaRepeat,
  });

  factory AudioTimeline.fromJson(Map<String, dynamic> json) {
    return AudioTimeline(
      sentenceJa: TimeRange.fromJson(json['sentence_ja'] ?? {}),
      sentenceEn: TimeRange.fromJson(json['sentence_en'] ?? {}),
      words: (json['words'] as List<dynamic>?)
              ?.map((w) => WordTimeRange.fromJson(w))
              .toList() ??
          [],
      sentenceJaRepeat: TimeRange.fromJson(json['sentence_ja_repeat'] ?? {}),
    );
  }

  // Helper method to get current highlighted word index based on time
  int? getCurrentWordIndex(double currentTime) {
    for (var wordTime in words) {
      if (wordTime.contains(currentTime)) {
        return wordTime.wordIndex;
      }
    }
    return null;
  }

  /// Check if current time is in Japanese sentence section
  bool isInJapaneseSentence(double currentTime) {
    return sentenceJa.contains(currentTime) || sentenceJaRepeat.contains(currentTime);
  }
  
  /// Check if current time is in English sentence section
  bool isInEnglishSentence(double currentTime) {
    return sentenceEn.contains(currentTime);
  }
  
  /// Check if current time is in word explanation section
  bool isInWordExplanation(double currentTime) {
    return getCurrentWordIndex(currentTime) != null;
  }
}

class PackedAudio {
  final String url;
  final double duration;
  final AudioTimeline timeline;

  PackedAudio({
    required this.url,
    required this.duration,
    required this.timeline,
  });

  factory PackedAudio.fromJson(Map<String, dynamic> json) {
    return PackedAudio(
      url: json['url'] ?? '',
      duration: (json['duration'] ?? 0).toDouble(),
      timeline: AudioTimeline.fromJson(json['timeline'] ?? {}),
    );
  }
}