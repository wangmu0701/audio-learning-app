import os
import json
import time
import tempfile
import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections import defaultdict
from .logger import get_logger

# Attempt to import provider-specific libraries
try:
    import openai
except ImportError:
    openai = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None


@dataclass
class GenerationConfig:
    """Standardized configuration for LLM generation."""
    model_name: str
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    stop_sequences: Optional[List[str]] = None
    json_schema: Optional[Dict[str, Any]] = None
    service_tier: Optional[str] = None  # e.g, "flex"


class LLMProvider:
    """
    A unified provider for interacting with multiple LLM APIs (OpenAI, Gemini).
    
    This class attempts to initialize clients for all supported providers
    and dispatches requests to the correct client based on the model name
    provided in the GenerationConfig.
    """

    def __init__(self):
        """Initializes the provider, clients, and logger."""
        self.logger = get_logger(__name__)
        self._usage_counters: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Initialize clients
        self.openai_client: Optional[openai.OpenAI] = None
        self.gemini_client: Optional[Any] = None
        self.glm_client: Optional[openai.OpenAI] = None

        # Try to initialize OpenAI client
        if not openai:
            self.logger.warning("openai library not installed. To use OpenAI models, run: pip install openai")
        else:
            try:
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.openai_client = openai.OpenAI()
                    self.logger.info("OpenAI client initialized successfully.")
                else:
                    self.logger.warning("OPENAI_API_KEY not found. OpenAI client not initialized.")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")

        # Try to initialize Gemini client
        if not genai:
            self.logger.warning("google-generativeai library not installed. To use Gemini models, run: pip install google-generativeai")
        else:
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                if api_key:
                    genai.configure(api_key=api_key)
                    self.gemini_client = genai
                    self.logger.info("Gemini client initialized successfully.")
                else:
                    self.logger.warning("GEMINI_API_KEY not found. Gemini client not initialized.")
            except Exception as e:
                self.logger.error(f"Failed to initialize Gemini client: {e}")

        # Try to initialize GLM client (which uses the openai library)
        if not openai: # GLM client depends on the openai library structure
            self.logger.warning("openai library not installed. GLM client cannot be initialized.")
        else:
            try:
                api_key = os.getenv("GLM_API_KEY")
                if api_key:
                    self.glm_client = openai.OpenAI(
                        base_url="https://open.bigmodel.cn/api/paas/v4/",
                    )
                    self.logger.info("GLM client initialized successfully.")
                else:
                    self.logger.warning("GLM_API_KEY not found. GLM client not initialized.")
            except Exception as e:
                self.logger.error(f"Failed to initialize GLM client: {e}")

    def __del__(self):
        """Logs the final token usage when the object is destroyed."""
        if self.usage_counts():
            self.logger.info(f"Final LLM token usage: {json.dumps(self.usage_counts())}")

    def usage_counts(self) -> Dict[str, Dict[str, int]]:
        """Returns a dictionary of token usage counters, keyed by model name."""
        return self._usage_counters

    def reset_token_counts(self, baseline: Optional[Dict[str, Any]] = None):
        """Resets the token usage counters, optionally from a baseline."""
        self._usage_counters = defaultdict(lambda: defaultdict(int))
        if baseline:
            for model, counts in baseline.items():
                for key, value in counts.items():
                    self._usage_counters[model][key] = value

    def _update_usage_counters(self, model_name: str, input_tokens: int, output_tokens: int, is_batch: bool = False):
        """Updates the token usage counters."""
        counters = self._usage_counters[model_name]
        if is_batch:
            counters['batch_input_tokens'] += input_tokens
            counters['batch_output_tokens'] += output_tokens
        else:
            counters['input_tokens'] += input_tokens
            counters['output_tokens'] += output_tokens

    def generate_response(self, prompt: str, config: GenerationConfig) -> str:
        """
        Generate a response from the LLM, dispatching to the correct provider.
        
        Args:
            prompt: The input prompt.
            config: Generation configuration, must include model_name.
            
        Returns:
            Generated response text.
        """
        model_name = config.model_name
        if model_name.startswith("gpt-"):
            if not self.openai_client:
                raise ValueError("OpenAI client is not initialized. Check OPENAI_API_KEY or install openai library.")
            return self._generate_openai_response(prompt, config)
        elif model_name.lower().startswith("glm-"):
            if not self.glm_client:
                raise ValueError("GLM client is not initialized. Check GLM_API_KEY or install openai library.")
            return self._generate_glm_response(prompt, config)
        elif model_name.startswith("gemini"):
            if not self.gemini_client:
                raise ValueError("Gemini client is not initialized. Check GEMINI_API_KEY or install google-generativeai library.")
            return self._generate_gemini_response(prompt, config)
        else:
            raise ValueError(f"Unsupported or unknown model name: {model_name}")

    def generate_response_batch(self, prompts: List[str], config: GenerationConfig) -> str:
        """
        Generate responses in batch mode, dispatching to the correct provider.
        
        Args:
            prompts: List of input prompts.
            config: Generation configuration, must include model_name.
            
        Returns:
            An enriched batch ID for polling status, formatted as 
            "<provider>:<model_name>:<provider_job_id>".
        """
        model_name = config.model_name
        if model_name.startswith("gpt-"):
            if not self.openai_client:
                raise ValueError("OpenAI client is not initialized. Check OPENAI_API_KEY or install openai library.")
            return self._generate_openai_batch(prompts, config)
        elif model_name.lower().startswith("glm-"):
            raise NotImplementedError("Batch generation is not supported for GLM models yet.")
        elif model_name.startswith("gemini"):
            if not self.gemini_client:
                raise ValueError("Gemini client is not initialized. Check GEMINI_API_KEY or install google-generativeai library.")
            return self._generate_gemini_batch(prompts, config)
        else:
            raise ValueError(f"Unsupported or unknown model name: {model_name}")

    def poll_batch_status(self, batch_id: str) -> Tuple[bool, Union[str, List[Tuple[bool, str]]]]:
        """
        Poll the status of a batch job using the enriched batch ID.
        
        Args:
            batch_id: The enriched batch job ID to check.
            
        Returns:
            Tuple of (is_finished, results).
        """
        try:
            provider, model_name, job_id = batch_id.split(':', 2)
        except ValueError:
            raise ValueError("Invalid batch_id format. Expected '<provider>:<model_name>:<job_id>'.")

        if provider == "openai":
            if not self.openai_client:
                raise ValueError("OpenAI client is not initialized.")
            return self._poll_openai_batch(job_id)
        elif provider == "glm":
            raise NotImplementedError("Batch polling is not supported for GLM models yet.")
        elif provider == "gemini":
            if not self.gemini_client:
                raise ValueError("Gemini client is not initialized.")
            return self._poll_gemini_batch(job_id, model_name)
        else:
            raise ValueError(f"Unsupported provider found in batch ID: {provider}")

    # --- OpenAI specific methods ---

    def _build_openai_params(self, config: GenerationConfig) -> Dict[str, Any]:
        """Convert standardized config to OpenAI-specific parameters."""
        openai_params = {
            "model": config.model_name,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
        }
        if config.top_p is not None:
            openai_params["top_p"] = config.top_p
        if config.temperature is not None:
            openai_params["temperature"] = config.temperature
        if config.max_tokens is not None:
            openai_params["max_completion_tokens"] = config.max_tokens
        if config.stop_sequences:
            openai_params["stop"] = config.stop_sequences
        if config.service_tier is not None:
            openai_params["service_tier"] = config.service_tier
        if config.json_schema is not None:
            openai_params["response_format"] = {"type": "json_object", "json_object": config.json_schema}
        return openai_params

    def _generate_openai_response(self, prompt: str, config: GenerationConfig) -> str:
        """Generate a response from OpenAI."""
        messages = [{"role": "user", "content": prompt}]
        openai_params = self._build_openai_params(config)
        openai_params["messages"] = messages

        try:
            start_time = time.time()
            response = self.openai_client.chat.completions.create(**openai_params)
            latency_ms = (time.time() - start_time) * 1000
            self.logger.debug(f"OpenAI RPC latency: {latency_ms:.2f}ms")

            if response.usage:
                self._update_usage_counters(
                    model_name=response.model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens
                )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")

    def _generate_openai_batch(self, prompts: List[str], config: GenerationConfig) -> str:
        """Generate OpenAI batch and return enriched ID."""
        batch_requests = []
        for i, prompt in enumerate(prompts):
            openai_params = self._build_openai_params(config)
            openai_params["messages"] = [{"role": "user", "content": prompt}]
            batch_requests.append(json.dumps({
                "custom_id": f"request-{i}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": openai_params
            }))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('\n'.join(batch_requests))
            temp_file_path = f.name
        
        try:
            with open(temp_file_path, 'rb') as f:
                batch_file = self.openai_client.files.create(file=f, purpose="batch")
            
            batch_job = self.openai_client.batches.create(
                input_file_id=batch_file.id,
                endpoint="/v1/chat/completions",
                completion_window="24h"
            )
            
            return f"openai:{config.model_name}:{batch_job.id}"
        except Exception as e:
            raise Exception(f"OpenAI Batch API error: {e}")
        finally:
            os.unlink(temp_file_path)

    def _poll_openai_batch(self, job_id: str) -> Tuple[bool, Union[str, List[Tuple[bool, str]]]]:
        """Poll OpenAI batch job."""
        try:
            batch_job = self.openai_client.batches.retrieve(job_id)
            if batch_job.status == 'completed':
                result_content = self.openai_client.files.content(batch_job.output_file_id).content
                results_dict = {}
                for line in result_content.decode('utf-8').strip().split('\n'):
                    if not line.strip(): continue
                    result_obj = json.loads(line)
                    custom_id = result_obj.get('custom_id', '')
                    try:
                        request_idx = int(custom_id.split('-')[1])
                    except (IndexError, ValueError):
                        request_idx = len(results_dict)
                    
                    if result_obj.get('response'):
                        response_body = result_obj['response']['body']
                        content = response_body['choices'][0]['message']['content']
                        results_dict[request_idx] = (True, content.strip())
                        if response_body.get('usage'):
                            usage = response_body['usage']
                            self._update_usage_counters(
                                model_name=response_body['model'],
                                input_tokens=usage['prompt_tokens'],
                                output_tokens=usage['completion_tokens'],
                                is_batch=True
                            )
                    elif result_obj.get('error'):
                        results_dict[request_idx] = (False, result_obj['error'].get('message', 'Unknown error'))
                
                return True, [results_dict[i] for i in sorted(results_dict.keys())]
            
            elif batch_job.status in ['failed', 'expired', 'canceled']:
                return True, f"Batch failed with status: {batch_job.status}"
            else:
                return False, "Batch still processing"
        except Exception as e:
            return True, f"Error polling OpenAI batch status: {e}"

    def _generate_glm_response(self, prompt: str, config: GenerationConfig) -> str:
        """Generate a response from GLM."""
        messages = [{"role": "user", "content": prompt}]
        openai_params = self._build_openai_params(config)
        openai_params["messages"] = messages

        try:
            start_time = time.time()
            response = self.glm_client.chat.completions.create(**openai_params)
            latency_ms = (time.time() - start_time) * 1000
            self.logger.debug(f"GLM RPC latency: {latency_ms:.2f}ms")

            if response.usage:
                self._update_usage_counters(
                    model_name=response.model,
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens
                )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise Exception(f"GLM API error: {e}")

    # --- Gemini specific methods ---

    def _build_gemini_config(self, config: GenerationConfig) -> Dict[str, Any]:
        """Convert standardized config to Gemini-specific parameters."""
        gemini_config = {}
        if config.temperature is not None:
            gemini_config["temperature"] = config.temperature
        if config.max_tokens is not None:
            gemini_config["max_output_tokens"] = config.max_tokens
        if config.top_p is not None:
            gemini_config["top_p"] = config.top_p
        if config.stop_sequences:
            gemini_config["stop_sequences"] = config.stop_sequences
        
        gemini_config["response_mime_type"] = "application/json"
        if config.json_schema is not None:
            schema = config.json_schema.get("schema", config.json_schema)
            gemini_config["response_schema"] = schema
        return gemini_config

    def _generate_gemini_response(self, prompt: str, config: GenerationConfig) -> str:
        """Generate a response from Gemini."""
        gemini_config = self._build_gemini_config(config)
        try:
            start_time = time.time()
            model = self.gemini_client.GenerativeModel(config.model_name)
            response = model.generate_content(
                contents=prompt,
                generation_config=gemini_config if gemini_config else None
            )
            latency_ms = (time.time() - start_time) * 1000
            self.logger.debug(f"Gemini RPC latency: {latency_ms:.2f}ms")

            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                output_tokens = usage.candidates_token_count or 0
                if hasattr(usage, 'thoughts_token_count'):
                    output_tokens += usage.thoughts_token_count or 0
                if hasattr(usage, 'tool_use_prompt_token_count'):
                    output_tokens += usage.tool_use_prompt_token_count or 0
                self._update_usage_counters(
                    model_name=config.model_name,
                    input_tokens=usage.prompt_token_count or 0,
                    output_tokens=output_tokens
                )
            
            return response.text
        except Exception as e:
            raise Exception(f"Gemini API error: {e}")

    def _generate_gemini_batch(self, prompts: List[str], config: GenerationConfig) -> str:
        """Generate Gemini batch and return enriched ID."""
        gemini_config = self._build_gemini_config(config)
        inline_requests = []
        for prompt in prompts:
            request = {'contents': [{'parts': [{'text': prompt}]}]}
            if gemini_config:
                request['config'] = gemini_config
            inline_requests.append(request)
        
        try:
            batch_job = self.gemini_client.batches.create(
                model=config.model_name,
                src=inline_requests,
                config={'display_name': f"batch-{int(time.time())}"}
            )
            self.logger.debug(f"Created Gemini batch job: {batch_job.name}")
            return f"gemini:{config.model_name}:{batch_job.name}"
        except Exception as e:
            raise Exception(f"Gemini Batch API error: {e}")

    def _poll_gemini_batch(self, job_id: str, model_name: str) -> Tuple[bool, Union[str, List[Tuple[bool, str]]]]:
        """Poll Gemini batch job."""
        try:
            batch_job = self.gemini_client.batches.get(name=job_id)
            if batch_job.state.name == "JOB_STATE_SUCCEEDED":
                results = []
                if hasattr(batch_job, 'dest') and batch_job.dest and hasattr(batch_job.dest, 'inlined_responses'):
                    for inlined_response in batch_job.dest.inlined_responses:
                        try:
                            if hasattr(inlined_response, 'response') and inlined_response.response:
                                response = inlined_response.response
                                if hasattr(response, 'usage_metadata'):
                                    usage = response.usage_metadata
                                    output_tokens = usage.candidates_token_count or 0
                                    if hasattr(usage, 'thoughts_token_count'):
                                        output_tokens += usage.thoughts_token_count or 0
                                    if hasattr(usage, 'tool_use_prompt_token_count'):
                                        output_tokens += usage.tool_use_prompt_token_count or 0
                                    self._update_usage_counters(
                                        model_name=model_name,
                                        input_tokens=usage.prompt_token_count or 0,
                                        output_tokens=output_tokens,
                                        is_batch=True
                                    )
                                if (hasattr(response, 'candidates') and response.candidates and 
                                    response.candidates[0].content and response.candidates[0].content.parts):
                                    full_text = ''.join(part.text for part in response.candidates[0].content.parts if part.text).strip()
                                    results.append((True, full_text))
                                else:
                                    results.append((False, "No content in response"))
                            else:
                                results.append((False, "No response object in inlined response"))
                        except Exception as e:
                            results.append((False, f"Response parsing error: {e}"))
                else:
                    return True, "Batch completed but no responses available"
                return True, results
            
            elif batch_job.state.name in ["JOB_STATE_FAILED", "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"]:
                return True, f"Batch failed with state: {batch_job.state.name}"
            else:
                return False, f"Batch still processing (state: {batch_job.state.name})"
        except Exception as e:
            return True, f"Error polling Gemini batch status: {e}"