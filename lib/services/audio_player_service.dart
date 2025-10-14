import 'package:just_audio/just_audio.dart';
import '../models/sentence.dart';
import '../models/story_detail.dart';
import '../models/playback_mode.dart';
import 'story_repository.dart';

enum PlaybackPhase {
  intro,           // 播放 full_story_slow + full_story_translation
  sentenceLearning, // 逐句学习
  completed,       // 全部完成
}

class AudioPlayerService {
  final AudioPlayer _audioPlayer = AudioPlayer();
  final StoryRepository _repository = StoryRepository();
  
  StoryDetail? _currentStory;
  PlaybackMode _playbackMode = PlaybackMode.full;
  PlaybackPhase _currentPhase = PlaybackPhase.intro;
  int _currentSentenceIndex = 0;
  bool _isPlayingIntro = true; // true = slow, false = translation
  
  // Getters
  AudioPlayer get player => _audioPlayer;
  PlaybackMode get playbackMode => _playbackMode;
  PlaybackPhase get currentPhase => _currentPhase;
  int get currentSentenceIndex => _currentSentenceIndex;
  
  Sentence? get currentSentence {
    if (_currentStory == null || _currentSentenceIndex >= _currentStory!.sentences.length) {
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
        return _isPlayingIntro ? 'Full Story (Japanese)' : 'Full Story (English)';
      case PlaybackPhase.sentenceLearning:
        return 'Sentence ${_currentSentenceIndex + 1} / ${_currentStory?.sentences.length ?? 0}';
      case PlaybackPhase.completed:
        return 'Completed';
    }
  }
  
  /// Initialize and load a story
  Future<void> loadStory(String storyId, PlaybackMode mode) async {
    _currentStory = await _repository.loadStoryDetail(storyId);
    _playbackMode = mode;
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _isPlayingIntro = true;
  }
  
  /// Start playing from the beginning
  Future<void> startPlaying() async {
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _isPlayingIntro = true;
    
    await _playIntroPhase();
    
    // Listen for completion
    _setupCompletionListener();
  }
  
  /// Play intro phase (full story slow + translation)
  Future<void> _playIntroPhase() async {
    if (_currentStory == null) return;
    
    final audioFile = _isPlayingIntro ? 'audio/full_story_slow.mp3' : 'audio/full_story_translation.mp3';
    final audioPath = _repository.getAudioAssetPath(_currentStory!.storyId, audioFile);
    
    try {
      await _audioPlayer.setAsset(audioPath);
      await _audioPlayer.play();
    } catch (e) {
      print('Error playing intro: $e');
    }
  }
  
  /// Play current sentence based on mode
  Future<void> _playCurrentSentence() async {
    if (currentSentence == null) return;
    
    if (_playbackMode == PlaybackMode.full) {
      // Full mode: play packed audio with word explanations
      await _playPackedAudio();
    } else {
      // Fast mode: play only Japanese + English
      await _playFastModeAudio();
    }
  }
  
  /// Play packed audio (full learning cycle)
  Future<void> _playPackedAudio() async {
    if (currentSentence?.packedAudio == null) {
      print('No packed audio available');
      return;
    }
    
    final audioPath = _repository.getAudioAssetPath(
      _currentStory!.storyId,
      currentSentence!.packedAudio!.url,
    );
    
    try {
      await _audioPlayer.setAsset(audioPath);
      await _audioPlayer.play();
    } catch (e) {
      print('Error playing packed audio: $e');
    }
  }
  
  /// Play fast mode audio (Japanese + English only)
  Future<void> _playFastModeAudio() async {
    // In fast mode, we play sentence_ja_audio + sentence_en_audio
    // For simplicity, we can use the packed audio but it will include word explanations
    // TODO: In production, you might want to generate separate fast-mode audio files
    
    // For now, we'll use packed audio - the timeline will help us skip word parts
    await _playPackedAudio();
  }
  
  /// Setup listener for automatic playback progression
  void _setupCompletionListener() {
    _audioPlayer.playerStateStream.listen((state) {
      if (state.processingState == ProcessingState.completed) {
        _onPlaybackCompleted();
      }
    });
  }
  
  /// Handle playback completion
  void _onPlaybackCompleted() {
    if (_currentPhase == PlaybackPhase.intro) {
      if (_isPlayingIntro) {
        // Finished slow version, play translation
        _isPlayingIntro = false;
        _playIntroPhase();
      } else {
        // Finished intro, start sentence learning
        _currentPhase = PlaybackPhase.sentenceLearning;
        _currentSentenceIndex = 0;
        _playCurrentSentence();
      }
    } else if (_currentPhase == PlaybackPhase.sentenceLearning) {
      // Move to next sentence
      if (hasNextSentence) {
        _currentSentenceIndex++;
        _playCurrentSentence();
      } else {
        _currentPhase = PlaybackPhase.completed;
      }
    }
  }
  
  /// Move to next sentence manually
  Future<void> nextSentence() async {
    if (_currentPhase != PlaybackPhase.sentenceLearning) {
      // Skip intro and go directly to sentence learning
      _currentPhase = PlaybackPhase.sentenceLearning;
      _currentSentenceIndex = 0;
    } else if (hasNextSentence) {
      _currentSentenceIndex++;
    } else {
      return; // Already at last sentence
    }
    
    await _playCurrentSentence();
  }
  
  /// Move to previous sentence manually
  Future<void> previousSentence() async {
    if (_currentPhase != PlaybackPhase.sentenceLearning) {
      return; // Can't go back during intro
    }
    
    if (hasPreviousSentence) {
      _currentSentenceIndex--;
      await _playCurrentSentence();
    }
  }
  
  /// Pause playback
  Future<void> pause() async {
    await _audioPlayer.pause();
  }
  
  /// Resume playback
  Future<void> resume() async {
    await _audioPlayer.play();
  }
  
  /// Stop and reset
  Future<void> stop() async {
    await _audioPlayer.stop();
    _currentPhase = PlaybackPhase.intro;
    _currentSentenceIndex = 0;
    _isPlayingIntro = true;
  }
  
  /// Dispose resources
  void dispose() {
    _audioPlayer.dispose();
  }
}