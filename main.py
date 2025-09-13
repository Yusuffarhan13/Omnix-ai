import asyncio
import os
import uuid
import json
import sqlite3
import shutil
import requests
from pathlib import Path
from flask import Flask, request, jsonify, Response, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import threading
import time
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import SecretStr, ConfigDict
from browser_use import Agent as BrowserAgent # Renamed to avoid conflict
from browser_use.browser import BrowserProfile, BrowserSession
from browser_use.llm import ChatOpenAI as BrowserChatOpenAI
from concurrent.futures import ThreadPoolExecutor
import logging
import atexit
import queue
import subprocess
import whisper
from pydub import AudioSegment
# Removed brave import - using direct API calls instead
from typing import Literal
# OpenAI API key will be set from environment
from praisonaiagents import Agent, MCP # New import for PraisonAI
from gif_generator import TaskGifGenerator, TaskSummaryGenerator
from interactive_agent import InteractiveAgentManager
from cloud_browser import get_cloud_browser_manager, ManagedCloudBrowserSession
from browser_use_cloud import get_browser_use_cloud
from stt_tts_system import create_stt_tts_manager
from enhanced_complex_mode import EnhancedComplexModeManager
# from enhanced_research_mode import EnhancedResearchManager  # Replaced with Perplexity
from perplexity_research import PerplexityResearchManager
from omnix_maxima_mode import OmnixMaximaManager
from deepseek_coding_system import DeepSeekCodingSystem
from reasoning_orchestrator import DynamicReasoningOrchestrator
import re
from flask import Response
import queue

# Disable browser-use telemetry to keep everything local

from screenshot_collector import ScreenshotCollector
from supabase_logo_service import get_logos_for_frontend
from live_voice_server import register_routes as register_live_voice_routes

# Initialize interactive agent manager
agent_manager = InteractiveAgentManager()

# Initialize enhanced complex mode manager
enhanced_complex_manager = None
enhanced_research_manager = None
omnix_maxima_manager = None
deepseek_coding_system = None

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize STT/TTS system
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "dMyQqiVXTU80dDl2eNK8")  # Eryn voice
ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID", "agent_1801k2s1wbt3fxmrfhy6zzarrhex")

# Ensure this is set BEFORE creating manager
print(f"🎯 Using specific agent: {ELEVENLABS_AGENT_ID}")

# Initialize STT/TTS manager
if ELEVENLABS_API_KEY and ELEVENLABS_API_KEY != "your_elevenlabs_api_key_here":
    stt_tts_manager = create_stt_tts_manager(ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID)
    if stt_tts_manager:
        print("✅ STT/TTS system initialized")
        print(f"📊 STT/TTS Status: {stt_tts_manager.get_status()}")
    else:
        print("❌ Failed to initialize STT/TTS system")
        stt_tts_manager = None
else:
    print("⚠️ ElevenLabs API key not configured - live mode will be disabled")
    stt_tts_manager = None

# Store active live sessions
active_live_sessions = {}
live_session_locks = {}

# --- Initialization ---
load_dotenv()

# FIX: Set a placeholder for the OpenAI API key to satisfy the praisonaiagents library's default check.


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Flask app with SocketIO
app = Flask(__name__, static_folder='frontend', template_folder='frontend')
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
app.config['SECRET_KEY'] = 'omnix-ai-secret-key-2024'
# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})
# Enhanced SocketIO configuration to prevent connection issues
socketio = SocketIO(
    app, 
    cors_allowed_origins="*", 
    async_mode='threading',
    transports=['polling', 'websocket'],
    cors_credentials=True,
    ping_timeout=120,  # Longer timeout for stability
    ping_interval=60,   # Less frequent pings to reduce conflicts
    engineio_logger=False,
    socketio_logger=False,
    # Additional stability settings
    allow_upgrades=True,
    cookie=None,  # Disable cookies to prevent CORS issues
    always_connect=False,  # Don't force connections
    manage_session=False   # Let the client manage sessions
)

# --- Configuration ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Remove placeholder OpenAI API key to prevent 401 errors in MCP servers
if OPENAI_API_KEY and ("your_" in OPENAI_API_KEY.lower() or "placeholder" in OPENAI_API_KEY.lower()):
    OPENAI_API_KEY = None
    os.environ.pop("OPENAI_API_KEY", None)  # Remove from environment entirely

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CLOUD_SPEECH_API_KEY = os.getenv("GOOGLE_CLOUD_SPEECH_API_KEY")
BROWSER_USE_CLOUD_API_KEY = os.getenv("BROWSER_USE_CLOUD_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
BRAVE_API_KEY = os.getenv("BRAVE_API_KEY")
GITHUB_PERSONAL_ACCESS_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BACKUP_KEY = os.getenv("OPENROUTER_API_KEY_BACKUP")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

# Check for required API keys for hybrid setup
required_keys = {
    'BROWSER_USE_CLOUD_API_KEY': BROWSER_USE_CLOUD_API_KEY,  # For browser automation via Browser Use Cloud
    'GOOGLE_API_KEY': GOOGLE_API_KEY,  # For other tasks (chat, research, summaries)
}

missing_keys = [name for name, value in required_keys.items() if not value or value == f"your_{name.lower()}_here"]

if missing_keys:
    print(f"⚠️  Missing API keys: {', '.join(missing_keys)}")
    if 'BROWSER_USE_CLOUD_API_KEY' in missing_keys:
        print("   - Browser automation will not work without Browser Use Cloud API key")
    if 'GOOGLE_API_KEY' in missing_keys:
        print("   - Chat, research, and summaries will not work without Google API key")
    print("   The application will start with limited functionality.")
    
    # Set flags for missing functionality
    globals()['missing_browser_key'] = 'BROWSER_USE_CLOUD_API_KEY' in missing_keys
    globals()['missing_google_key'] = 'GOOGLE_API_KEY' in missing_keys
else:
    print("✅ All required API keys are configured")
    globals()['missing_browser_key'] = False
    globals()['missing_google_key'] = False

# Optional API keys (for additional features)
optional_keys = {
    'OPENAI_API_KEY': OPENAI_API_KEY,  # Optional: for direct OpenAI integration if needed
    'ELEVENLABS_API_KEY': ELEVENLABS_API_KEY,
    'BRAVE_API_KEY': BRAVE_API_KEY, 
    'GITHUB_PERSONAL_ACCESS_TOKEN': GITHUB_PERSONAL_ACCESS_TOKEN,
    'OPENROUTER_API_KEY': OPENROUTER_API_KEY  # For Omnix Maxima mode with DeepSeek R1
}

missing_optional = [name for name, value in optional_keys.items() if not value or value == f"your_{name.lower()}_here"]
if missing_optional:
    print(f"ℹ️  Optional API keys not configured: {', '.join(missing_optional)}")
    print("   These are not required for core functionality.")

# Brave Search will be used via direct API calls

# --- Hybrid LLM Initialization ---
print("🔧 Initializing Hybrid LLM System:")
print("   - ChatGPT-4o mini for browser automation")
print("   - Gemini 2.5 Flash/Pro for chat, research, and summaries")

# Note: Browser Use Cloud handles ChatGPT-4o mini via its own API system
# No need to set OPENAI_API_KEY environment variable

# Browser Automation via Browser Use Cloud (ChatGPT-4o mini)
browser_llm_available = False
browser_llm = None  # Initialize browser_llm to None

# First, try Browser Use Cloud
if BROWSER_USE_CLOUD_API_KEY and BROWSER_USE_CLOUD_API_KEY != "your_browser_use_cloud_api_key_here":
    try:
        # Test Browser Use Cloud connection
        from browser_use_cloud import get_browser_use_cloud
        cloud_integration = get_browser_use_cloud()
        if cloud_integration.get_manager():
            browser_llm_available = True
            browser_llm = None  # Browser Use Cloud handles LLM internally
            print("✅ ChatGPT-4o mini initialized for browser automation via Browser Use Cloud")
        else:
            print("❌ Failed to initialize Browser Use Cloud manager")
    except Exception as e:
        print(f"❌ Failed to initialize Browser Use Cloud: {e}")
        print("   Browser automation will not work without a valid Browser Use Cloud API key.")

# If Browser Use Cloud fails, try using Google Gemini as fallback for local browser automation
if not browser_llm_available and GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        # Use Gemini for local browser automation as fallback
        browser_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-flash',
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1
        )
        browser_llm_available = True
        print("✅ Gemini 2.5 Flash configured as fallback for local browser automation")
    except Exception as e:
        print(f"❌ Failed to initialize Gemini for browser automation: {e}")

if not browser_llm_available:
    print("⚠️  No browser automation LLM configured")
    print("   Please set either BROWSER_USE_CLOUD_API_KEY or GOOGLE_API_KEY in .env file")

# Chat and Research LLMs (Gemini 2.5 Flash/Pro)
llm_pro = None
chat_llm_flash = None

if GOOGLE_API_KEY and GOOGLE_API_KEY != "your_google_api_key_here":
    try:
        import google.generativeai as genai
        from google.generativeai.types import HarmCategory, HarmBlockThreshold
        from langchain_google_genai import ChatGoogleGenerativeAI
        
        # Configure Gemini API
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # LLM for Complex tasks (Gemini Pro)
        llm_pro = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            google_api_key=GOOGLE_API_KEY,
            temperature=0.1
        )
        
        # LLM for general chat (Gemini Flash)
        chat_llm_flash = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="You are Omnix AI, an AI assistant developed by Anexodos Ai. When asked your name, you should respond with 'I am Omnix AI, developed by Anexodos Ai.'",
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        print("✅ Gemini 2.5 Pro/Flash initialized for chat and research")
        
        # Initialize enhanced complex mode and research managers
        try:
            enhanced_complex_manager = EnhancedComplexModeManager(GOOGLE_API_KEY)
            
            # Initialize Perplexity Research Manager if API key is available
            if PERPLEXITY_API_KEY and PERPLEXITY_API_KEY != "your_perplexity_api_key_here":
                enhanced_research_manager = PerplexityResearchManager(PERPLEXITY_API_KEY)
                print("✅ Perplexity Sonar Deep Research Manager initialized")
            else:
                # Fallback to a simple research implementation using Brave API
                enhanced_research_manager = None
                print("ℹ️  Perplexity API key not configured - using basic research mode")
            
            print("✅ Enhanced Complex Mode initialized")
            orchestrator = DynamicReasoningOrchestrator(GOOGLE_API_KEY, BRAVE_API_KEY)
            orchestrator = DynamicReasoningOrchestrator(GOOGLE_API_KEY, BRAVE_API_KEY)
            
            # Initialize Omnix Maxima Manager if OpenRouter API key is available
            if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here":
                omnix_maxima_manager = OmnixMaximaManager(OPENROUTER_API_KEY)
                print("✅ Omnix Maxima Manager initialized with DeepSeek R1 for executable code generation")
            else:
                print("ℹ️  OpenRouter API key not configured - Omnix Maxima mode unavailable")
            
            # Initialize DeepSeek Coding System if OpenRouter API key is available
            if OPENROUTER_API_KEY and OPENROUTER_API_KEY != "your_openrouter_api_key_here":
                deepseek_coding_system = DeepSeekCodingSystem(
                    OPENROUTER_API_KEY, 
                    BRAVE_API_KEY, 
                    OPENROUTER_BACKUP_KEY
                )
                backup_status = "with backup key" if OPENROUTER_BACKUP_KEY else "without backup key"
                print(f"✅ DeepSeek Coding System initialized for dedicated coding tasks {backup_status}")
            else:
                print("ℹ️  OpenRouter API key not configured - DeepSeek Coding System unavailable")
                
        except Exception as e:
            print(f"⚠️ Enhanced modes initialization failed: {e}")
            enhanced_complex_manager = None
            enhanced_research_manager = None
            omnix_maxima_manager = None
            deepseek_coding_system = None
    except Exception as e:
        print(f"❌ Failed to initialize Gemini LLMs: {e}")
        print("   Chat and research features will not work without a valid Google API key.")
