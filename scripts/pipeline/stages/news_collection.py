from typing import List, Dict
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from pipeline.llm_provider import LLMProvider, GenerationConfig
from pipeline.logger import get_logger

logger = get_logger(__name__)

class NewsCollectionStage(PipelineStage):
    """Stage 1: Generate language-agnostic story ideas in English."""
    
    def __init__(self, config: Dict, llm_provider: LLMProvider):
        super().__init__(config)
        if not llm_provider:
            raise ValueError("LLMProvider is required.")
        self.llm_provider = llm_provider
        if 'output_base_dir' not in config:
            raise ValueError("Configuration must include 'output_base_dir'.")
    
    @property
    def stage_name(self) -> str:
        return "news_collection"
    
    @property
    def number_of_stories(self) -> int:
        return self.config.get('number_of_stories', 1)
    
    @property
    def output_base_dir(self) -> str:
        return self.config.get('output_base_dir', None)

    def process(self, input_story: Dict) -> Dict:
        raise NotImplementedError("This stage processes multiple stories at once. Use process_all instead.")

    def process_all(self, input_stories) -> List[Dict]:
        """
        Generates diverse, language-agnostic story ideas for the given date.
        The output (titles, summaries) is in English.
        """
        logger.info(f"Generating language-agnostic story ideas.")
        
        story_ideas_schema = {
            "type": "object",
            "properties": {
                "story_ideas": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "A short, catchy title in English."
                            },
                            "summary": {
                                "type": "string",
                                "description": "A brief summary in English (2-3 sentences)."
                            }
                        },
                        "required": ["title", "summary"]
                    }
                }
            },
            "required": ["story_ideas"]
        }

        prompt = f"""
You are creating educational content for language learners.

Generate {self.number_of_stories} interesting and diverse story ideas based on news, trends, or everyday scenarios.
The ideas should be simple, easy to visualize, and suitable for beginners.

Please format your response according to the provided JSON schema.
"""
        
        try:
            logger.info("Querying Gemini for story ideas with JSON schema...")
            
            generation_config = GenerationConfig(
                model_name=self.llm_model_name,
                temperature=0.8,
                max_tokens=60000,
                top_p=1.0,
                json_schema=story_ideas_schema
            )
            response = self.llm_provider.generate_response(prompt, generation_config)
            
            # Parse the JSON object and extract the list of story ideas
            story_ideas = json.loads(response.strip())["story_ideas"]
            
            # Add story_id to each story
            story_id_prefix = self.config["story_id_prefix"]
            for i, story in enumerate(story_ideas):
                story["story_id"] = f"{story_id_prefix}-{i:02d}"
                story["output_path"] = os.path.join(self.output_base_dir, f"S-{i:02d}")
                os.makedirs(story["output_path"], exist_ok=True)
                story["status"] = {
                    self.stage_name: True,
                }

            logger.info(f"Successfully generated {len(story_ideas)} story ideas.")
            
            if story_ideas:
                sample = story_ideas[0]
                logger.debug(f"Sample story idea: Title='{sample.get('title')}'")

            return story_ideas
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from LLM: {e}")
            logger.error(f"Raw response text: {response}")
            raise
            
        except (KeyError, TypeError) as e:
            logger.error(f"Error extracting 'story_ideas' from LLM response: {e}")
            logger.error(f"Parsed object: {response}")
            raise

        except Exception as e:
            logger.error(f"An unexpected error occurred during story idea generation: {e}")
            if 'response' in locals():
                logger.error(f"LLM response object: {response}")
            raise