## Product Vision

A pure audio-based Japanese learning app for absolute beginners (N5 level) designed for commute-time learning. The app generates fresh, interesting daily content that teaches Japanese through natural exposure and repetition, similar to how babies learn language.

## Core Principles

Audio-first: Can be used entirely without looking at the screen

Zero-to-hero: Designed for users with absolutely no Japanese knowledge

Daily fresh content: 5 new stories every day

Natural acquisition: Learning through repeated exposure rather than systematic memorization

Stateless (MVP): No user progress tracking to minimize complexity and cost

User Experience


## Primary Use Case

User is commuting (driving, on train/bus) and wants to learn Japanese without looking at their phone.


### User Flow

Open app

See list of dates, each date has 5 stories

Tap a story → Audio starts playing (~15 minutes)

Listen and learn

Optionally glance at phone to see visual text reinforcement

Content Display


📅 2025-10-09

- 新しいロボット / New Robot (13:12)

- 美味しいラーメン / Delicious Ramen (16:05)

- 東京の旅行 / Tokyo Travel (14:58)

- 朝の習慣 / Morning Routine (17:20)

- 友達との会話 / Conversation with Friends (15:03)

📅 2025-10-08

- [5 stories]

📅 2025-10-07

- [5 stories][Infinite scroll for history...]

### UI Features

Bilingual titles: Japanese + English translation (since user knows zero Japanese)

Duration display: Shows exact audio length

Date grouping: Stories organized by date

Recent focus: Shows last 7 days by default

Infinite scrolling: Can access all historical content

No filters (MVP): No topic filtering, no difficulty selection

No progress tracking (MVP): No "completed" checkmarks or learning statistics

### Content Specifications

Daily Generation (By a separate daily script)

5 stories per day

All N5 difficulty level (MVP)

13-17 minutes per story (including all learning components)

Diverse topics: Automatically varied (technology, food, daily life, travel, culture, business) but not surfaced to user

### Audio Structure (Per Story)

Total duration: 13-17 minutes

Full story in Japanese (slow speed) - ~90 seconds

Full story in English translation - ~90 seconds

Sentence-by-sentence breakdown (6-10 sentences) - ~10-12 minutesFor each sentence, break into word-level components:Japanese word (slow) - 2s

Romaji - 2s

English translation - 2s

Detailed explanation - 10-30s (varies by complexity)

Full story in Japanese (natural speed) - ~60 seconds


### Story Structure

Each story contains:

6-10 sentences

4-8 words per sentence (word = segmented unit)

N5 vocabulary only

High repetition: Same particles, verbs, and sentence patterns appear multiple times

Daily life context: Easy to visualize without visual aids

Interesting content: Based on real-world topics adapted for beginner


## N5 Grammar organized into 3 groups:



Group 1: Core Basics (MVP - 10-12 points)

Particles: は, を, に, で, の

Verb forms: です, ます, ました, ません

Basic sentence structure

Question marker か



Group 2: Expansion (Future - 12-15 points)

Particles: が, と, も, へ, から/まで, や

Verb forms: ている, てください, ましょう, たい

Adjectives: い-adjectives, な-adjectives



Group 3: N5 Advanced (Future - 10-12 points)

て form connections

Comparatives

Counters

Must/should expressions

Advanced question word usage



## Grammar Learning Strategy

Random exposure: Stories randomly use 3-5 grammar points from the active group

Natural repetition: High-frequency grammar (like は) appears in almost every story

Not systematic: No "Lesson 1 teaches は, Lesson 2 teaches を" structure

Baby-like learning: Through repeated exposure across different contexts

Progressive difficulty: MVP only uses Group 1, future phases gradually introduce Groups 2 and 3



## Data Architecture



### Multi-Language Support Design

Key Principle: Japanese story content is language-agnostic. Translations and explanations are language-specific.



This allows:

One Japanese story to serve multiple native languages

Easy addition of new native languages (Chinese, Spanish, etc.)

Cost efficiency (generate Japanese once, translate multiple times)

Core Data Models

Story (Language-Agnostic)

The core Japanese content that is shared across all languages.



### Firebase Storage Path: {learningLang}/



stories/

  ├─ 2025-10-09.json                # Japanese core content (shared)

  ├─ 2025-10-08.json

  └─ index.json                     # Story catalog (language-agnostic)



