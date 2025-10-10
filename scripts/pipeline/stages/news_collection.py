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
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.llm_provider = LLMProvider()
    
    def process(self, date: str) -> List[Dict]:
        """
        Generates diverse, language-agnostic story ideas for the given date.
        The output (titles, summaries) is in English.
        """
        logger.info(f"Generating language-agnostic story ideas for {date}...")
        
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

Generate 5 interesting and diverse story ideas based on news, trends, or everyday scenarios.
The ideas should be simple, easy to visualize, and suitable for beginners.

Please format your response according to the provided JSON schema.
"""
        
        try:
            logger.info("Querying Gemini for story ideas with JSON schema...")
            
            generation_config = GenerationConfig(
                model_name=self.llm_model_name,
                temperature=0.8,
                max_tokens=20000,
                top_p=1.0,
                json_schema=story_ideas_schema
            )
            response = self.llm_provider.generate_response(prompt, generation_config)
            
            # Parse the JSON object and extract the list of story ideas
            story_ideas = json.loads(response.strip())["story_ideas"]
            
            logger.info(f"Successfully generated {len(story_ideas)} story ideas.")
            
            if story_ideas:
                sample = story_ideas[0]
                logger.debug(f"Sample story idea: Title='{sample.get('title')}'")

            return story_ideas
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response from LLM: {e}")
            logger.error(f"Raw response text: {text}")
            raise
            
        except (KeyError, TypeError) as e:
            logger.error(f"Error extracting 'story_ideas' from LLM response: {e}")
            logger.error(f"Parsed object: {text}")
            raise

        except Exception as e:
            logger.error(f"An unexpected error occurred during story idea generation: {e}")
            if 'response' in locals():
                logger.error(f"LLM response object: {response}")
            raise