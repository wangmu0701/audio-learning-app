import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../models/story.dart';
import '../models/sentence.dart';
import '../models/playback_mode.dart';
import '../providers/story_providers.dart';
import '../providers/audio_providers.dart';
import '../services/audio_player_service.dart';

class PlayerScreen extends ConsumerStatefulWidget {
  final Story story;
  final PlaybackMode playbackMode;

  const PlayerScreen({
    super.key,
    required this.story,
    this.playbackMode = PlaybackMode.full,
  });

  @override
  ConsumerState<PlayerScreen> createState() => _PlayerScreenState();
}

class _PlayerScreenState extends ConsumerState<PlayerScreen> {
  StreamSubscription? _playerStateSubscription;
  StreamSubscription? _positionSubscription;

  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    final audioService = ref.read(audioServiceProvider);
    await audioService.loadStory(widget.story.storyId, widget.playbackMode);

    // Listen to player state changes
    _playerStateSubscription = audioService.player.playerStateStream.listen((
      state,
    ) {
      if (!mounted) return;

      ref.read(isPlayingProvider.notifier).state = state.playing;

      // When audio completes or changes, update current sentence
      if (state.processingState == ProcessingState.completed ||
          state.processingState == ProcessingState.ready) {
        Future.delayed(const Duration(milliseconds: 100), () {
          if (!mounted) return;
          ref.read(currentSentenceProvider.notifier).state =
              audioService.currentSentence;
          ref.read(currentSentenceIndexProvider.notifier).state =
              audioService.currentSentenceIndex;
        });
      }
    });

    // Listen to position changes for word highlighting
    _positionSubscription = audioService.player.positionStream.listen((
      position,
    ) {
      if (!mounted) return;
      ref.read(playbackPositionProvider.notifier).state = position;
      _updateHighlightedWord(position);
    });
  }

  void _updateHighlightedWord(Duration position) {
    if (!mounted) return;

    final audioService = ref.read(audioServiceProvider);

    // Only update highlights during sentence learning phase
    if (audioService.currentPhase != PlaybackPhase.sentenceLearning) {
      ref.read(highlightedWordIndexProvider.notifier).state = null;
      return;
    }

    final sentence = audioService.currentSentence;
    if (sentence == null) {
      ref.read(highlightedWordIndexProvider.notifier).state = null;
      return;
    }

    final currentSeconds = position.inMilliseconds / 1000.0;

    // Get the appropriate timeline based on mode
    final timeline = audioService.playbackMode == PlaybackMode.fast
        ? sentence.sentencePackedFastModeAudio?.timeline
        : sentence.packedAudio?.timeline;

    if (timeline == null) {
      ref.read(highlightedWordIndexProvider.notifier).state = null;
      return;
    }

    final wordIndex = timeline.getCurrentWordIndex(currentSeconds);
    ref.read(highlightedWordIndexProvider.notifier).state = wordIndex;
  }

  @override
  Widget build(BuildContext context) {
    final storyDetailAsync = ref.watch(
      storyDetailProvider(widget.story.storyId),
    );
    final audioService = ref.watch(audioServiceProvider);
    final isPlaying = ref.watch(isPlayingProvider);
    final highlightedWordIndex = ref.watch(highlightedWordIndexProvider);

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

          return Column(
            children: [
              // Story title area
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20.0),
                color: Colors.grey[100],
                child: Column(
                  children: [
                    Text(
                      storyDetail.titleJa,
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      storyDetail.title,
                      style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                      textAlign: TextAlign.center,
                    ),
                    const SizedBox(height: 8),
                    // Show current phase
                    Text(
                      audioService.currentPhaseDescription,
                      style: TextStyle(
                        fontSize: 12,
                        color: Colors.blue[700],
                        fontWeight: FontWeight.w500,
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),

              // Content area
              Expanded(
                child: _buildContentArea(
                  audioService,
                  storyDetail,
                  highlightedWordIndex,
                ),
              ),

              // Player controls
              _buildPlayerControls(isPlaying, audioService),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text('Error: $error')),
      ),
    );
  }

  Widget _buildContentArea(
    AudioPlayerService audioService,
    storyDetail,
    int? highlightedWordIndex,
  ) {
    // During intro phase, show a message
    if (audioService.currentPhase == PlaybackPhase.intro) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.headphones, size: 64, color: Colors.grey[400]),
            const SizedBox(height: 16),
            Text(
              'Listen to the full story',
              style: TextStyle(fontSize: 18, color: Colors.grey[600]),
            ),
            const SizedBox(height: 8),
            Text(
              audioService.currentPhaseDescription,
              style: TextStyle(fontSize: 14, color: Colors.grey[500]),
            ),
          ],
        ),
      );
    }

    // During sentence learning, show current sentence
    final currentSentence = audioService.currentSentence;
    if (currentSentence == null) {
      return const Center(child: Text('Loading sentence...'));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // Japanese sentence with highlighted words
          _buildJapaneseSentence(currentSentence, highlightedWordIndex),

          const SizedBox(height: 32),

          // English translation
          Text(
            currentSentence.sentenceEn,
            style: const TextStyle(
              fontSize: 18,
              color: Colors.black87,
              height: 1.5,
            ),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }

  Widget _buildJapaneseSentence(Sentence sentence, int? highlightedWordIndex) {
    final spans = <TextSpan>[];
    String remainingText = sentence.sentenceJa;

    // Sort words by position
    final sortedWords = List.from(sentence.words)
      ..sort((a, b) => a.position.compareTo(b.position));

    int currentPosition = 0;

    for (int i = 0; i < sortedWords.length; i++) {
      final word = sortedWords[i];
      final isHighlighted = highlightedWordIndex == i;

      // Add text before this word
      if (word.position > currentPosition) {
        spans.add(
          TextSpan(
            text: remainingText.substring(0, word.position - currentPosition),
          ),
        );
        remainingText = remainingText.substring(
          word.position - currentPosition,
        );
      }

      // Add the word (highlighted or not)
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

  Widget _buildPlayerControls(bool isPlaying, AudioPlayerService audioService) {
    return Container(
      padding: const EdgeInsets.all(24.0),
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
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Previous button (only during sentence learning)
          if (audioService.currentPhase == PlaybackPhase.sentenceLearning)
            IconButton(
              icon: const Icon(Icons.skip_previous),
              iconSize: 48,
              onPressed: audioService.hasPreviousSentence
                  ? () => audioService.previousSentence()
                  : null,
            ),

          const SizedBox(width: 24),

          // Play/Pause button
          IconButton(
            icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow),
            iconSize: 64,
            onPressed: _togglePlayPause,
          ),

          const SizedBox(width: 24),

          // Next button (only during sentence learning)
          if (audioService.currentPhase == PlaybackPhase.sentenceLearning)
            IconButton(
              icon: const Icon(Icons.skip_next),
              iconSize: 48,
              onPressed: audioService.hasNextSentence
                  ? () => audioService.nextSentence()
                  : null,
            ),
        ],
      ),
    );
  }

  void _togglePlayPause() {
    if (!mounted) return;

    final audioService = ref.read(audioServiceProvider);
    final isPlaying = ref.read(isPlayingProvider);

    if (isPlaying) {
      audioService.pause();
    } else {
      if (audioService.player.processingState == ProcessingState.idle) {
        audioService.startPlaying();
      } else {
        audioService.resume();
      }
    }
  }

  @override
  void dispose() {
    _playerStateSubscription?.cancel();
    _positionSubscription?.cancel();

    final audioService = ref.read(audioServiceProvider);
    audioService.pause();

    super.dispose();
  }
}
