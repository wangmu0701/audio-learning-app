#!/usr/bin/env python3

from datetime import datetime
import json
import os

from pipeline.stages.news_collection import NewsCollectionStage
from pipeline.logger import setup_advanced_logging, get_logger

def main():
    # Setup logging first
    setup_advanced_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Testing News Collection Stage")
    logger.info("=" * 60)
    
    date = datetime.now().strftime('%Y-%m-%d')
    
    # Test Stage 1: News Collection
    # The stage is now self-contained and doesn't need a config object.
    config = {
        "llm_model_name": "gemini-2.5-flash-lite"
    }
    stage = NewsCollectionStage(config)
    news_items = stage.process(date)
    
    # Create output directory if it doesn't exist
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    # Save results
    output_file = os.path.join(output_dir, 'news_test.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=2)
    
    logger.info("Test completed!")
    logger.info(f"Results saved to: {output_file}")
    
    if news_items:
        logger.info("Summary:")
        logger.info(f"   Total news items: {len(news_items)}")
        
        # Count by topic
        topics = {}
        for item in news_items:
            topic = item.get('topic', 'Unknown')
            topics[topic] = topics.get(topic, 0) + 1
        
        logger.info("   Topics distribution:")
        for topic, count in topics.items():
            logger.info(f"      {topic}: {count}")
    else:
        logger.warning("No news items were generated.")

if __name__ == '__main__':
    main()