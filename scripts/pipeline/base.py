from abc import ABC, abstractmethod
from typing import List, Dict

import os
import json
from .logger import get_logger

logger = get_logger(__name__)

class PipelineStage(ABC):
    """Base class for all pipeline stages"""
    
    def __init__(self, config: dict):
        self.config = config
    
    @property
    def llm_model_name(self) -> str:
        return self.config.get('llm_model_name', None)
    
    @abstractmethod
    def process(self, input_story: Dict) -> Dict:
        """
        Process input story and return augmented output.
        Each stage defines its own input/output types.
        """
        pass
    
    def process_all(self, input_stories: List[Dict]) -> List[Dict]:
        """
        Wrapper to process input data and handle any common pre/post processing.
        """
        output_stories = []
        for input_story in input_stories:
            try:
                output_story = self.process(input_story)
                output_story["status"][self.stage_name] = True
                output_stories.append(output_story)
                self.save_output(output_story)
            except Exception as e:
                # Log the error and continue with next story
                logger.error(f"Error processing story {input_story.get('id', 'unknown')}: {e}")
                continue
        return output_stories
    
    @property
    def stage_name(self) -> str:
        """Returns the name of the stage"""
        pass

    def save_output(self, story: Dict):
        """
        Saves the output of each story to its own output.json file.
        """
        output_file = os.path.join(story["output_path"], "output.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(story, f, ensure_ascii=False, indent=2)