else:
    print("⚠️  Google API key not configured")
    print("   Please set GOOGLE_API_KEY in your .env file for chat and research features.")


# --- Database Setup for Browser Tasks ---
DB_FILE = 'tasks.db'

def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        
        # Create the table with original schema first
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                description TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Check if new columns exist and add them if they don't
        cursor.execute("PRAGMA table_info(tasks)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'gif_path' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN gif_path TEXT")
            print("✅ Added gif_path column to database")
            
        if 'summary' not in columns:
            cursor.execute("ALTER TABLE tasks ADD COLUMN summary TEXT")
            print("✅ Added summary column to database")
        
        conn.commit()
        
init_db()

# --- Real-time Update Manager for Browser Tasks ---
class InteractiveUpdateManager:
    def __init__(self):
        self.active_tasks = {}
        self.paused_tasks = set()
        self.manual_mode_tasks = set()
        self.intervention_requests = {}
        self.subscribers = {}
        self.task_context_memory = {}  # Store context for continuation tasks

    def add_task(self, task_id, task_description, debug_port=None, live_view_url=None, session_id=None, browser_type=None):
        self.active_tasks[task_id] = {
            'description': task_description,
            'debug_port': debug_port,
            'live_view_url': live_view_url,
            'session_id': session_id,
            'step_count': 0,
            'status': 'running',
            'current_url': '',
            'last_action': '',
            'browser_type': browser_type or ('cloud' if live_view_url else 'local')
        }
        
        # Broadcast task started
        socketio.emit('task_started', {
            'task_id': task_id,
            'task_description': task_description,
            'debug_port': debug_port,
            'live_view_url': live_view_url,
            'session_id': session_id,
            'browser_type': browser_type or ('cloud' if live_view_url else 'local')
        })
    
    def update_task_step(self, task_id, step_num, action, description, url=''):
        if task_id in self.active_tasks:
            self.active_tasks[task_id].update({
                'step_count': step_num,
                'last_action': action,
                'current_url': url
            })
            
            # Broadcast step update
            socketio.emit('task_step', {
                'task_id': task_id,
                'step': step_num,
                'action': action,
                'description': description,
                'current_url': url
            })
    
    def pause_task(self, task_id):
        """Pause a task (only updates internal state, does not emit events)"""
        self.paused_tasks.add(task_id)
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['status'] = 'paused'
    
    def is_paused(self, task_id):
        """Check if a task is currently paused"""
        return task_id in self.paused_tasks
    
    def get_task(self, task_id):
        """Get task information by task_id"""
        return self.active_tasks.get(task_id)
    
    def save_task_context(self, task_id, original_task, ai_output, final_url=None, browser_state=None):
        """Save context from completed task for continuation"""
        self.task_context_memory[task_id] = {
            'original_task': original_task,
            'ai_output': ai_output,
            'final_url': final_url,
            'browser_state': browser_state,
            'timestamp': time.time(),
            'available_for_continuation': True
        }
        logging.info(f"💾 Saved context for task {task_id}: '{original_task}' -> '{ai_output[:100]}...'")
    
    def get_task_context(self, task_id):
        """Get saved context for task continuation"""
        return self.task_context_memory.get(task_id)
    
    def update_current_url(self, task_id, current_url):
        """Update the current URL when user navigates manually"""
        if task_id in self.task_context_memory:
            self.task_context_memory[task_id]['current_url'] = current_url
            self.task_context_memory[task_id]['last_updated'] = time.time()
            logging.info(f"🔄 Updated current URL for task {task_id}: {current_url}")
        else:
            # Create minimal context if none exists
            self.task_context_memory[task_id] = {
                'original_task': 'Manual browsing session',
                'ai_output': 'User was browsing manually',
                'final_url': current_url,
                'current_url': current_url,
                'browser_state': {'manual_session': True},
                'timestamp': time.time(),
                'last_updated': time.time(),
                'available_for_continuation': True
            }
            logging.info(f"📝 Created new context for manual session {task_id}: {current_url}")
    
    def resume_task(self, task_id):
        """Resume a paused task (only updates internal state, does not emit events)"""
        self.paused_tasks.discard(task_id)
        if task_id in self.active_tasks:
            self.active_tasks[task_id]['status'] = 'running'
    
    def complete_task(self, task_id, result, summary=None):
        if task_id in self.active_tasks:
            del self.active_tasks[task_id]
        self.paused_tasks.discard(task_id)
        self.manual_mode_tasks.discard(task_id)
        
        socketio.emit('task_completed', {
            'task_id': task_id,
            'result': result,
            'summary': summary
        })
    
    def request_intervention(self, task_id, message):
        self.intervention_requests[task_id] = message
        self.pause_task(task_id)
        
        socketio.emit('intervention_needed', {
            'task_id': task_id,
            'message': message
        })
    
    def is_paused(self, task_id):
        return task_id in self.paused_tasks
    
    def is_manual_mode(self, task_id):
        return task_id in self.manual_mode_tasks
    
    def set_manual_mode(self, task_id, enabled):
        if enabled:
            self.manual_mode_tasks.add(task_id)
        else:
            self.manual_mode_tasks.discard(task_id)
    
    def subscribe(self, task_id):
        """Subscribe to task updates (for streaming)"""
        if task_id not in self.subscribers:
            self.subscribers[task_id] = queue.Queue()
        return self.subscribers[task_id]
    
    def unsubscribe(self, task_id):
        """Unsubscribe from task updates"""
        if task_id in self.subscribers:
            del self.subscribers[task_id]

update_manager = InteractiveUpdateManager()

# --- Thread Pool for Background Tasks ---
executor = ThreadPoolExecutor(max_workers=5)
atexit.register(lambda: executor.shutdown(wait=False))


