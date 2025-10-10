#!/usr/bin/env python3

import json
import os

from pipeline.stages.word_segmentation import WordSegmentationStage
from pipeline.logger import setup_advanced_logging, get_logger

def main():
    # Setup logging first
    setup_advanced_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Testing Word Segmentation Stage")
    logger.info("=" * 60)

    input_file = 'output/stories_test.json'
    output_file = 'output/word_segmentation_test.json'

    # 1. Read stories from the output of the previous stage
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            stories = json.load(f)
        logger.info(f"Successfully loaded {len(stories)} stories from {input_file}")
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run test_stories.py first to generate the input for this stage.")
        return
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {input_file}. The file might be corrupted or empty.")
        return

    if not stories:
        logger.warning("Input file contains no stories. Nothing to process.")
        return

    # 2. Instantiate and run the WordSegmentationStage
    config = {
        "llm_model_name": "gemini-2.5-flash"
    }
    stage = WordSegmentationStage(config=config)
    processed_stories = stage.process(stories)
    
    # 3. Save the results
    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_stories, f, ensure_ascii=False, indent=2)
    
    logger.info("Test completed!")
    logger.info(f"Results saved to: {output_file}")
    
    # 4. Log a summary
    if processed_stories:
        logger.info(f"Processed {len(processed_stories)} stories.")
        for story in processed_stories:
            title = story.get('title', '[No Title]')
            breakdown = story.get('story_breakdown', [])
            if breakdown:
                first_sentence = breakdown[0]
                sentence_romaji = first_sentence.get('sentence_romaji', '')
                words = first_sentence.get('words', [])
                logger.info(f"  - '{title}': First sentence romaji: '{sentence_romaji}'")
                if words:
                    logger.info(f"    First word: {words[0]}")
    else:
        logger.warning("The stage did not return any stories.")

if __name__ == '__main__':
    main()
