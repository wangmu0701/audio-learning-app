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

    def __init__(self, config: Dict, llm_provider: LLMProvider):
        """Initializes the ContentPedagogyStage."""
        super().__init__(config)
        logger.info("ContentPedagogyStage initialized.")
        if not llm_provider:
            raise ValueError("LLMProvider is required.")
        self.llm_provider = llm_provider

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
            You are an expert Japanese language teacher designing an audio-first learning course for absolute beginners (JLPT N5 level).
            Your task is to generate the pedagogical content (the English translation and a conversational explanation) for each word in a given Japanese sentence.

            **Guiding Principles for Explanations:**
            1.  **Audio-First & Conversational**: Use short, simple sentences. The tone should be friendly, patient, and encouraging, like a helpful guide.
            2.  **Assume Zero Knowledge**: Explain every concept simply. Avoid jargon.
            3.  **Context is King**: The explanation must relate to the word's function in the provided full sentence context.
            4.  **CRITICAL RULE: No Direct Quoting**: To ensure high-quality audio, your explanation text must be **purely in English**. Do NOT quote the Japanese word (e.g., 'yasai') or its Romaji (e.g., 'yasai') directly in the prose. Instead, refer to it conceptually.

            **Examples of "Conceptual Referencing" (Good vs. Bad):**
            -   **Word to explain:** `野菜` (yasai)
            -   **BAD (Direct Quote):** "The word 'yasai' means 'vegetables'."  <-- AVOID THIS.
            -   **GOOD (Conceptual Reference):** "This word means 'vegetables'. It's the noun that appeared right before the 'and' particle in the sentence."
            -   **GOOD (Conceptual Reference):** "The meaning of this word is 'vegetables.' In the story, this is one of the things everyone planted together."

            **Full Sentence Context:**
            -   Japanese: {sentence_ja}
            -   English: {sentence_en}

            **Focus Grammar Points for this Sentence:**
            {', '.join(grammar_points) if grammar_points else 'None'}

            **Words to Process:**
            {json.dumps(words_ja, ensure_ascii=False)} // This is an array of word objects, each with 'word_ja', 'word_romaji', 'position'

            **Instructions:**
            Your task is to add the 'word_en' and 'explanation' keys to each word object in the input array.
            1.  For each word object, add a **`word_en`** key. Its value should be the most accurate, concise English meaning for the word *in the context of this specific sentence*.
            2.  For each word object, add an **`explanation`** key. Its value should be a simple, conversational explanation following all the **Guiding Principles** above.
            3.  If a word is one of the "Focus Grammar Points," be sure to mention this in its explanation.
            4.  Your entire output must be a single JSON array of objects, strictly following the schema and example below. The output array must have the exact same number of items as the input "Words to Process" list.

            **Example**
            {{
                "word_pedagogy":
                    [
                        {{
                            "word_ja": "みんな",
                            "word_romaji": "minna",
                            "position": 0,
                            "word_en": "everyone",
                            "explanation": "This first word means 'everyone' or 'all'. It's a friendly way to talk about a group of people doing something together."
                        }},
                        {{
                            "word_ja": "で",
                            "word_romaji": "de",
                            "position": 3,
                            "word_en": "by / with",
                            "explanation": "Next up is a particle. In our sentence, it tells us that the action is being done 'by everyone' together. While this particle can also mark a location, here it's about the group performing the action."
                        }}
                    ]
            }}
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