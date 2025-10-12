import os
from dataclasses import dataclass
from typing import Optional, List

from google.cloud import texttospeech
from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class TTSConfig:
    """Standardized configuration for Text-to-Speech synthesis."""
    language_code: str
    voice_name: str
    speaking_rate: float = 1.0
    audio_encoding: texttospeech.AudioEncoding = texttospeech.AudioEncoding.MP3

class TTSProvider:
    """
    A provider for interacting with Google Cloud Text-to-Speech API.
    """

    def __init__(self):
        """Initializes the TTS provider and client."""
        self.client: Optional[texttospeech.TextToSpeechClient] = None
        
        # Note: Google Cloud TTS authentication typically uses a service account,
        # not a simple API key like Gemini. The client library automatically
        # finds credentials if the GOOGLE_APPLICATION_CREDENTIALS environment
        # variable is set to the path of your service account JSON file.
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            logger.warning(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set. "
                "TTSProvider may not be able to authenticate."
            )
            # Attempt to initialize without explicit credentials, which might work in some environments (e.g., GCP VMs)
        
        try:
            self.client = texttospeech.TextToSpeechClient()
            logger.info("Google Cloud TTS client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Google Cloud TTS client: {e}")
            self.client = None

    def synthesize_speech(self, text: str, config: TTSConfig) -> Optional[bytes]:
        """
        Synthesizes speech from text.

        Args:
            text: The text to synthesize.
            config: The TTS configuration (language, voice, speed).

        Returns:
            The raw audio content in bytes (e.g., MP3 data), or None if failed.
        """
        if not self.client:
            logger.error("TTS client is not initialized. Cannot synthesize speech.")
            return None
        
        if not text:
            logger.warning("Synthesize speech called with empty text.")
            return None

        try:
            synthesis_input = texttospeech.SynthesisInput(text=text)

            voice = texttospeech.VoiceSelectionParams(
                language_code=config.language_code,
                name=config.voice_name
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=config.audio_encoding,
                speaking_rate=config.speaking_rate
            )

            response = self.client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            return response.audio_content

        except Exception as e:
            logger.error(f"TTS synthesis failed for text '{text[:30]}...'. Error: {e}")
            return None
