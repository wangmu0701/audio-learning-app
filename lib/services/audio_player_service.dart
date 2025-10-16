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
  int _introStep =
      0; // 0=slow/normal, 1=translation, 2=normal(complete mode only)
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

  bool get isFirstSentence {
    return _currentSentenceIndex == 0;
  }

  String get currentPhaseDescription {
    switch (_currentPhase) {
      case PlaybackPhase.intro:
        if (_playbackMode == PlaybackMode.full) {
          switch (_introStep) {
            case 0:
              return 'Full Story (Slow Japanese)';
            case 1:
              return 'Full Story (English)';
            case 2:
              return 'Full Story (Normal Japanese)';
            default:
              return 'Full Story';
          }
        } else {
          return _introStep == 0
              ? 'Full Story (Japanese)'
              : 'Full Story (English)';
        }
      case PlaybackPhase.sentenceLearning:
        return 'Sentence ${_currentSentenceIndex + 1} / ${_currentStory?.sentences.length ?? 0}';
      case PlaybackPhase.completed:
        return 'Completed';
    }
  }

  /// Initialize and load a story
  Future<void> loadStory(String storyId, PlaybackMode mode) async {
    print('Loading story: $storyId with mode: $mode');

    await _audioPlayer.stop();

    _currentStory = await _repository.loadStoryDetail(storyId);
    _playbackMode = mode;
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _introStep = 0;

    if (!_isListenerSetup) {
      _setupCompletionListener();
      _isListenerSetup = true;
    }
  }

  void _setupCompletionListener() {
    _audioPlayer.playerStateStream.listen((state) {
      if (state.processingState == ProcessingState.completed) {
        print(
          'Audio completed, current phase: $_currentPhase, intro step: $_introStep',
        );
        _onPlaybackCompleted();
      }
    });
  }

  /// Start playing from the beginning
  Future<void> startPlaying() async {
    print('Starting playback from beginning');
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _introStep = 0;

    await _playIntroPhase();
  }

  /// Play current sentence
  Future<void> _playCurrentSentence() async {
    if (currentSentence == null) {
      print('No current sentence');
      return;
    }

    final audioUrl = _playbackMode == PlaybackMode.fast
        ? currentSentence!.sentencePackedFastModeAudio?.url
        : currentSentence!.packedAudio?.url;

    if (audioUrl == null) {
      print('No audio available for current sentence');
      return;
    }

    final audioPath = _repository.getAudioAssetPath(
      _currentStory!.storyId,
      audioUrl,
    );
    print('Playing sentence ${_currentSentenceIndex + 1}: $audioPath');

    try {
      // Don't use stop() - just set the new asset directly
      // This avoids the "Operation Stopped" error
      await Future.delayed(const Duration(milliseconds: 200));
      await _audioPlayer.setAsset(audioPath);
      await _audioPlayer.play();
      print('Sentence playback started successfully');
    } catch (e) {
      print('Error playing sentence: $e');
    }
  }

  /// Play intro phase
  Future<void> _playIntroPhase() async {
    if (_currentStory == null) return;

    String audioFile;

    if (_playbackMode == PlaybackMode.full) {
      switch (_introStep) {
        case 0:
          audioFile = 'audio/full_story_slow.mp3';
          break;
        case 1:
          audioFile = 'audio/full_story_translation.mp3';
          break;
        case 2:
          audioFile = 'audio/full_story_normal.mp3';
          break;
        default:
          audioFile = 'audio/full_story_slow.mp3';
      }
    } else {
      audioFile = _introStep == 0
          ? 'audio/full_story_normal.mp3'
          : 'audio/full_story_translation.mp3';
    }

    final audioPath = _repository.getAudioAssetPath(
      _currentStory!.storyId,
      audioFile,
    );
    print('Playing intro step $_introStep: $audioPath');

    try {
      // Don't use stop() - just set the new asset directly
      await Future.delayed(const Duration(milliseconds: 200));
      await _audioPlayer.setAsset(audioPath);
      await _audioPlayer.play();
    } catch (e) {
      print('Error playing intro: $e');
    }
  }

  /// Handle playback completion
  Future<void> _onPlaybackCompleted() async {
    if (_currentPhase == PlaybackPhase.intro) {
      final maxIntroSteps = _playbackMode == PlaybackMode.full ? 3 : 2;

      if (_introStep < maxIntroSteps - 1) {
        // Continue to next intro step
        _introStep++;
        await _playIntroPhase();
      } else {
        // Intro completed, start sentence learning
        print('Intro completed, starting sentence learning');
        _currentPhase = PlaybackPhase.sentenceLearning;
        _currentSentenceIndex = 0;
        await _playCurrentSentence();
      }
    } else if (_currentPhase == PlaybackPhase.sentenceLearning) {
      if (hasNextSentence) {
        _currentSentenceIndex++;
        await _playCurrentSentence();
      } else {
        print('All sentences completed');
        _currentPhase = PlaybackPhase.completed;
      }
    }
  }

  /// Jump to intro
  Future<void> jumpToIntro() async {
    print('Jumping to intro');
    _currentPhase = PlaybackPhase.intro;
    _introStep = 0;
    await _playIntroPhase(); // 移除这里的延迟，方法内部已经有了
  }

  /// Jump to first sentence
  Future<void> jumpToFirstSentence() async {
    print('Jumping to first sentence');
    _currentPhase = PlaybackPhase.sentenceLearning;
    _currentSentenceIndex = 0;
    await _playCurrentSentence(); // 这个方法内部已经有延迟了
  }

  /// Move to next sentence
  Future<void> nextSentence() async {
    print('Manual next sentence');

    if (_currentPhase == PlaybackPhase.intro) {
      // Jump to first sentence
      await jumpToFirstSentence();
    } else if (_currentPhase == PlaybackPhase.sentenceLearning &&
        hasNextSentence) {
      _currentSentenceIndex++;
      await _playCurrentSentence(); // 这个方法内部已经有延迟了
    }
  }

  /// Move to previous sentence
  Future<void> previousSentence() async {
    print('Manual previous sentence');

    if (_currentPhase == PlaybackPhase.sentenceLearning) {
      if (isFirstSentence) {
        // Go back to intro
        await jumpToIntro();
      } else {
        _currentSentenceIndex--;
        await _playCurrentSentence(); // 这个方法内部已经有延迟了
      }
    }
  }

  Future<void> pause() async {
    await _audioPlayer.pause();
  }

  Future<void> resume() async {
    await _audioPlayer.play();
  }

  Future<void> stop() async {
    await _audioPlayer.stop();
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _introStep = 0;
  }

  void dispose() {
    _audioPlayer.dispose();
  }
}
