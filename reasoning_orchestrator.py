import asyncio
import logging
from typing import Dict, Any, List
from langchain_google_genai import ChatGoogleGenerativeAI
from reasoning_experts.math_logic_expert import MathLogicExpert
from reasoning_experts.code_generation_expert import CodeGenerationExpert
from reasoning_experts.creative_writing_expert import CreativeWritingExpert
from reasoning_experts.web_research_expert import WebResearchExpert
from shared_memory import SharedMemorySystem
import json


class DynamicReasoningOrchestrator:
    """An orchestrator that dynamically routes tasks to specialized experts."""

    def __init__(self, google_api_key: str, brave_api_key: str):
        self.google_api_key = google_api_key
        self.brave_api_key = brave_api_key
        self.logger = logging.getLogger(__name__)
        self.router_llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            google_api_key=self.google_api_key,
            temperature=0.0,
        )
        self.experts = {
            "math_logic": MathLogicExpert(google_api_key),
            "code_generation": CodeGenerationExpert(google_api_key),
            "creative_writing": CreativeWritingExpert(google_api_key),
            "web_research": WebResearchExpert(google_api_key, brave_api_key),
        }
        self.shared_memory = SharedMemorySystem(google_api_key)
        self.logger.info("🚀 Dynamic Reasoning Orchestrator initialized")

    async def route_task(self, prompt: str) -> List[str]:
        """Determine which expert(s) to use for a given prompt."""
        self.logger.info(f"🚦 Routing task: {prompt}")
        
        routing_prompt = f"""
        Given the following prompt, which of the following experts are best suited to handle it?
        You can choose one or more experts.

        Experts:
        - math_logic: For mathematical and logical problems.
        - code_generation: For writing, analyzing, and debugging code.
        - creative_writing: For generating creative content.
        - web_research: For finding and verifying information from the web.

        Prompt: "{prompt}"

        Please provide your answer as a JSON list of expert names.
        """
        
        try:
            response = await asyncio.to_thread(
                self.router_llm.invoke,
                routing_prompt
            )
            return json.loads(response.content)
        except Exception as e:
            self.logger.error(f"❌ Failed to route task: {e}")
            return ["web_research"] # Default to web research if routing fails

    async def execute_task(self, prompt: str) -> str:
        """Execute a task by routing it to the appropriate expert(s) and synthesizing the results."""
        self.shared_memory.clear_memory()
        
        experts_to_use = await self.route_task(prompt)
        
        tasks = []
        for expert_name in experts_to_use:
            if expert_name in self.experts:
                expert = self.experts[expert_name]
                # This is a simplified example; you would need to adapt the expert's method based on the prompt
                if hasattr(expert, 'solve'):
                    tasks.append(expert.solve(prompt))
                elif hasattr(expert, 'generate_code'):
                    tasks.append(expert.generate_code(prompt))
                elif hasattr(expert, 'write'):
                    tasks.append(expert.write(prompt))
                elif hasattr(expert, 'research'):
                    tasks.append(expert.research(prompt))

        results = await asyncio.gather(*tasks)
        
        for i, expert_name in enumerate(experts_to_use):
            self.shared_memory.add_response(expert_name, results[i])
            
        return await self.shared_memory.synthesize_responses()