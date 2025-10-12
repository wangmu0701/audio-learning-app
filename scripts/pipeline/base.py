from abc import ABC, abstractmethod
from typing import List, Dict

class PipelineStage(ABC):
    """Base class for all pipeline stages"""
    
    def __init__(self, config: dict):
        self.config = config
    
    @property
    def llm_model_name(self) -> str:
        return self.config.get('llm_model_name', None)
    
    @abstractmethod
    def process(self, input_data: List[Dict]) -> List[Dict]:
        """
        Process input and return output.
        Each stage defines its own input/output types.
        
        Args:
            input_data: Input data for this stage
            
        Returns:
            Processed output data
        """
        pass
    
    def validate_output(self, output: Dict) -> bool:
        """
        Optional: validate output before passing to next stage
        
        Args:
            output: The output to validate
            
        Returns:
            True if valid, False otherwise
        """
        return True