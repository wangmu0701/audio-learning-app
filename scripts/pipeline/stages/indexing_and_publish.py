import sys
import os
import json
import shutil
import re
from typing import List, Dict, Tuple, Set
from datetime import datetime, timezone

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from pipeline.logger import get_logger

try:
    from pydub import AudioSegment
except ImportError:
    AudioSegment = None

logger = get_logger(__name__)

class IndexingAndPublishStage(PipelineStage):
    """
    Stage 8: Indexing and Publish.
    
    Reorganizes generated stories into a final, app-ready format. This stage
    is idempotent and can be re-run safely. It prevents duplicate stories
    and cleans up after itself in case of errors.
    """
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.output_dir = config.get('publish_output_dir', 'app_assets')
        self.story_counters = {}

    @property
    def stage_name(self) -> str:
        return "indexing_and_publish"
    @property
    def difficulty(self) -> str:
        return self.config.get('level', 'N5')

    @property
    def grammar_group(self) -> int:
        return self.config.get('grammar_group', 0)

    def _initialize_from_index(self) -> Set[Tuple[str, str]]:
        """Loads existing index, initializes counters, and returns existing story keys."""
        index_path = os.path.join(self.output_dir, 'index.json')
        existing_keys = set()

        if not os.path.exists(index_path):
            return existing_keys

        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not read or parse {index_path}. Assuming no existing stories.")
            return existing_keys

        for story_meta in index_data.get('stories', []):
            # Add key for de-duplication
            title = story_meta.get('title')
            difficulty = story_meta.get('difficulty')
            if title and difficulty:
                existing_keys.add((title, difficulty))

            # Update counters to avoid re-using IDs
            story_id = story_meta.get('id', '')
            # Match against the new format, e.g., N5_G0_001
            match = re.match(r"([A-Z0-9]+)_G(\d+)_(\d+)", story_id)
            if match:
                difficulty_from_id = match.group(1)
                group_from_id, num_from_id = int(match.group(2)), int(match.group(3))
                counter_key = (difficulty_from_id, group_from_id)
                current_max = self.story_counters.get(counter_key, 0)
                self.story_counters[counter_key] = max(current_max, num_from_id)
        
        logger.info(f"Initialized from existing index: Found {len(existing_keys)} stories and updated counters.")
        return existing_keys


    def process(self, input_story: Dict) -> Dict:
        raise NotImplementedError("This stage processes multiple stories at once. Use process_all instead.")


    def process_all(self, input_stories: List[Dict]) -> List[Dict]:
        """
        Processes all stories, skipping duplicates, and handling errors gracefully.
        """
        logger.info(f"Starting indexing and publish stage for {len(input_stories)} stories.")
        os.makedirs(os.path.join(self.output_dir, 'stories'), exist_ok=True)
        
        existing_story_keys = self._initialize_from_index()
        print(f'Existing stories in index: {existing_story_keys}')
        index_metadata_list = []
        for story in input_stories:
            story_title = story.get('title')
            story_difficulty = self.difficulty

            print(f'Processing story: {story_title} at difficulty {story_difficulty}')
            # 1. Prevent Duplicates
            if (story_title, story_difficulty) in existing_story_keys:
                logger.info(f"Skipping already published story: '{story_title}' (Difficulty {story_difficulty})")
                continue

            # 2. Generate ID before processing
            app_story_id = self._generate_story_id()
            target_story_path = os.path.join(self.output_dir, 'stories', app_story_id)

            # 3. Process story and handle errors
            result = self._process_single_story(story, app_story_id, target_story_path)

            if isinstance(result, Exception):
                logger.error(f"Failed to process story '{story_title}': {result}", exc_info=False)
                logger.info(f"Cleaning up failed story directory: {target_story_path}")
                shutil.rmtree(target_story_path, ignore_errors=True)
            else:
                logger.info(f"Successfully processed and published story: {app_story_id}")
                index_metadata_list.append(result)

        if not index_metadata_list:
            logger.info("No new stories to publish.")

        self._update_index_json(index_metadata_list)
        return index_metadata_list

    def _process_single_story(self, story: Dict, app_story_id: str, target_story_path: str) -> Dict:
        """Processes a single story. Returns index metadata on success or Exception on failure."""
        try:
            # Aggregate, clean, copy, and save
            self._aggregate_metadata(story)
            story['story_id'] = app_story_id
            published_story_data = self._clean_story_data(story)
            
            os.makedirs(target_story_path, exist_ok=True)
            self._copy_audio_files(story['output_path'], target_story_path)
            
            story_json_path = os.path.join(target_story_path, 'story.json')
            with open(story_json_path, 'w', encoding='utf-8') as f:
                json.dump(published_story_data, f, ensure_ascii=False, indent=2)

            # Return metadata for the index
            return {
                "id": app_story_id,
                "folder": os.path.join('stories', app_story_id),
                "title_ja": story.get('title_ja'),
                "title": story.get('title'),
                "summary": story.get('summary'),
                "difficulty": self.difficulty,
                "grammar_group": self.grammar_group,
                "grammar_points": story.get('grammar_points'),
                "topics": story.get('topics', []),
                "duration_seconds": story.get('duration_seconds'),
                "duration_fast_mode_seconds": story.get('duration_fast_mode_seconds'),
                "sentence_count": story.get('sentence_count'),
                "word_count": story.get('word_count')
            }
        except Exception as e:
            return e

    def _generate_story_id(self) -> str:
        """Generates a unique, app-friendly story ID like 'N5_G0_001'."""
        difficulty = self.difficulty.upper()
        group = self.grammar_group
        counter_key = (difficulty, group)
        count = self.story_counters.get(counter_key, 0) + 1
        self.story_counters[counter_key] = count
        return f"{difficulty}_G{group}_{count:03d}"

    def _aggregate_metadata(self, story: Dict):
        """Calculates and adds story-level metadata."""
        all_grammar, total_duration, total_words = set(), 0.0, 0
        source_path = story.get('output_path')

        if AudioSegment and source_path:
            for key, dur_key in [('full_story_slow', 'audio_full_story_slow_duration'), 
                                 ('full_story_normal', 'audio_full_story_normal_duration'), 
                                 ('full_story_translation', 'audio_full_story_translation_duration')]:
                path, duration = os.path.join(source_path, 'audio', f'{key}.mp3'), 0.0
                if os.path.exists(path):
                    try: duration = len(AudioSegment.from_mp3(path)) / 1000.0
                    except Exception as e: logger.warning(f"Could not read duration from {path}: {e}")
                else: logger.warning(f"Audio file not found: {path}")
                story[dur_key] = duration
                total_duration += duration

        fast_mode_duration = story.get('audio_full_story_normal_duration', 0.0) + \
                             story.get('audio_full_story_translation_duration', 0.0)

        for sentence in story.get('story_breakdown', []):
            all_grammar.update(sentence.get('grammar_points_short', []))
            total_duration += sentence.get('sentence_packed_audio', {}).get('duration', 0.0)
            fast_mode_duration += sentence.get('sentence_packed_fast_mode_audio', {}).get('duration', 0.0)
            total_words += len(sentence.get('words', []))
            
        story['grammar_points'] = sorted(list(all_grammar))
        story['duration_seconds'] = round(total_duration)
        story['duration_fast_mode_seconds'] = round(fast_mode_duration)
        story['sentence_count'] = len(story.get('story_breakdown', []))
        story['word_count'] = total_words

    def _clean_story_data(self, story: Dict) -> Dict:
        """
        Cleans the story object by removing temporary runtime fields and simplifying
        the audio timeline for the final app asset.
        """
        # Create a deep copy to avoid modifying the original story object in-place.
        published_story_data = json.loads(json.dumps(story))

        # 1. Remove top-level 'status' field
        if 'status' in published_story_data:
            del published_story_data['status']

        # 2. Clean up the word timeline in sentence_packed_audio
        if 'story_breakdown' in published_story_data:
            for sentence in published_story_data.get('story_breakdown', []):
                if 'sentence_packed_audio' in sentence and \
                   'timeline' in sentence['sentence_packed_audio'] and \
                   'words' in sentence['sentence_packed_audio']['timeline']:
                    
                    original_words_timeline = sentence['sentence_packed_audio']['timeline']['words']
                    cleaned_words_timeline = []
                    
                    for word_timeline in original_words_timeline:
                        if all(k in word_timeline for k in ['word_index', 'word_ja', 'explanation']) and \
                           'start' in word_timeline['word_ja'] and 'end' in word_timeline['explanation']:
                            
                            cleaned_words_timeline.append({
                                'word_index': word_timeline['word_index'],
                                'start': word_timeline['word_ja']['start'],
                                'end': word_timeline['explanation']['end']
                            })
                    
                    sentence['sentence_packed_audio']['timeline']['words'] = cleaned_words_timeline

        # 3. Ensure difficulty and grammar_group are set from the current run's config
        published_story_data['difficulty'] = self.difficulty
        published_story_data['grammar_group'] = self.grammar_group

        return published_story_data

    def _copy_audio_files(self, source_story_path: str, target_story_path: str):
        """Recursively copies the entire audio directory for a story."""
        source_audio_dir = os.path.join(source_story_path, 'audio')
        target_audio_dir = os.path.join(target_story_path, 'audio')
        if not os.path.isdir(source_audio_dir): return
        if os.path.isdir(target_audio_dir): shutil.rmtree(target_audio_dir)
        shutil.copytree(source_audio_dir, target_audio_dir)

    def _update_index_json(self, stories_metadata: List[Dict]):
        """Loads, updates, and saves the global index.json."""
        index_path = os.path.join(self.output_dir, 'index.json')
        index_data = {"version": "1.0.0", "stories": []}
        if os.path.exists(index_path):
            try:
                with open(index_path, 'r', encoding='utf-8') as f: index_data = json.load(f)
            except json.JSONDecodeError: logger.warning(f"Could not decode {index_path}. A new one will be created.")

        existing_stories = {s['id']: s for s in index_data.get('stories', [])}
        for new_meta in stories_metadata: existing_stories[new_meta['id']] = new_meta
            
        index_data['stories'] = sorted(list(existing_stories.values()), key=lambda s: s['id'])
        index_data['last_updated'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        index_data['total_stories'] = len(index_data['stories'])
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Successfully updated index.json at {index_path}.")
