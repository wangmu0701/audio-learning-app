import os
import json
import argparse
from typing import Tuple, List, Dict
from datetime import datetime

from pipeline.stages.news_collection import NewsCollectionStage
from pipeline.stages.story_generation import StoryGenerationStage
from pipeline.stages.word_segmentation import WordSegmentationStage
from pipeline.stages.content_pedagogy import ContentPedagogyStage
from pipeline.stages.audio_generation import AudioGenerationStage
from pipeline.stages.audio_package import AudioPackageStage
from pipeline.stages.indexing_and_publish import IndexingAndPublishStage
from pipeline.llm_provider import LLMProvider
from pipeline.tts_provider import TTSProvider
from pipeline.logger import get_logger

logger = get_logger(__name__)

def get_run_output_dir() -> Tuple[str, str, str]:
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

def load_existing_run(resume_id: str) -> Tuple[str, List[Dict]]:
    """
    Load all stories from an existing run.
    
    Args:
        resume_id: Format "YYYY-MM-DD/R-XXXX"
    
    Returns:
        Tuple of (run_output_dir, list of story objects)
    """
    run_output_dir = os.path.join("output", resume_id)
    
    if not os.path.exists(run_output_dir):
        raise ValueError(f"Resume ID not found: {resume_id}")
    
    # Find all story directories (S-00, S-01, etc.)
    story_dirs = sorted([d for d in os.listdir(run_output_dir) 
                         if os.path.isdir(os.path.join(run_output_dir, d)) 
                         and d.startswith('S-')])
    
    stories = []
    for story_dir in story_dirs:
        output_json = os.path.join(run_output_dir, story_dir, "output.json")
        if os.path.exists(output_json):
            with open(output_json, 'r', encoding='utf-8') as f:
                story = json.load(f)
                stories.append(story)
        else:
            logger.warning(f"No output.json found in {story_dir}, skipping")
    
    logger.info(f"Loaded {len(stories)} stories from {resume_id}")
    return run_output_dir, stories


def main():
    """
    Main function to run the entire content generation pipeline.
    Supports both new runs and resuming from existing runs.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Content Generation Pipeline')
    parser.add_argument('--resume_id', type=str, default=None,
                       help='Resume from existing run (format: YYYY-MM-DD/R-XXXX)')
    parser.add_argument('--number_of_stories', type=int, default=1,
                       help='The number of stories to generate (only for new runs)')
    args = parser.parse_args()
    
    logger.info("============================================================")
    logger.info("Starting the full content generation pipeline")
    logger.info("============================================================")

    # Instantiate shared providers
    llm_provider = LLMProvider()
    tts_provider = TTSProvider()
    config = {
        "llm_model_name": "gemini-2.5-flash",
        "language": "ja",
        "level": "N5",
        "grammar_group": 0,
        "audio_gap_major": 1.0,  # Major transitions (word-to-word, sentence-to-word)
        "audio_gap_minor": 0.5,  # Minor transitions (within word explanation)
        "publish_output_dir": "app_assets",
    }
    # Determine if this is a new run or resume
    if args.resume_id:
        # RESUME MODE
        logger.info(f"RESUME MODE: Loading existing run {args.resume_id}")
        run_output_dir, stories = load_existing_run(args.resume_id)
        logger.info(f"Using output directory: {run_output_dir}")
        config.update({
            "output_base_dir": run_output_dir,
        })
    else:
        # NEW RUN MODE
        logger.info("NEW RUN MODE: Creating new run")
        run_output_dir, today_str, run_id_str = get_run_output_dir()
        logger.info(f"Using output directory: {run_output_dir}")

        # Define configuration for new run
        config.update({
            "output_base_dir": run_output_dir,
            "number_of_stories": args.number_of_stories,
            "story_id_prefix": f"{today_str}-{run_id_str}",
        })

        # Stage 1: News Collection (only for new runs)
        logger.info("--- Stage 1: News Collection ---")
        news_stage = NewsCollectionStage(config=config, llm_provider=llm_provider)
        stories = news_stage.process_all([])
        logger.info(f"Generated {len(stories)} story ideas.")

    # Instantiate pipeline stages (2-7)
    story_gen_stage = StoryGenerationStage(config=config, llm_provider=llm_provider)
    word_segment_stage = WordSegmentationStage(config=config, llm_provider=llm_provider)
    content_pedagogy_stage = ContentPedagogyStage(config=config, llm_provider=llm_provider)
    audio_gen_stage = AudioGenerationStage(config=config, tts_provider=tts_provider)
    audio_package_stage = AudioPackageStage(config=config)
    indexing_and_publish_stage = IndexingAndPublishStage(config=config)

    pipeline_stages = [
        story_gen_stage, 
        word_segment_stage, 
        content_pedagogy_stage, 
        audio_gen_stage,
        audio_package_stage,
        indexing_and_publish_stage
    ]
    
    # Run the main pipeline stages
    try:
        for i, stage in enumerate(pipeline_stages):
            stage_num = i + 2  # Stages 2-7
            logger.info(f"--- Stage {stage_num}: {stage.stage_name.replace('_', ' ').title()} ---")
            stories = stage.process_all(stories)
            logger.info(f"Completed stage: {stage.stage_name} with {len(stories)} stories.")
     
    except Exception as e:
        logger.error(f"An error occurred during the pipeline execution: {e}", exc_info=True)

if __name__ == "__main__":
    main()