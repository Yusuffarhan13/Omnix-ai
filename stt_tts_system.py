#!/usr/bin/env python3
"""
STT/TTS System
Combines Google Speech-to-Text with ElevenLabs Text-to-Speech
for a more reliable voice interaction system
"""

import asyncio
import logging
import base64
import io
import os
import json
import time
from typing import Optional, Callable, Dict, Any
import aiohttp

# Google Cloud Speech-to-Text
try:
    from google.cloud import speech
    from google.api_core.client_options import ClientOptions
    GOOGLE_SPEECH_AVAILABLE = True
except ImportError:
    GOOGLE_SPEECH_AVAILABLE = False
    logging.warning("Google Cloud Speech not available. Install with: pip install google-cloud-speech")

# Fallback STT (Web Speech API or Whisper) - These are not directly used in this file
# but are referenced in the status for completeness, assuming they might be
# handled elsewhere or are conceptual flags.
# For this file, we'll just define them as False to avoid NameError.
WHISPER_LOCAL_AVAILABLE = False
SPEECH_RECOGNITION_AVAILABLE = False


class GoogleCloudSTTProcessor:
    """Google Cloud Speech-to-Text processor"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.client = None
        
        if GOOGLE_SPEECH_AVAILABLE:
            try:
                api_key = os.getenv("GOOGLE_CLOUD_SPEECH_API_KEY") or os.getenv("GOOGLE_API_KEY")
                if api_key:
                    client_options = ClientOptions(api_key=api_key)
                    self.client = speech.SpeechClient(client_options=client_options)
                    self.logger.info("✅ Google Cloud STT initialized with API key")
                else:
                    self.logger.warning("⚠️ GOOGLE_CLOUD_SPEECH_API_KEY not found in environment. Trying Application Default Credentials.")
                    # Fallback to default credentials if API key is not found
                    self.client = speech.SpeechClient()
                    self.logger.info("✅ Google Cloud STT initialized with Application Default Credentials.")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize Google Cloud STT: {e}")
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data to text using Google Cloud STT"""
        if not self.client:
            return None
            
        try:
            audio = speech.RecognitionAudio(content=audio_data)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
                sample_rate_hertz=48000,
                language_code="en-US",
            )
            
            response = self.client.recognize(config=config, audio=audio)
            
            if response.results:
                transcript = response.results[0].alternatives[0].transcript
                self.logger.info(f"🎤 Google Cloud STT: {transcript}")
                return transcript.strip()
            else:
                self.logger.warning("⚠️ No speech detected by Google Cloud STT")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Google Cloud STT error: {e}")
            return None


class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech processor"""
    
    def __init__(self, api_key: str, voice_id: str = None):
        self.api_key = api_key
        self.voice_id = voice_id or "dMyQqiVXTU80dDl2eNK8"  #Eryn voice
        self.logger = logging.getLogger(__name__)
        
        if not api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self.logger.info(f"✅ ElevenLabs TTS initialized with voice: {self.voice_id}")
    
    async def synthesize_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs"""
        if not text.strip():
            return None
            
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            # Optimized settings for faster generation
            data = {
                "text": text,
                "model_id": "eleven_turbo_v2",  # Faster model for real-time
                "voice_settings": {
                    "stability": 0.6,
                    "similarity_boost": 0.8,
                    "style": 0.0,
                    "use_speaker_boost": True
                },
                "optimize_streaming_latency": 4,  # Maximum optimization for streaming
                "output_format": "mp3_22050_32"   # Lower quality for speed
            }
            
            # Set timeout for faster response
            timeout = aiohttp.ClientTimeout(total=10)  # 10 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        self.logger.info(f"🔊 TTS: Generated {len(audio_data)} bytes for: {text[:50]}...")
                        return audio_data
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ TTS error {response.status}: {error_text}")
                        return None
                        
        except Exception as e:
            self.logger.error(f"❌ TTS synthesis error: {e}")
            return None


class STTTTSManager:
    """Manages the complete STT/TTS pipeline"""
    
    def __init__(self, elevenlabs_api_key: str, voice_id: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize STT (Google Cloud STT)
        self.stt_processor = GoogleCloudSTTProcessor()
        if not self.stt_processor.client:
            self.logger.error("❌ No STT processor available")
            self.stt_processor = None
        
        # Initialize TTS
        try:
            self.tts_processor = ElevenLabsTTS(elevenlabs_api_key, voice_id)
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize TTS: {e}")
            self.tts_processor = None
        
        # Callbacks
        self.on_transcript = None
        self.on_audio_response = None
        self.on_error = None
        
        self.logger.info("🎯 STT/TTS Manager initialized")
    
    def set_callbacks(self, 
                     on_transcript: Optional[Callable] = None,
                     on_audio_response: Optional[Callable] = None,
                     on_error: Optional[Callable] = None):
        """Set callback functions"""
        self.on_transcript = on_transcript
        self.on_audio_response = on_audio_response
        self.on_error = on_error
    
    async def process_audio_input(self, audio_data: bytes) -> Optional[str]:
        """Process audio input and return transcript"""
        if not self.stt_processor:
            self.logger.error("❌ No STT processor available")
            if self.on_error:
                self.on_error("Speech recognition not available")
            return None
        
        try:
            transcript = await self.stt_processor.transcribe_audio(audio_data)
            
            if transcript and self.on_transcript:
                self.on_transcript(transcript)
            
            return transcript
            
        except Exception as e:
            self.logger.error(f"❌ Audio processing error: {e}")
            if self.on_error:
                self.on_error(str(e))
            return None
    
    async def generate_speech_response(self, text: str) -> Optional[str]:
        """Generate speech from text and return base64 audio"""
        if not self.tts_processor:
            self.logger.error("❌ No TTS processor available")
            if self.on_error:
                self.on_error("Text-to-speech not available")
            return None
        
        try:
            audio_data = await self.tts_processor.synthesize_speech(text)
            
            if audio_data:
                # Convert to base64 for transmission
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                
                if self.on_audio_response:
                    self.on_audio_response(audio_base64)
                
                return audio_base64
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Speech generation error: {e}")
            if self.on_error:
                self.on_error(str(e))
            return None
    
    def is_available(self) -> bool:
        """Check if both STT and TTS are available"""
        return self.stt_processor is not None and self.tts_processor is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "stt_available": self.stt_processor is not None,
            "tts_available": self.tts_processor is not None,
            "stt_type": type(self.stt_processor).__name__ if self.stt_processor else None,
            "whisper_local_available": WHISPER_LOCAL_AVAILABLE,
            "fallback_stt_available": SPEECH_RECOGNITION_AVAILABLE
        }


# Factory function
def create_stt_tts_manager(elevenlabs_api_key: str, voice_id: str = None) -> Optional[STTTTSManager]:
    """Create STT/TTS manager with error handling"""
    try:
        manager = STTTTSManager(elevenlabs_api_key, voice_id)
        if manager.is_available():
            return manager
        else:
            logging.error("❌ STT/TTS manager not fully available")
            return None
    except Exception as e:
        logging.error(f"❌ Failed to create STT/TTS manager: {e}")
        return None