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
            voice_name="ja-JP-Chirp3-HD-Leda", # A standard female voice
            speaking_rate=1.0
        )
        self.tts_config_ja_slow = TTSConfig(
            language_code="ja-JP",
            voice_name="ja-JP-Chirp3-HD-Leda",
            speaking_rate=0.85 # Slightly slower for learning
        )
        self.tts_config_en = TTSConfig(
            language_code="en-US",
            voice_name="en-US-Journey-F", # A clear, friendly female voice
            speaking_rate=1.0
        )

    @property
    def stage_name(self) -> str:
        return "audio_generation"
    
    def process(self, story: Dict) -> Dict:
        """
        Processes stories to generate all audio files.
        """
        story_id = story.get("story_id", "unknown")
        story_audio_dir = os.path.join(story["output_path"], "audio")
        os.makedirs(story_audio_dir, exist_ok=True)
        logger.info(f"Generating audio for story: {story_id}")

        # This is the base path that all audio file paths in the JSON should be relative to.
        relative_to_path = story["output_path"]

        self._generate_story_level_audio(story, story_audio_dir, relative_to_path)
        self._generate_sentence_level_audio(story, story_audio_dir, relative_to_path)
        return story
        
    def _generate_story_level_audio(self, story: Dict, story_dir: str, relative_to_path: str):
        """Generates audio for the full story text and translation."""
        # This is now handled by packaging individual sentence audio.
        pass

    def _generate_sentence_level_audio(self, story: Dict, story_dir: str, relative_to_path: str):
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
                target_dict=sentence,
                key="sentence_ja_audio",
                relative_to_path=relative_to_path
            )

            # English sentence audio
            self._synthesize_and_save(
                text=sentence.get('sentence_en', ''),
                config=self.tts_config_en,
                file_path=os.path.join(sentences_dir, f"{sentence_id}_en.mp3"),
                target_dict=sentence,
                key="sentence_en_audio",
                relative_to_path=relative_to_path
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
                    target_dict=word, key="audio_ja_path",
                    relative_to_path=relative_to_path
                )
                self._synthesize_and_save(
                    text=word.get('word_en', ''), config=self.tts_config_en, 
                    file_path=os.path.join(words_dir, f"{word_id}_en.mp3"),
                    target_dict=word, key="audio_en_path",
                    relative_to_path=relative_to_path
                )

    def _synthesize_and_save(self, text: str, config: TTSConfig, file_path: str, target_dict: Dict, key: str, relative_to_path: str):
        """Helper to call TTS and save the audio file."""
        if not text:
            return

        # If file already exists, skip generation
        if os.path.exists(file_path):
            logger.info(f"    Audio file already exists, skipping: {file_path}")
            target_dict[key] = os.path.relpath(file_path, relative_to_path)
            return
        
        audio_content = self.tts_provider.synthesize_speech(text, config)
        time.sleep(1) # Add a delay to avoid rate limiting
        if audio_content:
            with open(file_path, "wb") as out:
                out.write(audio_content)
            # Store relative path
            target_dict[key] = os.path.relpath(file_path, relative_to_path)
            logger.debug(f"    Successfully saved audio to {file_path}")
        else:
            logger.warning(f"    Failed to generate audio for text: '{text[:30]}...' ")
            target_dict[key] = None

    def _sanitize_filename(self, name: str) -> str:
        """Sanitizes a string to be used as a valid filename."""
        # Remove invalid characters
        name = re.sub(r'[\\/*?"<>|]', "", name)
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        return name[:50] # Truncate to a reasonable length
