import asyncio
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

class CreativeWritingExpert:
    """An expert in generating creative content."""

    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.logger = logging.getLogger(__name__)
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            google_api_key=self.google_api_key,
            temperature=0.7,
        )
        self.logger.info("✍️ Creative Writing Expert initialized")

    async def write(self, topic: str, style: str = "neutral") -> str:
        """Write a creative piece on a given topic."""
        self.logger.info(f"Writing about '{topic}' in a {style} style.")
        
        prompt = f"""
        Please write a creative piece on the following topic.

        Topic: {topic}
        Style: {style}
        """
        
        try:
            response = await asyncio.to_thread(
                self.llm.invoke,
                prompt
            )
            return response.content
        except Exception as e:
            self.logger.error(f"❌ Failed to write creative piece: {e}")
            return f"Error writing creative piece: {e}"