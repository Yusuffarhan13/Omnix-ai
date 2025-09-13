"""
Perplexity Sonar Deep Research API Integration
This module replaces the existing research system with Perplexity's Sonar Deep Research API
"""

import os
import json
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import aiohttp

logger = logging.getLogger(__name__)


class PerplexityResearchManager:
    """
    Manager for Perplexity Sonar Deep Research API
    Provides comprehensive research capabilities using Perplexity's advanced AI model
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the Perplexity Research Manager
        
        Args:
            api_key: Perplexity API key
        """
        self.api_key = api_key
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Model configuration
        self.model = "sonar-deep-research"
        
        # Cache for research results (optional)
        self.cache = {}
        self.cache_duration = 3600  # Cache for 1 hour
        
        logger.info("✅ Perplexity Sonar Deep Research Manager initialized")
    
    async def conduct_research(
        self, 
        query: str,
        use_cache: bool = True,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Conduct deep research using Perplexity's Sonar Deep Research API
        
        Args:
            query: The research query
            use_cache: Whether to use cached results if available
            stream: Whether to stream the response
            
        Returns:
            Dictionary containing research results
        """
        try:
            # Check cache first
            if use_cache and query in self.cache:
                cached_result = self.cache[query]
                if (datetime.now() - cached_result['timestamp']).seconds < self.cache_duration:
                    logger.info(f"📦 Returning cached result for: {query}")
                    return cached_result['data']
            
            logger.info(f"🔍 Starting Perplexity Deep Research for: {query}")
            
            # Prepare the request payload
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a comprehensive research assistant. Provide detailed, well-sourced information with citations."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                "stream": stream
            }
            
            # Make async request to Perplexity API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=self.headers,
                    json=payload
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"API Error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    # Process the response
                    processed_result = self._process_research_response(result, query)
                    
                    # Cache the result
                    if use_cache:
                        self.cache[query] = {
                            'timestamp': datetime.now(),
                            'data': processed_result
                        }
                    
                    return processed_result
                    
        except Exception as e:
            logger.error(f"❌ Research error: {str(e)}")
            return self._create_error_response(str(e))
    
    def _process_research_response(self, response: Dict, query: str) -> Dict[str, Any]:
        """
        Process the raw API response into a structured format
        
        Args:
            response: Raw API response from Perplexity
            query: Original query for context
            
        Returns:
            Processed research results
        """
        try:
            # Extract the main content from the response
            choices = response.get('choices', [])
            if not choices:
                raise ValueError("No choices in response")
            
            message = choices[0].get('message', {})
            content = message.get('content', '')
            
            # Extract citations if available
            citations = response.get('citations', [])
            
            # Parse the content to extract key information
            # Perplexity's response typically includes structured information
            
            # Create structured response
            result = {
                'success': True,
                'query': query,
                'summary': content,
                'sources': self._extract_sources(citations),
                'key_insights': self._extract_key_insights(content),
                'timestamp': datetime.now().isoformat(),
                'model': self.model,
                'confidence_score': None,  # Not displaying confidence scores
                'metadata': {
                    'total_tokens': response.get('usage', {}).get('total_tokens', 0),
                    'search_queries_performed': response.get('search_queries', 0),
                    'sources_analyzed': len(citations)
                }
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return self._create_error_response(str(e))
    
    def _extract_sources(self, citations: List) -> List[Dict]:
        """
        Extract and format source citations
        
        Args:
            citations: Raw citations from API response
            
        Returns:
            Formatted list of sources
        """
        sources = []
        for i, citation in enumerate(citations):
            if isinstance(citation, dict):
                sources.append({
                    'title': citation.get('title', f'Source {i+1}'),
                    'url': citation.get('url', ''),
                    'snippet': citation.get('snippet', ''),
                    'credibility': 0.9,  # Perplexity pre-filters for quality
                    'type': 'web'
                })
            elif isinstance(citation, str):
                # Handle string citations
                sources.append({
                    'title': f'Source {i+1}',
                    'url': citation,
                    'snippet': '',
                    'credibility': 0.9,
                    'type': 'web'
                })
        return sources
    
    def _extract_key_insights(self, content: str) -> List[str]:
        """
        Extract key insights from the research content
        
        Args:
            content: The main research content
            
        Returns:
            List of key insights
        """
        insights = []
        
        # Simple extraction based on content structure
        # Perplexity often structures content with clear sections
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for bullet points or numbered items
            if line and (line.startswith('•') or line.startswith('-') or 
                        (len(line) > 2 and line[0].isdigit() and line[1] in '.)')):
                # Clean up the insight
                insight = line.lstrip('•-0123456789.) ').strip()
                if insight and len(insight) > 20:  # Filter out very short items
                    insights.append(insight)
        
        # If no bullet points found, extract first few sentences as insights
        if not insights:
            sentences = content.split('. ')
            insights = [s.strip() + '.' for s in sentences[:5] if len(s.strip()) > 20]
        
        return insights[:10]  # Limit to top 10 insights
    
    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Create a standardized error response
        
        Args:
            error_message: The error message
            
        Returns:
            Error response dictionary
        """
        return {
            'success': False,
            'error': error_message,
            'summary': f"Research failed: {error_message}",
            'sources': [],
            'key_insights': [],
            'timestamp': datetime.now().isoformat(),
            'model': self.model,
            'confidence_score': 0
        }
    
    def conduct_research_sync(self, query: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Synchronous wrapper for conduct_research
        
        Args:
            query: The research query
            use_cache: Whether to use cached results
            
        Returns:
            Research results
        """
        try:
            # Create new event loop for sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.conduct_research(query, use_cache))
            return result
        except Exception as e:
            logger.error(f"Sync research error: {e}")
            return self._create_error_response(str(e))
        finally:
            if 'loop' in locals():
                loop.close()
    
    def clear_cache(self):
        """Clear the research cache"""
        self.cache.clear()
        logger.info("🗑️ Research cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'entries': len(self.cache),
            'queries': list(self.cache.keys()),
            'cache_duration_seconds': self.cache_duration
        }


class PerplexityStreamingResearch:
    """
    Streaming research implementation for real-time updates
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def stream_research(self, query: str, callback=None):
        """
        Stream research results in real-time
        
        Args:
            query: Research query
            callback: Callback function for streaming updates
        """
        payload = {
            "model": "sonar-deep-research",
            "messages": [
                {
                    "role": "user",
                    "content": query
                }
            ],
            "stream": True
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                headers=self.headers,
                json=payload
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            # Parse SSE format
                            line_str = line.decode('utf-8').strip()
                            if line_str.startswith('data: '):
                                data_str = line_str[6:]
                                if data_str != '[DONE]':
                                    data = json.loads(data_str)
                                    if callback:
                                        await callback(data)
                                    else:
                                        print(data)
                        except Exception as e:
                            logger.error(f"Stream parsing error: {e}")


# Utility function for testing
def test_perplexity_research():
    """Test the Perplexity research integration"""
    api_key = os.getenv('PERPLEXITY_API_KEY')
    if not api_key:
        print("❌ PERPLEXITY_API_KEY not found in environment variables")
        return
    
    manager = PerplexityResearchManager(api_key)
    
    # Test query
    test_query = "What are the latest developments in quantum computing in 2025?"
    
    print(f"🔍 Testing research with query: {test_query}")
    result = manager.conduct_research_sync(test_query)
    
    if result['success']:
        print(f"✅ Research successful!")
        print(f"📝 Summary: {result['summary'][:500]}...")
        print(f"📚 Sources found: {len(result['sources'])}")
        print(f"💡 Key insights: {len(result['key_insights'])}")
    else:
        print(f"❌ Research failed: {result['error']}")


if __name__ == "__main__":
    test_perplexity_research()