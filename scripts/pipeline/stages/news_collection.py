import google.generativeai as genai
from typing import List
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from pipeline.base import PipelineStage
from config import get_language_config

class NewsCollectionStage(PipelineStage):
    """Stage 1: Generate news items using Gemini (without search for now)"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        api_key = config['gemini']['api_key']
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(config['gemini']['model'])
        self.lang_config = get_language_config()
    
    def process(self, date: str) -> List[dict]:
        """
        Generate news-like items for the given date.
        
        Note: Currently generates content directly without real-time search.
        Can be upgraded to use Google Search grounding later.
        """
        print(f"\n🔍 Generating news content for {date}...")
        print(f"📚 Language pair: {self.lang_config['native_name']} -> {self.lang_config['learning_name']}")
        print(f"⚠️  Note: Using direct generation (not real-time search)")
        
        native_lang = self.lang_config['native']
        summary_lang = "English" if native_lang == "en" else "Chinese"
        
        prompt = f"""
You are creating educational content for Japanese language learners.

Generate 10 interesting story ideas that would be good for Japanese language learners whose native language is {summary_lang}.
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
            print("🤖 Querying Gemini...")
            
            # Generate without search tools for now
            response = self.model.generate_content(prompt)
            
            text = response.text.strip()
            
            # Remove markdown code blocks if present
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            text = text.strip()
            
            news_items = json.loads(text)
            
            print(f"✅ Generated {len(news_items)} story ideas")
            
            if news_items:
                print(f"\n📰 Sample story idea:")
                print(f"   Title: {news_items[0]['title']}")
                print(f"   Topic: {news_items[0]['topic']}")
                print(f"   Summary: {news_items[0]['summary'][:80]}...")
            
            return news_items
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON response: {e}")
            print(f"Raw response:\n{text}")
            raise
            
        except Exception as e:
            print(f"❌ Error generating content: {e}")
            if 'response' in locals():
                try:
                    print(f"Response text: {response.text}")
                except:
                    print(f"Response: {response}")
            raise