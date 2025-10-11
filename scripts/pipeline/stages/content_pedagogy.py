import sys
import os
import json
from typing import List, Dict

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from pipeline.logger import get_logger
from pipeline.llm_provider import LLMProvider, GenerationConfig

logger = get_logger(__name__)

class ContentPedagogyStage(PipelineStage):
    """
    Stage 4 & 5 Combined: Content Pedagogy.

    Generates translations and explanations for each word in a story.
    """

    def __init__(self, config: Dict):
        """Initializes the ContentPedagogyStage."""
        super().__init__(config)
        logger.info("ContentPedagogyStage initialized.")
        self.llm_provider = LLMProvider()

    def process(self, stories: List[Dict]) -> List[Dict]:
        """
        Processes stories to add word-level translations and explanations.
        """
        logger.info(f"ContentPedagogyStage received {len(stories)} stories to process.")

        for story in stories:
            if 'story_breakdown' not in story or not story['story_breakdown']:
                logger.warning(f"Story '{story.get('title')}' has no breakdown. Skipping.")
                continue

            for sentence in story['story_breakdown']:
                try:
                    pedagogy_data = self._get_pedagogy_for_sentence(sentence)
                    
                    # Merge pedagogy data back into the original words list
                    original_words = sentence.get('words', [])
                    if len(original_words) != len(pedagogy_data):
                        raise ValueError("Mismatch between original word count and pedagogy data count.")

                    for i, word_obj in enumerate(original_words):
                        word_obj.update(pedagogy_data[i])

                except Exception as e:
                    logger.error(f"Failed to generate pedagogy for sentence: '{sentence.get('sentence_ja')}'. Error: {e}")
                    # Mark words as unprocessed
                    for word_obj in sentence.get('words', []):
                        word_obj['word_en'] = ""
                        word_obj['explanation'] = "ERROR: Generation failed."
        
        return stories

    def _get_pedagogy_for_sentence(self, sentence: Dict) -> List[Dict]:
        """Generates translation and explanation for all words in a sentence."""
        
        # 1. Prepare context for the prompt
        sentence_ja = sentence.get('sentence_ja', '')
        sentence_en = sentence.get('sentence_en', '')
        grammar_points = sentence.get('grammar_points', [])
        words_ja = [word.get('word_ja', '') for word in sentence.get('words', [])]

        if not all([sentence_ja, sentence_en, words_ja]):
            logger.warning("Sentence object is missing required data for pedagogy generation.")
            return []

        # 2. Define JSON Schema
        pedagogy_schema = {
            "type": "object",
            "properties": {
                "word_pedagogy": {
                    "type": "array",
                    "description": "An array containing the English translation and explanation for each Japanese word provided.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "word_en": {
                                "type": "string",
                                "description": "The contextual English translation of the Japanese word."
                            },
                            "explanation": {
                                "type": "string",
                                "description": "A conversational, audio-friendly explanation of the word, its usage, and relevant grammar."
                            }
                        },
                        "required": ["word_en", "explanation"]
                    }
                }
            },
            "required": ["word_pedagogy"]
        }

        # 3. Construct Prompt
        prompt = f"""
        You are an expert Japanese teacher creating audio-first learning content for absolute beginners (N5 level).
        Your task is to provide a contextual translation and a simple, conversational explanation for each word in a given sentence.

        **Full Sentence Context:**
        - Japanese: {sentence_ja}
        - English: {sentence_en}

        **Focus Grammar Points for this Sentence:**
        {', '.join(grammar_points) if grammar_points else 'None'}

        **Words to Process:**
        {json.dumps(words_ja, ensure_ascii=False)}

        **Instructions:**
        For each word in the "Words to Process" list, provide its English meaning and a pedagogical explanation.
        1.  **word_en**: Provide the most accurate English meaning for the word *in the context of this specific sentence*.
        2.  **explanation**: Provide a simple, conversational explanation suitable for an audio lesson. It should be friendly and easy to understand for someone with zero Japanese knowledge. If the word relates to one of the focus grammar points, mention it. Keep it concise (10-30 seconds of speaking time).
        3.  Your output must be a single JSON object. The `word_pedagogy` array must have the exact same number of items as the input `Words to Process` list.
        """

        # 4. Call LLM
        generation_config = GenerationConfig(
            model_name=self.llm_model_name,
            temperature=0.4,
            max_tokens=4096,
            top_p=1.0,
            json_schema=pedagogy_schema
        )

        response_text = self.llm_provider.generate_response(prompt, generation_config)
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        response_data = json.loads(response_text)

        pedagogy_list = response_data.get('word_pedagogy', [])
        if len(pedagogy_list) != len(words_ja):
            raise ValueError(f"Pedagogy mismatch: Got {len(pedagogy_list)} results for {len(words_ja)} words.")

        return pedagogy_list