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

    Takes stories with Japanese sentences, breaks them down into words,
    and generates romaji for all text.
    """

    def __init__(self, config: Dict):
        """Initializes the WordSegmentationStage."""
        super().__init__(config)
        logger.info("WordSegmentationStage initialized.")
        self.llm_provider = LLMProvider()

    def process(self, stories: List[Dict]) -> List[Dict]:
        """
        Processes a list of stories to add word segmentation and romaji.
        """
        logger.info(f"WordSegmentationStage received {len(stories)} stories to process.")
        
        processed_stories = []
        for story in stories:
            try:
                if 'story_breakdown' not in story or not story['story_breakdown']:
                    logger.warning(f"Story '{story.get('title')}' has no breakdown. Skipping.")
                    continue

                for sentence in story['story_breakdown']:
                    words_with_romaji, sentence_romaji = self._process_sentence(sentence)
                    sentence['words'] = words_with_romaji
                    sentence['sentence_romaji'] = sentence_romaji
                    sentence.pop('tokens_ja', None)
                    sentence.pop('tokens_ja_pos', None)
                
                processed_stories.append(story)

            except Exception as e:
                logger.error(f"Dropping story '{story.get('title')}' due to processing error: {e}")
                continue
        
        return processed_stories

    def _process_sentence(self, sentence: Dict) -> Tuple[List[Dict], str]:
        """Orchestrates tokenization and romanization for a single sentence."""
        sentence_ja = sentence.get('sentence_ja', '')
        if not sentence_ja:
            return [], ""

        tokens_ja, tokens_pos = self._get_tokenization(sentence_ja, sentence.get('grammar_points', []))
        sentence_romaji, word_romaji_list = self._get_romanization(sentence_ja, tokens_ja)

        if len(tokens_ja) != len(word_romaji_list):
            raise ValueError(f"Mismatch between token count ({len(tokens_ja)}) and romaji count ({len(word_romaji_list)}).")

        words = []
        for i, token_ja in enumerate(tokens_ja):
            words.append({
                "word_ja": token_ja,
                "word_romaji": word_romaji_list[i],
                "position": tokens_pos[i]
            })
        
        return words, sentence_romaji

    def _get_tokenization(self, sentence_ja: str, grammar_points: List[str]) -> Tuple[List[str], List[int]]:
        """Calls an LLM to get N5-level tokenization for a sentence."""
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

        prompt = f"""
        You are an expert Japanese language teacher who specializes in creating learning materials for absolute beginners (JLPT N5 level).
        Your primary goal is to segment a Japanese sentence into "learning units" (tokens) that are easy for a beginner to understand as whole concepts.

        **Guiding Principle: "Pedagogical First, Not Linguistic"**
        This means you should prioritize how a beginner learns. Beginners learn full conjugated forms first, not word stems and endings. For example, they learn "tabemashita" (ate) as one complete idea. Do NOT perform pure morphological analysis.

        **Explicit Rules:**
        1.  **Keep Conjugations Whole:** Verbs and adjectives must be kept as a single token with their endings. Do NOT split endings like `~ます`, `~ました`, `~ません`, `~ませんでした`, `~かったです`, `~くないです` from the word stem.
        2.  **Isolate Particles:** Particles (e.g., `は`, `が`, `を`, `に`, `へ`, `で`, `の`, `と`, `も`) must always be their own separate tokens.
        3.  **Group Logical Compounds:** Keep logical noun phrases like names or compound words together (e.g., `田中さん`, `近所の人たち`).
        4.  **Exclude Punctuation:** Do not include any punctuation (e.g., '。', '、', '「', '」') as items in the output array.

        **Example of Correct vs. Incorrect Tokenization:**
        -   For the sentence `私はパンを食べました。`:
            -   **CORRECT (Pedagogical):** `["私", "は", "パン", "を", "食べました"]`
            -   **INCORRECT (Linguistic):** `["私", "は", "パン", "を", "食べ", "ました"]`  <-- AVOID THIS!

        **Task:**
        Tokenize the following sentence according to the rules and examples above.

        -   **Sentence to Tokenize:** `{sentence_ja}`

        Your output must be a single JSON object containing only a single key, `tokens_ja`, which is an array of the tokenized strings.
        """

        generation_config = GenerationConfig(
            model_name=self.llm_model_name,
            temperature=0.2,
            max_tokens=2048,
            top_p=1.0,
            json_schema=tokenization_schema
        )

        response_text = self.llm_provider.generate_response(prompt, generation_config)
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        response_data = json.loads(response_text)
        tokens = response_data['tokens_ja']

        # Validate tokens and get positions
        validated = True
        pos = 0
        tokens_pos = []
        PUNCTUATION_TO_SKIP = [' ', '　', '。', '、', '，', '？', '！', '「', '」', '『', '』', '（', '）']

        for token in tokens:
            while pos < len(sentence_ja) and sentence_ja[pos] in PUNCTUATION_TO_SKIP:
                pos += 1
            if sentence_ja.startswith(token, pos):
                tokens_pos.append(pos)
                pos += len(token)
            else:
                validated = False
                break
        
        while pos < len(sentence_ja) and validated:
            if sentence_ja[pos] in PUNCTUATION_TO_SKIP:
                pos += 1
            else:
                validated = False
                break

        if not validated:
            raise ValueError(f"Tokenization mismatch! Original: <{sentence_ja}>, Reconstructed: <{''.join(tokens)}>")

        return tokens, tokens_pos

    def _get_romanization(self, sentence_ja: str, tokens_ja: List[str]) -> Tuple[str, List[str]]:
        """Calls an LLM to get romaji for a sentence and its tokens."""
        romaji_schema = {
            "type": "object",
            "properties": {
                "sentence_romaji": {
                    "type": "string",
                    "description": "The Hepburn-style romanization of the entire sentence."
                },
                "word_romaji_list": {
                    "type": "array",
                    "description": "An array of romaji for each word in the provided token list.",
                    "items": {"type": "string"}
                }
            },
            "required": ["sentence_romaji", "word_romaji_list"]
        }

        prompt = f"""
        You are a Japanese-to-Romaji translation expert.
        Your task is to provide the standard Hepburn-style romanization for a Japanese sentence and its pre-tokenized words.

        **Sentence to Romanize:**
        {sentence_ja}

        **Tokens to Romanize:**
        {json.dumps(tokens_ja, ensure_ascii=False)}

        **Instructions:**
        1. Provide the romaji for the entire sentence.
        2. Provide the romaji for each individual token in the list.
        3. The number of items in your `word_romaji_list` must exactly match the number of tokens in the input list.
        4. Your output must be a single JSON object following the schema.
        """

        generation_config = GenerationConfig(
            model_name=self.llm_model_name,
            temperature=0.1, # Very low temp for deterministic output
            max_tokens=20480,
            top_p=1.0,
            json_schema=romaji_schema
        )

        response_text = self.llm_provider.generate_response(prompt, generation_config)
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        response_data = json.loads(response_text)

        sentence_romaji = response_data.get('sentence_romaji', '')
        word_romaji_list = response_data.get('word_romaji_list', [])

        if len(word_romaji_list) != len(tokens_ja):
            raise ValueError(f"Romanization mismatch: Got {len(word_romaji_list)} romaji words for {len(tokens_ja)} tokens.")

        return sentence_romaji, word_romaji_list