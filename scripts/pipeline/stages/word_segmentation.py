import sys
import os
import json
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from pipeline.logger import get_logger
from pipeline.llm_provider import LLMProvider, GenerationConfig

logger = get_logger(__name__)

class WordSegmentationStage(PipelineStage):
    """
    Stage 3: Word Segmentation & Romanization.

    Takes stories with Japanese sentences and breaks them down into
    words using an LLM.
    """

    def __init__(self, config: Dict):
        """Initializes the WordSegmentationStage."""
        super().__init__(config)
        logger.info("WordSegmentationStage initialized.")
        self.llm_provider = LLMProvider()

    def process(self, stories: List[Dict]) -> List[Dict]:
        """
        Processes a list of stories to add word segmentation.
        """
        logger.info(f"WordSegmentationStage received {len(stories)} stories to process.")
        
        processed_stories = []
        for story in stories:
            try:
                if 'story_breakdown' not in story or not story['story_breakdown']:
                    logger.warning(f"Story '{story.get('title')}' has no breakdown. Skipping.")
                    continue

                for sentence in story['story_breakdown']:
                    tokens, tokens_pos = self._get_tokenization_for_sentence(sentence)
                    sentence['tokens_ja'] = tokens
                    sentence['tokens_ja_pos'] = tokens_pos
                
                # If we get here, all sentences in the story were processed successfully
                processed_stories.append(story)

            except ValueError as e:
                logger.error(f"Dropping story '{story.get('title')}' due to tokenization error: {e}")
                continue # Skip to the next story
        
        return processed_stories

    def _get_tokenization_for_sentence(self, sentence: Dict) -> Tuple[List[str], List[int]]:
        """Calls an LLM to get N5-level tokenization for a sentence."""
        sentence_ja = sentence.get('sentence_ja', '')
        if not sentence_ja:
            return []

        # 1. Define JSON Schema
        tokenization_schema = {
            "type": "object",
            "properties": {
                "tokens_ja": {
                    "type": "array",
                    "description": "The Japanese sentence tokenized into words appropriate for an N5 learner.",
                    "items": {"type": "string"}
                }
            },
            "required": ["tokens_ja"]
        }

        # 2. Construct Prompt
        grammar_points_info = ", ".join(sentence.get('grammar_points', []))
        prompt = f"""
        You are an expert in Japanese linguistics, specializing in teaching beginners (N5 level).
        Your task is to tokenize a Japanese sentence into meaningful words for a learner.

        **Sentence to Tokenize:**
        {sentence_ja}

        **Context:**
        This sentence focuses on the following N5 grammar points: {grammar_points_info}

        **Instructions:**
        1.  Tokenize the sentence into words (tokens) that are most logical for an N5 learner. For example, group particles with the word they modify where appropriate for beginners (e.g., 'は' might be separate), but keep verb stems and endings together.
        2.  **Do not include any punctuation** (e.g., '。', '、', '「', '」') as items in the `tokens_ja` array. The tokens should only be the words.
        3.  Your output must be a single JSON object that strictly follows the provided schema.
        """

        # 3. Call LLM
        generation_config = GenerationConfig(
            model_name=self.llm_model_name,
            temperature=0.2, # Low temperature for deterministic tokenization
            max_tokens=2048,
            top_p=1.0,
            json_schema=tokenization_schema
        )

        response_text = self.llm_provider.generate_response(prompt, generation_config)
        
        # 4. Parse and Return
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        
        response_data = json.loads(response_text)
        
        # 5. Validate that tokens reconstruct the sentence
        validated = True
        pos = 0
        tokens_pos = []
        # Define a comprehensive list of punctuation and whitespace to skip
        PUNCTUATION_TO_SKIP = [' ', '　', '。', '、', '，', '？', '！', '「', '」', '『', '』', '（', '）']

        for token in response_data['tokens_ja']:
            # Skip any leading punctuation before this token
            while pos < len(sentence_ja) and sentence_ja[pos] in PUNCTUATION_TO_SKIP:
                pos += 1
            
            # Now, check if the token starts at the current position
            if sentence_ja.startswith(token, pos):
                tokens_pos.append(pos)
                pos += len(token)
            else:
                # Mismatch found
                validated = False
                break
        
        # After checking all tokens, ensure the rest of the sentence is only skippable characters
        while pos < len(sentence_ja) and validated:
            if sentence_ja[pos] in PUNCTUATION_TO_SKIP:
                pos += 1
            else:
                validated = False
                break

        if not validated:
            raise ValueError(f"Tokenization mismatch! Original: <{sentence_ja}>, Reconstructed: <{''.join(response_data['tokens_ja'])}>",)

        return response_data['tokens_ja'], tokens_pos