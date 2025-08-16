#!/usr/bin/env python3
"""
GIF Generator for Browser Task Screenshots
Creates animated GIFs from browser automation screenshots and generates summaries.
"""

import os
import glob
import base64
import json
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image
import tempfile


class TaskGifGenerator:
    """Generates GIF animations from browser task screenshots"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.gifs_dir = Path("task_gifs")
        self.gifs_dir.mkdir(exist_ok=True)
    
    def find_task_screenshots(self) -> List[str]:
        """Find all screenshots for a given task"""
        # Look for browser-use agent directories that might contain our screenshots
        possible_dirs = [
            f"./browser_use_agents/*/screenshots/",
            f"./agent_*/screenshots/",
            f"./Task_{self.task_id}/screenshots/",
            f"./temp_*{self.task_id}*/screenshots/",
        ]
        
        screenshot_files = []
        for pattern in possible_dirs:
            screenshot_files.extend(glob.glob(f"{pattern}*.png"))
        
        # Sort by step number if available
        def extract_step_number(filepath):
            filename = os.path.basename(filepath)
            if 'step_' in filename:
                try:
                    return int(filename.split('step_')[1].split('.')[0])
                except:
                    pass
            return 0
        
        screenshot_files.sort(key=extract_step_number)
        return screenshot_files
    
    def create_gif_from_screenshots(self, screenshot_paths: List[str], output_path: str, duration: int = 2000) -> bool:
        """Create an animated GIF from screenshot files"""
        if not screenshot_paths:
            return False
        
        try:
            images = []
            for path in screenshot_paths:
                if os.path.exists(path):
                    img = Image.open(path)
                    # Resize to reasonable size for web display
                    img = img.resize((800, 600), Image.Resampling.LANCZOS)
                    images.append(img)
            
            if images:
                # Save as GIF with loop
                images[0].save(
                    output_path,
                    save_all=True,
                    append_images=images[1:],
                    duration=duration,
                    loop=0,  # 0 means infinite loop
                    optimize=True
                )
                return True
        except Exception as e:
            print(f"Error creating GIF: {e}")
        
        return False
    
    def create_gif_from_base64(self, screenshots_b64: List[str], output_path: str, duration: int = 2000) -> bool:
        """Create an animated GIF from base64 screenshot data"""
        if not screenshots_b64:
            return False
        
        try:
            images = []
            for b64_data in screenshots_b64:
                # Decode base64 to image
                img_data = base64.b64decode(b64_data)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                    tmp.write(img_data)
                    tmp.flush()
                    
                    img = Image.open(tmp.name)
                    # Resize to reasonable size for web display
                    img = img.resize((800, 600), Image.Resampling.LANCZOS)
                    images.append(img)
                    
                os.unlink(tmp.name)
            
            if images:
                # Save as GIF with loop
                images[0].save(
                    output_path,
                    save_all=True,
                    append_images=images[1:],
                    duration=duration,
                    loop=0,  # 0 means infinite loop
                    optimize=True
                )
                return True
        except Exception as e:
            print(f"Error creating GIF from base64: {e}")
        
        return False
    
    def generate_task_gif(self, screenshots_b64: List[str] = None, duration: int = 2000) -> str:
        """Generate GIF for a task and return the file path"""
        output_path = self.gifs_dir / f"task_{self.task_id}.gif"
        
        # Try to create GIF from provided base64 screenshots first
        if screenshots_b64 and self.create_gif_from_base64(screenshots_b64, str(output_path), duration):
            return str(output_path)
        
        # Fallback: try to find screenshots on disk
        screenshot_files = self.find_task_screenshots()
        if screenshot_files and self.create_gif_from_screenshots(screenshot_files, str(output_path), duration):
            return str(output_path)
        
        return ""


class TaskSummaryGenerator:
    """Generates summaries of browser automation tasks"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def generate_summary(self, task_description: str, actions_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a comprehensive summary of the task execution"""
        
        # Prepare actions summary
        actions_summary = []
        for i, action in enumerate(actions_log, 1):
            # Handle both dict and string types in actions_log
            if isinstance(action, dict):
                action_type = action.get('action_type', 'unknown')
                details = action.get('details', '')
                url = action.get('url', '')
                actions_summary.append(f"Step {i}: {action_type} - {details} (URL: {url})")
            elif isinstance(action, str):
                # If action is a string, use it directly
                actions_summary.append(f"Step {i}: {action}")
            else:
                # Fallback for any other type
                actions_summary.append(f"Step {i}: {str(action)}")
        
        actions_text = "\n".join(actions_summary) if actions_summary else "No detailed actions recorded"
        
        prompt = f"""
        Analyze this browser automation task and provide a comprehensive summary:
        
        **Original Task:** {task_description}
        
        **Actions Performed:**
        {actions_text}
        
        Please provide:
        1. **Task Overview**: Brief description of what was accomplished
        2. **Key Steps**: Main actions taken (in numbered list)
        3. **Outcome**: Whether the task was successful and what was achieved
        4. **Duration**: Estimated time taken based on number of steps
        5. **Notable Events**: Any interesting or important actions during execution
        
        Keep it concise but informative. Format as JSON with these keys:
        - overview
        - key_steps (array)
        - outcome
        - duration_estimate
        - notable_events (array)
        """
        
        try:
            response = self.llm.generate_content(prompt)
            # Try to parse as JSON, fallback to text summary
            try:
                import json
                summary_data = json.loads(response.text)
            except:
                # Fallback to structured text
                summary_data = {
                    "overview": response.text[:200],
                    "key_steps": ["Task execution completed"],
                    "outcome": "Task completed",
                    "duration_estimate": f"Approximately {len(actions_log)} steps",
                    "notable_events": []
                }
            
            return summary_data
            
        except Exception as e:
            # Fallback summary
            return {
                "overview": f"Browser automation task: {task_description}",
                "key_steps": [f"Executed {len(actions_log)} automation steps"],
                "outcome": "Task completed",
                "duration_estimate": f"Approximately {len(actions_log)} steps",
                "notable_events": ["Task execution completed"]
            }