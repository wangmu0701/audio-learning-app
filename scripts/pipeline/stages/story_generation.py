import sys
import os
import json
import random
from typing import List, Dict, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from pipeline.logger import get_logger
from pipeline.grammar import load_grammar, GrammarPoint
from pipeline.llm_provider import LLMProvider, GenerationConfig

logger = get_logger(__name__)

class StoryGenerationStage(PipelineStage):
    """
    Stage 2: Story Generation + Grammar Tagging.

    Takes story ideas and generates full Japanese stories, focusing on
    specific grammar points.
    """

    def __init__(self, config: Dict):
        """Initializes the StoryGenerationStage."""
        super().__init__(config)
        self.llm_provider = LLMProvider()
        self.grammar_points = load_grammar(self.language, self.level, self.grammar_group)
        if not self.grammar_points:
            raise ValueError(f"No grammar points loaded for {self.language}-{self.level}, group {self.grammar_group}")

    @property
    def language(self) -> str:
        return self.config.get('language', 'ja')
    
    @property
    def level(self) -> str:
        return self.config.get('level', 'N5')
    
    @property
    def grammar_group(self) -> Optional[int]:
        return self.config.get('grammar_group', None)
    
    def process(self, story_ideas: List[Dict]) -> List[Dict]:
        """
        Processes a list of story ideas to generate stories.
        """
        logger.info(f"StoryGenerationStage received {len(story_ideas)} ideas to process.")
        
        generated_stories = []
        for idea in story_ideas:
            try:
                logger.info(f"Generating story for idea: '{idea.get('title')}'")
                generated_story_data = self._generate_single_story(idea)
                # Merge the original idea with the new data
                idea.update(generated_story_data)
                generated_stories.append(idea)
            except Exception as e:
                logger.error(f"Failed to generate story for idea '{idea.get('title')}'. Error: {e}")
                # Optionally, skip this story and continue with the next
                continue

        logger.info(f"Successfully generated {len(generated_stories)} stories.")
        return generated_stories

    def _generate_single_story(self, story_idea: Dict) -> Dict:
        """Generates a single story, ensuring each sentence is tagged with grammar points from the full group list."""
        # 1. Use the full list of grammar points for the configured group
        logger.debug(f"Using {len(self.grammar_points)} grammar points from group {self.grammar_group}.")

        # 2. Define the JSON schema (remains the same)
        story_schema = {
            "type": "object",
            "properties": {
                "title_ja": {
                    "type": "string",
                    "description": "A translation of the original English story title into Japanese."
                },
                "story_breakdown": {
                    "type": "array",
                    "description": "An array where each object represents a sentence in the story.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "sentence_ja": {
                                "type": "string",
                                "description": "A single sentence of the story in Japanese."
                            },
                            "sentence_en": {
                                "type": "string",
                                "description": "A natural, fluent English translation of the Japanese sentence."
                            },
                            "grammar_points": {
                                "type": "array",
                                "description": "A list of the names of the grammar points from the provided list that are used in this sentence.",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["sentence_ja", "sentence_en", "grammar_points"]
                    }
                }
            },
            "required": ["title_ja", "story_breakdown"]
        }

        # 3. Construct the new, more robust prompt
        grammar_list_str = "\n".join([f"- {p.name}" for p in self.grammar_points])
        prompt = f"""
        You are a creative writer and translator for Japanese language learning content.
        Your task is to take a story idea, translate its title to Japanese, write a simple story, and then provide a sentence-by-sentence breakdown with translations.

        **Story Idea:**
        - Title: {story_idea.get('title')}
        - Summary: {story_idea.get('summary')}

        **Available N5 Grammar Points (Group {self.grammar_group}):**
        {grammar_list_str}

        **Instructions:**
        1.  First, translate the English story idea **Title** into a suitable Japanese title.
        2.  Write a short story in Japanese (6-10 sentences) based on the story idea.
        3.  For each sentence you write, you **must** try to use one or two grammar points from the **Available N5 Grammar Points** list.
        4.  Break the story into individual sentences.
        5.  For each sentence, create a JSON object containing:
            a. The Japanese sentence (`sentence_ja`).
            b. A natural, fluent English translation of the sentence (`sentence_en`).
            c. A list of the exact names of the grammar points you used in that sentence (`grammar_points`).
        6.  Your entire output must be a single JSON object that strictly follows the provided schema, containing the translated Japanese title (`title_ja`) and the sentence breakdown (`story_breakdown`).
        """

        # 4. Call the LLM
        generation_config = GenerationConfig(
            model_name=self.llm_model_name,
            temperature=0.7,
            max_tokens=4096,
            top_p=1.0,
            json_schema=story_schema
        )

        response_text = self.llm_provider.generate_response(prompt, generation_config)
        
        # 5. Parse and return the structured data
        if response_text.startswith('```json'):
            response_text = response_text[7:-3].strip()
        
        response_data = json.loads(response_text)
        return response_data
