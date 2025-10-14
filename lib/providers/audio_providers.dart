import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../services/audio_player_service.dart';
import '../models/sentence.dart';

// Audio service provider
final audioServiceProvider = Provider<AudioPlayerService>((ref) {
  final service = AudioPlayerService();
  ref.onDispose(() {
    service.dispose();
  });
  return service;
});

// Current sentence provider
final currentSentenceProvider = StateProvider<Sentence?>((ref) => null);

// Current sentence index provider
final currentSentenceIndexProvider = StateProvider<int>((ref) => 0);

// Playing state provider
final isPlayingProvider = StateProvider<bool>((ref) => false);

// Current playback position provider
final playbackPositionProvider = StateProvider<Duration>((ref) => Duration.zero);

// Current highlighted word index provider (based on timeline)
final highlightedWordIndexProvider = StateProvider<int?>((ref) => null);