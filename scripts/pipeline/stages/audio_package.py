import sys
import os
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from pipeline.logger import get_logger

logger = get_logger(__name__)

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None

class AudioPackageStage(PipelineStage):
    """
    Stage 7: Audio Package.

    Combines individual audio files into a single, seamless 'fast_mode' packaged
    audio file for the entire story, with timeline metadata for precise
    highlighting control. This stage is disabled if pydub is not installed.
    """

    def __init__(self, config: Dict):
        """Initializes the AudioPackageStage."""
        super().__init__(config)
        self.enabled = PYDUB_AVAILABLE
        
        if not self.enabled:
            logger.error("pydub library not found. AudioPackageStage will be disabled. To enable, run: pip install pydub")
            return

        # Audio gap configuration (in seconds)
        self.gap_major = config.get('audio_gap_major', 0.5)  # Major transitions
        self.gap_minor = config.get('audio_gap_minor', 0.3)  # Minor transitions
        
        logger.info(f"AudioPackageStage initialized with gaps: major={self.gap_major}s, minor={self.gap_minor}s")

    @property
    def stage_name(self) -> str:
        return "audio_package"
    
    def process_all(self, stories: List[Dict]) -> List[Dict]:
        """Override process_all to handle the enabled/disabled state of the stage."""
        if not self.enabled:
            logger.warning("Skipping AudioPackageStage because pydub library is not installed.")
            return stories
        
        return super().process_all(stories)

    def process(self, story: Dict) -> Dict:
        """
        Processes a story to create a single packaged 'fast_mode' audio file
        with timeline metadata for the entire story.
        """
        story_id = story.get("story_id", "unknown")
        logger.info(f"Packaging 'fast_mode' audio for story: {story_id}")

        base_path = story["output_path"]
        packed_audio_dir = os.path.join(base_path, "audio", "packed")
        os.makedirs(packed_audio_dir, exist_ok=True)

        output_file = os.path.join(packed_audio_dir, "fast_mode.mp3")

        # Overwrite existing files to ensure consistency between audio and timeline
        if os.path.exists(output_file):
            logger.info(f"  'fast_mode' packed audio already exists, overwriting: {output_file}")

        try:
            # Create silence segments
            silence_major = AudioSegment.silent(duration=int(self.gap_major * 1000))
            silence_minor = AudioSegment.silent(duration=int(self.gap_minor * 1000))

            audio_segments = []
            timeline_data = {
                'full_story_normal': None,
                'full_story_translation': None,
                'sentences': []
            }
            current_time = 0.0

            # 1. Full Story Normal
            full_story_normal_path = os.path.join(base_path, "audio", "full_story_normal.mp3")
            if not os.path.exists(full_story_normal_path):
                raise FileNotFoundError(f"Required audio file not found: {full_story_normal_path}")
            
            audio = AudioSegment.from_mp3(full_story_normal_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            timeline_data['full_story_normal'] = {'start': current_time, 'end': current_time + duration}
            current_time += duration

            audio_segments.append(silence_major)
            current_time += self.gap_major

            # 2. Full Story Translation
            full_story_translation_path = os.path.join(base_path, "audio", "full_story_translation.mp3")
            if not os.path.exists(full_story_translation_path):
                raise FileNotFoundError(f"Required audio file not found: {full_story_translation_path}")

            audio = AudioSegment.from_mp3(full_story_translation_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            timeline_data['full_story_translation'] = {'start': current_time, 'end': current_time + duration}
            current_time += duration

            audio_segments.append(silence_major)
            current_time += self.gap_major

            # 3. Sentences and Words
            sentences = story.get('story_breakdown', [])
            for sent_idx, sentence in enumerate(sentences):
                sentence_timeline = {
                    'sentence_index': sent_idx,
                    'sentence_ja': None,
                    'sentence_en': None,
                    'words': []
                }

                # Sentence JA
                sentence_ja_path = sentence.get('sentence_ja_audio')
                if not sentence_ja_path: raise ValueError(f"Missing sentence_ja_audio for sentence {sent_idx}")
                full_path = os.path.join(base_path, sentence_ja_path)
                if not os.path.exists(full_path): raise FileNotFoundError(f"File not found: {full_path}")
                
                audio = AudioSegment.from_mp3(full_path)
                duration = len(audio) / 1000.0
                audio_segments.append(audio)
                sentence_timeline['sentence_ja'] = {'start': current_time, 'end': current_time + duration}
                current_time += duration

                audio_segments.append(silence_minor)
                current_time += self.gap_minor

                # Sentence EN
                sentence_en_path = sentence.get('sentence_en_audio')
                if not sentence_en_path: raise ValueError(f"Missing sentence_en_audio for sentence {sent_idx}")
                full_path = os.path.join(base_path, sentence_en_path)
                if not os.path.exists(full_path): raise FileNotFoundError(f"File not found: {full_path}")

                audio = AudioSegment.from_mp3(full_path)
                duration = len(audio) / 1000.0
                audio_segments.append(audio)
                sentence_timeline['sentence_en'] = {'start': current_time, 'end': current_time + duration}
                current_time += duration

                audio_segments.append(silence_major)
                current_time += self.gap_major

                # Words
                words = sentence.get('words', [])
                for word_idx, word in enumerate(words):
                    word_timeline = { 'word_index': word_idx, 'word_ja': None, 'word_en': None }

                    # Word JA
                    word_ja_path = word.get('audio_ja_path')
                    if not word_ja_path: raise ValueError(f"Missing audio_ja_path for word {word_idx} in sentence {sent_idx}")
                    full_path = os.path.join(base_path, word_ja_path)
                    if not os.path.exists(full_path): raise FileNotFoundError(f"File not found: {full_path}")

                    audio = AudioSegment.from_mp3(full_path)
                    duration = len(audio) / 1000.0
                    audio_segments.append(audio)
                    word_timeline['word_ja'] = {'start': current_time, 'end': current_time + duration}
                    current_time += duration

                    audio_segments.append(silence_minor)
                    current_time += self.gap_minor

                    # Word EN
                    word_en_path = word.get('audio_en_path')
                    if not word_en_path: raise ValueError(f"Missing audio_en_path for word {word_idx} in sentence {sent_idx}")
                    full_path = os.path.join(base_path, word_en_path)
                    if not os.path.exists(full_path): raise FileNotFoundError(f"File not found: {full_path}")

                    audio = AudioSegment.from_mp3(full_path)
                    duration = len(audio) / 1000.0
                    audio_segments.append(audio)
                    word_timeline['word_en'] = {'start': current_time, 'end': current_time + duration}
                    current_time += duration

                    sentence_timeline['words'].append(word_timeline)

                    if word_idx < len(words) - 1:
                        audio_segments.append(silence_major)
                        current_time += self.gap_major
                
                timeline_data['sentences'].append(sentence_timeline)

                if sent_idx < len(sentences) - 1:
                    audio_segments.append(silence_major)
                    current_time += self.gap_major

            # Merge and Export
            if not audio_segments:
                logger.warning(f"No audio segments collected for story {story_id}, skipping packaging.")
                return story
            
            combined_audio = sum(audio_segments)
            combined_audio.export(output_file, format="mp3")
            logger.info(f"  Successfully saved 'fast_mode' packed audio to {output_file}")

            # Augment story dictionary
            story['fast_mode'] = {
                'audio_url': os.path.relpath(output_file, base_path),
                'duration': current_time,
                'timeline': timeline_data
            }

            logger.info(f"  Successfully packaged 'fast_mode' for story {story_id}")
            return story

        except Exception as e:
            logger.error(f"Failed to package audio for story {story_id}: {e}", exc_info=True)
            # Return story without 'fast_mode' key on failure
            if 'fast_mode' in story:
                del story['fast_mode']
            return story