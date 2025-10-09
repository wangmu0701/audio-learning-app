class Story {
  final String storyId;
  final String date;
  final String title;
  final String difficulty;
  final List<String> topics;
  final int durationSeconds;

  Story({
    required this.storyId,
    required this.date,
    required this.title,
    required this.difficulty,
    required this.topics,
    required this.durationSeconds,
  });

  // Helper method to format duration as MM:SS
  String get formattedDuration {
    final minutes = durationSeconds ~/ 60;
    final seconds = durationSeconds % 60;
    return '${minutes.toString().padLeft(2, '0')}:${seconds.toString().padLeft(2, '0')}';
  }
}