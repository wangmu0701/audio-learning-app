import 'word.dart';

class Sentence {
  final String id;
  final String sentenceJa;
  final String sentenceEn;
  final List<Word> words;

  Sentence({
    required this.id,
    required this.sentenceJa,
    required this.sentenceEn,
    required this.words,
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
    );
  }
}
