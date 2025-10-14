class Word {
  final String wordJa;
  final String wordRomaji;
  final String wordEn;
  final String explanation;
  final int position; // Position in the sentence for highlighting

  Word({
    required this.wordJa,
    required this.wordRomaji,
    required this.wordEn,
    required this.explanation,
    required this.position,
  });

  factory Word.fromJson(Map<String, dynamic> json) {
    return Word(
      wordJa: json['word_ja'] ?? '',
      wordRomaji: json['word_romaji'] ?? '',
      wordEn: json['word_en'] ?? '',
      explanation: json['explanation'] ?? '',
      position: json['position'] ?? 0,
    );
  }
}