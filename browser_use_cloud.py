#!/usr/bin/env python3
"""
Browser Use Cloud Integration
Provides cloud-hosted browser automation with live preview URLs
"""

import os
import requests
import logging
import asyncio
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class BrowserUseCloudTask:
    task_id: str
    live_url: str
    status: str
    result: Optional[str] = None
    steps_taken: int = 0


class BrowserUseCloudManager:
    """Manages Browser Use Cloud API integration"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("BROWSER_USE_CLOUD_API_KEY")
        self.base_url = "https://api.browser-use.com/api/v1"
        
        if not self.api_key:
            raise ValueError("BROWSER_USE_CLOUD_API_KEY must be set")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        self.active_tasks = {}
        
        logging.info(f"🌐 Browser Use Cloud initialized")
    
    def create_task(self, task_description: str, task_id: str = None) -> BrowserUseCloudTask:
        """Create a new browser automation task"""
        
        try:
            logging.info(f"🚀 Creating Browser Use Cloud task: {task_description}")
            
            payload = {
                "task": task_description,
                "include_screenshot": True,
                "include_recording": True,
                "timeout": 300  # 5 minute timeout
            }
            
            response = requests.post(
                f"{self.base_url}/run-task",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")
            
            data = response.json()
            logging.info(f"📊 Browser Use Cloud API response: {data}")
            
            # Extract task ID from response
            cloud_task_id = data.get("id") or data.get("task_id") or task_id
            
            # Create task object
            cloud_task = BrowserUseCloudTask(
                task_id=cloud_task_id,
                live_url=data.get("live_url") or data.get("live_view_url") or data.get("view_url"),
                status="created"
            )
            
            if task_id:
                self.active_tasks[task_id] = cloud_task
            
            logging.info(f"✅ Browser Use Cloud task created with ID: {cloud_task_id}")
            
            # Wait for task to start and get live URL
            if cloud_task_id:
                logging.info(f"🔄 Waiting for task to start...")
                self._wait_for_task_ready(cloud_task, timeout=30)
            
            logging.info(f"🔗 Live URL: {cloud_task.live_url}")
            
            if not cloud_task.live_url:
                logging.warning("⚠️ No live URL returned from Browser Use Cloud API - live view will not be available")
            
            return cloud_task
            
        except Exception as e:
            logging.error(f"❌ Failed to create Browser Use Cloud task: {e}")
            raise
    
    def _wait_for_task_ready(self, cloud_task: BrowserUseCloudTask, timeout: int = 30):
        """Wait for task to be ready and get live URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                status_data = self.get_task_status(cloud_task.task_id)
                
                # Update live URL if available
                live_url = status_data.get("live_url") or status_data.get("live_view_url") or status_data.get("view_url")
                if live_url and not cloud_task.live_url:
                    cloud_task.live_url = live_url
                    logging.info(f"✅ Got live URL: {live_url}")
                    return
                
                # Check if task is running
                status = status_data.get("status", "").lower()
                if status in ["running", "active", "started"]:
                    cloud_task.status = "running"
                    if live_url:
                        return
                elif status in ["failed", "error"]:
                    cloud_task.status = "failed"
                    logging.error(f"❌ Task failed: {status_data.get('error', 'Unknown error')}")
                    return
                
                logging.info(f"⏳ Task status: {status}, waiting...")
                time.sleep(2)
                
            except Exception as e:
                logging.warning(f"⚠️ Error checking task status: {e}")
                time.sleep(2)
    
    def get_task_status(self, cloud_task_id: str) -> Dict[str, Any]:
        """Get the status of a running task"""
        
        try:
            response = requests.get(
                f"{self.base_url}/task/{cloud_task_id}",
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"status": "unknown", "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logging.error(f"Error getting task status: {e}")
            return {"status": "error", "error": str(e)}
    
    def pause_task(self, cloud_task_id: str) -> Dict[str, Any]:
        """Pause a running task"""
        
        try:
            logging.info(f"⏸️ Pausing Browser Use Cloud task: {cloud_task_id}")
            url = f"{self.base_url}/pause-task"
            payload = {"task_id": cloud_task_id}
            
            logging.info(f"🔍 Pause API request: PUT {url} with payload: {payload}")
            
            response = requests.put(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"✅ Task paused successfully")
                return result
            else:
                logging.error(f"❌ Failed to pause task: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ Error pausing task: {e}")
            return {"success": False, "error": str(e)}
    
    def resume_task(self, cloud_task_id: str) -> Dict[str, Any]:
        """Resume a paused task"""
        
        try:
            logging.info(f"▶️ Resuming Browser Use Cloud task: {cloud_task_id}")
            
            response = requests.put(
                f"{self.base_url}/resume-task",
                headers=self.headers,
                json={"task_id": cloud_task_id},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                logging.info(f"✅ Task resumed successfully")
                return result
            else:
                logging.error(f"❌ Failed to resume task: {response.status_code} - {response.text}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logging.error(f"❌ Error resuming task: {e}")
            return {"success": False, "error": str(e)}
    
    def wait_for_completion(self, cloud_task: BrowserUseCloudTask, timeout: int = 300, update_manager=None) -> Dict[str, Any]:
        """Wait for task completion with timeout and pause detection"""
        
        # Safety check for None cloud_task
        if cloud_task is None:
            logging.error("❌ Cannot wait for completion: cloud_task is None")
            return {"status": "error", "error": "No cloud task provided for completion monitoring"}
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Check if task has been paused locally before checking Browser Use Cloud status
                if update_manager:
                    # Find the local task ID that corresponds to this Browser Use Cloud task
                    local_task_id = None
                    for task_id, stored_task in self.active_tasks.items():
                        if stored_task.task_id == cloud_task.task_id:
                            local_task_id = task_id
                            break
                    
                    # If found and paused locally, stop monitoring
                    if local_task_id and update_manager.is_paused(local_task_id):
                        logging.info(f"⏸️ Task {local_task_id} paused locally - stopping completion monitoring")
                        cloud_task.status = "paused_locally"
                        return {"status": "paused", "result": "Task paused by user", "local_pause": True}
                
                status = self.get_task_status(cloud_task.task_id)
                current_status = status.get("status", "").lower()
                
                if current_status in ["completed", "finished", "done"]:
                    cloud_task.status = "completed"
                    cloud_task.result = status.get("result")
                    logging.info(f"✅ Task completed successfully")
                    return status
                elif current_status in ["failed", "error", "cancelled"]:
                    cloud_task.status = "failed"
                    cloud_task.result = status.get("error", "Task failed")
                    logging.error(f"❌ Task failed: {cloud_task.result}")
                    return status
                elif current_status in ["running", "active", "processing"]:
                    # Update steps taken if available
                    if "steps_taken" in status:
                        cloud_task.steps_taken = status["steps_taken"]
                        logging.info(f"📊 Task progress: {cloud_task.steps_taken} steps taken")
                
                # Show progress
                elapsed = int(time.time() - start_time)
                logging.info(f"⏳ Waiting for completion... ({elapsed}s elapsed, status: {current_status})")
                
                # Wait before next check
                time.sleep(5)  # Increase interval to reduce API calls
                
            except Exception as e:
                logging.error(f"Error waiting for completion: {e}")
                time.sleep(2)
        
        # Timeout reached
        logging.error(f"⏰ Task timed out after {timeout} seconds")
        cloud_task.status = "timeout"
        return {"status": "timeout", "error": f"Task timed out after {timeout} seconds"}
    
    def get_task_info(self, task_id: str) -> Optional[BrowserUseCloudTask]:
        """Get task information"""
        return self.active_tasks.get(task_id)
    
    def cleanup_task(self, task_id: str):
        """Clean up task resources - now pauses instead of ending for true continuation"""
        if task_id in self.active_tasks:
            cloud_task = self.active_tasks[task_id]
            
            # Pause the Browser Use Cloud task instead of ending it
            try:
                pause_result = self.pause_task(cloud_task.task_id)
                if pause_result.get("success", False):
                    cloud_task.status = "paused_for_continuation"
                    logging.info(f"⏸️ Browser Use Cloud task {task_id} paused for continuation (maintains browser state)")
                else:
                    cloud_task.status = "manual_control"
                    logging.info(f"🔄 Browser Use Cloud task {task_id} moved to manual control mode (pause failed)")
            except Exception as e:
                logging.error(f"❌ Error pausing task {task_id}: {e}")
                cloud_task.status = "manual_control"
                logging.info(f"🔄 Browser Use Cloud task {task_id} moved to manual control mode (fallback)")


class SimpleBrowserUseCloudIntegration:
    """Simple integration for Browser Use Cloud without complex session management"""
    
    def __init__(self):
        self.cloud_manager = None
        
    def get_manager(self) -> BrowserUseCloudManager:
        """Get or create cloud manager"""
        if self.cloud_manager is None:
            try:
                self.cloud_manager = BrowserUseCloudManager()
            except ValueError as e:
                logging.warning(f"Browser Use Cloud not configured: {e}")
                return None
        
        return self.cloud_manager
    
    async def execute_cloud_task(self, task_id: str, task_description: str) -> Dict[str, Any]:
        """Execute a task using Browser Use Cloud"""
        
        manager = self.get_manager()
        if not manager:
            return {
                "success": False,
                "error": "Browser Use Cloud not configured - check BROWSER_USE_CLOUD_API_KEY",
                "live_url": None
            }
        
        try:
            # Create cloud task with better error handling
            logging.info(f"🎯 Executing cloud task: {task_description}")
            cloud_task = manager.create_task(task_description, task_id)
            
            if not cloud_task.task_id:
                raise Exception("No task ID returned from Browser Use Cloud API")
            
            result = {
                "success": True,
                "task_id": cloud_task.task_id,
                "live_url": cloud_task.live_url,
                "status": cloud_task.status
            }
            
            # If no live URL, try to get it after a delay
            if not cloud_task.live_url:
                logging.info("🔄 Retrying to get live URL...")
                await asyncio.sleep(5)
                status_data = manager.get_task_status(cloud_task.task_id)
                live_url = status_data.get("live_url") or status_data.get("live_view_url")
                if live_url:
                    cloud_task.live_url = live_url
                    result["live_url"] = live_url
            
            logging.info(f"✅ Cloud task execution result: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to execute cloud task: {e}"
            logging.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "live_url": None
            }


# Global instance
browser_use_cloud = SimpleBrowserUseCloudIntegration()

def get_browser_use_cloud() -> SimpleBrowserUseCloudIntegration:
    """Get the global Browser Use Cloud integration instance"""
    return browser_use_cloud