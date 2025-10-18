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
  /// 现在 intro 阶段也返回正确的句子索引
  int getCurrentSentenceIndex(Duration position) {
    if (_fastModeAudio == null) return 0;

    final seconds = position.inMilliseconds / 1000.0;
    final timeline = _fastModeAudio!.timeline;

    // 1. 检查是否在日语 intro 阶段
    for (var item in timeline.storyPlaybackTimelineJa) {
      if (item.contains(seconds)) {
        return item.sentenceIndex;
      }
    }

    // 2. 检查是否在英语 intro 阶段
    for (var item in timeline.storyPlaybackTimelineEn) {
      if (item.contains(seconds)) {
        return item.sentenceIndex;
      }
    }

    // 3. 检查是否在详细学习阶段
    for (int i = 0; i < timeline.sentences.length; i++) {
      final sentence = timeline.sentences[i];
      final sentenceEnd = sentence.words.isNotEmpty
          ? sentence.words.last.end
          : sentence.sentenceEn.end;

      if (seconds >= sentence.sentenceJa.start && seconds <= sentenceEnd) {
        return i;
      }
    }

    // 4. 如果超出所有范围，返回最后一句
    return timeline.sentences.isEmpty ? 0 : timeline.sentences.length - 1;
  }

  /// 根据播放位置和句子索引获取当前单词索引
  /// 只在详细学习阶段返回单词索引，intro 阶段返回 null
  int? getCurrentWordIndex(Duration position, int sentenceIndex) {
    if (_fastModeAudio == null) return null;

    final seconds = position.inMilliseconds / 1000.0;
    final timeline = _fastModeAudio!.timeline;

    // 检查是否在 intro 阶段（日语或英语）
    for (var item in timeline.storyPlaybackTimelineJa) {
      if (item.contains(seconds)) {
        return null; // Intro 阶段不返回单词索引
      }
    }
    for (var item in timeline.storyPlaybackTimelineEn) {
      if (item.contains(seconds)) {
        return null; // Intro 阶段不返回单词索引
      }
    }

    // 详细学习阶段才返回单词索引
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

  /// 跳转到下一句
  Future<Duration?> jumpToNextSentence() async {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return null;

    final currentIndex = getCurrentSentenceIndex(_audioPlayer.position);
    final timeline = _fastModeAudio!.timeline;
    final currentSeconds = _audioPlayer.position.inMilliseconds / 1000.0;

    Duration? newPosition;

    // 1. 如果在日语 intro 阶段，跳到下一句的日语部分
    for (int i = 0; i < timeline.storyPlaybackTimelineJa.length; i++) {
      if (timeline.storyPlaybackTimelineJa[i].contains(currentSeconds)) {
        if (i < timeline.storyPlaybackTimelineJa.length - 1) {
          final nextStart = timeline.storyPlaybackTimelineJa[i + 1].start;
          newPosition = Duration(milliseconds: (nextStart * 1000).toInt());
        } else {
          // 日语 intro 的最后一句，跳到英语 intro 的第一句
          if (timeline.storyPlaybackTimelineEn.isNotEmpty) {
            final nextStart = timeline.storyPlaybackTimelineEn[0].start;
            newPosition = Duration(milliseconds: (nextStart * 1000).toInt());
          }
        }
        if (newPosition != null) {
          await seek(newPosition);
        }
        return newPosition;
      }
    }

    // 2. 如果在英语 intro 阶段，跳到下一句的英语部分
    for (int i = 0; i < timeline.storyPlaybackTimelineEn.length; i++) {
      if (timeline.storyPlaybackTimelineEn[i].contains(currentSeconds)) {
        if (i < timeline.storyPlaybackTimelineEn.length - 1) {
          final nextStart = timeline.storyPlaybackTimelineEn[i + 1].start;
          newPosition = Duration(milliseconds: (nextStart * 1000).toInt());
        } else {
          // 英语 intro 的最后一句，跳到详细学习的第一句
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

    // 3. 如果在详细学习阶段，跳到下一句
    if (currentIndex < timeline.sentences.length - 1) {
      final nextStart = timeline.sentences[currentIndex + 1].sentenceJa.start;
      newPosition = Duration(milliseconds: (nextStart * 1000).toInt());
      await seek(newPosition);
    }

    return newPosition;
  }

  /// 跳转到上一句
  Future<Duration?> jumpToPreviousSentence() async {
    if (_fastModeAudio == null || _audioPlayer.duration == null) return null;

    final timeline = _fastModeAudio!.timeline;
    final currentSeconds = _audioPlayer.position.inMilliseconds / 1000.0;

    Duration? newPosition;

    // 1. 如果在日语 intro 阶段
    for (int i = 0; i < timeline.storyPlaybackTimelineJa.length; i++) {
      if (timeline.storyPlaybackTimelineJa[i].contains(currentSeconds)) {
        // 检查是否播放超过 1 秒
        if (currentSeconds - timeline.storyPlaybackTimelineJa[i].start > 1.0) {
          // 跳回当前句开始
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineJa[i].start * 1000)
                .toInt(),
          );
        } else if (i > 0) {
          // 跳到上一句
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineJa[i - 1].start * 1000)
                .toInt(),
          );
        } else {
          // 已经是第一句，跳到开头
          newPosition = Duration.zero;
        }
        if (newPosition != null) {
          await seek(newPosition);
        }
        return newPosition;
      }
    }

    // 2. 如果在英语 intro 阶段
    for (int i = 0; i < timeline.storyPlaybackTimelineEn.length; i++) {
      if (timeline.storyPlaybackTimelineEn[i].contains(currentSeconds)) {
        if (currentSeconds - timeline.storyPlaybackTimelineEn[i].start > 1.0) {
          // 跳回当前句开始
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineEn[i].start * 1000)
                .toInt(),
          );
        } else if (i > 0) {
          // 跳到上一句英语
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineEn[i - 1].start * 1000)
                .toInt(),
          );
        } else {
          // 英语的第一句，跳回日语的最后一句
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
        return newPosition;
      }
    }

    // 3. 如果在详细学习阶段
    final currentIndex = getCurrentSentenceIndex(_audioPlayer.position);
    if (currentIndex >= 0 && currentIndex < timeline.sentences.length) {
      final currentSentence = timeline.sentences[currentIndex];

      if (currentSeconds - currentSentence.sentenceJa.start > 1.0) {
        // 跳回当前句开始
        newPosition = Duration(
          milliseconds: (currentSentence.sentenceJa.start * 1000).toInt(),
        );
      } else if (currentIndex > 0) {
        // 跳到上一句
        newPosition = Duration(
          milliseconds:
              (timeline.sentences[currentIndex - 1].sentenceJa.start * 1000)
                  .toInt(),
        );
      } else {
        // 详细学习的第一句，跳回英语 intro 的最后一句
        if (timeline.storyPlaybackTimelineEn.isNotEmpty) {
          newPosition = Duration(
            milliseconds: (timeline.storyPlaybackTimelineEn.last.start * 1000)
                .toInt(),
          );
        } else if (timeline.storyPlaybackTimelineJa.isNotEmpty) {
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

    // 1. 检查是否在日语 intro 阶段
    for (var item in timeline.storyPlaybackTimelineJa) {
      if (item.contains(seconds)) {
        return false; // Intro 阶段，不显示单词解释
      }
    }

    // 2. 检查是否在英语 intro 阶段
    for (var item in timeline.storyPlaybackTimelineEn) {
      if (item.contains(seconds)) {
        return false; // Intro 阶段，不显示单词解释
      }
    }

    // 3. 检查是否在详细学习阶段的句子播放部分
    for (var sentence in timeline.sentences) {
      // 在日语句子播放阶段
      if (sentence.sentenceJa.contains(seconds)) {
        return false;
      }
      // 在英语句子播放阶段
      if (sentence.sentenceEn.contains(seconds)) {
        return false;
      }
    }

    // 4. 如果不在以上任何阶段，可能在单词解释阶段
    return true;
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
