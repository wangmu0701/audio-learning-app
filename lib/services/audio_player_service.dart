import 'package:just_audio/just_audio.dart';
import '../models/sentence.dart';
import '../models/story_detail.dart';
import '../models/playback_mode.dart';
import 'story_repository.dart';

enum PlaybackPhase { intro, sentenceLearning, completed }

class AudioPlayerService {
  final AudioPlayer _audioPlayer = AudioPlayer();
  final StoryRepository _repository = StoryRepository();

  StoryDetail? _currentStory;
  PlaybackMode _playbackMode = PlaybackMode.full;
  PlaybackPhase _currentPhase = PlaybackPhase.intro;
  int _currentSentenceIndex = 0;
  bool _isPlayingIntro = true;
  bool _isListenerSetup = false;

  // Getters
  AudioPlayer get player => _audioPlayer;
  PlaybackMode get playbackMode => _playbackMode;
  PlaybackPhase get currentPhase => _currentPhase;
  int get currentSentenceIndex => _currentSentenceIndex;

  Sentence? get currentSentence {
    if (_currentStory == null ||
        _currentPhase != PlaybackPhase.sentenceLearning ||
        _currentSentenceIndex >= _currentStory!.sentences.length) {
      return null;
    }
    return _currentStory!.sentences[_currentSentenceIndex];
  }

  bool get hasNextSentence {
    if (_currentStory == null) return false;
    return _currentSentenceIndex < _currentStory!.sentences.length - 1;
  }

  bool get hasPreviousSentence {
    return _currentSentenceIndex > 0;
  }

  String get currentPhaseDescription {
    switch (_currentPhase) {
      case PlaybackPhase.intro:
        return _isPlayingIntro
            ? 'Full Story (Japanese)'
            : 'Full Story (English)';
      case PlaybackPhase.sentenceLearning:
        return 'Sentence ${_currentSentenceIndex + 1} / ${_currentStory?.sentences.length ?? 0}';
      case PlaybackPhase.completed:
        return 'Completed';
    }
  }

  /// Initialize and load a story
  Future<void> loadStory(String storyId, PlaybackMode mode) async {
    print('Loading story: $storyId with mode: $mode');

    // Reset state
    await _audioPlayer.stop();

    _currentStory = await _repository.loadStoryDetail(storyId);
    _playbackMode = mode;
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _isPlayingIntro = true;

    // Setup completion listener only once
    if (!_isListenerSetup) {
      _setupCompletionListener();
      _isListenerSetup = true;
    }
  }

  /// Setup listener for automatic playback progression
  void _setupCompletionListener() {
    _audioPlayer.playerStateStream.listen((state) {
      if (state.processingState == ProcessingState.completed) {
        print('Audio completed, current phase: $_currentPhase');
        _onPlaybackCompleted();
      }
    });
  }

  /// Start playing from the beginning
  Future<void> startPlaying() async {
    print('Starting playback from beginning');
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _isPlayingIntro = true;

    await _playIntroPhase();
  }

  /// Play intro phase (full story)
  Future<void> _playIntroPhase() async {
    if (_currentStory == null) {
      print('No story loaded');
      return;
    }

    // In fast mode, use normal speed; in full mode, use slow speed
    final audioFile = _isPlayingIntro
        ? (_playbackMode == PlaybackMode.fast
              ? 'audio/full_story_normal.mp3'
              : 'audio/full_story_slow.mp3')
        : 'audio/full_story_translation.mp3';

    final audioPath = _repository.getAudioAssetPath(
      _currentStory!.storyId,
      audioFile,
    );

    print('Playing intro: $audioPath');

    try {
      await _audioPlayer.setAsset(audioPath);
      print('Asset loaded, starting playback');
      await _audioPlayer.play();
      print('Playback started successfully');
    } catch (e) {
      print('Error playing intro: $e');
    }
  }

  /// Play current sentence based on mode
  Future<void> _playCurrentSentence() async {
    if (currentSentence == null) {
      print('No current sentence');
      return;
    }

    // Choose the appropriate audio based on mode
    final audioUrl = _playbackMode == PlaybackMode.fast
        ? currentSentence!.sentencePackedFastModeAudio?.url
        : currentSentence!.packedAudio?.url;

    if (audioUrl == null) {
      print('No audio available for current sentence in $_playbackMode mode');
      return;
    }

    final audioPath = _repository.getAudioAssetPath(
      _currentStory!.storyId,
      audioUrl,
    );

    print(
      'Playing sentence ${_currentSentenceIndex + 1} ($_playbackMode mode): $audioPath',
    );

    try {
      await _audioPlayer.setAsset(audioPath);
      await _audioPlayer.play();
      print('Sentence playback started');
    } catch (e) {
      print('Error playing sentence: $e');
    }
  }

  /// Handle playback completion
  Future<void> _onPlaybackCompleted() async {
    if (_currentPhase == PlaybackPhase.intro) {
      if (_isPlayingIntro) {
        // Finished slow/normal version, play translation
        print('Intro first part completed, playing translation');
        _isPlayingIntro = false;
        await _playIntroPhase();
      } else {
        // Finished intro, start sentence learning
        print('Intro completed, starting sentence learning');
        _currentPhase = PlaybackPhase.sentenceLearning;
        _currentSentenceIndex = 0;
        await _playCurrentSentence();
      }
    } else if (_currentPhase == PlaybackPhase.sentenceLearning) {
      // Move to next sentence
      if (hasNextSentence) {
        print('Sentence completed, moving to next');
        _currentSentenceIndex++;
        await _playCurrentSentence();
      } else {
        print('All sentences completed');
        _currentPhase = PlaybackPhase.completed;
      }
    }
  }

  /// Move to next sentence manually
  Future<void> nextSentence() async {
    print('Manual next sentence');

    if (_currentPhase != PlaybackPhase.sentenceLearning) {
      // Skip intro and go to first sentence
      _currentPhase = PlaybackPhase.sentenceLearning;
      _currentSentenceIndex = 0;
    } else if (hasNextSentence) {
      _currentSentenceIndex++;
    } else {
      return;
    }

    await _playCurrentSentence();
  }

  /// Move to previous sentence manually
  Future<void> previousSentence() async {
    print('Manual previous sentence');

    if (_currentPhase != PlaybackPhase.sentenceLearning) {
      return;
    }

    if (hasPreviousSentence) {
      _currentSentenceIndex--;
      await _playCurrentSentence();
    }
  }

  /// Pause playback
  Future<void> pause() async {
    print('Pausing playback');
    await _audioPlayer.pause();
  }

  /// Resume playback
  Future<void> resume() async {
    print('Resuming playback');
    await _audioPlayer.play();
  }

  /// Stop and reset
  Future<void> stop() async {
    print('Stopping playback');
    await _audioPlayer.stop();
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _isPlayingIntro = true;
  }

  /// Dispose resources
  void dispose() {
    print('Disposing audio service');
    _audioPlayer.dispose();
  }
}
