import asyncio
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

class MathLogicExpert:
    """An expert in solving mathematical and logical problems."""

    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.logger = logging.getLogger(__name__)
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            google_api_key=self.google_api_key,
            temperature=0.0,
        )
        self.logger.info("🧠 Math & Logic Expert initialized")

    async def solve(self, problem: str) -> str:
        """Solve a mathematical or logical problem."""
        self.logger.info(f"🔢 Solving problem: {problem}")
        
        prompt = f"""
        Please solve the following mathematical or logical problem. Show your work step-by-step and provide a clear, final answer.

        Problem: {problem}
        """
        
        try:
            response = await asyncio.to_thread(
                self.llm.invoke,
                prompt
            )
            return response.content
        except Exception as e:
            self.logger.error(f"❌ Failed to solve problem: {e}")
            return f"Error solving problem: {e}"