import google.generativeai as genai
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
    """Stage 1: Generate news items using Gemini (without search for now)"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.lang_config = {
            'native': 'en',
            'learning': 'ja',
            'native_name': 'English',
            'learning_name': 'Japanese',
            'romanization': 'romaji',
        }
        self.llm_provider = LLMProvider()
    
    def process(self, date: str) -> List[Dict]:
        """
        Generate news-like items for the given date.
        
        Note: Currently generates content directly without real-time search.
        Can be upgraded to use Google Search grounding later.
        """
        logger.info(f"Generating news content for {date}...")
        logger.info(f"Language pair: {self.lang_config['native_name']} -> {self.lang_config['learning_name']}")
        logger.warning("Using direct generation (not real-time search)")
        
        native_lang = self.lang_config['native']
        summary_lang = "English" if native_lang == "en" else "Chinese"
        
        prompt = f"""
You are creating educational content for Japanese language learners.

Generate 5 interesting story ideas that would be good for Japanese language learners whose native language is {summary_lang}.
These should be based on typical Japanese news topics and everyday scenarios.
Cover diverse topics: technology, food, travel, culture, business, daily life, etc.

For each story idea, provide:
1. A catchy Japanese title (short, 5-10 characters)
2. A brief summary in {summary_lang} (2-3 sentences)
3. The main topic category (choose from: 科技 Technology, 食べ物 Food, 日常生活 Daily Life, 旅行 Travel, 文化 Culture, ビジネス Business)
4. A plausible URL (can be example.com)

Make the content realistic and educational. Stories should be appropriate for different JLPT levels.

Format your response as a JSON array like this:
[
  {{
    "title": "新しいロボット",
    "summary": "A Japanese company developed a new robot assistant for elderly care. The robot can help with daily tasks and provide companionship.",
    "topic": "科技 Technology",
    "url": "https://example.com/tech-news"
  }},
  ...
]

Return ONLY the JSON array, no other text before or after.
"""
        
        try:
            logger.info("Querying Gemini...")
            
            generation_config = GenerationConfig(
                model_name=self.llm_model_name,
                temperature=0.7,
                max_tokens=2048,
                top_p=1.0,
            )
            # Generate without search tools for now
            response = self.llm_provider.generate_response(prompt, generation_config)
            
            text = response.strip()
            
            # Remove markdown code blocks if present
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            news_items = json.loads(text)
            
            logger.info(f"Successfully generated {len(news_items)} story ideas.")
            
            if news_items:
                sample = news_items[0]
                logger.debug(f"Sample story idea: Title='{sample['title']}', Topic='{sample['topic']}'")

            return news_items
            
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON response: {e}")
            logger.error(f"Raw response text: {text}")
            raise
            
        except Exception as e:
            logger.error(f"An unexpected error occurred during content generation: {e}")
            if 'response' in locals():
                logger.error(f"LLM response object: {response}")
            raise