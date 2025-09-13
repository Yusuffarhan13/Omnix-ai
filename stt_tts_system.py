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
import whisper
import torch

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
WHISPER_LOCAL_AVAILABLE = True  # We now have Whisper available
SPEECH_RECOGNITION_AVAILABLE = False


class ElevenLabsSTTProcessor:
    """ElevenLabs Speech-to-Text processor"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
        
        if not api_key:
            raise ValueError("ElevenLabs API key is required for STT")
        
        self.logger.info("✅ ElevenLabs STT initialized")
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio data to text using ElevenLabs STT"""
        if not self.api_key:
            return None
            
        try:
            url = "https://api.elevenlabs.io/v1/speech-to-text"
            headers = {
                "xi-api-key": self.api_key
            }
            
            # Prepare the multipart form data
            files = {
                'file': ('audio.wav', audio_data, 'audio/wav')
            }
            data = {
                'model_id': 'scribe_v1',  # ElevenLabs Scribe v1 model (correct ID)
                'language_code': 'en',  # English
                'num_speakers': 1,  # Single speaker for live conversation
                'optimize_for_latency': True,  # Enable latency optimization
                'punctuation_threshold': 0.7,  # Lower threshold for faster processing
                'silence_threshold_ms': 300  # Shorter silence detection for speed
            }
            
            import requests
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                transcript = result.get('text', '').strip()
                if transcript:
                    self.logger.info(f"🎤 ElevenLabs STT: {transcript}")
                    return transcript
                else:
                    self.logger.warning("⚠️ No speech detected by ElevenLabs STT")
                    return None
            else:
                self.logger.error(f"❌ ElevenLabs STT error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ ElevenLabs STT error: {e}")
            return None

class GoogleCloudSTTProcessor:
    """Google Cloud Speech-to-Text processor (legacy fallback)"""
    
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


class WhisperSTTProcessor:
    """Local Whisper Speech-to-Text processor using OpenAI Whisper medium model"""
    
    def __init__(self, model_name: str = "medium"):
        self.model_name = model_name
        self.model = None
        self.logger = logging.getLogger(__name__)
        
        # Check if CUDA is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info(f"🎯 Whisper will use device: {self.device}")
        
        # Load the model
        try:
            self.logger.info(f"📥 Loading Whisper {model_name} model...")
            self.model = whisper.load_model(model_name, device=self.device)
            self.logger.info(f"✅ Whisper {model_name} model loaded successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to load Whisper model: {e}")
            raise e
    
    async def transcribe_audio(self, audio_data: bytes) -> Optional[str]:
        """Transcribe audio using local Whisper model"""
        if not self.model:
            self.logger.error("❌ Whisper model not loaded")
            return None
        
        try:
            # Save audio to temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                try:
                    # Run transcription in a thread to avoid blocking
                    import asyncio
                    loop = asyncio.get_event_loop()
                    
                    def transcribe_sync():
                        result = self.model.transcribe(temp_file.name, language="en")
                        return result["text"].strip()
                    
                    # Run in thread pool to avoid blocking the event loop
                    transcript = await loop.run_in_executor(None, transcribe_sync)
                    
                    self.logger.info(f"🎤 Whisper transcription: {transcript}")
                    return transcript
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file.name)
                    except OSError:
                        pass
                        
        except Exception as e:
            self.logger.error(f"❌ Whisper transcription error: {e}")
            return None


