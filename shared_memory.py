import asyncio
import logging
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI

class SharedMemorySystem:
    """A system for storing and synthesizing responses from multiple reasoning systems."""

    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.logger = logging.getLogger(__name__)
        self.memory: Dict[str, Any] = {}
        self.synthesis_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            google_api_key=self.google_api_key,
            temperature=0.1,
            max_output_tokens=8192,
        )
        self.logger.info("🧠 Shared Memory System initialized")

    def add_response(self, source: str, response: Any):
        """Add a response from a reasoning system to the memory."""
        self.logger.info(f"📝 Adding response from '{source}' to shared memory.")
        self.memory[source] = response

    async def synthesize_responses(self) -> str:
        """Combine all responses in memory to generate a comprehensive answer."""
        self.logger.info("🔄 Synthesizing responses from shared memory...")
        
        synthesis_prompt = "Please synthesize the following information from different reasoning systems into a single, coherent, and comprehensive answer:\n\n"
        for source, response in self.memory.items():
            synthesis_prompt += f"--- From {source} ---\n{response}\n\n"
        
        synthesis_prompt += "Please provide a final, synthesized answer that combines the key insights from all sources."

        try:
            response = await asyncio.to_thread(
                self.synthesis_llm.invoke,
                synthesis_prompt
            )
            return response.content
        except Exception as e:
            self.logger.error(f"❌ Synthesis failed: {e}")
            return f"Error during synthesis: {e}"

    def clear_memory(self):
        """Clear all responses from the memory."""
        self.logger.info("🗑️ Clearing shared memory.")
        self.memory = {}