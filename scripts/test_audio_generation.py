#!/usr/bin/env python3

import json
import os

from pipeline.stages.audio_generation import AudioGenerationStage
from pipeline.tts_provider import TTSProvider
from pipeline.logger import setup_advanced_logging, get_logger

def main():
    setup_advanced_logging()
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("Testing Audio Generation Stage")
    logger.info("=" * 60)

    input_file = 'output/content_pedagogy_test.json'
    output_file = 'output/audio_generation_test.json'

    # Read input
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            stories = json.load(f)
        logger.info(f"Successfully loaded {len(stories)} stories from {input_file}")
    except FileNotFoundError:
        logger.error(f"Input file not found: {input_file}")
        logger.error("Please run previous stages first to generate the input for this stage.")
        return
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {input_file}. The file might be corrupted or empty.")
        return

    if not stories:
        logger.warning("Input file contains no stories. Nothing to process.")
        return

    # Instantiate and run stage
    config = {
        "llm_model_name": "gemini-2.5-flash",
        "output_audio_dir": "output/audio"
    }
    tts_provider = TTSProvider()
    stage = AudioGenerationStage(config=config, tts_provider=tts_provider)
    processed_stories = stage.process(stories)
    
    # Save output
    os.makedirs('output', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_stories, f, ensure_ascii=False, indent=2)
    
    logger.info("Test completed!")
    logger.info(f"Results saved to: {output_file}")
    
    if processed_stories:
        logger.info(f"Processed {len(processed_stories)} stories.")
        first_story = processed_stories[0]
        logger.info(f"Example audio path for story '{first_story.get('title')}':")
        logger.info(f"  -> {first_story.get('audio_full_story_slow_path')}")
    else:
        logger.warning("The stage did not return any stories.")

if __name__ == '__main__':
    main()
