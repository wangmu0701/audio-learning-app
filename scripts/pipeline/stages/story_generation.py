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

    def __init__(self, config: Dict, llm_provider: LLMProvider):
        """Initializes the StoryGenerationStage."""
        super().__init__(config)
        if not llm_provider:
            raise ValueError("LLMProvider is required.")
        self.llm_provider = llm_provider

        self.target_grammar_points, self.previous_grammar_points = load_grammar(
            self.language, self.level, self.grammar_group
        )
        self.cumulative_grammar_points = self.target_grammar_points + self.previous_grammar_points

        if not self.cumulative_grammar_points:
            raise ValueError(f"No grammar points loaded for {self.language}-{self.level}, group {self.grammar_group}")

        self.grammar_point_map = {p.name: p for p in self.cumulative_grammar_points}

    @property
    def stage_name(self) -> str:
        return "story_generation"
    
    @property
    def language(self) -> str:
        return self.config.get('language', 'ja')
    
    @property
    def level(self) -> str:
        return self.config.get('level', 'N5')
    
    @property
    def grammar_group(self) -> Optional[int]:
        return self.config.get('grammar_group', None)

    def process(self, story: Dict) -> Dict:
        """
        Processes a single story idea to generate a story, then validates
        and augments the generated data.
        """
        idea = story
        logger.info(f"Generating story for idea: '{idea.get('title')}'")
        generated_story_data = self._generate_single_story(idea)

        # Post-processing and validation
        for sentence_data in generated_story_data.get("story_breakdown", []):
            validated_grammar_names = []
            short_names = []
            llm_grammar_points = sentence_data.get("grammar_points", [])

            for gp_name in llm_grammar_points:
                if gp_name in self.grammar_point_map:
                    validated_grammar_names.append(gp_name)
                    short_names.append(self.grammar_point_map[gp_name].short)
                else:
                    logger.warning(f"LLM generated an invalid grammar point: '{gp_name}' for sentence: '{sentence_data.get('sentence_ja')}'")
            
            sentence_data["grammar_points"] = validated_grammar_names
            sentence_data["grammar_points_short"] = short_names

        # Merge the original idea with the new, validated data
        idea.update(generated_story_data)
        return idea

    def _generate_single_story(self, story_idea: Dict) -> Dict:
        """Generates a single story using a structured, conditional prompt."""
        logger.debug(f"Targeting {len(self.target_grammar_points)} new grammar points and using {len(self.previous_grammar_points)} previous points.")

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
                                "description": "A list of the names of the grammar points from the provided lists that are used in this sentence.",
                                "items": {"type": "string"}
                            }
                        },
                        "required": ["sentence_ja", "sentence_en", "grammar_points"]
                    }
                }
            },
            "required": ["title_ja", "story_breakdown"]
        }

        prompt_parts = [
            "You are a creative writer for Japanese language learning content.",
            "Your task is to take a story idea, write a simple story, and provide a sentence-by-sentence breakdown.",
            f"\n**Story Idea:**",
            f"- Title: {story_idea.get('title')}",
            f"- Summary: {story_idea.get('summary')}",
        ]

        # Determine header and source names based on context
        if self.previous_grammar_points:
            target_header = f"**New Grammar Points (Group {self.grammar_group}):**"
            source_list_name = "the 'New Grammar Points' list"
        else:
            target_header = f"**Available Grammar Points (Group {self.grammar_group}):**"
            source_list_name = "the 'Available Grammar Points' list"

        if self.target_grammar_points:
            target_list_str = "\n".join([f"- {p.name}" for p in self.target_grammar_points])
            prompt_parts.append(f"\n{target_header}\n{target_list_str}")

        # Conditionally add previous grammar points section
        if self.previous_grammar_points:
            previous_list_str = "\n".join([f"- {p.name}" for p in self.previous_grammar_points])
            prompt_parts.append(f"\n**Previously Learned Grammar Points:**\n{previous_list_str}")

        # Build instructions dynamically
        instructions = [
            "\n**Instructions:**",
            "1. Translate the English **Title** into a suitable Japanese title.",
            f"2. Write a short, simple story (6-10 sentences) that is easy for a beginner {self.level} learner to understand.",
            f"3. **CRITICAL RULE: Every single sentence (`sentence_ja`) MUST use at least one grammar point from {source_list_name}.**",
        ]

        if self.previous_grammar_points:
            instructions.append("4. You may also use grammar from the 'Previously Learned Grammar Points' list to make the story natural.")
            final_instructions_start_num = 5
        else:
            final_instructions_start_num = 4

        instructions.extend([
            f"{final_instructions_start_num}. Break the story into individual sentences and create a JSON object for each, containing:",
            "   a. The Japanese sentence (`sentence_ja`).",
            "   b. A natural English translation (`sentence_en`).",
            "   c. A list of all grammar points used (`grammar_points`). The names MUST exactly match the provided lists (e.g., `Particle は (wa)`).",
            f"{final_instructions_start_num + 1}. Your entire output must be a single, valid JSON object, with no text outside the JSON structure.",
        ])
        prompt_parts.extend(instructions)

        prompt_parts.append(f'''\n**Output Schema and Example:**
            {{
            "title_ja": "Example Japanese Title",
            "story_breakdown": [
                {{
                "sentence_ja": "ケンさんはバスで学校に行きます。",
                "sentence_en": "Ken goes to school by bus.",
                "grammar_points": [
                    "Particle は (wa)",
                    "Particle で (de)",
                    "Verb form 〜ます (~masu)"
                ]
                }}
            ]
            }}
        ''')

        prompt = "\n".join(prompt_parts)

        generation_config = GenerationConfig(
            model_name=self.llm_model_name,
            temperature=0.7,
            max_tokens=30000,
            top_p=1.0,
            json_schema=story_schema
        )

        response_text = self.llm_provider.generate_response(prompt, generation_config)
        response_data = json.loads(response_text)
        return response_data