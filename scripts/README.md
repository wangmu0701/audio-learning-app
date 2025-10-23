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

I'll begin with focusing on N5 level grammars and then expand to N4 level eventually.

## App Development
The system consists of two main components:

Backend Data Generation System - Python scripts that generate learning content
Flutter Mobile App - iOS app that delivers the learning experience


1. Backend Data Generation System
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


2. Flutter Mobile App
A very simple flutter based iOS app.