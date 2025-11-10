import 'package:just_audio/just_audio.dart';
import 'package:audio_session/audio_session.dart';
import '../models/story_detail.dart';
import 'story_repository.dart';

class AudioPlayerService {
  final AudioPlayer _audioPlayer = AudioPlayer();
  final StoryRepository _repository = StoryRepository();
  bool _audioSessionConfigured = false;

  StoryDetail? _currentStory;
  FastModeAudio? _fastModeAudio;

  // Getters
  AudioPlayer get player => _audioPlayer;
  StoryDetail? get currentStory => _currentStory;
  FastModeAudio? get fastModeAudio => _fastModeAudio;

  /// Load and prepare story for playback
  Future<void> loadStory(String storyId) async {
    print('Loading story: $storyId');

    // Configure audio session for background playback (only once)
    if (!_audioSessionConfigured) {
      await _configureAudioSession();
      _audioSessionConfigured = true;
    }

    // Stop current playback
    await _audioPlayer.stop();

    // Load story data
    _currentStory = await _repository.loadStoryDetail(storyId);
    if (_currentStory == null) {
      print('Failed to load story');
      return;
    }

    _fastModeAudio = _currentStory!.fastModeAudio;
    if (_fastModeAudio == null) {
      print('No fast mode audio available');
      return;
    }

    // Set audio path
    final audioPath = _repository.getAudioAssetPath(
      storyId,
      _fastModeAudio!.url,
    );
    print('Loading audio: $audioPath');

    try {
      await _audioPlayer.setAsset(audioPath);
      print('Audio loaded successfully, duration: ${_audioPlayer.duration}');

      // Setup auto-replay when playback completes
      _audioPlayer.playerStateStream.listen((state) {
        if (state.processingState == ProcessingState.completed) {
          // Auto-replay from the beginning
          _audioPlayer.seek(Duration.zero);
          _audioPlayer.play();
        }
      });
    } catch (e) {
      print('Error loading audio: $e');
    }
  }

  /// Configure audio session for background playback and lock screen controls
  Future<void> _configureAudioSession() async {
    try {
      final session = await AudioSession.instance;
      await session.configure(
        const AudioSessionConfiguration(
          avAudioSessionCategory: AVAudioSessionCategory.playback,
          avAudioSessionCategoryOptions:
              AVAudioSessionCategoryOptions.duckOthers,
          avAudioSessionMode: AVAudioSessionMode.spokenAudio,
          avAudioSessionRouteSharingPolicy:
              AVAudioSessionRouteSharingPolicy.defaultPolicy,
          avAudioSessionSetActiveOptions: AVAudioSessionSetActiveOptions.none,
          androidAudioAttributes: AndroidAudioAttributes(
            contentType: AndroidAudioContentType.speech,
            flags: AndroidAudioFlags.none,
            usage: AndroidAudioUsage.media,
          ),
          androidAudioFocusGainType: AndroidAudioFocusGainType.gain,
          androidWillPauseWhenDucked: true,
        ),
      );

      print('Audio session configured for background playback');
    } catch (e) {
      print('Error configuring audio session: $e');
    }
  }

  /// Start playback
  Future<void> play() async {
    await _audioPlayer.play();
  }

  /// Pause playback
  Future<void> pause() async {
    await _audioPlayer.pause();
  }

  /// Seek to position
  Future<void> seek(Duration position) async {
    await _audioPlayer.seek(position);
  }

  /// Get current sentence index based on playback position
  /// Now handles intro phase and detailed learning phase
  int getCurrentSentenceIndex(Duration position) {
    if (_fastModeAudio == null) return 0;

    final seconds = position.inMilliseconds / 1000.0;
    final timeline = _fastModeAudio!.timeline;

    // 1. Check if in Japanese intro phase
    for (var item in timeline.storyPlaybackTimelineJa) {
      if (item.contains(seconds)) {
        return item.sentenceIndex;
      }
    }

    // 2. Check if in detailed learning phase
    for (int i = 0; i < timeline.sentences.length; i++) {
      final sentence = timeline.sentences[i];
      final sentenceEnd = sentence.words.isNotEmpty
          ? sentence.words.last.end
          : sentence.sentenceJa.end;

      if (seconds >= sentence.sentenceJa.start && seconds <= sentenceEnd) {
        return i;
      }
    }

    // 3. If beyond all ranges, return last sentence
    return timeline.sentences.isEmpty ? 0 : timeline.sentences.length - 1;
  }

  /// Get current word index based on playback position and sentence index
  /// Only returns word index during detailed learning phase, returns null during intro
  int? getCurrentWordIndex(Duration position, int sentenceIndex) {
    if (_fastModeAudio == null) return null;

    final seconds = position.inMilliseconds / 1000.0;
    final timeline = _fastModeAudio!.timeline;

    // Check if in intro phase (Japanese)
    for (var item in timeline.storyPlaybackTimelineJa) {
      if (item.contains(seconds)) {
        return null; // No word index during intro
      }
    }

    // Detailed learning phase - return word index
    if (sentenceIndex < 0 || sentenceIndex >= timeline.sentences.length) {
      return null;
    }

    final sentence = timeline.sentences[sentenceIndex];

    for (int i = 0; i < sentence.words.length; i++) {
      final word = sentence.words[i];
      if (seconds >= word.start && seconds <= word.end) {
        return word.wordIndex;
      }
    }

    return null;
  }

