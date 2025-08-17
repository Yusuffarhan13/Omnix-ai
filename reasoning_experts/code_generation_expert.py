import asyncio
import logging
from langchain_google_genai import ChatGoogleGenerativeAI

class CodeGenerationExpert:
    """An expert in generating and debugging code."""

    def __init__(self, google_api_key: str):
        self.google_api_key = google_api_key
        self.logger = logging.getLogger(__name__)
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            google_api_key=self.google_api_key,
            temperature=0.1,
        )
        self.logger.info("💻 Code Generation & Debugging Expert initialized")

    async def generate_code(self, request: str) -> str:
        """Generate code based on a request."""
        self.logger.info(f"Generating code for: {request}")
        
        prompt = f"""
        Please generate high-quality, well-documented code for the following request.

        Request: {request}
        """
        
        try:
            response = await asyncio.to_thread(
                self.llm.invoke,
                prompt
            )
            return response.content
        except Exception as e:
            self.logger.error(f"❌ Failed to generate code: {e}")
            return f"Error generating code: {e}"

    async def debug_code(self, code: str, error: str) -> str:
        """Debug a piece of code given an error message."""
        self.logger.info(f"Debugging code with error: {error}")
        
        prompt = f"""
        Please debug the following code.

        Code:
        ```
        {code}
        ```

        Error: {error}
        """
        
        try:
            response = await asyncio.to_thread(
                self.llm.invoke,
                prompt
            )
            return response.content
        except Exception as e:
            self.logger.error(f"❌ Failed to debug code: {e}")
            return f"Error debugging code: {e}"