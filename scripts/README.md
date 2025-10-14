## Requirements:

1: Always reply in Chinese.
2: Don't write code unless got approval explicitly. Always explain your ideas and then ask for approval for coding.

## Project Description
Japanese Learning App - Project Description
Project Background
I'm planning a trip to Japan in 2 years and want to learn Japanese, but I only have time during my commute to study. Existing Japanese learning apps either require constant screen attention or have boring content. I need an audio-first learning app that allows me to learn efficiently while driving or on the subway.
Core Principles

Audio-first: Can learn completely without looking at the screen
Zero-to-hero: Designed for learners with absolutely no Japanese knowledge
Natural acquisition: Learn through repeated exposure, like how babies learn language, rather than memorizing grammar rules
Personal use: This is my personal learning tool, not a commercial product (at least initially)

Learning Content Plan
Phase 1: M-MVP (First 2 weeks)

Goal: Validate that the learning method works
Content: 5 stories covering N5 Group 1 grammar points (the most basic 10-12 grammar points)
Duration: Each story is approximately 15 minutes of audio
Deployment: Bundled as iOS app assets, manually reinstall every 7 days

Phase 2: MVP (1-2 months)

Goal: Complete coverage of all N5 grammar points
Content: 30 stories

10 stories - N5 Group 1 (basic grammar)
10 stories - N5 Group 2 (extended grammar)
10 stories - N5 Group 3 (advanced grammar)


Requirements: Ensure all N5 grammar points and common vocabulary are adequately covered

Phase 3: Full N5 (2-4 months)

Goal: Achieve fluency at N5 level
Content: 100 stories for deeper repetition and practice
Features:

More diverse topics
More natural conversation scenarios
More vocabulary accumulation



Phase 4: N4 (4-12 months)

Goal: Advance to N4 level
Content: 200 stories
Note: This phase will be decided based on learning effectiveness after completing N5

Learning Experience
Typical Use Case

Morning commute, open the app
Select the next story
Press play
Listen to the complete story (15 minutes) learning cycle:

Full story in slow Japanese
English translation
Sentence-by-sentence detailed breakdown (Japanese → English → Romaji → Grammar explanation)
Full story in natural-speed Japanese


Glance at screen for text when needed

App Interface (Minimalist Design)

Story list arranged in learning order
Each story displays: Japanese title + English translation + duration
Tap to enter playback screen
Playback screen: Large play/pause button + current sentence text display
Local tracking of completed stories (simple progress tracking)

Success Criteria

Short-term: M-MVP keeps me engaged for 2 weeks without getting bored
Mid-term: MVP enables me to have simple daily conversations in Japanese
Long-term: When I go to Japan in 2 years, I can handle basic travel scenarios

Future Possibilities
If this method works for me and the content quality is good, I might:

Release to App Store for others to use
Add support for other native languages like Chinese
Expand to other JLPT levels (N4, N3...)
But these are secondary; the primary goal is to learn Japanese myself

## App Development
The system consists of two main components:

Backend Data Generation System - Python scripts that generate learning content
Flutter Mobile App - iOS app that delivers the learning experience


1. Backend Data Generation System
Current Status: Implemented ✅
A pipeline-based content generation system that transforms story ideas into complete learning materials.
Pipeline Stages (All Implemented)
Stage 1: Story Idea Generation

Generate diverse, interesting story ideas
Topics cover daily life, technology, food, travel, culture, business
Output: Story titles and summaries in English

Stage 2: Story Generation with Grammar Tagging

Generate complete Japanese stories (6-10 sentences per story)
Select specific grammar points from the target grammar group
Tag which grammar points each sentence uses
Ensure stories are audio-friendly (vivid, easy to visualize)

Stage 3: Word Segmentation & Romanization

Break Japanese sentences into pedagogically meaningful words
Keep verb conjugations whole (not morphological splitting)
Generate Hepburn romanization for all text
Track word positions within sentences

Stage 4 & 5: Content Pedagogy (Translation & Explanation)

Generate contextual English translations for each word
Create conversational, audio-friendly explanations
Connect explanations to relevant grammar points
Avoid quoting Japanese/Romaji in explanations (for TTS quality)

Stage 6: Audio Generation

