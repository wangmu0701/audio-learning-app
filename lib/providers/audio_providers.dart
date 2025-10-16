import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../services/audio_player_service.dart';

// Audio service provider
final audioServiceProvider = Provider<AudioPlayerService>((ref) {
  final service = AudioPlayerService();
  ref.onDispose(() {
    service.dispose();
  });
  return service;
});

// Playing state provider
final isPlayingProvider = StateProvider<bool>((ref) => false);

// Current playback position provider
final playbackPositionProvider = StateProvider<Duration>(
  (ref) => Duration.zero,
);

// Current sentence index provider
final currentSentenceIndexProvider = StateProvider<int>((ref) => 0);

// Current highlighted word index provider
final currentWordIndexProvider = StateProvider<int?>((ref) => null);