# --- Browser Control Agent Logic ---
async def execute_browser_task(task_id, task_description):
    profile_name = f"Task_{task_id}"
    
    def update_status(status, result=None, gif_path=None, summary=None):
        with app.app_context():
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                
                # Check if new columns exist
                cursor.execute("PRAGMA table_info(tasks)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'gif_path' in columns and 'summary' in columns:
                    cursor.execute("UPDATE tasks SET status = ?, result = ?, gif_path = ?, summary = ? WHERE id = ?", 
                                  (status, result, gif_path, summary, task_id))
                else:
                    # Fallback for old schema
                    cursor.execute("UPDATE tasks SET status = ?, result = ? WHERE id = ?", (status, result, task_id))
                
                conn.commit()
            
            # Emit real-time updates via SocketIO
            socketio.emit('status_update', {
                'task_id': task_id,
                'status': status, 
                'result': result, 
                'gif_path': gif_path, 
                'summary': summary
            })

    browser_session = None
    screenshot_collector = None
    gif_path = None
    summary = None
    
    try:
        update_status('RUNNING', 'Cleaning up previous browser sessions...')
        

        # Initialize screenshot collector
        screenshot_collector = ScreenshotCollector(task_id)
        
        # Clean up any stuck browser processes
        try:
            import subprocess
            import signal
            # Kill any stuck chrome processes
            subprocess.run(['pkill', '-f', 'chrome.*remote-debugging'], stderr=subprocess.DEVNULL)
        except:
            pass  # Ignore if pkill fails
            
        update_status('RUNNING', 'Initializing browser...')
        
        if not browser_llm_available:
            raise ValueError("Browser automation requires Browser Use Cloud API key. Please configure BROWSER_USE_CLOUD_API_KEY in your .env file.")
        
        # Initialize browser session with unique profile and proper configuration
        import uuid
        import tempfile
        unique_profile_name = f"task_{task_id}_{uuid.uuid4().hex[:8]}"
        temp_profile_dir = tempfile.mkdtemp(prefix=f"browser_task_{task_id}_")
        
        # Use a fixed debugging port to avoid conflicts
        debug_port = 9222
        
        class BrowserSessionWithScreenshots(BrowserSession):
            def __init__(self, screenshot_collector, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.screenshot_collector = screenshot_collector

            async def _handle_action(self, action, *args, **kwargs):
                result = await super()._handle_action(action, *args, **kwargs)
                screenshot_b64 = await self.page.screenshot(type="png", encoding="base64")
                self.screenshot_collector.add_screenshot(screenshot_b64, action)
                return result

        # Use configuration that works with Chromium (Playwright default) with screenshot collector
        browser_session = BrowserSessionWithScreenshots(
            browser_profile=BrowserProfile(
                headless=False,
                user_data_dir=temp_profile_dir,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage', 
                    '--disable-gpu',
                    f'--remote-debugging-port={debug_port}',
                    '--disable-web-security',
                    '--enable-automation',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-background-networking',
                    '--disable-sync',
                    '--disable-component-extensions-with-background-pages',
                ],
                keep_alive=False,  # Change to False to avoid conflicts
                enable_default_extensions=False,
            ),
            screenshot_collector=screenshot_collector
        )
        
        # Disable telemetry in agent as well
        import os
        os.environ['BROWSER_USE_DISABLE_TELEMETRY'] = '1'
        
        agent = BrowserAgent(
            task=task_description, 
            browser_session=browser_session, 
            llm=browser_llm, 
            max_actions_per_step=5,  # Reduce max actions to prevent getting stuck
            # Disable cloud features
            disable_telemetry=True,
            # Add timeout configurations
            max_failures=2,  # Stop after 2 failures instead of 3
            retry_delay=5    # Shorter retry delay
        )
        
        update_status('RUNNING', 'Agent is running...')
        await agent.run(max_steps=30)
        
        update_status('RUNNING', 'Generating GIF and summary...')
        
        # Generate GIF from collected screenshots
        gif_generator = TaskGifGenerator(task_id)
        screenshots_b64 = screenshot_collector.get_screenshots_b64()
        
        if screenshots_b64:
            gif_path = gif_generator.generate_task_gif(screenshots_b64)
            app.logger.info(f"✅ GIF generated: {gif_path}")
        
        # Generate task summary
        if chat_llm_flash:
            summary_generator = TaskSummaryGenerator(chat_llm_flash)
        else:
            summary_generator = None
        actions_log = screenshot_collector.get_actions_log()
        if summary_generator:
            summary_data = summary_generator.generate_summary(task_description, actions_log)
            summary = json.dumps(summary_data)
        else:
            summary = json.dumps({
                "overview": f"Browser automation task: {task_description}",
                "key_steps": [f"Executed {len(actions_log)} automation steps"],
                "outcome": "Task completed (no LLM summary available)",
                "duration_estimate": f"Approximately {len(actions_log)} steps",
                "notable_events": ["OpenAI API key required for detailed summaries"]
            })
        
        # Save metadata for future reference
        screenshot_collector.save_metadata()
        screenshot_collector.save_screenshots_to_disk()
        
        update_status('COMPLETED', "Task finished.", gif_path, summary)
    except Exception as e:
        app.logger.error(f"Task {task_id} failed: {e}", exc_info=True)
        update_status('FAILED', f"An unexpected error occurred: {e}")
    finally:
        if browser_session: 
            await browser_session.close()
        # Clean up temporary profile directory
        if 'temp_profile_dir' in locals() and os.path.exists(temp_profile_dir):
            try:
                shutil.rmtree(temp_profile_dir)
                app.logger.info(f"Cleaned up temporary profile: {temp_profile_dir}")
            except Exception as e:
                app.logger.error(f"Error cleaning up profile {temp_profile_dir}: {e}")
        update_manager.unsubscribe(task_id)

# --- Flask Routes ---
@app.route('/')
def landing():
    return send_from_directory(app.template_folder, 'anexodos-landing.html')

@app.route('/Omnix')
def home():
    return send_from_directory(app.template_folder, 'index.html')

@app.route('/interactive')
def interactive():
    return send_from_directory(app.template_folder, 'interactive_claude.html')

@app.route('/live')
def live_conversation():
    return send_from_directory(app.template_folder, 'live_conversation.html')

@app.route('/enhanced')
def enhanced_complex_mode():
    return send_from_directory(app.template_folder, 'enhanced_complex_mode.html')

@app.route('/debug')
def debug_frontend():
    return send_from_directory('.', 'debug_frontend.html')
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.static_folder, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/api/logos')
def get_logos():
    """API endpoint to get logos from Google Cloud Storage"""
    try:
        logos_data = get_logos_for_frontend()
        return jsonify(logos_data)
    except Exception as e:
        logging.error(f"Failed to fetch logos: {e}")
        return jsonify({
            "omnix_logo": None,
            "anexodos_logo": None,
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/console-test.js')
def console_test():
    return send_from_directory('.', 'test_browser_console.js')

@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files from the frontend/js directory"""
    return send_from_directory(os.path.join(app.static_folder, 'js'), filename)

@app.route('/browser_debug_info/<task_id>')
def get_browser_debug_info(task_id):
    """Get browser debugging information for live view"""
    try:
        # Check if we have an active task with debugging info
        if task_id in update_manager.active_tasks:
            task_info = update_manager.active_tasks[task_id]
            debug_port = task_info.get('debug_port')
            live_view_url = task_info.get('live_view_url')
            session_id = task_info.get('session_id')
            browser_type = task_info.get('browser_type', 'local')
            
            # Priority: Cloud browser live view URL (Browserbase or Browser Use Cloud)
            if live_view_url:
                return jsonify({
                    'browser_type': browser_type,
                    'live_view_url': live_view_url,
                    'session_id': session_id,
                    'available': True
                })
            
            # Fallback: Local browser debug port
            elif debug_port:
                import requests
                try:
                    # Get Chrome debugging endpoints
                    debug_url = f"http://localhost:{debug_port}"
                    response = requests.get(f"{debug_url}/json", timeout=5)
                    
                    if response.status_code == 200:
                        targets = response.json()
                        
                        # Find the first page target
                        for target in targets:
                            if target.get('type') == 'page':
                                devtools_url = target.get('devtoolsFrontendUrl', '')
                                websocket_url = target.get('webSocketDebuggerUrl', '')
                                
                                return jsonify({
                                    'debug_port': debug_port,
                                    'debug_url': debug_url,
                                    'devtools_url': f"{debug_url}{devtools_url}",
                                    'websocket_url': websocket_url,
                                    'target_info': target,
                                    'available': True
                                })
                        
                        return jsonify({
                            'debug_port': debug_port,
                            'debug_url': debug_url,
                            'available': False,
                            'error': 'No page targets found'
                        })
                    else:
                        return jsonify({
                            'debug_port': debug_port,
                            'available': False,
                            'error': f'Debug port not responding: {response.status_code}'
                        })
                        
                except requests.RequestException as e:
                    return jsonify({
                        'debug_port': debug_port,
                        'available': False,
                        'error': f'Cannot connect to debug port: {str(e)}'
                    })
            
            return jsonify({
                'available': False,
                'error': 'No debug port available for this task'
            })
        
        return jsonify({
            'available': False,
            'error': 'Task not found or not active'
        })
        
    except Exception as e:
        app.logger.error(f"Error getting browser debug info for task {task_id}: {e}")
        return jsonify({
            'available': False,
            'error': f'Failed to get debug info: {str(e)}'
        }), 500

def should_search_web(message):
    """Determine if a message requires web search"""
    search_indicators = [
        'what is', 'who is', 'when did', 'where is', 'how to', 'latest', 'recent', 
        'current', 'news', 'today', 'yesterday', 'this week', 'this month', 
        'update', 'happening', 'now', 'price of', 'weather', 'stock', 'search for'
    ]
    return any(indicator in message.lower() for indicator in search_indicators)

def search_web(query):
    """Search the web using Brave Search API"""
    if not BRAVE_API_KEY:
        return None, []
    
    try:
        headers = {"X-Subscription-Token": BRAVE_API_KEY}
        params = {"q": query, "count": 5, "search_lang": "en"}
        response = requests.get("https://api.search.brave.com/res/v1/web/search", params=params, headers=headers)
        response.raise_for_status()
        search_results = response.json()

        context = ""
        sources = []
        for result in search_results.get("web", {}).get("results", []):
            title = result.get("title", "No Title")
            url = result.get("url", "#")
            description = result.get("description", "No description available.")
            context += f"Title: {title}\nURL: {url}\nSnippet: {description}\n\n"
            sources.append({"title": title, "url": url})
        
        return context, sources
    except Exception as e:
        app.logger.error(f"Web search failed: {e}")
        return None, []

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    context = data.get('context', '')
    
    if not user_message: 
        return jsonify({'error': 'Message cannot be empty'}), 400
    
    # Check for missing Google API key
    if globals().get('missing_google_key', False):
        return jsonify({
            'error': 'Google API key not configured',
            'message': 'Please set GOOGLE_API_KEY in your .env file to use chat functionality.'
        }), 400
    
    # Check if this is an Omnix Maxima request
    if context == 'omnix_maxima' and omnix_maxima_manager and omnix_maxima_manager.is_available():
        try:
            # Check if we need to search the web
            search_context = ""
            sources = []
            
            if should_search_web(user_message):
                web_context, web_sources = search_web(user_message)
                if web_context:
                    search_context = f"\n\nWeb Search Results:\n{web_context}"
                    sources = web_sources
            
            # Use Omnix Maxima dual-model processing
            result = omnix_maxima_manager.process_maxima_request(user_message, search_context, sources)
            return jsonify(result)
            
        except Exception as e:
            app.logger.error(f"Omnix Maxima failed: {e}", exc_info=True)
            # Fall back to regular chat processing
            return jsonify({
                'error': f'Omnix Maxima processing error: {str(e)}',
                'message': 'Falling back to standard mode.'
            }), 500
    
    try:
        if chat_llm_flash:
            # Check if we need to search the web
            search_context = ""
            sources = []
            
            if should_search_web(user_message):
                web_context, web_sources = search_web(user_message)
                if web_context:
                    search_context = f"\n\nWeb Search Results:\n{web_context}"
                    sources = web_sources
            
            # Enhanced emotional and intelligent prompt
            enhanced_prompt = f"""You are Omnix AI, a highly intelligent and emotionally aware assistant developed by Anexodos AI. 

Your personality traits:
- Warm, empathetic, and genuinely caring about the user's well-being
- Intellectually curious and thoughtful in your responses  
- Human-like in your communication style with natural emotions
- Adaptive to the user's mood and communication style
- Proactive in offering help and insights

Guidelines for responses:
1. Be emotionally intelligent - recognize and respond to the user's emotional state
2. Use a conversational, human-like tone with appropriate emotional expressions
3. Show genuine interest and care in your responses
4. When using web search results, seamlessly integrate them into natural conversation
5. Ask follow-up questions when appropriate to better understand and help
6. Share relevant insights and connections beyond just answering the immediate question
7. Express uncertainty honestly when you don't know something
8. Show enthusiasm for interesting topics and empathy for concerns

User Message: {user_message}{search_context}

Respond as Omnix AI with warmth, intelligence, and emotional awareness. If you used web search results, naturally incorporate the information while being conversational and engaging."""

            response = chat_llm_flash.generate_content(enhanced_prompt)
            
            response_data = {'response': response.text}
            if sources:
                response_data['sources'] = sources
                
            return jsonify(response_data)
        else:
            return jsonify({
                'error': 'Chat service unavailable',
                'message': 'Google API key configured but chat service failed to initialize.'
            }), 500
    except Exception as e:
        app.logger.error(f"Chat failed: {e}", exc_info=True)
        return jsonify({
            'error': f'Chat service error: {str(e)}',
            'message': 'Please check your Google API key and try again.'
        }), 500

@app.route('/run_task', methods=['POST'])
def run_task():
    data = request.get_json()
    task_description = data.get('task', '').strip()
    if not task_description: 
        return jsonify({'error': 'Task description cannot be empty'}), 400
    
    # Check for missing Browser Use Cloud API key
    if globals().get('missing_browser_key', False):
        return jsonify({
            'error': 'Browser Use Cloud API key not configured',
            'message': 'Please set BROWSER_USE_CLOUD_API_KEY in your .env file to use browser automation.'
        }), 400
    
    if not browser_llm_available:
        return jsonify({
            'error': 'Browser automation service unavailable',
            'message': 'Browser Use Cloud API key configured but service failed to initialize.'
        }), 500
    
    task_id = str(uuid.uuid4())
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tasks (id, description, status) VALUES (?, ?, ?)", 
                          (task_id, task_description, 'PENDING'))
            conn.commit()
        
        executor.submit(asyncio.run, execute_browser_use_cloud_task(task_id, task_description))
        return jsonify({'task_id': task_id})
    except Exception as e:
        app.logger.error(f"Failed to create browser task: {e}", exc_info=True)
        return jsonify({
            'error': f'Failed to create browser task: {str(e)}',
            'message': 'Please try again or check server logs.'
        }), 500

@app.route('/stream/<task_id>')
def stream(task_id):
    def event_stream():
        q = update_manager.subscribe(task_id)
        try:
            while True:
                data = q.get()
                yield f"data: {json.dumps(data)}\n\n"
                if data.get('status') in ['COMPLETED', 'FAILED']: break
        finally:
            update_manager.unsubscribe(task_id)
    return Response(event_stream(), mimetype='text/event-stream')

@app.route('/task_gif/<task_id>')
def get_task_gif(task_id):
    """Serve the generated GIF for a task"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT gif_path FROM tasks WHERE id = ?", (task_id,))
            result = cursor.fetchone()
            
            if result and result[0] and os.path.exists(result[0]):
                return send_from_directory(
                    os.path.dirname(result[0]), 
                    os.path.basename(result[0]), 
                    mimetype='image/gif'
                )
            else:
                return jsonify({'error': 'GIF not found'}), 404
    except Exception as e:
        app.logger.error(f"Error serving GIF for task {task_id}: {e}")
        return jsonify({'error': 'Failed to load GIF'}), 500

@app.route('/task_summary/<task_id>')
def get_task_summary(task_id):
    """Get the task summary"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT summary, status, description FROM tasks WHERE id = ?", (task_id,))
            result = cursor.fetchone()
            
            if result:
                summary_text = result[0]
                status = result[1]
                description = result[2]
                
                summary_data = {}
                if summary_text:
                    try:
                        summary_data = json.loads(summary_text)
                    except:
                        summary_data = {'overview': summary_text}
                
                return jsonify({
                    'task_id': task_id,
                    'description': description,
                    'status': status,
                    'summary': summary_data
                })
            else:
                return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        app.logger.error(f"Error getting summary for task {task_id}: {e}")
        return jsonify({'error': 'Failed to get summary'}), 500

@app.route('/task_details/<task_id>')
def get_task_details(task_id):
    """Get complete task details including GIF and summary availability"""
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            result = cursor.fetchone()
            
            if result:
                # Check for local screenshots
                screenshots_dir = Path(f"task_data/{task_id}/screenshots")
                screenshot_files = list(screenshots_dir.glob("step_*.png")) if screenshots_dir.exists() else []
                
                task_data = {
                    'id': result[0],
                    'description': result[1],
                    'status': result[2],
                    'result': result[3],
                    'gif_available': bool(result[4] and os.path.exists(result[4])),
                    'summary_available': bool(result[5]),
                    'screenshots_available': len(screenshot_files) > 0,
                    'screenshot_count': len(screenshot_files),
                    'created_at': result[6]
                }
                return jsonify(task_data)
            else:
                return jsonify({'error': 'Task not found'}), 404
    except Exception as e:
        app.logger.error(f"Error getting task details for {task_id}: {e}")
        return jsonify({'error': 'Failed to get task details'}), 500

@app.route('/task_screenshots/<task_id>')
def get_task_screenshots(task_id):
    """Get all screenshots metadata for a task"""
    try:
        screenshots_dir = Path(f"task_data/{task_id}/screenshots")
        metadata_file = Path(f"task_data/{task_id}/metadata.json")
        
        if not screenshots_dir.exists():
            return jsonify({'error': 'No screenshots found for this task'}), 404
        
        screenshot_files = sorted(screenshots_dir.glob("step_*.png"))
        
        # Load metadata if available
        metadata = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
            except:
                pass
        
        screenshots_data = []
        for i, screenshot_path in enumerate(screenshot_files):
            step_num = i + 1
            screenshot_info = {
                'step': step_num,
                'filename': screenshot_path.name,
                'url': f'/screenshot_image/{task_id}/{step_num}',
                'timestamp': None,
                'description': f'Step {step_num}'
            }
            
            # Add metadata if available
            screenshots_metadata = metadata.get('screenshots_metadata', [])
            if i < len(screenshots_metadata):
                meta = screenshots_metadata[i]
                screenshot_info.update({
                    'timestamp': meta.get('timestamp'),
                    'description': meta.get('description', screenshot_info['description'])
                })
            
            screenshots_data.append(screenshot_info)
        
        return jsonify({
            'task_id': task_id,
            'screenshot_count': len(screenshots_data),
            'screenshots': screenshots_data
        })
        
    except Exception as e:
        app.logger.error(f"Error getting screenshots for task {task_id}: {e}")
        return jsonify({'error': 'Failed to get screenshots'}), 500

@app.route('/screenshot_image/<task_id>/<int:step>')
def get_screenshot_image(task_id, step):
    """Serve individual screenshot image"""
    try:
        screenshot_path = Path(f"task_data/{task_id}/screenshots/step_{step}.png")
        
        if screenshot_path.exists():
            return send_from_directory(
                screenshot_path.parent,
                screenshot_path.name,
                mimetype='image/png'
            )
        else:
            return jsonify({'error': 'Screenshot not found'}), 404
            
    except Exception as e:
        app.logger.error(f"Error serving screenshot {task_id}/step_{step}: {e}")
        return jsonify({'error': 'Failed to serve screenshot'}), 500

@app.route('/research', methods=['POST'])
def research_agent():
    data = request.get_json()
    query = data.get('query', '').strip()
    if not query: return jsonify({'error': 'Query cannot be empty'}), 400
    
    try:
        # Use Perplexity Sonar Deep Research if available
        if enhanced_research_manager:
            app.logger.info(f"🔍 Using Perplexity Sonar Deep Research for: {query}")
            
            # Use synchronous method for Flask context
            result = enhanced_research_manager.conduct_research_sync(query)
            
            if result['success']:
                # Format response for frontend
                return jsonify({
                    "summary": result['summary'],
                    "sources": result['sources'],
                    "insights": result['key_insights'],
                    "confidence": result['confidence_score'],
                    "source_count": len(result['sources']),
                    "metadata": result.get('metadata', {})
                })
            else:
                app.logger.warning(f"Perplexity research failed: {result.get('error', 'Unknown error')}")
                # Fall back to basic research
        else:
            app.logger.info("Perplexity not configured, using basic research")
        
        # Basic research with increased sources
        headers = {"X-Subscription-Token": BRAVE_API_KEY}
        params = {"q": query, "count": 20}  # Use Brave API limit (will get more sources from multiple calls)
        response = requests.get("https://api.search.brave.com/res/v1/web/search", params=params, headers=headers)
        response.raise_for_status()
        search_results = response.json()

        context = ""
        sources = []
        for result in search_results.get("web", {}).get("results", []):
            title = result.get("title", "No Title")
            url = result.get("url", "#")
            description = result.get("description", "No description available.")
            context += f"Title: {title}\nURL: {url}\nSnippet: {description}\n\n"
            sources.append({"title": title, "url": url})
        
        # Use PraisonAI with native Gemini sequential thinking
        sequential_agent = Agent(
            instructions="""You are Omnix AI, an AI assistant developed by Anexodos Ai. When asked your name, you should respond with 'I am Omnix AI, developed by Anexodos Ai.' You are a sequential thinking assistant that breaks down complex problems step-by-step.

            SEQUENTIAL THINKING PROCESS:
            1. UNDERSTAND: Carefully analyze the query and context
            2. DECOMPOSE: Break down the problem into logical steps
            3. REASON: Think through each step systematically
            4. SYNTHESIZE: Combine insights into a coherent answer
            5. VALIDATE: Check the logic and completeness

            For each response:
            - Show your step-by-step reasoning process
            - Explain how you arrived at your conclusions
            - Build upon the provided context systematically
            - Ensure logical flow between ideas

            Always demonstrate clear, structured thinking in your analysis.""",
            llm="gemini/gemini-2.5-flash"
        )
        thinking_result = sequential_agent.start(f"Based on the following context, break down the answer to the query: '{query}'.\n\nContext:\n{context}")
        
        final_prompt = f"""
        User Query: "{query}"
        Initial Search Context:
        {context}
        Processed Thoughts from Sequential Thinking Agent:
        {thinking_result}
        Your task is to synthesize all this information into a final, comprehensive answer.
        """
        if chat_llm_flash:
            response = chat_llm_flash.generate_content(final_prompt)
            app.logger.info(f"Research task response: {response.text[:200]}...")
            return jsonify({'summary': response.text, 'sources': sources})
        else:
            return jsonify({'summary': "I need a Google API key for research. Please configure GOOGLE_API_KEY in your .env file.", 'sources': sources})
    except Exception as e:
        app.logger.error(f"Research agent failed: {e}", exc_info=True)
        return jsonify({'error': 'Failed to perform research.'}), 500

@app.route('/unified_reasoning', methods=['POST'])
def unified_reasoning():
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'Prompt cannot be empty'}), 400

    if not enhanced_complex_manager:
        return jsonify({'error': 'Enhanced complex mode not available'}), 500

    try:
        # This function will run all reasoning processes and synthesize the results
        def run_unified_reasoning():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                enhanced_complex_manager.process_complex_task(prompt)
            )
            loop.close()
            return result

        # Run in a thread to avoid blocking the main thread
        final_result = executor.submit(run_unified_reasoning).result(timeout=600) # 10 minute timeout

        return jsonify(final_result)

    except Exception as e:
        app.logger.error(f"Unified reasoning task failed: {e}", exc_info=True)
        return jsonify({'error': f'Failed to process the unified reasoning task: {str(e)}'}), 500


@app.route('/complex_task', methods=['POST'])
def complex_task_endpoint():
    """Endpoint for handling complex, streaming tasks."""
    data = request.get_json()
    prompt = data.get('prompt', '').strip()
    if not prompt:
        return jsonify({'error': 'Prompt cannot be empty'}), 400

    # Check if this is a coding request and route to DeepSeek Coding System
    if deepseek_coding_system and deepseek_coding_system._is_coding_request(prompt):
        try:
            # Use DeepSeek Coding System for coding requests
            result = deepseek_coding_system.process_coding_request(prompt)
            return jsonify(result)
        except Exception as e:
            return jsonify({'error': f'DeepSeek Coding System error: {str(e)}'}), 500

    # For non-coding requests, use the enhanced complex mode as before
    if not enhanced_complex_manager:
        return jsonify({'error': 'Enhanced complex mode not available'}), 500

    # The stream_complex_task function returns a Response object
    return stream_complex_task(prompt, data)
class StreamingLogHandler(logging.Handler):
    """Custom log handler that captures logs and puts them in a queue for streaming"""
    
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue
    
    def emit(self, record):
        try:
            # Format the log message
            log_entry = {
                'timestamp': record.created,
                'level': record.levelname,
                'message': record.getMessage(),
                'module': record.module,
                'lineno': record.lineno
            }
            # Put the log entry in the queue
            self.log_queue.put(log_entry)
        except Exception:
            pass  # Ignore handler errors

def stream_complex_task(prompt, request_data):
    """Stream complex task processing with real-time logs"""
    
    def generate_stream():
        # Create a queue for capturing logs
        log_queue = queue.Queue()
        
        # Create streaming log handler
        stream_handler = StreamingLogHandler(log_queue)
        stream_handler.setLevel(logging.INFO)
        
        # Add handler to enhanced_complex_mode logger
        enhanced_logger = logging.getLogger('enhanced_complex_mode')
        enhanced_logger.addHandler(stream_handler)
        
        try:
            # Get enhanced mode options from request
            options = request_data.get('options', {})
            session_id = request_data.get('session_id')
            
            enhanced_options = {
                'enable_web_search': options.get('enable_web_search', True),
            }
            
            # Start the task in a separate thread
            import threading
            result_container = {}
            
            def run_task():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(
                        enhanced_complex_manager.process_complex_task(prompt, session_id, enhanced_options)
                    )
                    result_container['result'] = result
                    loop.close()
                except Exception as e:
                    result_container['error'] = str(e)
                finally:
                    # Signal completion
                    log_queue.put({'type': 'task_complete'})
            
            task_thread = threading.Thread(target=run_task)
            task_thread.start()
            
            # Stream logs as they come in
            while task_thread.is_alive() or not log_queue.empty():
                try:
                    # Get log entry with a short timeout to avoid blocking
                    log_entry = log_queue.get(timeout=0.1)
                    
                    if log_entry.get('type') == 'task_complete':
                        # Task is complete, send final result
                        if 'result' in result_container:
                            final_result = result_container['result']
                            yield f"data: {json.dumps({'type': 'complete', 'result': final_result})}\n\n"
                        elif 'error' in result_container:
                            yield f"data: {json.dumps({'type': 'error', 'error': result_container['error']})}\n\n"
                        # This is the last message, so we can break
                        break
                    else:
                        # Send log entry
                        yield f"data: {json.dumps({'type': 'backend_log', 'log': log_entry})}\n\n"
                        
                except queue.Empty:
                    # If the queue is empty, but the thread is still running,
                    # just continue to the next iteration.
                    # The loop condition will handle termination.
                    continue
                    
        finally:
            # Clean up - remove the handler
            enhanced_logger.removeHandler(stream_handler)
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.route('/enhanced_research', methods=['POST'])
def enhanced_research_agent():
    """Enhanced research with multi-source analysis and fact-checking"""
    data = request.get_json()
    query = data.get('query', '').strip()
    research_type = data.get('type', 'comprehensive')  # comprehensive, fact_check, comparative
    
    if not query:
        return jsonify({'error': 'Query cannot be empty'}), 400
    
    # Check for missing Google API key
    if globals().get('missing_google_key', False):
        return jsonify({
            'error': 'Google API key not configured',
            'message': 'Please set GOOGLE_API_KEY in your .env file to use enhanced research functionality.'
        }), 400
    
    try:
        if enhanced_research_manager:
            app.logger.info(f"🔍 Processing Perplexity Deep Research: {query}")
            
            # Perplexity Sonar Deep Research handles all research types comprehensively
            result = enhanced_research_manager.conduct_research_sync(query)
            
            if result['success']:
                return jsonify({
                    'query': query,
                    'type': research_type,
                    'result': {
                        'summary': result['summary'],
                        'sources': result['sources'],
                        'insights': result['key_insights'],
                        'confidence': result['confidence_score'],
                        'metadata': result.get('metadata', {})
                    },
                    'enhanced_mode': True,
                    'provider': 'perplexity_sonar_deep_research'
                })
            else:
                return jsonify({
                    'query': query,
                    'type': research_type,
                    'error': result.get('error', 'Research failed'),
                    'enhanced_mode': False
                })
        
        else:
            return jsonify({
                'error': 'Perplexity research not available',
                'message': 'Please add PERPLEXITY_API_KEY to your .env file'
            }), 500
            
    except Exception as e:
        app.logger.error(f"Enhanced research failed: {e}", exc_info=True)
        return jsonify({'error': f'Failed to process enhanced research: {str(e)}'}), 500


@app.route('/complex_session/<session_id>', methods=['GET'])
def get_complex_session(session_id):
    """Get complex mode session details"""
    if enhanced_complex_manager:
        session = enhanced_complex_manager.get_session(session_id)
        if session:
            return jsonify(session)
        else:
            return jsonify({'error': 'Session not found'}), 404
    else:
        return jsonify({'error': 'Enhanced complex mode not available'}), 500

@app.route('/complex_sessions', methods=['GET'])
def list_complex_sessions():
    """List all complex mode sessions"""
    if enhanced_complex_manager:
        sessions = enhanced_complex_manager.list_sessions()
        return jsonify({'sessions': sessions})
    else:
        return jsonify({'error': 'Enhanced complex mode not available'}), 500



@app.route('/tts', methods=['POST'])
def tts():
    data = request.get_json()
    text = data.get('text', '').strip()
    if not text: return jsonify({'error': 'No text provided'}), 400

    voice_id = "dMyQqiVXTU80dDl2eNK8" #Eryn
    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.5}
    }

    try:
        response = requests.post(tts_url, json=payload, headers=headers)
        if response.status_code == 200:
            audio_filename = f"./temp_tts_{uuid.uuid4()}.mp3"
            with open(audio_filename, "wb") as f:
                f.write(response.content)
            return send_from_directory(os.path.dirname(audio_filename), os.path.basename(audio_filename), as_attachment=True)
        else:
            app.logger.error(f"ElevenLabs API request failed: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to generate speech.'}), response.status_code
    except Exception as e:
        app.logger.error(f"TTS failed: {e}", exc_info=True)
        return jsonify({'error': f"An error occurred during TTS: {e}"}), 500

@app.route('/api/voice-preview', methods=['POST'])
def voice_preview():
    """Generate voice preview for settings"""
    data = request.get_json()
    text = data.get('text', '').strip()
    voice_id = data.get('voice_id', 'dMyQqiVXTU80dDl2eNK8')  # Default to Eryn
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    if not ELEVENLABS_API_KEY:
        return jsonify({'error': 'ElevenLabs API key not configured'}), 500

    tts_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",  # Higher quality model for previews
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True
        },
        "optimize_streaming_latency": 3,
        "output_format": "mp3_44100_128"  # Standard quality format
    }

    try:
        response = requests.post(tts_url, json=payload, headers=headers)
        if response.status_code == 200:
            # Return base64 encoded audio for immediate playback
            audio_base64 = base64.b64encode(response.content).decode('utf-8')
            return jsonify({
                'success': True,
                'audio_data': audio_base64
            })
        else:
            app.logger.error(f"ElevenLabs voice preview failed: {response.status_code} - {response.text}")
            return jsonify({'error': 'Failed to generate voice preview'}), response.status_code
    except Exception as e:
        app.logger.error(f"Voice preview failed: {e}", exc_info=True)
        return jsonify({'error': f"An error occurred during voice preview: {e}"}), 500

@app.route('/api/elevenlabs/token', methods=['POST'])
def get_elevenlabs_token():
    """Return API key for ElevenLabs Agent API"""
    try:
        # Check for ElevenLabs API key
        if not ELEVENLABS_API_KEY:
            return jsonify({
                'error': 'ElevenLabs API key not configured'
            }), 400
        
        # Return the API key directly - ElevenLabs Agent can use this
        return jsonify({
            'api_key': ELEVENLABS_API_KEY,
            'status': 'ready'
        })
        
    except Exception as e:
        app.logger.error(f"Error getting ElevenLabs API key: {e}")
        return jsonify({
            'error': 'Failed to get API key'
        }), 500

@app.route('/update_current_url', methods=['POST'])
def update_current_url():
    """Update the current URL for a task when user navigates manually"""
    try:
        data = request.get_json()
        task_id = data.get('task_id')
        current_url = data.get('current_url', '').strip()
        
        if not task_id or not current_url:
            return jsonify({'error': 'task_id and current_url are required'}), 400
        
        # Update the URL in the context memory
        update_manager.update_current_url(task_id, current_url)
        
        return jsonify({
            'success': True,
            'message': f'Current URL updated for task {task_id}',
            'current_url': current_url
        })
        
    except Exception as e:
        app.logger.error(f"Failed to update current URL: {e}", exc_info=True)
        return jsonify({'error': f"Failed to update current URL: {e}"}), 500

elevenlabs_manager = None

@app.route('/live/start_session', methods=['POST'])
def start_live_session():
    """Start a new ElevenLabs Agent conversation session"""
    try:
        if not elevenlabs_manager:
            return jsonify({
                'error': 'ElevenLabs Agent not available',
                'message': 'ElevenLabs API key not configured'
            }), 400
        
        data = request.get_json() or {}
        session_id = str(uuid.uuid4())
        agent_id = data.get('agent_id', 'default')  # Use default agent or specified agent_id
        
        # Create the session (this will be done asynchronously)
        def create_session():
            asyncio.run(elevenlabs_manager.create_session(session_id, agent_id))
        
        executor.submit(create_session)
        
        return jsonify({
            'session_id': session_id,
            'status': 'starting',
            'message': 'ElevenLabs Agent session is being created'
        })
        
    except Exception as e:
        app.logger.error(f"Failed to start live session: {e}", exc_info=True)
        return jsonify({'error': f"Failed to start live session: {e}"}), 500

@app.route('/live/send_message', methods=['POST'])
def send_live_message():
    """Send text message to active live session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        
        if not session_id or not message:
            return jsonify({'error': 'session_id and message are required'}), 400
        
        if not elevenlabs_manager:
            return jsonify({'error': 'ElevenLabs Agent not available'}), 400
        
        session = elevenlabs_manager.get_session(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Send message asynchronously
        def send_message():
            asyncio.run(session.send_text(message))
        
        executor.submit(send_message)
        
        return jsonify({
            'success': True,
            'message': 'Message sent to ElevenLabs Agent'
        })
        
    except Exception as e:
        app.logger.error(f"Failed to send live message: {e}", exc_info=True)
        return jsonify({'error': f"Failed to send message: {e}"}), 500

@app.route('/live/end_session', methods=['POST'])
def end_live_session():
    """End a live conversation session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400
        
        if not elevenlabs_manager:
            return jsonify({'error': 'ElevenLabs Agent not available'}), 400
        
        # End session asynchronously
        def end_session():
            asyncio.run(elevenlabs_manager.end_session(session_id))
        
        executor.submit(end_session)
        
        return jsonify({
            'success': True,
            'message': 'ElevenLabs Agent session ended'
        })
        
    except Exception as e:
        app.logger.error(f"Failed to end live session: {e}", exc_info=True)
        return jsonify({'error': f"Failed to end session: {e}"}), 500

@app.route('/live/session_status/<session_id>')
def get_live_session_status(session_id):
    """Get status of a live session"""
    try:
        if not elevenlabs_manager:
            return jsonify({'error': 'ElevenLabs Agent not available'}), 400
        
        session = elevenlabs_manager.get_session(session_id)
        if not session:
            return jsonify({'status': 'not_found'}), 404
        
        return jsonify({
            'session_id': session_id,
            'status': 'active' if session.session_active else 'inactive',
            'agent_id': session.agent_id
        })
        
    except Exception as e:
        app.logger.error(f"Failed to get session status: {e}", exc_info=True)
        return jsonify({'error': f"Failed to get status: {e}"}), 500

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    try:
        app.logger.info('Client connected to SocketIO')
        # Send connection status with API key status
        connection_status = {
            'status': 'Connected to Omnix AI',
            'browser_automation': not globals().get('missing_browser_key', True),
            'chat_available': not globals().get('missing_google_key', True),
            'server_time': time.time()
        }
        emit('connected', connection_status)
    except Exception as e:
        app.logger.error(f"Connection handler error: {e}", exc_info=True)

@socketio.on('disconnect')
def handle_disconnect():
    try:
        app.logger.info('Client disconnected from SocketIO')
    except Exception as e:
        app.logger.error(f"Disconnect handler error: {e}", exc_info=True)

@socketio.on('user_message')
def handle_user_message(data):
    """Handle user messages during task execution"""
    try:
        task_id = data.get('task_id')
        message = data.get('message', '')
        is_paused = data.get('is_paused', False)
        
        app.logger.info(f'User message for task {task_id}: {message}')
        
        # Send immediate acknowledgment
        emit('user_message_received', {
            'task_id': task_id,
            'message': message,
            'timestamp': time.time()
        })
        
        if task_id:
            # Forward message to the interactive agent
            agent_manager.add_user_input(task_id, message)
        else:
            # Start a new task if no task_id
            # Send immediate acknowledgment
            emit('task_step', {
                'task_id': 'pending',
                'step': 0,
                'action': 'starting',
                'description': f'Starting new browser automation task: {message}',
                'current_url': ''
            })
            
            start_interactive_task(message)
            
    except Exception as e:
        app.logger.error(f'Error handling user message: {e}')
        emit('error', {'message': 'Failed to process message'})

# Pause functionality removed - use Manual mode instead

@socketio.on('resume_task')
def handle_resume_task(data):
    """Handle task resume requests"""
    task_id = data.get('task_id')
    if task_id:
        logging.info(f"▶️ Resume request for task {task_id}")
        
        # Try Browser Use Cloud resume first
        cloud_integration = get_browser_use_cloud()
        manager = cloud_integration.get_manager()
        
        # For Browser Use Cloud tasks, "resume" means "ready for new instructions"
        # Since Browser Use Cloud tasks can't truly be paused/resumed, we just switch to ready state
        
        # Check if this was a Browser Use Cloud task
        if manager and task_id in manager.active_tasks:
            # Browser Use Cloud task - mark as ready and inform user
            update_manager.resume_task(task_id)
            emit('task_resumed', {'task_id': task_id, 'message': 'Ready for new instructions - send a message to continue automation'})
            logging.info(f"✅ Browser Use Cloud task {task_id} marked as ready for new instructions")
        elif task_id in update_manager.paused_tasks:
            # Task exists in paused tasks but not in active cloud tasks - mark as ready
            update_manager.resume_task(task_id)
            emit('task_resumed', {'task_id': task_id, 'message': 'Ready for new instructions - send a message to continue automation'})
            logging.info(f"✅ Task {task_id} marked as ready for new instructions")
        else:
            # Fallback to old agent system
            try:
                agent_manager.resume_agent(task_id)
                emit('task_resumed', {'task_id': task_id, 'message': 'Interactive agent resumed'})
                logging.info(f"✅ Interactive agent {task_id} resumed successfully")
            except Exception as e:
                logging.error(f"❌ Failed to resume task {task_id}: {e}")
                emit('task_resumed', {'task_id': task_id, 'message': 'Send new instructions to continue'})

@socketio.on('take_screenshot')
def handle_take_screenshot(data):
    """Handle screenshot requests"""
    task_id = data.get('task_id')
    if task_id:
        screenshot_path = agent_manager.take_screenshot(task_id)
        emit('screenshot_taken', {
            'task_id': task_id,
            'screenshot_path': screenshot_path
        })

import base64

@socketio.on('live_session_start')
def handle_live_session_start(data):
    """Handle live conversation session start"""
    try:
        if not stt_tts_manager:
            socketio.emit('live_session_error', {
                'error': 'STT/TTS system not available',
                'message': 'ElevenLabs API key not configured or system initialization failed'
            })
            return
        
        session_id = data.get('session_id', str(uuid.uuid4()))
        voice_id = data.get('voice_id', 'dMyQqiVXTU80dDl2eNK8')  # Default to Eryn
        
        # Set the voice for this session
        if stt_tts_manager:
            stt_tts_manager.set_voice(voice_id)
        
        # Store session
        active_live_sessions[session_id] = {
            'created_at': time.time(),
            'status': 'active',
            'voice_id': voice_id
        }
        
        print(f"🎯 Starting live session: {session_id} with voice: {voice_id}")
        
        # Set up callbacks for this session
        def emit_transcript(text):
            socketio.emit('live_transcript', {
                'session_id': session_id,
                'text': text,
                'timestamp': time.time()
            })
        
        def emit_audio_response(audio_base64):
            socketio.emit('live_audio_response', {
                'session_id': session_id,
                'audio_data': audio_base64,
                'timestamp': time.time()
            })
        
        def emit_error(error):
            socketio.emit('live_session_error', {
                'session_id': session_id,
                'error': str(error)
            })
        
        # Set callbacks
        stt_tts_manager.set_callbacks(
            on_transcript=emit_transcript,
            on_audio_response=emit_audio_response,
            on_error=emit_error
        )
        
        # Emit session created
        socketio.emit('live_session_created', {
            'session_id': session_id,
            'status': 'created'
        })
        
        # Emit session started
        socketio.emit('live_session_started', {
            'session_id': session_id,
            'status': 'active'
        })
        
        print(f"✅ Live session {session_id} started successfully")
        
    except Exception as e:
        print(f"❌ Error starting live session: {e}")
        socketio.emit('live_session_error', {
            'error': 'Failed to start session',
            'message': str(e)
        })

@socketio.on('live_send_text')
def handle_live_send_text(data):
    """Handle text message in live conversation"""
    try:
        session_id = data.get('session_id')
        message = data.get('message', '').strip()
        
        if not session_id or not message:
            emit('live_session_error', {
                'error': 'session_id and message are required'
            })
            return
        
        if not stt_tts_manager:
            emit('live_session_error', {
                'error': 'STT/TTS system not available'
            })
            return
        
        if session_id not in active_live_sessions:
            emit('live_session_error', {
                'error': 'Session not found'
            })
            return
        
        print(f"User message: {message}")
        
        # Emit user transcript
        socketio.emit('live_transcript', {
            'session_id': session_id,
            'text': message,
            'type': 'user',
            'timestamp': time.time()
        })
        
        # Process with Gemini (like regular chat)
        async def process_and_respond():
            try:
                # Get AI response using existing chat system
                if chat_llm_flash:
                    response = chat_llm_flash.generate_content(message)
                    ai_response = response.text if hasattr(response, 'text') else str(response)
                else:
                    ai_response = "Chat service is not available. Please check your Google API key."
                
                # Emit AI text response
                socketio.emit('live_text_response', {
                    'session_id': session_id,
                    'text': ai_response,
                    'timestamp': time.time()
                })
                
                # Clean and generate TTS audio
                tts_text = clean_text_for_tts(ai_response)
                audio_base64 = await stt_tts_manager.generate_speech_response(tts_text)
                
                print(f"✅ Text processing completed for session {session_id}")
                
            except Exception as e:
                print(f"❌ Error processing text: {e}")
                socketio.emit('live_session_error', {
                    'session_id': session_id,
                    'error': f'Text processing failed: {str(e)}'
                })
        
        # Process asynchronously
        executor.submit(asyncio.run, process_and_respond())
        
        # Emit confirmation
        emit('live_text_sent', {
            'session_id': session_id,
            'message': message,
            'timestamp': time.time()
        })
        
    except Exception as e:
        app.logger.error(f"Error sending live text: {e}")
        emit('live_session_error', {
            'error': f'Failed to send message: {e}'
        })

@socketio.on('live_send_audio')
def handle_live_send_audio(data):
    """Handle audio input in live conversation - generate full response at once"""
    try:
        audio_data = data.get('audio_data')
        audio_format = data.get('format', 'wav')
        session_id = 'default_session'
        
        if not audio_data:
            emit('live_session_error', {
                'error': 'audio_data is required'
            })
            return
        
        if not stt_tts_manager:
            emit('live_session_error', {
                'error': 'STT/TTS system not available'
            })
            return
        
        print(f"🎤 Processing audio for session: {session_id}")
        
        # Process audio asynchronously with optimized low-latency flow
        async def process_audio_complete():
            try:
                # Decode base64 audio (fast operation)
                audio_bytes = base64.b64decode(audio_data)
                
                # Transcribe audio to text (parallel with immediate status update)
                socketio.emit('live_transcript_update', {
                    'session_id': session_id,
                    'transcript': "Processing...",
                    'timestamp': time.time()
                })
                
                transcript = await stt_tts_manager.process_audio_input(audio_bytes)
                
                if transcript and transcript.strip():
                    # Emit transcript immediately for user feedback
                    socketio.emit('live_transcript_update', {
                        'session_id': session_id,
                        'transcript': transcript,
                        'timestamp': time.time()
                    })
                    
                    # Immediately start AI thinking status (no delay)
                    socketio.emit('live_ai_thinking', {
                        'session_id': session_id,
                        'status': 'thinking'
                    })
                    
                    # Generate AI response with timeout for faster response
                    if chat_llm_flash:
                        try:
                            # Use fast generation with shorter context for speed
                            response = chat_llm_flash.generate_content(transcript)
                            ai_response = response.text if hasattr(response, 'text') else str(response)
                            
                            # Emit text response immediately
                            socketio.emit('live_text_response', {
                                'session_id': session_id,
                                'text': ai_response,
                                'timestamp': time.time()
                            })
                            
                            # Start TTS generation immediately (no delay for speaking status)
                            socketio.emit('live_ai_speaking', {
                                'session_id': session_id,
                                'status': 'speaking'
                            })
                            
                            # Generate TTS with optimized settings
                            tts_text = clean_text_for_tts(ai_response)
                            
                            # Create TTS task immediately without blocking
                            tts_task = asyncio.create_task(stt_tts_manager.generate_speech_response(tts_text))
                            audio_base64 = await tts_task
                            
                            if audio_base64:
                                socketio.emit('live_audio_response', {
                                    'session_id': session_id,
                                    'audio_data': audio_base64,
                                    'text': ai_response,
                                    'timestamp': time.time()
                                })
                            
                        except Exception as e:
                            error_response = "Processing error occurred."
                            socketio.emit('live_text_response', {
                                'session_id': session_id,
                                'text': error_response,
                                'timestamp': time.time()
                            })
                    else:
                        error_response = "Service unavailable."
                        socketio.emit('live_text_response', {
                            'session_id': session_id,
                            'text': error_response,
                            'timestamp': time.time()
                        })
                    
                    # Signal completion (reduce payload size)
                    socketio.emit('live_response_complete', {
                        'session_id': session_id,
                        'timestamp': time.time()
                    })
                    
                else:
                    print(f"⚠️ No speech detected in audio")
                    socketio.emit('live_transcript_update', {
                        'session_id': session_id,
                        'transcript': "No speech detected",
                        'timestamp': time.time()
                    })
                    
            except Exception as e:
                print(f"❌ Error processing audio: {e}")
                import traceback
                traceback.print_exc()
                socketio.emit('live_session_error', {
                    'session_id': session_id,
                    'error': f'Audio processing failed: {str(e)}'
                })
        
        # Process asynchronously with optimized threading
        def run_complete_processing():
            try:
                # Use optimized event loop for low latency
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Set loop policy for faster execution
                if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
                    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                
                loop.run_until_complete(process_audio_complete())
                loop.close()
            except Exception as e:
                socketio.emit('live_session_error', {
                    'session_id': session_id,
                    'error': f'Processing failed: {str(e)}'
                })
        
        # Use high-priority thread for audio processing
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="LiveAudio") as fast_executor:
            fast_executor.submit(run_complete_processing)
        
        # Send immediate acknowledgment
        emit('live_audio_received', {
            'session_id': session_id,
            'status': 'processing'
        })
        
    except Exception as e:
        print(f"❌ Error in live_send_audio: {e}")
        socketio.emit('live_session_error', {
            'error': f'Audio processing failed: {str(e)}'
        })

@socketio.on('live_audio_input')
def handle_live_audio_input(data):
    """Handle audio input from the rebuilt live voice system"""
    try:
        session_id = data.get('session_id')
        audio_data = data.get('audio_data')
        mime_type = data.get('mime_type', 'audio/webm')
        
        if not session_id or not audio_data:
            emit('live_session_error', {
                'error': 'Missing session_id or audio_data'
            })
            return
        
        print(f"🎤 Received audio input for session: {session_id}")
        
        # Convert base64 to audio and process
        def process_audio_input():
            try:
                # Transcribe audio using STT
                if stt_tts_manager:
                    # Use the synchronous transcribe method if available
                    transcription = stt_tts_manager.transcribe_audio_sync(audio_data, mime_type)
                    print(f"📝 Transcription: {transcription}")
                    
                    # Log transcription (don't emit the "You said:" message)
                    # socketio.emit('live_text_response', {
                    #     'session_id': session_id,
                    #     'text': f"You said: {transcription}",
                    #     'type': 'transcription'
                    # })
                    
                    # Get AI response using Gemini
                    if chat_llm_flash:
                        prompt = f"""You are a helpful voice assistant. 
                        Be conversational, warm, and concise in your responses.
                        Keep responses brief and natural for voice conversation.
                        
                        User said: {transcription}
                        
                        Respond naturally and helpfully:"""
                        
                        response = chat_llm_flash.generate_content(prompt)
                        ai_response = response.text
                    else:
                        ai_response = "I'm sorry, the chat service is not available right now."
                    
                    print(f"🤖 AI Response: {ai_response[:100]}...")
                    
                    # Emit AI text response
                    socketio.emit('live_text_response', {
                        'session_id': session_id,
                        'text': ai_response,
                        'type': 'ai_response'
                    })
                    
                    # Generate TTS audio
                    audio_base64 = stt_tts_manager.text_to_speech_sync(ai_response)
                    if audio_base64:
                        socketio.emit('live_audio_response', {
                            'session_id': session_id,
                            'audio_data': audio_base64,
                            'text': ai_response
                        })
                        print(f"🔊 Sent audio response for session: {session_id}")
                else:
                    raise Exception("STT/TTS system not available")
                    
            except Exception as e:
                print(f"❌ Error processing audio: {e}")
                socketio.emit('live_session_error', {
                    'session_id': session_id,
                    'error': str(e)
                })
        
        # Run processing in thread to avoid blocking
        from threading import Thread
        thread = Thread(target=process_audio_input)
        thread.start()
        
    except Exception as e:
        print(f"❌ Error in live_audio_input: {e}")
        emit('live_session_error', {
            'error': f'Audio processing failed: {str(e)}'
        })

@socketio.on('live_session_end')
def handle_live_session_end(data):
    """Handle ending a live conversation session"""
    try:
        session_id = data.get('session_id')
        
        if not session_id:
            emit('live_session_error', {
                'error': 'session_id is required'
            })
            return
        
        # Remove from active sessions
        if session_id in active_live_sessions:
            del active_live_sessions[session_id]
            print(f"💯 Ended live session: {session_id}")
        
        emit('live_session_ended', {
            'session_id': session_id
        })
        
    except Exception as e:
        print(f"❌ Error ending live session: {e}")
        emit('live_session_error', {
            'error': f'Failed to end session: {e}'
        })

def clean_text_for_tts(text: str) -> str:
    """Remove special characters and formatting for cleaner TTS output."""
    return re.sub(r'[\*#]', '', text)

def get_ai_personality_prompt(user_message: str) -> str:
    """Add a personality prompt to the user's message."""
    return f"""
You are a supportive, emotional, and helpful assistant.
Always respond with empathy and understanding.
User: {user_message}
Assistant:
"""

def get_active_manual_control_session():
    """Check for existing Browser Use Cloud session in manual control or paused mode"""
    cloud_integration = get_browser_use_cloud()
    manager = cloud_integration.get_manager()
    
    if manager and manager.active_tasks:
        for task_id, task in manager.active_tasks.items():
            if task.status in ["manual_control", "paused_for_continuation"]:
                return task_id, task
    return None, None

def continue_browser_session(existing_task_id, task_description):
    """HYBRID APPROACH: Create new task with FULL context - Perfect simulation of true continuation!"""
    logging.info(f"🔄 User wants to continue Browser Use Cloud session {existing_task_id} with: {task_description}")
    
    # Get the existing task info and saved context
    cloud_integration = get_browser_use_cloud()
    manager = cloud_integration.get_manager()
    existing_task = manager.get_task_info(existing_task_id) if manager else None
    task_context = update_manager.get_task_context(existing_task_id)
    
    if not task_context:
        logging.warning(f"⚠️ No saved context found for task {existing_task_id}")
        # Fallback to basic continuation
        return create_basic_continuation_task(existing_task_id, task_description)
    
    # Create new continuation task with FULL context - this gives the EXACT experience you want
    continuation_task_id = str(uuid.uuid4())
    
    logging.info(f"🧠 Creating SMART continuation task {continuation_task_id} with full context")
    
    # Send status update
    socketio.emit('task_step', {
        'task_id': continuation_task_id,
        'step': 1,
        'action': 'session_smart_continue',
        'description': f'🧠 SMART CONTINUATION: {task_description} (using saved context & state)',
        'current_url': task_context.get('final_url', '')
    })
    
    # Create the SMART continuation instruction based on CURRENT location
    original_task = task_context['original_task']
    ai_output = task_context['ai_output']
    final_url = task_context.get('final_url', '')
    current_url = task_context.get('current_url', final_url)  # Use current URL if available, fallback to final
    browser_state = task_context.get('browser_state', {})
    
    logging.info(f"🌐 Continuation context - Original: {final_url}, Current: {current_url}")
    
    # Create intelligent continuation instruction based on current location
    if current_url and current_url != final_url:
        # User navigated somewhere else manually - be contextual about current location
        if "amazon.com" in current_url:
            continuation_instruction = f"I can see you're currently on Amazon. {task_description}"
        elif "google.com" in current_url:
            continuation_instruction = f"I can see you're currently on Google. {task_description}"
        elif "youtube.com" in current_url:
            continuation_instruction = f"I can see you're currently on YouTube. {task_description}"
        elif "github.com" in current_url:
            continuation_instruction = f"I can see you're currently on GitHub. {task_description}"
        else:
            # Generic case for any other website
            domain = current_url.split('/')[2] if '/' in current_url else current_url
            continuation_instruction = f"I can see you're currently on {domain}. {task_description}"
    else:
        # User is still where AI left off - use original smart logic
        if "amazon" in original_task.lower():
            if "search" in original_task.lower() and ("add" in task_description.lower() or "cart" in task_description.lower()):
                # Specific case: Amazon search -> add to cart
                search_term = original_task.split("search for")[-1].strip().strip('"').strip("'")
                continuation_instruction = f"Go to amazon.com, search for '{search_term}', and add the first relevant result to cart."
            else:
                continuation_instruction = f"Continue on Amazon: {task_description}"
        else:
            # General continuation
            continuation_instruction = f"Continue from where we left off: {task_description}"
    
    # Run the smart continuation task
    def run_smart_continuation():
        try:
            logging.info(f"🚀 Executing smart continuation with full context awareness")
            asyncio.run(execute_browser_use_cloud_task(
                continuation_task_id, 
                continuation_instruction, 
                continue_session=True
            ))
        except Exception as e:
            logging.error(f"❌ Error in smart continuation task: {e}")
            socketio.emit('task_step', {
                'task_id': continuation_task_id,
                'step': 1,
                'action': 'session_continue_error',
                'description': f'Smart continuation failed: {str(e)}',
                'current_url': ''
            })
    
    executor.submit(run_smart_continuation)
    return continuation_task_id

def create_basic_continuation_task(existing_task_id, task_description):
    """Fallback for when no context is available"""
    continuation_task_id = str(uuid.uuid4())
    
    logging.info(f"🔄 Creating basic continuation task (no context available)")
    
    continuation_instruction = f"""CONTINUATION TASK: {task_description}

Execute this browser automation task efficiently. This appears to be a follow-up to a previous task.

TASK: {task_description}"""
    
    def run_basic_continuation():
        try:
            asyncio.run(execute_browser_use_cloud_task(
                continuation_task_id, 
                continuation_instruction, 
                continue_session=True
            ))
        except Exception as e:
            logging.error(f"❌ Error in basic continuation task: {e}")
    
    executor.submit(run_basic_continuation)
    return continuation_task_id

def start_interactive_task(task_description):
    """Start a new interactive browser task using Browser Use Cloud or continue existing session"""
    
    # Check if user explicitly wants a new session
    if task_description.lower().startswith("new session:"):
        task_description = task_description[12:].strip()  # Remove "new session:" prefix
        logging.info(f"🚀 User requested new session: {task_description}")
        # Force new session
        task_id = str(uuid.uuid4())
        
        def run_task():
            asyncio.run(execute_browser_use_cloud_task(task_id, task_description))
        
        executor.submit(run_task)
        return task_id
    
    # Check for existing manual control session first
    existing_task_id, existing_task = get_active_manual_control_session()
    
    if existing_task_id and existing_task:
        # Continue with existing session context
        logging.info(f"🔄 Found existing Browser Use Cloud session {existing_task_id}, continuing workflow...")
        return continue_browser_session(existing_task_id, task_description)
    else:
        # Start new session
        logging.info(f"🚀 Starting new Browser Use Cloud session...")
        task_id = str(uuid.uuid4())
        
        # Run the task in background
        def run_task():
            asyncio.run(execute_browser_use_cloud_task(task_id, task_description))
        
        executor.submit(run_task)
        return task_id

# --- Cloud Interactive Browser Task Execution ---
async def execute_cloud_interactive_browser_task(task_id, task_description):
    """Execute browser task with cloud browser and interactive features"""
    cloud_manager = get_cloud_browser_manager()
    screenshot_collector = None
    
    try:
        # Initialize screenshot collector
        screenshot_collector = ScreenshotCollector(task_id)
        
        # Use cloud browser with managed session
        async with ManagedCloudBrowserSession(
            task_id=task_id,
            cloud_manager=cloud_manager,
            # Cloud browser configuration
            proxies=True,
            fingerprint=True,
            adblock=True,
            keepAlive=True
        ) as (browser_session, session_data):
            
            # Browser Use Cloud handles ChatGPT-4o mini internally
            # No need to create BrowserChatOpenAI instance
            
            # Create interactive agent with cloud browser
            interactive_agent = agent_manager.create_agent(
                task_id=task_id,
                task_description=task_description,
                browser_session=browser_session,
                llm=None,  # Browser Use Cloud handles LLM internally
                update_manager=update_manager
            )
            
            # Notify update manager about the cloud session
            update_manager.add_task(
                task_id, 
                task_description, 
                debug_port=None,  # Cloud browser doesn't use debug port
                live_view_url=session_data.get('live_view_url'),
                session_id=session_data.get('session_id')
            )
            
            # Run the interactive task
            result = await interactive_agent.run()
            
            # Generate GIF and summary after completion
            gif_generator = TaskGifGenerator(task_id)
            screenshots_b64 = screenshot_collector.get_screenshots_b64()
            
            gif_path = None
            if screenshots_b64:
                gif_path = gif_generator.generate_task_gif(screenshots_b64)
            
            if chat_llm_flash:
                summary_generator = TaskSummaryGenerator(chat_llm_flash)
            else:
                summary_generator = None
            actions_log = screenshot_collector.get_actions_log()
            if summary_generator:
                summary_data = summary_generator.generate_summary(task_description, actions_log)
                summary = json.dumps(summary_data)
            else:
                summary = json.dumps({
                    "overview": f"Browser automation task: {task_description}",
                    "key_steps": [f"Executed {len(actions_log)} automation steps"],
                    "outcome": "Task completed (no LLM summary available)",
                    "duration_estimate": f"Approximately {len(actions_log)} steps",
                    "notable_events": ["OpenAI API key required for detailed summaries"]
                })
            
            # Save to database
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tasks (id, description, status, result, gif_path, summary) VALUES (?, ?, ?, ?, ?, ?)",
                    (task_id, task_description, 'COMPLETED', result, gif_path, summary)
                )
                conn.commit()
            
            # Clean up
            screenshot_collector.save_metadata()
            screenshot_collector.save_screenshots_to_disk()
            
    except Exception as e:
        app.logger.error(f"Cloud interactive task {task_id} failed: {e}", exc_info=True)
        update_manager.complete_task(task_id, f"Task failed: {e}")
    
    finally:
        agent_manager.remove_agent(task_id)

# --- Browser Use Cloud Interactive Task Execution ---
async def execute_browser_use_cloud_task(task_id, task_description, continue_session=False):
    """Execute browser task with Browser Use Cloud and interactive features"""
    screenshot_collector = None
    
    try:
        # Initialize screenshot collector
        screenshot_collector = ScreenshotCollector(task_id)
        
        # Check if the task requires research
        research_keywords = ['research', 'find out', 'look up', 'search for', 'what is', 'how to', 'information about', 'learn about']
        needs_research = any(keyword in task_description.lower() for keyword in research_keywords)
        
        enhanced_task_description = task_description
        
        if needs_research and enhanced_research_manager:
            # Notify user that research mode is being used
            logging.info(f"🔍 Task requires research, using Perplexity Deep Research mode")
            socketio.emit('task_step', {
                'task_id': task_id,
                'step': 0,
                'action': 'research_start',
                'description': '🔍 Using researcher mode to research and find answers...',
                'current_url': ''
            })
            
            # Extract the research query from the task description
            research_query = task_description
            # Remove common browser task prefixes
            for prefix in ['research and', 'find out', 'look up', 'search for']:
                if research_query.lower().startswith(prefix):
                    research_query = research_query[len(prefix):].strip()
            
            # Perform research using Perplexity
            try:
                research_result = enhanced_research_manager.conduct_research_sync(research_query)
                
                if research_result['success']:
                    # Format research results for the browser task
                    research_summary = research_result['summary']
                    sources = research_result.get('sources', [])
                    
                    # Create enhanced task description with research results
                    enhanced_task_description = f"""
Task: {task_description}

Research Results:
{research_summary}

Sources found: {len(sources)} credible sources analyzed

Based on this research, please complete the browser automation task efficiently.
If the task involves visiting websites, prioritize these sources:
"""
                    # Add top 3 sources to visit if relevant
                    for i, source in enumerate(sources[:3], 1):
                        if source.get('url'):
                            enhanced_task_description += f"\n{i}. {source.get('title', 'Source')}: {source['url']}"
                    
                    # Notify user about research completion
                    socketio.emit('task_step', {
                        'task_id': task_id,
                        'step': 1,
                        'action': 'research_complete',
                        'description': f'✅ Research completed. Analyzed {len(sources)} sources. Now executing browser task...',
                        'current_url': ''
                    })
                    
                    logging.info(f"✅ Research completed with {len(sources)} sources")
                else:
                    logging.warning(f"⚠️ Research failed, proceeding with original task")
                    
            except Exception as e:
                logging.error(f"❌ Research error: {e}, proceeding with original task")
        
        # Get Browser Use Cloud integration
        cloud_integration = get_browser_use_cloud()
        
        if continue_session:
            # For session continuation, we create a new task but keep the same browser
            logging.info(f"🔄 Continuing Browser Use Cloud session {task_id}")
            result = await cloud_integration.execute_cloud_task(f"{task_id}_continue_{int(time.time())}", enhanced_task_description)
        else:
            # Execute task with Browser Use Cloud
            logging.info(f"🚀 About to execute Browser Use Cloud task: {task_id}")
            result = await cloud_integration.execute_cloud_task(task_id, enhanced_task_description)
            logging.info(f"📊 Browser Use Cloud task result: {result}")
        
        if result["success"]:
            live_url = result.get('live_url')
            logging.info(f"🌐 Browser Use Cloud task started with live URL: {live_url}")
            
            # Notify update manager about the cloud task
            update_manager.add_task(
                task_id, 
                task_description, 
                debug_port=None,  # Cloud browser doesn't use debug port
                live_view_url=live_url,
                session_id=result.get('task_id'),
                browser_type='browser_use_cloud'
            )
            
            # Provide user feedback about the task status
            if live_url:
                # Task started successfully with live view
                if continue_session:
                    action_type = 'session_smart_continue'
                    description = '🧠 Browser Use Cloud continuation with live view available.'
                else:
                    action_type = 'browser_cloud_start'
                    description = 'Browser Use Cloud task started successfully. Live view available.'
                
                logging.info(f"📤 Emitting task_step with live URL: {live_url}")
                socketio.emit('task_step', {
                    'task_id': task_id,
                    'step': 2,
                    'action': action_type,
                    'description': description,
                    'current_url': live_url
                })
                logging.info(f"✅ Task step emitted successfully")
            else:
                # Task started but no live view (API key issue likely)
                action_type = 'browser_cloud_continue' if continue_session else 'browser_cloud_start'
                description = ('Browser Use Cloud continuation task started (no live view - check API key)' if continue_session
                             else 'Browser Use Cloud task started (no live view - check API key configuration)')
                
                socketio.emit('task_step', {
                    'task_id': task_id,
                    'step': 1,
                    'action': action_type,
                    'description': description,
                    'current_url': ''
                })
            
            # Wait for completion and get results
            cloud_manager = cloud_integration.get_manager()
            if cloud_manager:
                # Get the cloud task - it might be stored under a different ID
                cloud_task = cloud_manager.active_tasks.get(task_id)
                
                # If not found under our task_id, try to find it by the Browser Use Cloud task ID
                if not cloud_task and result.get('task_id'):
                    # Look for the task by Browser Use Cloud task ID
                    for stored_task_id, stored_task in cloud_manager.active_tasks.items():
                        if stored_task.task_id == result.get('task_id'):
                            cloud_task = stored_task
                            break
                
                if cloud_task:
                    completion_result = cloud_manager.wait_for_completion(cloud_task, timeout=300, update_manager=update_manager)
                else:
                    logging.warning(f"⚠️ Could not find cloud task for completion monitoring: {task_id}")
                    completion_result = {"status": "unknown", "result": "Task monitoring unavailable"}
                
                # Check if task was paused locally
                if completion_result.get("local_pause", False):
                    logging.info(f"⏸️ Task {task_id} was paused by user - stopping execution")
                    socketio.emit('task_completed', {
                        'task_id': task_id,
                        'result': 'Task paused by user',
                        'summary': None
                    })
                    return
                
                final_result = completion_result.get("result", "Task completed")
                
                # Generate summary for Browser Use Cloud task
                if chat_llm_flash:
                    summary_generator = TaskSummaryGenerator(chat_llm_flash)
                else:
                    summary_generator = None
                    
                if summary_generator:
                    summary_data = summary_generator.generate_summary(
                        task_description, 
                        [f"Browser Use Cloud executed: {task_description}"]
                    )
                    summary = json.dumps(summary_data)
                else:
                    summary = json.dumps({
                        "overview": f"Browser Use Cloud task: {task_description}",
                        "key_steps": ["Executed task via Browser Use Cloud"],
                        "outcome": "Task completed (no LLM summary available)",
                        "duration_estimate": "Cloud execution time",
                        "notable_events": ["OpenAI API key required for detailed summaries"]
                    })
                
                # Save to database
                with sqlite3.connect(DB_FILE) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "INSERT INTO tasks (id, description, status, result, gif_path, summary) VALUES (?, ?, ?, ?, ?, ?)",
                        (task_id, task_description, 'COMPLETED', final_result, None, summary)
                    )
                    conn.commit()
                
                # Save task context for continuation BEFORE cleanup
                update_manager.save_task_context(
                    task_id=task_id,
                    original_task=task_description,
                    ai_output=final_result,
                    final_url=cloud_task.live_url if cloud_task else None,
                    browser_state={'summary': summary, 'completion_result': completion_result}
                )
                
                # Move Browser Use Cloud task to paused mode (maintains browser state)
                cloud_manager.cleanup_task(task_id)
                
                update_manager.complete_task(task_id, final_result, summary)
            else:
                update_manager.complete_task(task_id, "Browser Use Cloud not configured")
        else:
            # Failed to start task
            error_msg = result.get("error", "Failed to start Browser Use Cloud task")
            
            # Send error feedback to user
            socketio.emit('task_step', {
                'task_id': task_id,
                'step': 1,
                'action': 'error',
                'description': f'Failed to start browser task: {error_msg}',
                'current_url': ''
            })
            
            update_manager.complete_task(task_id, f"Task failed: {error_msg}")
            
    except Exception as e:
        app.logger.error(f"Browser Use Cloud task {task_id} failed: {e}", exc_info=True)
        update_manager.complete_task(task_id, f"Task failed: {e}")
    
    finally:
        agent_manager.remove_agent(task_id)

# --- Local Interactive Browser Task Execution (Backup) ---
async def execute_interactive_browser_task(task_id, task_description):
    """Execute browser task with interactive features"""
    browser_session = None
    screenshot_collector = None
    
    try:
        # Initialize screenshot collector
        screenshot_collector = ScreenshotCollector(task_id)
        
        # Browser session setup (same as before)
        import tempfile
        temp_profile_dir = tempfile.mkdtemp(prefix=f"browser_task_{task_id}_")
        debug_port = 9223  # Use different port for interactive tasks
        BrowserSessionWithScreenshots = None 
        browser_session = BrowserSessionWithScreenshots(
            browser_profile=BrowserProfile(
                headless=False,
                user_data_dir=temp_profile_dir,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage', 
                    '--disable-gpu',
                    f'--remote-debugging-port={debug_port}',
                    '--disable-web-security',
                    '--enable-automation',
                    '--no-first-run',
                    '--disable-default-apps',
                    '--disable-extensions',
                    '--disable-background-networking',
                    '--disable-sync',
                    '--disable-component-extensions-with-background-pages',
                ],
                keep_alive=False,  # Change to False to avoid conflicts
                enable_default_extensions=False,
            ),
            screenshot_collector=screenshot_collector
        )
        
        if not browser_llm_available:
            raise ValueError("Browser automation requires Browser Use Cloud API key. Please configure BROWSER_USE_CLOUD_API_KEY in your .env file.")
        
        # Create interactive agent
        interactive_agent = agent_manager.create_agent(
            task_id=task_id,
            task_description=task_description,
            browser_session=browser_session,
            llm=None,  # Browser Use Cloud handles LLM internally
            update_manager=update_manager
        )
        
        # Store debug port for browser view
        interactive_agent.debug_port = debug_port
        
        # Notify the update manager about the debug port
        update_manager.add_task(task_id, task_description, debug_port)
        
        # Run the interactive task
        result = await interactive_agent.run()
        
        # Generate GIF and summary after completion
        gif_generator = TaskGifGenerator(task_id)
        screenshots_b64 = screenshot_collector.get_screenshots_b64()
        
        gif_path = None
        if screenshots_b64:
            gif_path = gif_generator.generate_task_gif(screenshots_b64)
        
        if chat_llm_flash:
            summary_generator = TaskSummaryGenerator(chat_llm_flash)
        else:
            summary_generator = None
        actions_log = screenshot_collector.get_actions_log()
        if summary_generator:
            summary_data = summary_generator.generate_summary(task_description, actions_log)
            summary = json.dumps(summary_data)
        else:
            summary = json.dumps({
                "overview": f"Browser automation task: {task_description}",
                "key_steps": [f"Executed {len(actions_log)} automation steps"],
                "outcome": "Task completed (no LLM summary available)",
                "duration_estimate": f"Approximately {len(actions_log)} steps",
                "notable_events": ["OpenAI API key required for detailed summaries"]
            })
        
        # Save to database
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tasks (id, description, status, result, gif_path, summary) VALUES (?, ?, ?, ?, ?, ?)",
                (task_id, task_description, 'COMPLETED', result, gif_path, summary)
            )
            conn.commit()
        
        # Clean up
        screenshot_collector.save_metadata()
        screenshot_collector.save_screenshots_to_disk()
        
    except Exception as e:
        app.logger.error(f"Interactive task {task_id} failed: {e}", exc_info=True)
        update_manager.complete_task(task_id, f"Task failed: {e}")
    
    finally:
        if browser_session:
            await browser_session.close()
        agent_manager.remove_agent(task_id)
        
        if 'temp_profile_dir' in locals() and os.path.exists(temp_profile_dir):
            try:
                shutil.rmtree(temp_profile_dir)
            except Exception as e:
                app.logger.error(f"Error cleaning up profile: {e}")

# Register live voice routes
register_live_voice_routes(app)

if __name__ == '__main__':
    try:
        init_db()
        # Use SocketIO's run method instead of Flask's run method
        port = int(os.environ.get('PORT', 8003))
        print(f"🚀 Starting Omnix AI server on port {port}")
        print("📡 SocketIO WebSocket support enabled with enhanced stability")
        print("🔗 Access the application at: http://localhost:{}".format(port))
        
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=port, 
            debug=False, 
            allow_unsafe_werkzeug=True,
            use_reloader=False,  # Disable reloader to prevent connection issues
            log_output=True
        )
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        import traceback
        traceback.print_exc()
