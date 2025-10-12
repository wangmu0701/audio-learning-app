import sys
import os
import re
import time
from typing import List, Dict


sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from pipeline.logger import get_logger
from pipeline.tts_provider import TTSProvider, TTSConfig

logger = get_logger(__name__)

class AudioGenerationStage(PipelineStage):
    """
    Stage 6: Audio Generation.

    Takes the fully processed story data and generates all necessary
    audio files using a Text-to-Speech (TTS) service.
    """

    def __init__(self, config: Dict, tts_provider: TTSProvider):
        """Initializes the AudioGenerationStage."""
        super().__init__(config)
        logger.info("AudioGenerationStage initialized.")
        if not tts_provider:
            raise ValueError("TTSProvider is required.")
        self.tts_provider = tts_provider

        # Define voice configurations
        self.tts_config_ja_normal = TTSConfig(
            language_code="ja-JP",
            voice_name="ja-JP-Wavenet-B", # A standard female voice
            speaking_rate=1.0
        )
        self.tts_config_ja_slow = TTSConfig(
            language_code="ja-JP",
            voice_name="ja-JP-Wavenet-B",
            speaking_rate=0.85 # Slightly slower for learning
        )
        self.tts_config_en = TTSConfig(
            language_code="en-US",
            voice_name="en-US-Journey-F", # A clear, friendly female voice
            speaking_rate=1.0
        )

    def process(self, stories: List[Dict]) -> List[Dict]:
        """
        Processes stories to generate all audio files.
        """
        logger.info(f"AudioGenerationStage received {len(stories)} stories to process.")
        
        base_audio_dir = self.config.get('output_audio_dir', 'output/audio')
        os.makedirs(base_audio_dir, exist_ok=True)

        for i, story in enumerate(stories):
            story_id = self._sanitize_filename(story.get('title', f'story_{i+1}'))
            story['id'] = story_id
            story_dir = os.path.join(base_audio_dir, story_id)
            os.makedirs(story_dir, exist_ok=True)
            logger.info(f"Processing story: {story_id}")

            try:
                self._generate_story_level_audio(story, story_dir)
                self._generate_sentence_level_audio(story, story_dir)
            except Exception as e:
                logger.error(f"Failed to process audio for story '{story_id}'. Error: {e}")
                continue

        return stories

    def _generate_story_level_audio(self, story: Dict, story_dir: str):
        """Generates audio for the full story text and translation."""
        logger.debug(f"Generating story-level audio for {story['id']}")
        # Full Japanese story (slow and normal)
        full_story_ja = " ".join([s.get('sentence_ja', '') for s in story.get('story_breakdown', [])])
        self._synthesize_and_save(
            text=full_story_ja, 
            config=self.tts_config_ja_slow, 
            file_path=os.path.join(story_dir, "full_story_slow.mp3"),
            story=story,
            key="audio_full_story_slow_path"
        )
        self._synthesize_and_save(
            text=full_story_ja, 
            config=self.tts_config_ja_normal, 
            file_path=os.path.join(story_dir, "full_story_normal.mp3"),
            story=story,
            key="audio_full_story_normal_path"
        )

        # Full English translation
        full_story_en = " ".join([s.get('sentence_en', '') for s in story.get('story_breakdown', [])])
        self._synthesize_and_save(
            text=full_story_en, 
            config=self.tts_config_en, 
            file_path=os.path.join(story_dir, "full_story_translation.mp3"),
            story=story,
            key="audio_full_story_translation_path"
        )

    def _generate_sentence_level_audio(self, story: Dict, story_dir: str):
        """Generates audio for each sentence and its components."""
        sentences_dir = os.path.join(story_dir, "sentences")
        os.makedirs(sentences_dir, exist_ok=True)

        for i, sentence in enumerate(story.get('story_breakdown', [])):
            sentence_id = f"s{i+1}"
            sentence['id'] = sentence_id
            logger.debug(f"  Generating audio for sentence: {sentence_id}")

            # Japanese sentence audio
            self._synthesize_and_save(
                text=sentence.get('sentence_ja', ''),
                config=self.tts_config_ja_slow,
                file_path=os.path.join(sentences_dir, f"{sentence_id}_ja.mp3"),
                story=sentence,
                key="sentence_ja_audio"
            )

            # English sentence audio
            self._synthesize_and_save(
                text=sentence.get('sentence_en', ''),
                config=self.tts_config_en,
                file_path=os.path.join(sentences_dir, f"{sentence_id}_en.mp3"),
                story=sentence,
                key="sentence_en_audio"
            )

            # Word-level audio
            words_dir = os.path.join(sentences_dir, sentence_id + "_words")
            os.makedirs(words_dir, exist_ok=True)
            for j, word in enumerate(sentence.get('words', [])):
                word_id = f"w{j+1}"
                word['id'] = word_id
                self._synthesize_and_save(
                    text=word.get('word_ja', ''), config=self.tts_config_ja_slow, 
                    file_path=os.path.join(words_dir, f"{word_id}_ja.mp3"),
                    story=word, key="audio_ja_path"
                )
                self._synthesize_and_save(
                    text=word.get('word_romaji', ''), config=self.tts_config_en, # Read romaji with English voice
                    file_path=os.path.join(words_dir, f"{word_id}_romaji.mp3"),
                    story=word, key="audio_romaji_path"
                )
                self._synthesize_and_save(
                    text=word.get('word_en', ''), config=self.tts_config_en, 
                    file_path=os.path.join(words_dir, f"{word_id}_en.mp3"),
                    story=word, key="audio_en_path"
                )
                self._synthesize_and_save(
                    text=word.get('explanation', ''), config=self.tts_config_en, 
                    file_path=os.path.join(words_dir, f"{word_id}_explanation.mp3"),
                    story=word, key="audio_explanation_path"
                )

    def _synthesize_and_save(self, text: str, config: TTSConfig, file_path: str, story: Dict, key: str):
        """Helper to call TTS and save the audio file."""
        if not text:
            return

        # If file already exists, skip generation
        if os.path.exists(file_path):
            logger.info(f"    Audio file already exists, skipping: {file_path}")
            story[key] = os.path.relpath(file_path, self.config.get('output_audio_dir', 'output/audio'))
            return
        
        audio_content = self.tts_provider.synthesize_speech(text, config)
        time.sleep(1) # Add a delay to avoid rate limiting
        if audio_content:
            with open(file_path, "wb") as out:
                out.write(audio_content)
            # Store relative path
            story[key] = os.path.relpath(file_path, self.config.get('output_audio_dir', 'output/audio'))
            logger.debug(f"    Successfully saved audio to {file_path}")
        else:
            logger.warning(f"    Failed to generate audio for text: '{text[:30]}...' ")
            story[key] = None

    def _sanitize_filename(self, name: str) -> str:
        """Sanitizes a string to be used as a valid filename."""
        # Remove invalid characters
        name = re.sub(r'[\\/*?"<>|]', "", name)
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        return name[:50] # Truncate to a reasonable length