translations/

  ├─ en/

  │   ├─ 2025-10-09.json            # English translations/explanations

  │   ├─ 2025-10-08.json

  │   └─ index_en.json              # English index (with English titles + durations)

  └─ zh/

      ├─ 2025-10-09.json            # Chinese translations/explanations (future)

      └─ index_zh.json



audio/

  ├─ ja/                            # Japanese audio (shared)

  │   └─ 2025-10-09/

  │       ├─ story_full.mp3

  │       └─ sentences/

  │           ├─ s1.mp3

  │           ├─ s2.mp3

  │           └─ ...

  ├─ en/                            # English audio

  │   └─ 2025-10-09/

  │       ├─ story_full_translation.mp3

  │       └─ explanations/

  │           ├─ s1-w1.mp3

  │           ├─ s1-w2.mp3

  │           └─ ...

  └─ zh/                            # Chinese audio (future)





## Content Generation Pipeline



### Pipeline Overview

The pipeline consists of stages that transform input through multiple steps to produce the final content.



Stage 1: News Collection

Purpose: Generate interesting story ideas for the day

Use LLM to generate 5 diverse, interesting story ideas

Topics cover: technology, food, daily life, travel, culture, business

Each idea includes: Japanese title, English summary, topic category, sample URL

MVP uses LLM generation (not real-time news search)

Future: Could integrate actual news APIs or web search



Stage 2: Story Generation + Grammar Tagging

Purpose: Generate complete Japanese stories with grammar annotations

Randomly select 3-5 grammar points from active group

Generate interesting N5-level story in Japanese

Structure output as 6-10 sentences

Tag which grammar points each sentence uses

Appropriate for audio-only learning (vivid, easy to visualize)


Stage 3: Word Segmentation & Romanization

Segment Japanese sentences into meaningful words

Generate romaji (romanization) for each word and full sentence

Create word IDs for tracking

Segmentation Principles (N5/Baby Level):

Romaji is language-agnostic (standard Hepburn romanization)

Word boundaries optimized for beginner comprehension


Stage 4: Translation Generation

Purpose: Generate translations in target native language

Translate Japanese title to native language

Translate each complete sentence

Translate each individual word with context

Contextually appropriate

Brief and clear for audio consumption



Stage 5: Explanation Generation

Purpose: Generate grammar explanations for each word in native language



For each word, generate conversational explanation suitable for audio

Explanation style: oral, friendly, not academic

Focus on grammar points relevant to N5 learners

Vary explanation depth based on word importance



Conversational tone (spoken, not written)

Appropriate length: 8-25 seconds when read aloud

Focus on why/when/how, not just what

Connect to grammar points being taught

Assume zero prior Japanese knowledge





Stage 6: Audio Generation

Purpose: Generate all audio files using Text-to-Speech

Complete Story (Japanese text)

Complete Translation (English text and explanations)



Stage 7: Index Generation & Packaging

Purpose: Create index files for app to consume

Update index.json (language-agnostic story list)

Update index_{lang}.json (language-specific with translations)

Validate all files are complete



Stage 8: Upload to Firebase

Purpose: Deploy all generated content to Firebase Cloud Storage





##MVP Scope vs Future Phases



### MVP (Launch ASAP - Weeks 1-4)

Goal: Get a working app to start learning immediately

Included:



✅ N5 difficulty only

✅ Group 1 grammar points only (10-12 basic points)

✅ English as native language only

✅ 5 stories per day

✅ Word-level breakdown with explanations

✅ ~9 minute audio per story

✅ Last 7 days + infinite scroll

✅ No user progress tracking (stateless)

✅ No topic filtering

✅ Bilingual titles (Japanese + English)

✅ Audio duration display



Not Included:



❌ Chinese language support

❌ N4-N1 difficulty levels

❌ Group 2-3 grammar points

❌ Progress tracking

❌ Topic filtering

❌ Learning statistics

❌ User accounts



### Phase 2 (Months 2-3)

Chinese language support (reuse same Japanese stories)

Group 2 grammar points (expansion)

Smart grammar progression (track what user has heard)

### Phase 3 (Months 3-4)


N4 difficulty level

Group 3 grammar points

Basic progress tracking (which stories played)

Future Phases