  /// Jump to next sentence
  Future<Duration?> jumpToNextSentence() async {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return null;

    final currentIndex = getCurrentSentenceIndex(_audioPlayer.position);
    final timeline = _fastModeAudio!.timeline;
    final currentSeconds = _audioPlayer.position.inMilliseconds / 1000.0;

    Duration? newPosition;

    // 1. If in Japanese intro phase, jump to next sentence's Japanese part
    for (int i = 0; i < timeline.storyPlaybackTimelineJa.length; i++) {
      if (timeline.storyPlaybackTimelineJa[i].contains(currentSeconds)) {
        if (i < timeline.storyPlaybackTimelineJa.length - 1) {
          final nextStart = timeline.storyPlaybackTimelineJa[i + 1].start;
          newPosition = Duration(milliseconds: (nextStart * 1000).toInt());
        } else {
          // Last sentence in Japanese intro, jump to detailed learning phase
          if (timeline.sentences.isNotEmpty) {
            final nextStart = timeline.sentences[0].sentenceJa.start;
            newPosition = Duration(milliseconds: (nextStart * 1000).toInt());
          }
        }
        if (newPosition != null) {
          await seek(newPosition);
        }
        return newPosition;
      }
    }

    // 2. If in detailed learning phase, jump to next sentence
    if (currentIndex < timeline.sentences.length - 1) {
      final nextStart = timeline.sentences[currentIndex + 1].sentenceJa.start;
      newPosition = Duration(milliseconds: (nextStart * 1000).toInt());
      await seek(newPosition);
    } else {
      // At the last sentence, jump back to the beginning
      newPosition = Duration.zero;
      await seek(newPosition);
    }

    return newPosition;
  }

  /// Jump to previous sentence
  Future<Duration?> jumpToPreviousSentence() async {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return null;

    final timeline = _fastModeAudio!.timeline;
    final currentSeconds = _audioPlayer.position.inMilliseconds / 1000.0;

    Duration? newPosition;

    // 1. If in Japanese intro phase
    for (int i = 0; i < timeline.storyPlaybackTimelineJa.length; i++) {
      if (timeline.storyPlaybackTimelineJa[i].contains(currentSeconds)) {
        // Check if played more than 1 second
        if (currentSeconds - timeline.storyPlaybackTimelineJa[i].start > 1.0) {
          // Jump back to current sentence start
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineJa[i].start * 1000)
                .toInt(),
          );
        } else if (i > 0) {
          // Jump to previous sentence
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineJa[i - 1].start * 1000)
                .toInt(),
          );
        } else {
          // Already first sentence, jump to beginning
          newPosition = Duration.zero;
        }
        if (newPosition != null) {
          await seek(newPosition);
        }
        return newPosition;
      }
    }

    // 2. If in detailed learning phase
    final currentIndex = getCurrentSentenceIndex(_audioPlayer.position);
    if (currentIndex >= 0 && currentIndex < timeline.sentences.length) {
      final currentSentence = timeline.sentences[currentIndex];

      if (currentSeconds - currentSentence.sentenceJa.start > 1.0) {
        // Jump back to current sentence start
        newPosition = Duration(
          milliseconds: (currentSentence.sentenceJa.start * 1000).toInt(),
        );
      } else if (currentIndex > 0) {
        // Jump to previous sentence
        newPosition = Duration(
          milliseconds:
              (timeline.sentences[currentIndex - 1].sentenceJa.start * 1000)
                  .toInt(),
        );
      } else {
        // First sentence in detailed learning, jump back to Japanese intro last sentence
        if (timeline.storyPlaybackTimelineJa.isNotEmpty) {
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineJa.last.start * 1000)
                .toInt(),
          );
        } else {
          newPosition = Duration.zero;
        }
      }
      if (newPosition != null) {
        await seek(newPosition);
      }
    }

    return newPosition;
  }

  bool isInWordExplanationPhase(Duration position) {
    if (_fastModeAudio == null) return false;

    final seconds = position.inMilliseconds / 1000.0;
    final timeline = _fastModeAudio!.timeline;

    // 1. Check if in Japanese intro phase
    for (var item in timeline.storyPlaybackTimelineJa) {
      if (item.contains(seconds)) {
        return false; // Intro phase, don't show word explanation
      }
    }

    // 2. Check if in detailed learning phase sentence playback
    for (var sentence in timeline.sentences) {
      // During Japanese sentence playback
      if (sentence.sentenceJa.contains(seconds)) {
        return false;
      }
    }

    // 3. If not in any of the above phases, might be in word explanation phase
    return true;
  }

  /// Check if at the end (can't jump to next sentence)
  bool isAtEnd(Duration position) {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return true;

    final seconds = position.inMilliseconds / 1000.0;
    final timeline = _fastModeAudio!.timeline;

    // If in detailed learning phase's last sentence, check if near the end
    if (timeline.sentences.isNotEmpty) {
      final lastSentence = timeline.sentences.last;
      final lastWordEnd = lastSentence.words.isNotEmpty
          ? lastSentence.words.last.end
          : lastSentence.sentenceJa.end;

      // If already after the last word of the last sentence, it's the end
      if (seconds >= lastWordEnd) {
        return true;
      }
    }

    return false;
  }

  /// Check if can jump to next sentence
  bool canJumpToNext(Duration position) {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return false;

    // Next button is always enabled now
    // At the last sentence, it will jump back to the beginning
    return true;
  }

  /// Stop playback
  Future<void> stop() async {
    await _audioPlayer.stop();
  }

  /// Dispose resources
  void dispose() {
    _audioPlayer.dispose();
  }
}
