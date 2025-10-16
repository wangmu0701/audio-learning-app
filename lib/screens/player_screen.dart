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

    _playerStateSubscription = audioService.player.playerStateStream.listen((
      state,
    ) {
      if (!mounted) return;
      ref.read(isPlayingProvider.notifier).state = state.playing;
    });

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
              // Story title and phase info
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
    if (audioService.currentPhase == PlaybackPhase.intro) {
      // Show all sentences during intro
      return ListView.builder(
        padding: const EdgeInsets.all(24.0),
        itemCount: storyDetail.sentences.length,
        itemBuilder: (context, index) {
          final sentence = storyDetail.sentences[index];
          return Padding(
            padding: const EdgeInsets.only(bottom: 24.0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Sentence number
                Text(
                  'Sentence ${index + 1}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[600],
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                // Japanese
                Text(
                  sentence.sentenceJa,
                  style: const TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.w500,
                    height: 1.5,
                  ),
                ),
                const SizedBox(height: 8),
                // English
                Text(
                  sentence.sentenceEn,
                  style: TextStyle(
                    fontSize: 16,
                    color: Colors.grey[700],
                    height: 1.5,
                  ),
                ),
                if (index < storyDetail.sentences.length - 1)
                  Padding(
                    padding: const EdgeInsets.only(top: 16.0),
                    child: Divider(color: Colors.grey[300]),
                  ),
              ],
            ),
          );
        },
      );
    }

    // During sentence learning
    final currentSentence = audioService.currentSentence;
    if (currentSentence == null) {
      return const Center(child: Text('Loading...'));
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _buildJapaneseSentence(currentSentence, highlightedWordIndex),
          const SizedBox(height: 32),
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

    final sortedWords = List.from(sentence.words)
      ..sort((a, b) => a.position.compareTo(b.position));

    int currentPosition = 0;

    for (int i = 0; i < sortedWords.length; i++) {
      final word = sortedWords[i];
      final isHighlighted = highlightedWordIndex == i;

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
    final canGoPrevious =
        audioService.currentPhase == PlaybackPhase.sentenceLearning;
    final canGoNext =
        audioService.currentPhase == PlaybackPhase.intro ||
        (audioService.currentPhase == PlaybackPhase.sentenceLearning &&
            audioService.hasNextSentence);

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
          // Previous button
          IconButton(
            icon: const Icon(Icons.skip_previous),
            iconSize: 48,
            onPressed: canGoPrevious
                ? () => audioService.previousSentence()
                : null,
            color: canGoPrevious ? Colors.black : Colors.grey,
          ),

          const SizedBox(width: 24),

          // Play/Pause button
          IconButton(
            icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow),
            iconSize: 64,
            onPressed: _togglePlayPause,
          ),

          const SizedBox(width: 24),

          // Next button
          IconButton(
            icon: const Icon(Icons.skip_next),
            iconSize: 48,
            onPressed: canGoNext ? () => audioService.nextSentence() : null,
            color: canGoNext ? Colors.black : Colors.grey,
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
    // Cancel subscriptions first
    _playerStateSubscription?.cancel();
    _positionSubscription?.cancel();

    // Don't use ref.read in dispose - it's too late
    // Just let the audio continue playing or be managed by the service

    super.dispose();
  }
}
