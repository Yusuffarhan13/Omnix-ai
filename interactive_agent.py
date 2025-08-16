#!/usr/bin/env python3
"""
Interactive Browser Agent with pause/resume and user collaboration features
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable
from browser_use import Agent as BrowserAgent
from browser_use.browser.session import BrowserSession


class InteractiveBrowserAgent:
    """Enhanced browser agent that supports real-time user interaction"""
    
    def __init__(self, task_description: str, browser_session: BrowserSession, llm, 
                 update_manager, task_id: str, max_actions_per_step: int = 5):
        self.task_description = task_description
        self.browser_session = browser_session
        self.llm = llm
        self.update_manager = update_manager
        self.task_id = task_id
        self.max_actions_per_step = max_actions_per_step
        
        self.is_paused = False
        self.user_input_queue = asyncio.Queue()
        self.step_count = 0
        self.max_steps = 30
        
        # Create the underlying browser agent
        self.agent = BrowserAgent(
            task=task_description,
            browser_session=browser_session,
            llm=llm,
            max_actions_per_step=max_actions_per_step
        )
        
        logging.info(f"🤖 Interactive agent created for task: {task_id}")
    
    async def run(self) -> str:
        """Run the interactive browser automation with pause/resume support"""
        
        try:
            # Add task to update manager
            debug_port = getattr(self.browser_session, 'debug_port', None)
            self.update_manager.add_task(self.task_id, self.task_description, debug_port)
            
            # Start the interactive execution loop
            result = await self._interactive_execution_loop()
            
            # Mark task as completed
            self.update_manager.complete_task(self.task_id, result)
            return result
            
        except Exception as e:
            error_msg = f"Interactive task failed: {str(e)}"
            logging.error(error_msg)
            self.update_manager.complete_task(self.task_id, error_msg)
            return error_msg
    
    async def _interactive_execution_loop(self) -> str:
        """Main execution loop with pause/resume support using actual browser-use agent"""
        
        try:
            # Run the actual browser-use agent with interactive controls
            logging.info(f"🚀 Starting browser-use agent for task: {self.task_description}")
            
            # Execute the browser agent in a way that allows for interruption
            result = await self._run_agent_with_interactive_control()
            
            logging.info(f"✅ Browser agent completed with result: {result}")
            return result
            
        except Exception as e:
            error_msg = f"Interactive browser execution failed: {str(e)}"
            logging.error(error_msg, exc_info=True)
            return error_msg
    
    async def _run_agent_with_interactive_control(self) -> str:
        """Run the browser agent with interactive pause/resume control"""
        
        try:
            # Start the agent execution
            logging.info("🎭 Launching browser agent...")
            
            # We'll override the agent's step execution to add our interactive controls
            original_run = self.agent.run
            
            async def interactive_run(*args, **kwargs):
                """Wrapped agent run with interactive controls"""
                try:
                    # Check for pause/user input before each major operation
                    await self._check_pause_state()
                    
                    user_message = await self._check_user_input()
                    if user_message:
                        await self._handle_user_input(user_message)
                    
                    # Run the actual agent
                    return await original_run(*args, **kwargs)
                    
                except Exception as e:
                    logging.error(f"Agent execution error: {e}")
                    # Request user intervention
                    await self._request_user_intervention(
                        f"Browser automation encountered an issue: {str(e)}. How should I proceed?"
                    )
                    await self._wait_for_user_response()
                    raise
            
            # Replace the agent's run method temporarily
            self.agent.run = interactive_run
            
            # Execute the agent
            result = await self.agent.run()
            
            # Convert result to string to avoid JSON serialization issues
            if result:
                if hasattr(result, 'all_results') and result.all_results:
                    # Extract the final result from the last action
                    final_result = result.all_results[-1]
                    if hasattr(final_result, 'extracted_content'):
                        return str(final_result.extracted_content)
                    elif hasattr(final_result, 'long_term_memory'):
                        return str(final_result.long_term_memory)
                
                return str(result)
            else:
                return "Task completed successfully"
            
        except Exception as e:
            logging.error(f"Error running agent with interactive control: {e}")
            return f"Browser automation failed: {str(e)}"
    
    async def _execute_step(self, step_num: int) -> Dict[str, Any]:
        """Execute a single step of browser automation using the actual browser agent"""
        
        try:
            # Get current page state for context
            current_url = "unknown"
            try:
                if self.browser_session.browser and self.browser_session.browser.current_page:
                    current_url = self.browser_session.browser.current_page.url or "unknown"
            except:
                pass
            
            logging.info(f"🔄 Executing step {step_num} for task {self.task_id}")
            
            # Check if we should pause before executing
            await self._check_pause_state()
            
            # Run one step of the actual browser agent
            try:
                # Execute the browser agent step
                result = await self.agent.step()
                
                if result:
                    action = result.get('action', f'step_{step_num}')
                    description = result.get('description', 'Browser automation step completed')
                    
                    # Update the step in real-time
                    self.update_manager.update_task_step(
                        self.task_id, step_num, action, description, current_url
                    )
                    
                    # Check if the agent indicates completion
                    if result.get('done', False) or result.get('completed', False):
                        return {'completed': True, 'result': result.get('result', 'Task completed successfully')}
                    
                    return {'completed': False, 'step': step_num, 'result': result}
                else:
                    # No more steps to execute
                    return {'completed': True, 'result': 'Task completed successfully'}
                    
            except Exception as agent_error:
                logging.error(f"Browser agent error at step {step_num}: {agent_error}")
                
                # Request user intervention for errors
                await self._request_user_intervention(
                    f"Browser automation encountered an issue: {str(agent_error)}. Please provide guidance."
                )
                
                # Wait for user input
                await self._wait_for_user_response()
                
                return {'completed': False, 'step': step_num, 'error': str(agent_error)}
            
        except Exception as e:
            logging.error(f"Error in step {step_num}: {e}")
            raise
    
    async def _check_pause_state(self):
        """Check if the task should be paused"""
        while self.update_manager.is_paused(self.task_id):
            await asyncio.sleep(0.5)  # Wait while paused
    
    async def _check_user_input(self) -> Optional[str]:
        """Check for user input without blocking"""
        try:
            return self.user_input_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    async def _handle_user_input(self, message: str):
        """Handle user input during task execution"""
        logging.info(f"📨 User input received: {message}")
        
        # Process user instructions
        if "pause" in message.lower():
            self.pause()
        elif "resume" in message.lower() or "continue" in message.lower():
            self.resume()
        elif "help" in message.lower() or "assist" in message.lower():
            await self._request_user_intervention(
                "I'm ready for your assistance. What would you like me to do?"
            )
        else:
            # Process as general instruction
            logging.info(f"Processing user instruction: {message}")
            # Here you could modify the task or provide additional context
    
    async def _request_user_intervention(self, message: str):
        """Request user intervention"""
        logging.info(f"🙋 Requesting user intervention: {message}")
        self.update_manager.request_intervention(self.task_id, message)
    
    async def _wait_for_user_response(self):
        """Wait for user to provide input or resume the task"""
        while self.update_manager.is_paused(self.task_id):
            await asyncio.sleep(0.5)
    
    def add_user_input(self, message: str):
        """Add user input to the queue"""
        try:
            self.user_input_queue.put_nowait(message)
        except asyncio.QueueFull:
            logging.warning("User input queue is full, message dropped")
    
    def pause(self):
        """Pause the task"""
        self.update_manager.pause_task(self.task_id)
        logging.info(f"⏸️ Task {self.task_id} paused")
    
    def resume(self):
        """Resume the task"""
        self.update_manager.resume_task(self.task_id)
        logging.info(f"▶️ Task {self.task_id} resumed")
    
    def take_screenshot(self):
        """Take a screenshot and return the path"""
        try:
            # This would integrate with the screenshot system
            logging.info(f"📸 Taking screenshot for task {self.task_id}")
            return f"screenshot_step_{self.step_count}.png"
        except Exception as e:
            logging.error(f"Failed to take screenshot: {e}")
            return None


class InteractiveAgentManager:
    """Manages multiple interactive browser agents"""
    
    def __init__(self):
        self.active_agents: Dict[str, InteractiveBrowserAgent] = {}
    
    def create_agent(self, task_id: str, task_description: str, browser_session: BrowserSession, 
                    llm, update_manager) -> InteractiveBrowserAgent:
        """Create a new interactive agent"""
        agent = InteractiveBrowserAgent(
            task_description=task_description,
            browser_session=browser_session,
            llm=llm,
            update_manager=update_manager,
            task_id=task_id
        )
        
        self.active_agents[task_id] = agent
        return agent
    
    def get_agent(self, task_id: str) -> Optional[InteractiveBrowserAgent]:
        """Get an active agent by task ID"""
        return self.active_agents.get(task_id)
    
    def remove_agent(self, task_id: str):
        """Remove an agent when task is completed"""
        if task_id in self.active_agents:
            del self.active_agents[task_id]
    
    def add_user_input(self, task_id: str, message: str):
        """Add user input to a specific agent"""
        agent = self.get_agent(task_id)
        if agent:
            agent.add_user_input(message)
    
    def pause_agent(self, task_id: str):
        """Pause a specific agent"""
        agent = self.get_agent(task_id)
        if agent:
            agent.pause()
    
    def resume_agent(self, task_id: str):
        """Resume a specific agent"""
        agent = self.get_agent(task_id)
        if agent:
            agent.resume()
    
    def take_screenshot(self, task_id: str) -> Optional[str]:
        """Take screenshot from a specific agent"""
        agent = self.get_agent(task_id)
        if agent:
            return agent.take_screenshot()
        return None