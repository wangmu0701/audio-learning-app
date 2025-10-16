import 'package:just_audio/just_audio.dart';
import '../models/story_detail.dart';
import 'story_repository.dart';

class AudioPlayerService {
  final AudioPlayer _audioPlayer = AudioPlayer();
  final StoryRepository _repository = StoryRepository();

  StoryDetail? _currentStory;
  FastModeAudio? _fastModeAudio;

  // Getters
  AudioPlayer get player => _audioPlayer;
  StoryDetail? get currentStory => _currentStory;
  FastModeAudio? get fastModeAudio => _fastModeAudio;

  /// 加载并准备播放故事
  Future<void> loadStory(String storyId) async {
    print('Loading story: $storyId');

    // 停止当前播放
    await _audioPlayer.stop();

    // 加载故事数据
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

    // 设置音频路径
    final audioPath = _repository.getAudioAssetPath(
      storyId,
      _fastModeAudio!.url,
    );
    print('Loading audio: $audioPath');

    try {
      await _audioPlayer.setAsset(audioPath);
      print('Audio loaded successfully, duration: ${_audioPlayer.duration}');
    } catch (e) {
      print('Error loading audio: $e');
    }
  }

  /// 开始播放
  Future<void> play() async {
    await _audioPlayer.play();
  }

  /// 暂停播放
  Future<void> pause() async {
    await _audioPlayer.pause();
  }

  /// 跳转到指定位置
  Future<void> seek(Duration position) async {
    await _audioPlayer.seek(position);
  }

  /// 根据播放位置获取当前句子索引
  /// 返回 -1 表示还在 intro 阶段
  int getCurrentSentenceIndex(Duration position) {
    if (_fastModeAudio == null) return 0;

    final seconds = position.inMilliseconds / 1000.0;
    final sentences = _fastModeAudio!.timeline.sentences;

    // 如果还没开始第一句，返回 -1 表示在 intro 阶段
    if (sentences.isNotEmpty && seconds < sentences[0].sentenceJa.start) {
      return -1;
    }

    for (int i = 0; i < sentences.length; i++) {
      final sentence = sentences[i];
      final sentenceEnd = sentence.words.isNotEmpty
          ? sentence.words.last.end
          : sentence.sentenceEn.end;

      if (seconds >= sentence.sentenceJa.start && seconds <= sentenceEnd) {
        return i;
      }
    }

    // 如果超出所有句子的范围，返回最后一句
    return sentences.isEmpty ? 0 : sentences.length - 1;
  }

  /// 根据播放位置和句子索引获取当前单词索引
  int? getCurrentWordIndex(Duration position, int sentenceIndex) {
    if (_fastModeAudio == null) return null;

    final sentences = _fastModeAudio!.timeline.sentences;
    if (sentenceIndex < 0 || sentenceIndex >= sentences.length) return null;

    final seconds = position.inMilliseconds / 1000.0;
    final sentence = sentences[sentenceIndex];

    for (int i = 0; i < sentence.words.length; i++) {
      final word = sentence.words[i];
      if (seconds >= word.start && seconds <= word.end) {
        return word.wordIndex;
      }
    }

    return null;
  }

  /// 跳转到下一句
  Future<void> jumpToNextSentence() async {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return;

    final currentIndex = getCurrentSentenceIndex(_audioPlayer.position);
    final sentences = _fastModeAudio!.timeline.sentences;

    // 如果在 intro 阶段（currentIndex == -1），跳转到第一句
    if (currentIndex == -1) {
      if (sentences.isNotEmpty) {
        final firstStart = sentences[0].sentenceJa.start;
        await seek(Duration(milliseconds: (firstStart * 1000).toInt()));
      }
    }
    // 否则跳转到下一句
    else if (currentIndex < sentences.length - 1) {
      final nextStart = sentences[currentIndex + 1].sentenceJa.start;
      await seek(Duration(milliseconds: (nextStart * 1000).toInt()));
    }
  }

  /// 跳转到上一句（或当前句子开始，或 intro 开始）
  Future<void> jumpToPreviousSentence() async {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return;

    final currentIndex = getCurrentSentenceIndex(_audioPlayer.position);
    final sentences = _fastModeAudio!.timeline.sentences;

    // 如果在 intro 阶段，跳到开头
    if (currentIndex == -1) {
      await seek(Duration.zero);
      return;
    }

    final currentSentence = sentences[currentIndex];
    final currentSeconds = _audioPlayer.position.inMilliseconds / 1000.0;

    // 如果当前句子播放超过 1 秒，跳回当前句子开始
    if (currentSeconds - currentSentence.sentenceJa.start > 1.0) {
      await seek(
        Duration(
          milliseconds: (currentSentence.sentenceJa.start * 1000).toInt(),
        ),
      );
    }
    // 如果是第一句且播放不到 1 秒，跳回 intro 开始
    else if (currentIndex == 0) {
      await seek(Duration.zero);
    }
    // 否则跳到上一句
    else {
      final prevStart = sentences[currentIndex - 1].sentenceJa.start;
      await seek(Duration(milliseconds: (prevStart * 1000).toInt()));
    }
  }

  /// 停止播放
  Future<void> stop() async {
    await _audioPlayer.stop();
  }

  /// 释放资源
  void dispose() {
    _audioPlayer.dispose();
  }
}
