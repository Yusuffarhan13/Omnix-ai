"""
Server-side live voice processing system
Handles all voice processing on the server without Socket.IO
"""

import os
import uuid
import json
import time
import base64
import asyncio
import threading
from queue import Queue
from flask import Response, request, jsonify
import requests
from dotenv import load_dotenv

load_dotenv()

class ServerSideLiveVoiceSystem:
    """Handles live voice entirely on the server side"""
    
    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("ELEVENLABS_AGENT_ID", "agent_1801k2s1wbt3fxmrfhy6zzarrhex")
        self.voice_id = os.getenv("ELEVENLABS_VOICE_ID", "dMyQqiVXTU80dDl2eNK8")
        self.sessions = {}
        self.base_url = "https://api.elevenlabs.io/v1"
        
    def create_session(self, session_id=None):
        """Create a new voice session"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        session = {
            'id': session_id,
            'created_at': time.time(),
            'status': 'active',
            'conversation': [],
            'audio_queue': Queue()
        }
        
        self.sessions[session_id] = session
        return session_id
    
    def process_text_input(self, session_id, text):
        """Process text input and generate audio response"""
        if session_id not in self.sessions:
            return {'error': 'Session not found'}
        
        session = self.sessions[session_id]
        
        # Add to conversation history
        session['conversation'].append({
            'role': 'user',
            'content': text,
            'timestamp': time.time()
        })
        
        try:
            # Generate response using ElevenLabs Conversational AI
            response = self._call_elevenlabs_agent(text)
            
            # Add response to conversation
            session['conversation'].append({
                'role': 'assistant',
                'content': response['text'],
                'timestamp': time.time()
            })
            
            # Generate audio for the response
            audio_data = self._generate_audio(response['text'])
            
            return {
                'text': response['text'],
                'audio': audio_data,
                'session_id': session_id
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def process_audio_input(self, session_id, audio_data):
        """Process audio input (transcribe and respond)"""
        if session_id not in self.sessions:
            return {'error': 'Session not found'}
        
        try:
            # Transcribe audio using ElevenLabs or Whisper
            transcript = self._transcribe_audio(audio_data)
            
            # Process as text
            return self.process_text_input(session_id, transcript)
            
        except Exception as e:
            return {'error': str(e)}
    
    def _call_elevenlabs_agent(self, text):
        """Generate AI response using Google Gemini"""
        print(f"📝 Processing transcription: {text}")
        
        try:
            # Try to use Google Gemini for response generation
            import google.generativeai as genai
            
            # Check if Gemini is already configured in environment
            # The main app uses GOOGLE_API_KEY for Gemini
            api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
            
            if api_key:
                print(f"✅ Found API key, configuring Gemini...")
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                # Create a conversational prompt
                prompt = f"""You are a helpful voice assistant. 
                Be conversational, warm, and concise in your responses.
                Keep responses brief and natural for voice conversation.
                
                User said: {text}
                
                Respond naturally and helpfully:"""
                
                print(f"🚀 Sending to Gemini: {text[:50]}...")
                response = model.generate_content(prompt)
                ai_response = response.text.strip()
                
                print(f"🤖 AI Response: {ai_response[:100]}...")
                
                return {
                    'text': ai_response,
                    'audio': None
                }
            else:
                # Try ElevenLabs API if available
                if self.api_key:
                    headers = {
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    }
                    
                    url = f"{self.base_url}/convai/conversation"
                    payload = {
                        "agent_id": self.agent_id,
                        "message": {
                            "role": "user",
                            "content": text
                        }
                    }
                    
                    response = requests.post(url, json=payload, headers=headers)
                    if response.status_code == 200:
                        return response.json()
                
                # Final fallback
                print(f"⚠️ No Google API key found. User said: {text}")
                print(f"Debug - GOOGLE_API_KEY exists: {bool(os.getenv('GOOGLE_API_KEY'))}")
                print(f"Debug - GEMINI_API_KEY exists: {bool(os.getenv('GEMINI_API_KEY'))}")
                return {
                    'text': "I apologize, but the AI service is temporarily unavailable. Please check that GOOGLE_API_KEY is set in your .env file.",
                    'audio': None
                }
                
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return {
                'text': "I'm having trouble processing your request. Please try again.",
                'audio': None
            }
    
    def _generate_audio(self, text):
        """Generate audio from text using ElevenLabs TTS"""
        if not self.api_key:
            return None
            
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/text-to-speech/{self.voice_id}"
        
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                # Return base64 encoded audio
                return base64.b64encode(response.content).decode('utf-8')
        except Exception as e:
            print(f"Error generating audio: {e}")
            
        return None
    
    def _transcribe_audio(self, audio_data):
        """Transcribe audio to text using local Whisper model"""
        try:
            import whisper
            import tempfile
            import base64
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)
            
            # Save audio to temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(audio_bytes)
                temp_file.flush()
                
                try:
                    # Load Whisper model if not already loaded
                    if not hasattr(self, 'whisper_model') or self.whisper_model is None:
                        print("Loading Whisper base model...")
                        self.whisper_model = whisper.load_model("base")
                        print("✅ Whisper base model loaded")
                    
                    # Transcribe audio
                    result = self.whisper_model.transcribe(temp_file.name, language="en")
                    transcript = result["text"].strip()
                    
                    print(f"🎤 Whisper transcription: {transcript}")
                    return transcript
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_file.name)
                    except OSError:
                        pass
            
        except ImportError:
            return "Please install whisper package: pip install openai-whisper"
        except Exception as e:
            print(f"Error transcribing audio: {e}")
            return "Sorry, I couldn't understand the audio. Please try again."
    
    def stream_session(self, session_id):
        """Stream session updates using Server-Sent Events"""
        def generate():
            session = self.sessions.get(session_id)
            if not session:
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                return
                
            yield f"data: {json.dumps({'status': 'connected', 'session_id': session_id})}\n\n"
            
            # Keep connection alive and send updates
            last_update = 0
            while session['status'] == 'active':
                # Check for new conversation items
                if len(session['conversation']) > last_update:
                    for item in session['conversation'][last_update:]:
                        yield f"data: {json.dumps({'type': 'message', 'data': item})}\n\n"
                    last_update = len(session['conversation'])
                
                # Small delay to prevent CPU spinning
                time.sleep(0.1)
                
                # Send heartbeat every 30 seconds
                if int(time.time()) % 30 == 0:
                    yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        return Response(generate(), mimetype="text/event-stream")
    
    def end_session(self, session_id):
        """End a voice session"""
        if session_id in self.sessions:
            self.sessions[session_id]['status'] = 'ended'
            # Clean up after a delay
            threading.Timer(60.0, lambda: self.sessions.pop(session_id, None)).start()
            return {'status': 'ended', 'session_id': session_id}
        return {'error': 'Session not found'}

# Initialize the system
live_voice_system = ServerSideLiveVoiceSystem()

def register_routes(app):
    """Register Flask routes for the live voice system"""
    
    @app.route('/api/live/session/create', methods=['POST'])
    def create_live_session():
        """Create a new live voice session"""
        session_id = live_voice_system.create_session()
        return jsonify({
            'session_id': session_id,
            'status': 'created'
        })
    
    @app.route('/api/live/session/<session_id>/text', methods=['POST'])
    def send_text_message(session_id):
        """Send text message to live session"""
        data = request.json
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        result = live_voice_system.process_text_input(session_id, text)
        return jsonify(result)
    
    @app.route('/api/live/session/<session_id>/audio', methods=['POST'])
    def send_audio_message(session_id):
        """Send audio message to live session"""
        data = request.json
        audio_data = data.get('audio', '')
        
        if not audio_data:
            return jsonify({'error': 'Audio data is required'}), 400
        
        result = live_voice_system.process_audio_input(session_id, audio_data)
        return jsonify(result)
    
    @app.route('/api/live/session/<session_id>/stream')
    def stream_session(session_id):
        """Stream session updates using SSE"""
        return live_voice_system.stream_session(session_id)
    
    @app.route('/api/live/session/<session_id>/end', methods=['POST'])
    def end_server_live_session(session_id):
        """End a live voice session"""
        result = live_voice_system.end_session(session_id)
        return jsonify(result)
    
    @app.route('/api/live/session/<session_id>/status', methods=['GET'])
    def get_session_status(session_id):
        """Get session status"""
        if session_id in live_voice_system.sessions:
            session = live_voice_system.sessions[session_id]
            return jsonify({
                'session_id': session_id,
                'status': session['status'],
                'created_at': session['created_at'],
                'message_count': len(session['conversation'])
            })
        return jsonify({'error': 'Session not found'}), 404