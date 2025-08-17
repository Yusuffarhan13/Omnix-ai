import os
import base64
import json
from pathlib import Path
import time

class ScreenshotCollector:
    def __init__(self, task_id):
        self.task_id = task_id
        self.screenshots_dir = Path(f"task_data/{task_id}/screenshots")
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.screenshots = []
        self.actions_log = []
        self.metadata = {
            'task_id': self.task_id,
            'start_time': time.time(),
            'screenshots_metadata': []
        }

    def add_screenshot(self, screenshot_b64, description):
        step_num = len(self.screenshots) + 1
        filename = f"step_{step_num}.png"
        filepath = self.screenshots_dir / filename
        
        # Decode and save the screenshot
        try:
            img_data = base64.b64decode(screenshot_b64)
            with open(filepath, "wb") as f:
                f.write(img_data)
            
            self.screenshots.append({
                'step': step_num,
                'filepath': str(filepath),
                'b64': screenshot_b64,
                'description': description
            })
            
            # Log action and metadata
            self.actions_log.append(f"Step {step_num}: {description}")
            self.metadata['screenshots_metadata'].append({
                'step': step_num,
                'filename': filename,
                'description': description,
                'timestamp': time.time()
            })
            
        except Exception as e:
            print(f"Error saving screenshot for step {step_num}: {e}")

    def get_screenshots_b64(self):
        return [s['b64'] for s in self.screenshots]

    def get_actions_log(self):
        return self.actions_log

    def save_metadata(self):
        self.metadata['end_time'] = time.time()
        self.metadata['total_steps'] = len(self.screenshots)
        
        metadata_path = self.screenshots_dir.parent / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(self.metadata, f, indent=4)

    def save_screenshots_to_disk(self):
        # This is already done in add_screenshot, but can be used for bulk saving if needed
        for screenshot in self.screenshots:
            try:
                img_data = base64.b64decode(screenshot['b64'])
                with open(screenshot['filepath'], "wb") as f:
                    f.write(img_data)
            except Exception as e:
                print(f"Error re-saving screenshot {screenshot['filepath']}: {e}")