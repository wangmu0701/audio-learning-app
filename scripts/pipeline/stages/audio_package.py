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

    Combines individual audio files into seamless packaged audio files
    with timeline metadata for precise highlighting control.
    This stage is disabled if pydub is not installed.
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
        Processes a story to create packaged audio files with timeline metadata.
        Only packages sentence-level audio (not full story).
        Raises exception if any critical step fails.
        """
        story_id = story.get("id", "unknown")
        logger.info(f"Packaging audio for story: {story_id}")
        
        base_path = story["output_path"]
        packed_audio_dir = os.path.join(base_path, "audio", "packed")
        os.makedirs(packed_audio_dir, exist_ok=True)

        # Package audio for each sentence
        for i, sentence in enumerate(story.get('story_breakdown', [])):
            sentence_id = sentence.get('id', f's{i+1}')
            logger.debug(f"  Packaging sentence: {sentence_id}")
            self._pack_sentence_audio(sentence, base_path, packed_audio_dir, sentence_id)
            self._pack_sentence_fast_mode_audio(sentence, base_path, packed_audio_dir, sentence_id)

        logger.info(f"  Successfully packaged {len(story.get('story_breakdown', []))} sentences")
        return story

    def _pack_sentence_audio(self, sentence: Dict, base_path: str, packed_dir: str, sentence_id: str):
        """
        Packages all audio for a single sentence into one file with timeline.
        Adds silence gaps at all transition points for natural, even pacing.
        
        Order with gaps:
        - sentence_ja → [gap_minor] → sentence_en → [gap_major] → 
        - word_ja → [gap_minor] → word_en → [gap_minor] → word_romaji → [gap_minor] → explanation → [gap_major] → next word_ja
        - ... → [gap_major] → sentence_ja (repeat)

        Raises:
            FileNotFoundError: If required audio files are missing
            Exception: If audio merging fails
        """
        output_file = os.path.join(packed_dir, f"{sentence_id}.mp3")
        
        # Check if already exists
        if os.path.exists(output_file):
            logger.debug(f"    Packed audio already exists, skipping: {output_file}")
            # Still need to read duration for timeline
            try:
                existing_audio = AudioSegment.from_mp3(output_file)
                sentence['sentence_packed_audio'] = {
                    'url': os.path.relpath(output_file, base_path),
                    'duration': len(existing_audio) / 1000.0  # Convert to seconds
                }
            except Exception as e:
                logger.warning(f"Could not read existing packed audio {output_file}: {e}")
            return

        # Create silence segments
        silence_major = AudioSegment.silent(duration=int(self.gap_major * 1000))  # Convert to ms
        silence_minor = AudioSegment.silent(duration=int(self.gap_minor * 1000))

        # Collect audio segments in order
        audio_segments = []
        timeline_data = {
            'sentence_ja': None,
            'sentence_en': None,
            'words': [],
            'sentence_ja_repeat': None
        }
        
        current_time = 0.0  # in seconds

        # 1. Sentence Japanese audio
        sentence_ja_path = sentence.get('sentence_ja_audio')
        if not sentence_ja_path:
            raise ValueError(f"Missing sentence_ja_audio path for sentence {sentence_id}")
        
        full_path = os.path.join(base_path, sentence_ja_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Required audio file not found: {full_path}")
        
        audio = AudioSegment.from_mp3(full_path)
        duration = len(audio) / 1000.0
        audio_segments.append(audio)
        timeline_data['sentence_ja'] = {
            'start': current_time,
            'end': current_time + duration
        }
        current_time += duration
        
        # Add minor gap after sentence_ja
        audio_segments.append(silence_minor)
        current_time += self.gap_minor

        # 2. Sentence English audio
        sentence_en_path = sentence.get('sentence_en_audio')
        if not sentence_en_path:
            raise ValueError(f"Missing sentence_en_audio path for sentence {sentence_id}")
        
        full_path_en = os.path.join(base_path, sentence_en_path)
        if not os.path.exists(full_path_en):
            raise FileNotFoundError(f"Required audio file not found: {full_path_en}")
        
        audio = AudioSegment.from_mp3(full_path_en)
        duration = len(audio) / 1000.0
        audio_segments.append(audio)
        timeline_data['sentence_en'] = {
            'start': current_time,
            'end': current_time + duration
        }
        current_time += duration
        
        # Add major gap before first word
        audio_segments.append(silence_major)
        current_time += self.gap_major

        # 3. Word-level audio with consistent gaps
        words = sentence.get('words', [])
        if not words:
            raise ValueError(f"No words found in sentence {sentence_id}")
        
        for word_idx, word in enumerate(words):
            word_timeline = {
                'word_index': word_idx,
                'word_ja': None,
                'word_en': None,
                'word_romaji': None,
                'explanation': None
            }

            # Word JA
            word_ja_path = word.get('audio_ja_path')
            if not word_ja_path:
                raise ValueError(f"Missing audio_ja_path for word {word_idx} in sentence {sentence_id}")
            word_full_path = os.path.join(base_path, word_ja_path)
            if not os.path.exists(word_full_path):
                raise FileNotFoundError(f"Required audio file not found: {word_full_path}")
            
            audio = AudioSegment.from_mp3(word_full_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            word_timeline['word_ja'] = {
                'start': current_time,
                'end': current_time + duration
            }
            current_time += duration
            
            # Add minor gap after word_ja
            audio_segments.append(silence_minor)
            current_time += self.gap_minor

            # Word EN
            word_en_path = word.get('audio_en_path')
            if not word_en_path:
                raise ValueError(f"Missing audio_en_path for word {word_idx} in sentence {sentence_id}")
            word_full_path = os.path.join(base_path, word_en_path)
            if not os.path.exists(word_full_path):
                raise FileNotFoundError(f"Required audio file not found: {word_full_path}")
            
            audio = AudioSegment.from_mp3(word_full_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            word_timeline['word_en'] = {
                'start': current_time,
                'end': current_time + duration
            }
            current_time += duration
            
            # Add minor gap after word_en
            audio_segments.append(silence_minor)
            current_time += self.gap_minor

            # Word Romaji
            word_romaji_path = word.get('audio_romaji_path')
            if not word_romaji_path:
                raise ValueError(f"Missing audio_romaji_path for word {word_idx} in sentence {sentence_id}")
            word_full_path = os.path.join(base_path, word_romaji_path)
            if not os.path.exists(word_full_path):
                raise FileNotFoundError(f"Required audio file not found: {word_full_path}")
            
            audio = AudioSegment.from_mp3(word_full_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            word_timeline['word_romaji'] = {
                'start': current_time,
                'end': current_time + duration
            }
            current_time += duration
            
            # Add minor gap after romaji
            audio_segments.append(silence_minor)
            current_time += self.gap_minor

            # Explanation
            explanation_path = word.get('audio_explanation_path')
            if not explanation_path:
                raise ValueError(f"Missing audio_explanation_path for word {word_idx} in sentence {sentence_id}")
            word_full_path = os.path.join(base_path, explanation_path)
            if not os.path.exists(word_full_path):
                raise FileNotFoundError(f"Required audio file not found: {word_full_path}")
            
            audio = AudioSegment.from_mp3(word_full_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            word_timeline['explanation'] = {
                'start': current_time,
                'end': current_time + duration
            }
            current_time += duration

            timeline_data['words'].append(word_timeline)
            
            # Add major gap before next word (but not after last word)
            if word_idx < len(words) - 1:
                audio_segments.append(silence_major)
                current_time += self.gap_major

        # 4. Add final repetition of sentence_ja
        audio_segments.append(silence_major)
        current_time += self.gap_major

        audio = AudioSegment.from_mp3(full_path) # Reuse path from the top
        duration = len(audio) / 1000.0
        audio_segments.append(audio)
        timeline_data['sentence_ja_repeat'] = {
            'start': current_time,
            'end': current_time + duration
        }
        current_time += duration

        # Merge all segments
        if not audio_segments:
            raise ValueError(f"No audio segments collected for sentence {sentence_id}")
        
        combined_audio = audio_segments[0]
        for segment in audio_segments[1:]:
            combined_audio += segment

        # Export
        combined_audio.export(output_file, format="mp3")
        logger.debug(f"    Successfully saved packed audio to {output_file}")

        # Update sentence with packed audio info
        sentence['sentence_packed_audio'] = {
            'url': os.path.relpath(output_file, base_path),
            'duration': current_time,
            'timeline': timeline_data
        }

    def _pack_sentence_fast_mode_audio(self, sentence: Dict, base_path: str, packed_dir: str, sentence_id: str):
        """
        Packages a streamlined 'fast mode' audio for a single sentence.
        
        Order with gaps:
        - sentence_ja → [gap_minor] → sentence_en → [gap_major] → 
        - word_ja → [gap_minor] → word_en → [gap_major] → next word_ja
        """
        output_file = os.path.join(packed_dir, f"{sentence_id}_fast.mp3")
        
        if os.path.exists(output_file):
            logger.debug(f"    Fast mode packed audio already exists, skipping: {output_file}")
            try:
                existing_audio = AudioSegment.from_mp3(output_file)
                sentence['sentence_packed_fast_mode_audio'] = {
                    'url': os.path.relpath(output_file, base_path),
                    'duration': len(existing_audio) / 1000.0
                }
            except Exception as e:
                logger.warning(f"Could not read existing fast mode packed audio {output_file}: {e}")
            return

        silence_major = AudioSegment.silent(duration=int(self.gap_major * 1000))
        silence_minor = AudioSegment.silent(duration=int(self.gap_minor * 1000))

        audio_segments = []
        timeline_data = {
            'sentence_ja': None,
            'sentence_en': None,
            'words': []
        }
        current_time = 0.0

        # 1. Sentence Japanese audio
        sentence_ja_path = sentence.get('sentence_ja_audio')
        full_path = os.path.join(base_path, sentence_ja_path)
        audio = AudioSegment.from_mp3(full_path)
        duration = len(audio) / 1000.0
        audio_segments.append(audio)
        timeline_data['sentence_ja'] = {'start': current_time, 'end': current_time + duration}
        current_time += duration
        
        audio_segments.append(silence_minor)
        current_time += self.gap_minor

        # 2. Sentence English audio
        sentence_en_path = sentence.get('sentence_en_audio')
        full_path_en = os.path.join(base_path, sentence_en_path)
        audio = AudioSegment.from_mp3(full_path_en)
        duration = len(audio) / 1000.0
        audio_segments.append(audio)
        timeline_data['sentence_en'] = {'start': current_time, 'end': current_time + duration}
        current_time += duration
        
        audio_segments.append(silence_major)
        current_time += self.gap_major

        # 3. Word-level audio (JA and EN only)
        words = sentence.get('words', [])
        for word_idx, word in enumerate(words):
            word_timeline = { 'word_index': word_idx, 'word_ja': None, 'word_en': None }

            # Word JA
            word_ja_path = word.get('audio_ja_path')
            word_full_path = os.path.join(base_path, word_ja_path)
            audio = AudioSegment.from_mp3(word_full_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            word_timeline['word_ja'] = {'start': current_time, 'end': current_time + duration}
            current_time += duration
            
            audio_segments.append(silence_minor)
            current_time += self.gap_minor

            # Word EN
            word_en_path = word.get('audio_en_path')
            word_full_path = os.path.join(base_path, word_en_path)
            audio = AudioSegment.from_mp3(word_full_path)
            duration = len(audio) / 1000.0
            audio_segments.append(audio)
            word_timeline['word_en'] = {'start': current_time, 'end': current_time + duration}
            current_time += duration

            timeline_data['words'].append(word_timeline)
            
            if word_idx < len(words) - 1:
                audio_segments.append(silence_major)
                current_time += self.gap_major

        if not audio_segments:
            return

        combined_audio = sum(audio_segments)
        combined_audio.export(output_file, format="mp3")
        logger.debug(f"    Successfully saved fast mode packed audio to {output_file}")

        sentence['sentence_packed_fast_mode_audio'] = {
            'url': os.path.relpath(output_file, base_path),
            'duration': current_time,
            'timeline': timeline_data
        }