class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech processor"""
    
    def __init__(self, api_key: str, voice_id: str = None):
        self.api_key = api_key
        self.voice_id = voice_id or "Hybl6rg76ZOcgqZqN5WN"  # Tala voice (default)
        self.logger = logging.getLogger(__name__)
        
        if not api_key:
            raise ValueError("ElevenLabs API key is required")
        
        self.logger.info(f"✅ ElevenLabs TTS initialized with voice: {self.voice_id}")
    
    def set_voice(self, voice_id: str):
        """Change the voice for TTS synthesis"""
        self.voice_id = voice_id
        self.logger.info(f"🔄 ElevenLabs TTS voice changed to: {self.voice_id}")
    
    async def synthesize_speech(self, text: str) -> Optional[bytes]:
        """Convert text to speech using ElevenLabs with smart chunking for long text"""
        if not text.strip():
            return None
        
        # Check text length and use appropriate strategy
        text_length = len(text)
        
        # For very long text (>2000 chars), chunk it
        if text_length > 2000:
            return await self._synthesize_long_text(text)
        # For medium text (>800 chars), use regular model for better quality
        elif text_length > 800:
            return await self._synthesize_with_regular_model(text)
        # For short text, use turbo model for speed
        else:
            return await self._synthesize_with_turbo_model(text)
    
    async def _synthesize_with_turbo_model(self, text: str) -> Optional[bytes]:
        """Synthesize short text with turbo model for speed"""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.3,
                    "similarity_boost": 0.6,
                    "style": 0.0,
                    "use_speaker_boost": False
                },
                "optimize_streaming_latency": 4,
                "output_format": "mp3_22050_32"
            }
            
            timeout = aiohttp.ClientTimeout(total=8)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        self.logger.info(f"🔊 Turbo TTS: {len(audio_data)} bytes for: {text[:50]}...")
                        return audio_data
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Turbo TTS error {response.status}: {error_text}")
                        return None
        except Exception as e:
            self.logger.error(f"❌ Turbo TTS error: {e}")
            return None
    
    async def _synthesize_with_regular_model(self, text: str) -> Optional[bytes]:
        """Synthesize medium text with regular model for better quality"""
        try:
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key
            }
            
            data = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.4,
                    "similarity_boost": 0.7,
                    "style": 0.0,
                    "use_speaker_boost": False
                },
                "optimize_streaming_latency": 3,
                "output_format": "mp3_44100_64"
            }
            
            timeout = aiohttp.ClientTimeout(total=8, connect=3)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        self.logger.info(f"🔊 Regular TTS: {len(audio_data)} bytes for: {text[:50]}...")
                        return audio_data
                    else:
                        error_text = await response.text()
                        self.logger.error(f"❌ Regular TTS error {response.status}: {error_text}")
                        return None
        except asyncio.TimeoutError:
            self.logger.error(f"❌ Regular TTS timeout for text: {text[:50]}...")
            return None
        except aiohttp.ClientError as e:
            self.logger.error(f"❌ Regular TTS client error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Regular TTS error: {type(e).__name__}: {str(e)}")
            return None
    
    async def _synthesize_long_text(self, text: str) -> Optional[bytes]:
        """Synthesize long text by chunking into smaller pieces"""
        try:
            # Split text into sentences and group them into chunks
            import re
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            
            chunks = []
            current_chunk = ""
            
            for sentence in sentences:
                # If adding this sentence would make chunk too long, start new chunk (reduced size)
                if len(current_chunk) + len(sentence) > 500 and current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = sentence
                else:
                    current_chunk += " " + sentence if current_chunk else sentence
            
            # Add the last chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            self.logger.info(f"🔄 Splitting long text into {len(chunks)} chunks")
            
            # Generate audio for each chunk with retry logic
            audio_segments = []
            for i, chunk in enumerate(chunks):
                self.logger.info(f"🎵 Processing chunk {i+1}/{len(chunks)}: {chunk[:50]}...")
                
                # Try up to 3 times for each chunk
                for attempt in range(3):
                    try:
                        audio_data = await self._synthesize_with_regular_model(chunk)
                        if audio_data:
                            audio_segments.append(audio_data)
                            # Add small delay to prevent rate limiting
                            if i < len(chunks) - 1:  # Don't delay after last chunk
                                await asyncio.sleep(0.5)
                            break
                        else:
                            if attempt < 2:  # Don't log error on last attempt
                                self.logger.warning(f"⚠️ Chunk {i+1} attempt {attempt+1} failed, retrying...")
                                await asyncio.sleep(1)  # Wait before retry
                    except Exception as e:
                        if attempt < 2:
                            self.logger.warning(f"⚠️ Chunk {i+1} attempt {attempt+1} error: {e}, retrying...")
                            await asyncio.sleep(1)  # Wait before retry
                        else:
                            self.logger.error(f"❌ All attempts failed for chunk {i+1}: {e}")
                else:
                    # If we get here, all attempts failed for this chunk
                    self.logger.warning(f"⚠️ Skipping failed chunk {i+1}, continuing with remaining chunks...")
                    continue
            
            # Combine audio segments (allow partial success)
            if audio_segments:
                combined_audio = b''.join(audio_segments)
                success_rate = len(audio_segments) / len(chunks)
                self.logger.info(f"🎶 Combined {len(audio_segments)}/{len(chunks)} chunks ({success_rate:.1%} success) into {len(combined_audio)} bytes")
                return combined_audio
            else:
                self.logger.error("❌ No audio chunks were successfully generated")
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Long text TTS error: {e}")
            return None


class STTTTSManager:
    """Manages the complete STT/TTS pipeline"""
    
    def __init__(self, elevenlabs_api_key: str, voice_id: str = None):
        self.logger = logging.getLogger(__name__)
        
        # Initialize STT (Whisper local with fallbacks)
        try:
            self.stt_processor = WhisperSTTProcessor("base")
            self.logger.info("✅ Using local Whisper base model for STT")
        except Exception as e:
            self.logger.warning(f"⚠️ Whisper STT not available: {e}")
            # Fallback to ElevenLabs STT
            try:
                self.stt_processor = ElevenLabsSTTProcessor(elevenlabs_api_key)
                self.logger.info("📞 Using ElevenLabs STT as fallback")
            except Exception as e2:
                self.logger.warning(f"⚠️ ElevenLabs STT not available: {e2}")
                # Final fallback to Google Cloud STT
                self.stt_processor = GoogleCloudSTTProcessor()
                if not self.stt_processor.client:
                    self.logger.error("❌ No STT processor available")
                    self.stt_processor = None
                else:
                    self.logger.info("☁️ Using Google Cloud STT as final fallback")
        
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
    
    def set_voice(self, voice_id: str):
        """Change the voice for TTS synthesis"""
        if self.tts_processor:
            self.tts_processor.set_voice(voice_id)
            self.logger.info(f"🎤 STT/TTS Manager voice changed to: {voice_id}")
        else:
            self.logger.warning("⚠️ Cannot change voice - TTS processor not available")
    
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
    
    def transcribe_audio_sync(self, audio_data: bytes, mime_type: str = "audio/wav") -> Optional[str]:
        """Synchronous audio transcription method"""
        if not self.stt_processor:
            self.logger.error("❌ No STT processor available")
            return None
        
        try:
            # Use asyncio to run the async method synchronously
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                transcript = loop.run_until_complete(self.stt_processor.transcribe_audio(audio_data))
                return transcript
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"❌ Audio transcription error: {e}")
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