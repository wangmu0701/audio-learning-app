enum PlaybackMode {
  full,  // 完整模式：包含单词讲解
  fast,  // 快速模式：仅日语+英语
}

extension PlaybackModeExtension on PlaybackMode {
  String get displayName {
    switch (this) {
      case PlaybackMode.full:
        return 'Complete Learning';
      case PlaybackMode.fast:
        return 'Quick Review';
    }
  }

  String get description {
    switch (this) {
      case PlaybackMode.full:
        return 'Full learning with word explanations';
      case PlaybackMode.fast:
        return 'Japanese + English only';
    }
  }
}