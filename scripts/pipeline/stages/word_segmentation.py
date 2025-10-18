import sys
import os
import json
import regex
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
    generates hiragana readings for correct pronunciation, and generates 
    romaji for all text.
    """

    def __init__(self, config: Dict, llm_provider: LLMProvider):
        """Initializes the WordSegmentationStage."""
        super().__init__(config)
        logger.info("WordSegmentationStage initialized.")
        if not llm_provider:
            raise ValueError("LLMProvider is required.")
        self.llm_provider = llm_provider

    @property
    def stage_name(self) -> str:
        return "word_segmentation"

    def process(self, story: Dict) -> Dict:
        """
        Processes a list of stories to add word segmentation and romaji.
        """
        for sentence in story['story_breakdown']:
            words_with_romaji, sentence_romaji = self._process_sentence(sentence)
            sentence['words'] = words_with_romaji
            sentence['sentence_romaji'] = sentence_romaji
            sentence.pop('tokens_ja', None)
            sentence.pop('tokens_ja_pos', None)
        return story

    def _process_sentence(self, sentence: Dict) -> Tuple[List[Dict], str]:
        """Orchestrates tokenization and romanization for a single sentence."""
        sentence_ja = sentence.get('sentence_ja', '')
        if not sentence_ja:
            return [], ""

        tokens_ja, tokens_hiragana, tokens_pos = self._get_tokenization(sentence_ja, sentence.get('grammar_points', []))
        sentence_romaji, word_romaji_list = self._get_romanization(sentence_ja, tokens_hiragana)

        if len(tokens_ja) != len(word_romaji_list):
            raise ValueError(f"Mismatch between token count ({len(tokens_ja)}) and romaji count ({len(word_romaji_list)}).")

        words = []
        for i, token_ja in enumerate(tokens_ja):
            words.append({
                "word_ja": token_ja,
                "word_hiragana": tokens_hiragana[i],
                "word_romaji": word_romaji_list[i],
                "position": tokens_pos[i]
            })
        
        return words, sentence_romaji

    def _get_tokenization(self, sentence_ja: str, grammar_points: List[str]) -> Tuple[List[str], List[str], List[int]]:
        """Calls an LLM to get N5-level tokenization with hiragana readings for a sentence."""
        tokenization_schema = {
            "type": "object",
            "properties": {
                "tokens": {
                    "type": "array",
                    "description": "The Japanese sentence tokenized into words with their hiragana readings.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "token_ja": {
                                "type": "string",
                                "description": "A single token from the sentence in its original form (kanji, hiragana, or katakana)."
                            },
                            "token_hiragana": {
                                "type": "string",
                                "description": "The hiragana reading representing the ACTUAL PRONUNCIATION of the token for TTS accuracy."
                            }
                        },
                        "required": ["token_ja", "token_hiragana"]
                    }
                }
            },
            "required": ["tokens"]
        }

        prompt = f"""
        You are an expert Japanese language teacher who specializes in creating learning materials for absolute beginners (JLPT N5 level).
        Your primary goal is to segment a Japanese sentence into "learning units" (tokens) that are easy for a beginner to understand as whole concepts, AND provide the correct hiragana reading for each token based on the sentence context.

        **CRITICAL: The hiragana output will be used for Text-to-Speech (TTS) generation, so it MUST represent the ACTUAL PRONUNCIATION, not just a character-by-character conversion.**

        **Guiding Principle: "Pedagogical First, Not Linguistic"**
        This means you should prioritize how a beginner learns. Beginners learn full conjugated forms first, not word stems and endings. For example, they learn "tabemashita" (ate) as one complete idea. Do NOT perform pure morphological analysis.

        **Explicit Rules for Tokenization:**
        1.  **Keep Conjugations Whole:** Verbs and adjectives must be kept as a single token with their endings. Do NOT split endings like `~ます`, `~ました`, `~ません`, `~ませんでした`, `~かったです`, `~くないです` from the word stem.
        2.  **Isolate Particles:** Particles (e.g., `は`, `が`, `を`, `に`, `へ`, `で`, `の`, `と`, `も`) must always be their own separate tokens.
        3.  **Group Logical Compounds:** Keep logical noun phrases like names or compound words together (e.g., `田中さん`, `近所の人たち`).
        4.  **Exclude Punctuation:** Do not include any punctuation (e.g., '。', '、', '「', '」') as items in the output array.

        **Explicit Rules for Hiragana Generation (CRITICAL FOR TTS):**
        1.  **Context-Based Reading:** Generate the hiragana reading based on how the word is ACTUALLY PRONOUNCED in this specific sentence.
        2.  **Convert Katakana to Hiragana:** For katakana words (外来語), convert them to hiragana. Example: `コーヒー` → `こーひー`
        3.  **Keep Most Hiragana As-Is:** For words already in hiragana, keep them the same UNLESS they are particles with special pronunciations (see next rule).
        4.  **CRITICAL - Particles with Special Pronunciations (for TTS accuracy):** 
            - The particle `は` is pronounced "wa", so output `わ` (NOT `は`)
            - The particle `を` is pronounced "o", so output `お` (NOT `を`)  
            - The particle `へ` is pronounced "e", so output `え` (NOT `へ`)
            - This is ESSENTIAL because TTS engines will read `は` as "ha", `を` as "wo", and `へ` as "he" if we don't convert them.
        5.  **Full Conversion:** Convert ALL kanji in the token to hiragana with correct readings. Example: `食べました` → `たべました`, `お母さん` → `おかあさん`
        6.  **Goal:** The `token_hiragana` output should represent the ACTUAL PRONUNCIATION for perfect TTS accuracy, not visual representation.

        **Example of Correct Tokenization and Hiragana (WITH PARTICLE CONVERSION):**
        -   For the sentence `私はコーヒーを飲みました。`:
            -   **CORRECT:**
