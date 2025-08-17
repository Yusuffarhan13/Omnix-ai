import asyncio
import logging
import requests
from langchain_google_genai import ChatGoogleGenerativeAI

class WebResearchExpert:
    """An expert in finding and verifying information from the web."""

    def __init__(self, google_api_key: str, brave_api_key: str):
        self.google_api_key = google_api_key
        self.brave_api_key = brave_api_key
        self.logger = logging.getLogger(__name__)
        self.llm = ChatGoogleGenerativeAI(
            model='gemini-2.5-pro',
            google_api_key=self.google_api_key,
            temperature=0.1,
        )
        self.logger.info("🌐 Web Research & Fact-Checking Expert initialized")

    async def research(self, query: str) -> str:
        """Research a topic on the web."""
        self.logger.info(f"🔎 Researching: {query}")
        
        try:
            headers = {"X-Subscription-Token": self.brave_api_key}
            params = {"q": query, "count": 5}
            response = requests.get("https://api.search.brave.com/res/v1/web/search", params=params, headers=headers)
            response.raise_for_status()
            search_results = response.json()

            context = ""
            for result in search_results.get("web", {}).get("results", []):
                context += f"Title: {result.get('title', '')}\nURL: {result.get('url', '')}\nSnippet: {result.get('description', '')}\n\n"

            prompt = f"""
            Based on the following search results, please provide a comprehensive answer to the query.

            Query: {query}

            Search Results:
            {context}
            """
            
            response = await asyncio.to_thread(
                self.llm.invoke,
                prompt
            )
            return response.content
        except Exception as e:
            self.logger.error(f"❌ Failed to research: {e}")
            return f"Error during research: {e}"