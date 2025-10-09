#!/usr/bin/env python3

from datetime import datetime
from config import CONFIG
from pipeline.stages.news_collection import NewsCollectionStage
import json

def main():
    print("=" * 60)
    print("Testing News Collection Stage")
    print("=" * 60)
    
    date = datetime.now().strftime('%Y-%m-%d')
    
    # Test Stage 1: News Collection
    stage = NewsCollectionStage(CONFIG)
    news_items = stage.process(date)
    
    # Create output directory if it doesn't exist
    import os
    os.makedirs('output', exist_ok=True)
    
    # Save results
    output_file = 'output/news_test.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Test completed!")
    print(f"📁 Results saved to: {output_file}")
    print(f"\n📊 Summary:")
    print(f"   Total news items: {len(news_items)}")
    
    # Count by topic
    topics = {}
    for item in news_items:
        topic = item['topic']
        topics[topic] = topics.get(topic, 0) + 1
    
    print(f"   Topics distribution:")
    for topic, count in topics.items():
        print(f"      {topic}: {count}")

if __name__ == '__main__':
    main()