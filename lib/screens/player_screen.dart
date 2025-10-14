import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import '../models/playback_mode.dart';
import '../models/story.dart';
import '../models/sentence.dart';
import '../providers/story_providers.dart';
import '../providers/audio_providers.dart';

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
  @override
  void initState() {
    super.initState();
    _initializePlayer();
  }

  Future<void> _initializePlayer() async {
    final audioService = ref.read(audioServiceProvider);

    await audioService.loadStory(widget.story.storyId, widget.playbackMode);
    
    // Update current sentence
    ref.read(currentSentenceProvider.notifier).state = audioService.currentSentence;
    
    // Listen to player state changes
    audioService.player.playerStateStream.listen((state) {
      ref.read(isPlayingProvider.notifier).state = state.playing;
      
      // When sentence completes, update current sentence
      if (state.processingState == ProcessingState.completed) {
        Future.delayed(const Duration(milliseconds: 100), () {
          ref.read(currentSentenceProvider.notifier).state = audioService.currentSentence;
          ref.read(currentSentenceIndexProvider.notifier).state = audioService.currentSentenceIndex;
        });
      }
    });
    
    // Listen to position changes for word highlighting
    audioService.player.positionStream.listen((position) {
      ref.read(playbackPositionProvider.notifier).state = position;
      _updateHighlightedWord(position);
    });
  }

  void _updateHighlightedWord(Duration position) {
    final sentence = ref.read(currentSentenceProvider);
    if (sentence?.packedAudio == null) return;
    
    final currentSeconds = position.inMilliseconds / 1000.0;
    final wordIndex = sentence!.packedAudio!.timeline.getCurrentWordIndex(currentSeconds);
    ref.read(highlightedWordIndexProvider.notifier).state = wordIndex;
  }

  @override
  Widget build(BuildContext context) {
    final storyDetailAsync = ref.watch(storyDetailProvider(widget.story.storyId));
    final currentSentence = ref.watch(currentSentenceProvider);
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

          if (currentSentence == null) {
            return const Center(child: Text('No sentence loaded'));
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
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey[600],
                      ),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),

              // Content area
              Expanded(
                child: SingleChildScrollView(
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
                ),
              ),

              // Player controls
              _buildPlayerControls(isPlaying),
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (error, stack) => Center(child: Text('Error: $error')),
      ),
    );
  }

  Widget _buildJapaneseSentence(Sentence sentence, int? highlightedWordIndex) {
    // Build the sentence with highlighted words
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
        spans.add(TextSpan(
          text: remainingText.substring(0, word.position - currentPosition),
        ));
        remainingText = remainingText.substring(word.position - currentPosition);
      }
      
      // Add the word (highlighted or not)
      final wordLength = word.wordJa.length;
      spans.add(TextSpan(
        text: word.wordJa,
        style: TextStyle(
          backgroundColor: isHighlighted ? Colors.yellow : Colors.transparent,
          fontWeight: isHighlighted ? FontWeight.bold : FontWeight.normal,
        ),
      ));
      
      remainingText = remainingText.substring(wordLength);
      currentPosition = word.position + wordLength;
    }
    
    // Add remaining text
    if (remainingText.isNotEmpty) {
      spans.add(TextSpan(text: remainingText));
    }
    
    return RichText(
      text: TextSpan(
        style: const TextStyle(
          fontSize: 24,
          color: Colors.black,
          height: 1.8,
        ),
        children: spans,
      ),
      textAlign: TextAlign.center,
    );
  }

  Widget _buildPlayerControls(bool isPlaying) {
    return Container(
      padding: const EdgeInsets.all(24.0),
      decoration: BoxDecoration(
        color: Colors.white,
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.1),
            blurRadius: 10,
            offset: const Offset(0, -5),
          ),
        ],
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          IconButton(
            icon: Icon(isPlaying ? Icons.pause : Icons.play_arrow),
            iconSize: 64,
            onPressed: _togglePlayPause,
          ),
        ],
      ),
    );
  }

  void _togglePlayPause() {
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
    super.dispose();
  }
}