```json
                {{
                    "tokens": [
                        {{"token_ja": "私", "token_hiragana": "わたし"}},
                        {{"token_ja": "は", "token_hiragana": "わ"}},
                        {{"token_ja": "コーヒー", "token_hiragana": "こーひー"}},
                        {{"token_ja": "を", "token_hiragana": "お"}},
                        {{"token_ja": "飲みました", "token_hiragana": "のみました"}}
                    ]
                }}
```
            -   **INCORRECT (will cause wrong TTS pronunciation):**
```json
                {{
                    "tokens": [
                        {{"token_ja": "私", "token_hiragana": "わたし"}},
                        {{"token_ja": "は", "token_hiragana": "は"}},  // WRONG! TTS will say "ha"
                        {{"token_ja": "コーヒー", "token_hiragana": "こーひー"}},
                        {{"token_ja": "を", "token_hiragana": "を"}},  // WRONG! TTS will say "wo"
                        {{"token_ja": "飲みました", "token_hiragana": "のみました"}}
                    ]
                }}
```

        **Task:**
        Tokenize the following sentence and provide hiragana readings for TTS accuracy according to the rules and examples above.

        -   **Sentence to Tokenize:** `{sentence_ja}`

        Your output must be a single JSON object containing only a single key, `tokens`, which is an array of objects with `token_ja` and `token_hiragana` fields.
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
        tokens_data = response_data['tokens']

        # Extract separate lists
        tokens_ja = [t['token_ja'] for t in tokens_data]
        tokens_hiragana = [t['token_hiragana'] for t in tokens_data]

        # Validate tokens by comparing cleaned-up strings
        original_cleaned = regex.sub(r'[\s\p{P}]+', '', sentence_ja)
        reconstructed_cleaned = ''.join(tokens_ja)
        if original_cleaned != reconstructed_cleaned:
            raise ValueError(f"Tokenization mismatch! Original: <{sentence_ja}>, Reconstructed: <{''.join(tokens_ja)}>")

        # Find token positions in the original sentence
        tokens_pos = []
        pos = 0
        for token in tokens_ja:
            try:
                token_pos = sentence_ja.index(token, pos)
                tokens_pos.append(token_pos)
                pos = token_pos + len(token)
            except ValueError:
                raise ValueError(f"Token '{token}' not found in sentence '{sentence_ja}' starting from position {pos}.")

        return tokens_ja, tokens_hiragana, tokens_pos

    def _get_romanization(self, sentence_ja: str, tokens_hiragana: List[str]) -> Tuple[str, List[str]]:
        """Calls an LLM to get romaji for a sentence and its hiragana tokens."""
        romaji_schema = {
            "type": "object",
            "properties": {
                "sentence_romaji": {
                    "type": "string",
                    "description": "The Hepburn-style romanization of the entire sentence."
                },
                "word_romaji_list": {
                    "type": "array",
                    "description": "An array of romaji for each hiragana token in the provided list.",
                    "items": {"type": "string"}
                }
            },
            "required": ["sentence_romaji", "word_romaji_list"]
        }

        prompt = f"""
        You are a Japanese-to-Romaji translation expert.
        Your task is to provide the standard Hepburn-style romanization for a Japanese sentence and its pre-tokenized hiragana words.

        **Sentence to Romanize:**
        {sentence_ja}

        **Hiragana Tokens to Romanize:**
        {json.dumps(tokens_hiragana, ensure_ascii=False)}

        **Instructions:**
        1. Provide the romaji for the entire sentence.
        2. Provide the romaji for each individual hiragana token in the list.
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

        if len(word_romaji_list) != len(tokens_hiragana):
            raise ValueError(f"Romanization mismatch: Got {len(word_romaji_list)} romaji words for {len(tokens_hiragana)} hiragana tokens.")

        return sentence_romaji, word_romaji_list