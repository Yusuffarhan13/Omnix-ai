#!/usr/bin/env python3
"""
Cloud Browser Manager using Browserbase
Provides cloud-hosted browser sessions with live view capabilities
"""

import os
import asyncio
import logging
from typing import Optional, Dict, Any
from browserbase import Browserbase
from browser_use.browser.session import BrowserSession
from browser_use.browser import BrowserProfile


class CloudBrowserManager:
    """Manages cloud browser sessions using Browserbase"""
    
    def __init__(self, api_key: str = None, project_id: str = None):
        self.api_key = api_key or os.getenv("BROWSERBASE_API_KEY")
        self.project_id = project_id or os.getenv("BROWSERBASE_PROJECT_ID")
        
        if not self.api_key or not self.project_id:
            raise ValueError("BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID must be set")
        
        self.client = Browserbase(api_key=self.api_key)
        self.active_sessions = {}
        
        logging.info(f"🌐 CloudBrowserManager initialized with project {self.project_id}")
    
    async def create_session(self, task_id: str, **session_config) -> Dict[str, Any]:
        """Create a new cloud browser session"""
        
        try:
            logging.info(f"🚀 Creating cloud browser session for task {task_id}")
            
            # Default session configuration
            config = {
                "projectId": self.project_id,
                "keepAlive": True,
                "proxies": True,  # Enable residential proxies
                "fingerprint": True,  # Generate unique fingerprints
                "adblock": True,  # Block ads for faster loading
                **session_config
            }
            
            # Create remote browser session
            session = self.client.sessions.create(**config)
            
            # Get live view URL
            debug_info = self.client.sessions.debug(session.id)
            
            session_data = {
                "session_id": session.id,
                "connect_url": session.connect_url,
                "live_view_url": debug_info.debugger_fullscreen_url,
                "live_view_basic": debug_info.debugger_url,
                "status": "active"
            }
            
            self.active_sessions[task_id] = session_data
            
            logging.info(f"✅ Cloud browser session created: {session.id}")
            logging.info(f"🔗 Live view URL: {debug_info.debugger_fullscreen_url}")
            
            return session_data
            
        except Exception as e:
            logging.error(f"❌ Failed to create cloud browser session: {e}")
            raise
    
    def get_session_info(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get session information for a task"""
        return self.active_sessions.get(task_id)
    
    async def close_session(self, task_id: str):
        """Close a cloud browser session"""
        
        if task_id in self.active_sessions:
            session_data = self.active_sessions[task_id]
            session_id = session_data["session_id"]
            
            try:
                # Note: Sessions are automatically cleaned up by Browserbase
                # but we can explicitly end them if needed
                logging.info(f"🕊️ Closing cloud browser session: {session_id}")
                
                del self.active_sessions[task_id]
                
            except Exception as e:
                logging.error(f"Error closing session {session_id}: {e}")


class ManagedCloudBrowserSession:
    """Context manager for cloud browser sessions"""
    
    def __init__(self, task_id: str, cloud_manager: CloudBrowserManager, **session_config):
        self.task_id = task_id
        self.cloud_manager = cloud_manager
        self.session_config = session_config
        self.browser_session = None
        self.session_data = None
    
    async def __aenter__(self) -> tuple[BrowserSession, Dict[str, Any]]:
        """Create and return browser session with cloud session data"""
        
        try:
            # Create cloud browser session
            self.session_data = await self.cloud_manager.create_session(
                self.task_id, **self.session_config
            )
            
            # Create browser-use session connected to cloud browser
            self.browser_session = BrowserSession(
                cdp_url=self.session_data["connect_url"],
                browser_profile=BrowserProfile(
                    headless=False,
                    keep_alive=False,
                ),
                keep_alive=False,
                initialized=False,
            )
            
            await self.browser_session.start()
            logging.info(f"✅ Connected to cloud browser session: {self.session_data['session_id']}")
            
            return self.browser_session, self.session_data
            
        except Exception as e:
            logging.error(f"❌ Failed to create managed cloud browser session: {e}")
            await self._cleanup()
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser session"""
        await self._cleanup()
    
    async def _cleanup(self):
        """Clean up resources"""
        if self.browser_session:
            try:
                await self.browser_session.close()
            except Exception as e:
                logging.error(f"Error closing browser session: {e}")
        
        if self.cloud_manager and self.task_id:
            try:
                await self.cloud_manager.close_session(self.task_id)
            except Exception as e:
                logging.error(f"Error closing cloud session: {e}")


# Singleton cloud browser manager
cloud_browser_manager = None

def get_cloud_browser_manager() -> CloudBrowserManager:
    """Get or create the global cloud browser manager"""
    global cloud_browser_manager
    
    if cloud_browser_manager is None:
        cloud_browser_manager = CloudBrowserManager()
    
    return cloud_browser_manager