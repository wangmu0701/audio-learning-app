import 'word.dart';
import 'audio_timeline.dart';

class Sentence {
  final String id;
  final String sentenceJa;
  final String sentenceEn;
  final List<Word> words;
  final PackedAudio? packedAudio;
  final PackedAudio? sentencePackedFastModeAudio; // 添加这行

  Sentence({
    required this.id,
    required this.sentenceJa,
    required this.sentenceEn,
    required this.words,
    this.packedAudio,
    this.sentencePackedFastModeAudio, // 添加这行
  });

  factory Sentence.fromJson(Map<String, dynamic> json) {
    return Sentence(
      id: json['id'] ?? '',
      sentenceJa: json['sentence_ja'] ?? '',
      sentenceEn: json['sentence_en'] ?? '',
      words:
          (json['words'] as List<dynamic>?)
              ?.map((w) => Word.fromJson(w))
              .toList() ??
          [],
      packedAudio: json['sentence_packed_audio'] != null
          ? PackedAudio.fromJson(json['sentence_packed_audio'])
          : null,
      sentencePackedFastModeAudio:
          json['sentence_packed_fast_mode_audio'] !=
              null // 添加这部分
          ? PackedAudio.fromJson(json['sentence_packed_fast_mode_audio'])
          : null,
    );
  }
}
