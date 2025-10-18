import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../models/story.dart';
import '../models/word.dart';
import '../providers/story_providers.dart';
import '../providers/audio_providers.dart';

class PlayerScreen extends ConsumerStatefulWidget {
  final Story story;

  const PlayerScreen({super.key, required this.story});

  @override
  ConsumerState<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends ConsumerState<PlayerScreen> {
  StreamSubscription? _playerStateSubscription;
  StreamSubscription? _positionSubscription;
  Word? _lastDisplayedWord;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    final audioService = ref.read(audioServiceProvider);
    final currentPlayingStoryId = ref.read(currentPlayingStoryIdProvider);

    // 只在不是当前播放的故事时才重新加载
    if (currentPlayingStoryId != widget.story.storyId) {
      await audioService.loadStory(widget.story.storyId);
      ref.read(currentPlayingStoryIdProvider.notifier).state =
          widget.story.storyId;
    }

    // 监听播放状态
    _playerStateSubscription = audioService.player.playerStateStream.listen((
      state,
    ) {
      if (!mounted) return;
      ref.read(isPlayingProvider.notifier).state = state.playing;
    });

    // 监听播放位置
    _positionSubscription = audioService.player.positionStream.listen((
      position,
    ) {
      if (!mounted) return;
      ref.read(playbackPositionProvider.notifier).state = position;
      _updateCurrentSentenceAndWord(position);
    });
  }

  void _updateCurrentSentenceAndWord(Duration position) {
    final audioService = ref.read(audioServiceProvider);

    // 更新当前句子索引
    final sentenceIndex = audioService.getCurrentSentenceIndex(position);
    ref.read(currentSentenceIndexProvider.notifier).state = sentenceIndex;

    // 更新当前单词索引
    final wordIndex = audioService.getCurrentWordIndex(position, sentenceIndex);
    ref.read(currentWordIndexProvider.notifier).state = wordIndex;
  }