Use Google Cloud Text-to-Speech to generate all audio files
Create full story audio (slow and normal speed)
Create sentence-level audio (Japanese and English)
Create word-level audio (Japanese, Romaji, English, Explanation)

Stage 7: Audio Packaging

Combine individual audio files into seamless packaged audio
Add silence gaps for natural pacing
Generate timeline metadata for precise text highlighting
Package one file per sentence with complete learning cycle

Stage 8: Story Publish
Publish the story so that the App can use it.
We need to design the data and file structure, both for MVP and for future.

Key Features

Resume capability: Can resume from any stage if generation is interrupted
Per-story output: Each story has its own directory with all assets
Provider abstraction: Supports multiple LLM providers (OpenAI, Gemini, GLM)
Configurable: Grammar groups, model selection, gap timings all configurable

What's Working

End-to-end generation from idea to packaged audio
Tested with Gemini Flash for cost efficiency
Output includes JSON metadata + MP3 audio files
Can generate 5 stories for M-MVP validation


2. Flutter Mobile App
Current Status: Partial Implementation 🚧
Basic UI structure exists but needs integration with real generated content.
What Exists

Library screen with story list
Player screen with playback UI
Story model and provider setup (Riverpod)
Filter functionality (difficulty, topics)
Fake data for UI testing

What Needs to Be Done
Phase 1: M-MVP (5 Stories)

Replace fake data with actual generated content
Load stories and audio from app assets
Implement actual audio playback with audio player package
Sync text highlighting with audio timeline
Simple local storage for "completed" status
Remove unnecessary filters (since M-MVP has only Group 1 stories)

Phase 2: MVP (30 Stories)

Story organization by grammar groups
Better navigation for 30 stories
Progress tracking across stories
Maybe add simple statistics (stories completed, time spent)

Phase 3: Full N5 (100 Stories)

Performance optimization for larger content
Better content discovery
Review/replay functionality for difficult stories


3. Content Strategy & Quality Assurance
M-MVP Coverage Strategy

5 stories targeting N5 Group 1 (10-12 grammar points)
Ensure each grammar point appears at least 2-3 times
Progressive difficulty within the 5 stories
High-frequency vocabulary repetition

MVP Coverage Strategy

30 stories structured to systematically cover:

All N5 grammar points with adequate repetition
Core N5 vocabulary (approximately 800 words)
Variety of real-life scenarios


Each grammar point appears in multiple contexts
Vocabulary frequency tracking and balanced distribution

Quality Validation

Manual review of generated stories for M-MVP
Audio quality check (pronunciation, pacing, clarity)
Grammar point verification
Learning effectiveness self-testing


4. Future Improvements (Post-MVP)
Content Generation Enhancements

Vocabulary management: Track and ensure comprehensive vocabulary coverage
Grammar frequency control: Automatically balance grammar point distribution
Difficulty calibration: Measure and adjust story complexity
Content variety: More sophisticated topic generation and mixing

App Enhancements

Spaced repetition: Intelligently suggest story review timing
Weak point detection: Identify grammar/vocabulary that needs more practice
Offline capability: Full offline mode after initial download
Multiple languages: Add Chinese as native language option

Deployment Evolution

App Store release: If effective, publish for others to use
Cloud content delivery: Replace bundled assets with downloadable content
Content updates: Add new stories without app updates
N4 pipeline: Extend generation system for intermediate level


5. Technical Decisions Pending
Asset Bundling vs Download

M-MVP: Bundle everything (~50-100MB) - Simpler, works offline immediately
MVP: TBD based on app size (~300-600MB may be too large)
Full N5: Likely need download strategy

Story Organization

How to structure/name story files?
Metadata format for story ordering and grouping?
Index file structure for app consumption?

Progress Persistence

Local-only with SharedPreferences?
Or simple cloud sync for multi-device?

Update Strategy

Manual app reinstall for M-MVP (acceptable for personal use)
Later: Design for easier content updates


Next Steps

Finalize M-MVP content specification

Exact grammar point distribution across 5 stories
Vocabulary list to emphasize
Story topics/themes


Generate M-MVP content

Run pipeline for 5 stories
Manual quality review
Iterate if needed


Complete Flutter app integration

Asset loading
Audio playback
Text-audio sync
Basic UI polish


Self-test and iterate

Use app for 2 weeks
Gather learnings
Adjust before scaling to 30 stories