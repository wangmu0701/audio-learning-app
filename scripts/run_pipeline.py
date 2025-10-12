
import os
import json
from pipeline.stages.news_collection import NewsCollectionStage
from pipeline.stages.story_generation import StoryGenerationStage
from pipeline.stages.word_segmentation import WordSegmentationStage
from pipeline.stages.content_pedagogy import ContentPedagogyStage
from pipeline.stages.audio_generation import AudioGenerationStage
from pipeline.llm_provider import LLMProvider
from pipeline.tts_provider import TTSProvider
from pipeline.logger import get_logger

logger = get_logger(__name__)

from datetime import datetime

def get_run_output_dir():
    """Determines the output directory for the current run."""
    base_dir = "output"
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_dir = os.path.join(base_dir, today_str)
    
    os.makedirs(today_dir, exist_ok=True)
    
    existing_runs = [d for d in os.listdir(today_dir) if os.path.isdir(os.path.join(today_dir, d)) and d.startswith('R-')]
    next_run_id = 0
    if existing_runs:
        next_run_id = max(int(run[2:]) for run in existing_runs) + 1
        
    run_id_str = f"R-{next_run_id:04d}"
    run_dir = os.path.join(today_dir, run_id_str)
    os.makedirs(run_dir)
    
    return run_dir, today_str, run_id_str

def main():
    """
    Main function to run the entire content generation pipeline.
    """
    logger.info("============================================================")
    logger.info("Starting the full content generation pipeline")
    logger.info("============================================================")

    # Get the output directory for this run
    run_output_dir, today_str, run_id_str = get_run_output_dir()
    logger.info(f"Using output directory: {run_output_dir}")

    # Define configuration for each stage
    config = {
        "llm_model_name": "gemini-2.5-flash-lite",
        "output_base_dir": run_output_dir,
        "language": "ja",
        "number_of_stories": 1,
        "level": "N5",
        "grammar_group": 0,
        "story_id_prefix": f"{today_str}-{run_id_str}",
    }

    # Instantiate shared providers
    llm_provider = LLMProvider()
    tts_provider = TTSProvider()

    # Instantiate stages
    news_stage = NewsCollectionStage(config=config, llm_provider=llm_provider)
    story_gen_stage = StoryGenerationStage(config=config, llm_provider=llm_provider)
    word_segment_stage = WordSegmentationStage(config=config, llm_provider=llm_provider)
    content_pedagogy_stage = ContentPedagogyStage(config=config, llm_provider=llm_provider)
    audio_gen_stage = AudioGenerationStage(config=config, tts_provider=tts_provider)

    # Run the pipeline
    pipeline_stages = [story_gen_stage, word_segment_stage, content_pedagogy_stage, audio_gen_stage]
    try:
        logger.info("--- Stage 1: News Collection ---")
        date = datetime.now().strftime('%Y-%m-%d')
        stories = news_stage.process_all([])
        for i, stage in enumerate(pipeline_stages):
            logger.info(f"--- Stage {i+2}: {stage.stage_name.replace('_', ' ').title()} ---")
            stories = stage.process_all(stories)
            logger.info(f"Completed stage: {stage.stage_name} with {len(stories)} stories.")
     
    except Exception as e:
        logger.error(f"An error occurred during the pipeline execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()