  @override
  Widget build(BuildContext context) {
    final storyDetailAsync = ref.watch(
      storyDetailProvider(widget.story.storyId),
    );
    final audioService = ref.watch(audioServiceProvider);
    final isPlaying = ref.watch(isPlayingProvider);
    final position = ref.watch(playbackPositionProvider);
    final currentSentenceIndex = ref.watch(currentSentenceIndexProvider);
    final currentWordIndex = ref.watch(currentWordIndexProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.story.title),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: storyDetailAsync.when(
        data: (storyDetail) {
          if (storyDetail == null) {
            return const Center(child: Text('Story not found'));
          }

          final duration = audioService.player.duration ?? Duration.zero;

          // 获取当前句子和单词
          final currentSentence =
              currentSentenceIndex >= 0 &&
                  currentSentenceIndex < storyDetail.sentences.length
              ? storyDetail.sentences[currentSentenceIndex]
              : null;

          final currentWord =
              currentSentence != null && currentWordIndex != null
              ? currentSentence.words[currentWordIndex]
              : null;

          // 更新 lastDisplayedWord 逻辑：
          // 1. 如果有新单词，更新
          // 2. 如果不在单词解释阶段，清除
          final isInWordPhase = audioService.isInWordExplanationPhase(position);
          if (currentWord != null) {
            _lastDisplayedWord = currentWord;
          } else if (!isInWordPhase) {
            // 在 intro 或句子播放阶段，清除单词解释
            _lastDisplayedWord = null;
          }

          return Column(
            children: [
              // Story title section
              _buildStoryHeader(storyDetail),

              // Main content area (scrollable)
              Expanded(
                child: SingleChildScrollView(
                  child: Column(
                    children: [
                      // Sentence display or intro display
                      if (currentSentence != null)
                        _buildSentenceDisplay(
                          currentSentence,
                          currentWordIndex,
                        ),

                      // Word explanation section
                      _buildWordExplanationSection(_lastDisplayedWord),
                    ],
                  ),
                ),
              ),

              // Player controls at bottom
              _buildPlayerControls(
                isPlaying: isPlaying,
                position: position,
                duration: duration,
                audioService: audioService,
              ),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Error: $error'),
            ],
          ),
        ),
      ),
    );
  }

  // Story header with title
  Widget _buildStoryHeader(storyDetail) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20.0),
      decoration: BoxDecoration(
        color: Colors.grey[100],
        border: Border(bottom: BorderSide(color: Colors.grey[300]!)),
      ),
      child: Column(
        children: [
          Text(
            storyDetail.titleJa,
            style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 4),
          Text(
            storyDetail.title,
            style: TextStyle(fontSize: 14, color: Colors.grey[600]),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  // Sentence display with word highlighting
  Widget _buildSentenceDisplay(sentence, int? highlightedWordIndex) {
    return Container(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Japanese sentence with highlighting
          _buildJapaneseSentence(sentence, highlightedWordIndex),
          const SizedBox(height: 16),
          // English translation
          Text(
            sentence.sentenceEn,
            style: const TextStyle(
              fontSize: 16,
              color: Colors.black87,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  // Japanese sentence with word-level highlighting
  Widget _buildJapaneseSentence(sentence, int? highlightedWordIndex) {
    final spans = <TextSpan>[];
    String remainingText = sentence.sentenceJa;

    final sortedWords = List.from(sentence.words)
      ..sort((a, b) => a.position.compareTo(b.position));

    int currentPosition = 0;

    for (int i = 0; i < sortedWords.length; i++) {
      final word = sortedWords[i];
      final isHighlighted = highlightedWordIndex == i;

      // Add text before this word
      if (word.position > currentPosition) {
        final beforeText = remainingText.substring(
          0,
          word.position - currentPosition,
        );
        spans.add(TextSpan(text: beforeText));
        remainingText = remainingText.substring(
          word.position - currentPosition,
        );
      }

      // Add the word with highlighting
      final wordLength = word.wordJa.length;
      spans.add(
        TextSpan(
          text: word.wordJa,
          style: TextStyle(
            backgroundColor: isHighlighted ? Colors.yellow : Colors.transparent,
            fontWeight: isHighlighted ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      );

      remainingText = remainingText.substring(wordLength);
      currentPosition = word.position + wordLength;
    }

    // Add remaining text
    if (remainingText.isNotEmpty) {
      spans.add(TextSpan(text: remainingText));
    }

    return RichText(
      text: TextSpan(
        style: const TextStyle(fontSize: 24, color: Colors.black, height: 1.8),
        children: spans,
      ),
      textAlign: TextAlign.center,
    );
  }

  // Word explanation section (always visible, shows different content)
  Widget _buildWordExplanationSection(Word? currentWord) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20.0),
      decoration: BoxDecoration(
        color: currentWord != null ? Colors.blue[50] : Colors.grey[100],
        border: Border(
          top: BorderSide(
            color: currentWord != null ? Colors.blue[200]! : Colors.grey[300]!,
          ),
        ),
      ),
      child: currentWord != null
          ? _buildWordExplanation(currentWord)
          : _buildListeningPrompt(),
    );
  }

  // Word explanation when a word is being played
  Widget _buildWordExplanation(Word word) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Word header
        Row(
          children: [
            Icon(Icons.book, size: 20, color: Colors.blue[700]),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '${word.wordJa} (${word.wordRomaji})',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Colors.blue[900],
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 8),

        // English meaning
        Text(
          '"${word.wordEn}"',
          style: TextStyle(
            fontSize: 16,
            fontStyle: FontStyle.italic,
            color: Colors.blue[700],
          ),
        ),
        const SizedBox(height: 12),

        // Detailed explanation
        Text(
          word.explanation,
          style: const TextStyle(
            fontSize: 14,
            height: 1.5,
            color: Colors.black87,
          ),
        ),
      ],
    );
  }

  // Listening prompt when no word is being played
  Widget _buildListeningPrompt() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.headphones, size: 20, color: Colors.grey[600]),
        const SizedBox(width: 8),
        Text(
          'Listening to sentence...',
          style: TextStyle(
            fontSize: 14,
            color: Colors.grey[600],
            fontStyle: FontStyle.italic,
          ),
        ),
      ],
    );
  }

  // Player controls with progress bar
  Widget _buildPlayerControls({
    required bool isPlaying,
    required Duration position,
    required Duration duration,
    required audioService,
  }) {
    final canGoNext = audioService.canJumpToNext(position);

    return Container(
      padding: const EdgeInsets.all(20.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.1),
            blurRadius: 10,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          // Progress bar
          Row(
            children: [
              // Current time
              Text(
                _formatDuration(position),
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
              const SizedBox(width: 8),

              // Slider
              Expanded(
                child: SliderTheme(
                  data: SliderTheme.of(context).copyWith(
                    trackHeight: 3.0,
                    thumbShape: const RoundSliderThumbShape(
                      enabledThumbRadius: 6.0,
                    ),
                    overlayShape: const RoundSliderOverlayShape(
                      overlayRadius: 14.0,
                    ),
                  ),
                  child: Slider(
                    value: position.inMilliseconds.toDouble().clamp(
                      0.0,
                      duration.inMilliseconds.toDouble(),
                    ),
                    min: 0.0,
                    max: duration.inMilliseconds.toDouble(),
                    onChanged: (value) {
                      final newPosition = Duration(milliseconds: value.toInt());
                      audioService.seek(newPosition);
                      // 立即更新状态
                      ref.read(playbackPositionProvider.notifier).state =
                          newPosition;
                      _updateCurrentSentenceAndWord(newPosition);
                    },
                  ),
                ),
              ),

              const SizedBox(width: 8),
              // Total duration
              Text(
                _formatDuration(duration),
                style: TextStyle(fontSize: 12, color: Colors.grey[600]),
              ),
            ],
          ),

          const SizedBox(height: 16),

          // Control buttons
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              // Previous button
              IconButton(
                icon: const Icon(Icons.skip_previous),
                iconSize: 48,
                onPressed: () async {
                  final newPosition = await audioService
                      .jumpToPreviousSentence();
                  if (newPosition != null) {
                    // 立即更新状态
                    ref.read(playbackPositionProvider.notifier).state =
                        newPosition;
                    _updateCurrentSentenceAndWord(newPosition);
                  }
                },
                color: Colors.black,
              ),

              const SizedBox(width: 24),

              // Play/Pause button
              IconButton(
                icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow),
                iconSize: 64,
                onPressed: () {
                  if (isPlaying) {
                    audioService.pause();
                  } else {
                    audioService.play();
                  }
                },
                color: Colors.blue,
              ),

              const SizedBox(width: 24),

              // Next button
              IconButton(
                icon: const Icon(Icons.skip_next),
                iconSize: 48,
                onPressed: canGoNext
                    ? () async {
                        final newPosition = await audioService
                            .jumpToNextSentence();
                        if (newPosition != null) {
                          // 立即更新状态
                          ref.read(playbackPositionProvider.notifier).state =
                              newPosition;
                          _updateCurrentSentenceAndWord(newPosition);
                        }
                      }
                    : null,
                color: canGoNext ? Colors.black : Colors.grey,
              ),
            ],
          ),
        ],
      ),
    );
  }

  // Format duration as MM:SS
  String _formatDuration(Duration duration) {
    String twoDigits(int n) => n.toString().padLeft(2, '0');
    final minutes = twoDigits(duration.inMinutes.remainder(60));
    final seconds = twoDigits(duration.inSeconds.remainder(60));
    return '$minutes:$seconds';
  }

  @override
  void dispose() {
    _playerStateSubscription?.cancel();
    _positionSubscription?.cancel();
    super.dispose();
  }
}
