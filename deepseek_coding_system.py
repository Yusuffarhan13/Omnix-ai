#!/usr/bin/env python3
"""
DeepSeek R1 Coding System - Dedicated system for coding tasks
Features:
- DeepSeek R1 for deep thinking, web search & sequential thinking
- Focus on executable HTML/CSS/JavaScript code generation
- Separate from complex mode - purely for coding requests
- No multi-stage reasoning - just pure DeepSeek R1 thinking
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional
import requests


class DeepSeekCodingSystem:
    """Dedicated DeepSeek R1 system for coding tasks with deep thinking, web search & sequential thinking"""
    
    def __init__(self, openrouter_api_key: str, brave_api_key: str = None, openrouter_backup_key: str = None):
        self.openrouter_api_key = openrouter_api_key
        self.openrouter_backup_key = openrouter_backup_key
        self.current_key = openrouter_api_key  # Track which key is currently being used
        self.brave_api_key = brave_api_key
        self.logger = logging.getLogger(__name__)
        
        # OpenRouter configuration for DeepSeek R1
        self.openrouter_base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.deepseek_model = "deepseek/deepseek-r1-0528:free"
        
        # Coding keywords for detection
        self.coding_keywords = [
            'code', 'function', 'class', 'algorithm', 'debug', 'error', 'bug', 'program', 'script',
            'html', 'css', 'javascript', 'js', 'web', 'website', 'page', 'dom', 'element',
            'variable', 'loop', 'if statement', 'array', 'object', 'method', 'framework',
            'coding', 'programming', 'development', 'software', 'application', 'create', 'build',
            'make', 'write', 'implement', 'generate', 'interactive', 'dynamic', 'animation',
            'python', 'java', 'c++', 'node.js', 'api', 'database', 'sql'
        ]
        
        # Web search API configuration
        self.search_base_url = "https://api.search.brave.com/res/v1/web/search"
        
        self.logger.info("✅ DeepSeek R1 Coding System initialized for dedicated coding tasks")
    
    def _call_deepseek_r1(self, prompt: str, max_tokens: int = 8000) -> str:
        """Call DeepSeek R1 via OpenRouter for coding tasks with automatic fallback"""
        def try_api_call(api_key: str, key_name: str) -> tuple:
            """Try API call with given key, return (success, result)"""
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.deepseek_model,
                    "messages": [
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    "max_tokens": max_tokens,
                    "temperature": 0.1,
                    "top_p": 0.95
                }
                
                response = requests.post(
                    self.openrouter_base_url,
                    headers=headers,
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return True, result["choices"][0]["message"]["content"]
                elif response.status_code == 429:
                    # Rate limited - return False to try backup
                    self.logger.warning(f"Rate limited on {key_name}: {response.text}")
                    return False, f"Rate limited on {key_name}"
                else:
                    self.logger.error(f"DeepSeek R1 API error on {key_name}: {response.status_code} - {response.text}")
                    return False, f"Error on {key_name}: {response.status_code}"
                    
            except Exception as e:
                self.logger.error(f"DeepSeek R1 call failed on {key_name}: {e}")
                return False, f"Exception on {key_name}: {str(e)}"
        
        # Try primary key first
        success, result = try_api_call(self.current_key, "primary key")
        if success:
            return result
        
        # If primary failed with rate limit and we have backup key, try backup
        if self.openrouter_backup_key and "Rate limited" in result:
            self.logger.info("🔄 Switching to backup OpenRouter API key due to rate limit...")
            success, backup_result = try_api_call(self.openrouter_backup_key, "backup key")
            if success:
                # Switch to backup key for future calls
                self.current_key = self.openrouter_backup_key
                self.logger.info("✅ Successfully switched to backup API key")
                return backup_result
            else:
                return f"Both API keys failed - Primary: {result}, Backup: {backup_result}"
        
        return result
    
    def _web_search(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform web search using Brave Search API"""
        if not self.brave_api_key:
            return []
        
        try:
            headers = {
                "Accept": "application/json",
                "Accept-Encoding": "gzip",
                "X-Subscription-Token": self.brave_api_key
            }
            
            params = {
                "q": query,
                "count": max_results,
                "offset": 0,
                "mkt": "en-US",
                "safesearch": "moderate",
                "freshness": "pm",  # Past month for recent coding info
                "text_decorations": False,
                "spellcheck": True
            }
            
            response = requests.get(
                self.search_base_url,
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                if 'web' in data and 'results' in data['web']:
                    for result in data['web']['results'][:max_results]:
                        results.append({
                            'title': result.get('title', ''),
                            'description': result.get('description', ''),
                            'url': result.get('url', ''),
                            'published': result.get('published', '')
                        })
                
                return results
            else:
                self.logger.error(f"Brave Search API error: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Web search failed: {e}")
            return []
    
    def _is_web_coding_request(self, user_message: str) -> bool:
        """Detect if user wants web code (HTML/CSS/JS) that can run in browser"""
        message_lower = user_message.lower()
        
        # Specific web coding keywords
        web_keywords = [
            'html', 'css', 'javascript', 'js', 'webpage', 'website', 'browser',
            'dom', 'element', 'responsive', 'frontend', 'ui', 'user interface', 
            'button', 'form', 'input', 'div', 'canvas', 'modal', 'popup', 
            'slider', 'carousel', 'animation', 'hover', 'grid layout', 'flexbox',
            'interactive', 'dashboard', 'component'
        ]
        
        # Non-web coding keywords that should be excluded
        non_web_keywords = [
            'api', 'rest api', 'server', 'backend', 'database', 'scraper', 
            'scraping', 'cache', 'caching', 'distributed', 'python', 'node.js',
            'java', 'c++', 'algorithm', 'sorting', 'fibonacci', 'sql'
        ]
        
        # Implementation keywords
        implementation_keywords = [
            'create', 'build', 'make', 'write', 'implement', 'code',
            'develop', 'program', 'script', 'generate'
        ]
        
        web_match = any(keyword in message_lower for keyword in web_keywords)
        non_web_match = any(keyword in message_lower for keyword in non_web_keywords)
        implementation_match = any(keyword in message_lower for keyword in implementation_keywords)
        
        return web_match and implementation_match and not non_web_match
    
    def _is_coding_request(self, user_message: str) -> bool:
        """Detect if the user request is related to coding/programming"""
        message_lower = user_message.lower()
        
        # Check for coding keywords
        keyword_match = any(keyword in message_lower for keyword in self.coding_keywords)
        
        # Check for code patterns
        code_patterns = [
            'def ', 'function ', 'class ', 'import ', 'from ', '#!/',
            'console.log', 'print(', 'return ', 'if (', 'for (', 'while (',
            '```', 'const ', 'var ', 'let ', 'public ', 'private ', 'static '
        ]
        pattern_match = any(pattern in message_lower for pattern in code_patterns)
        
        return keyword_match or pattern_match
    
    def process_coding_request(self, user_message: str) -> Dict[str, Any]:
        """
        Process coding requests using DeepSeek R1 with deep thinking, web search & sequential thinking
        """
        self.logger.info(f"🧠 DeepSeek Coding System: Processing request: {user_message[:100]}...")
        start_time = time.time()
        
        try:
            is_web_coding = self._is_web_coding_request(user_message)
            
            if is_web_coding:
                return self._process_web_coding(user_message, start_time)
            else:
                return self._process_general_coding(user_message, start_time)
                
        except Exception as e:
            self.logger.error(f"DeepSeek Coding System failed: {e}")
            return {
                'error': f'DeepSeek Coding System error: {str(e)}',
                'fallback_response': 'I apologize, but there was an error processing your coding request. Please try again.'
            }
    
    def _process_web_coding(self, user_message: str, start_time: float) -> Dict[str, Any]:
        """Process web coding requests for executable HTML/CSS/JS code"""
        
        # Step 1: Web search for relevant coding information
        search_query = f"HTML CSS JavaScript {user_message} tutorial example code 2024"
        search_results = self._web_search(search_query, max_results=3)
        
        search_context = ""
        if search_results:
            search_context = "\n\n🔍 **Recent Web Development Information:**\n"
            for result in search_results:
                search_context += f"- {result['title']}: {result['description']}\n"
        
        # Step 2: DeepSeek R1 with deep thinking, web search context & sequential thinking
        deepseek_prompt = f"""
You are DeepSeek R1, an advanced reasoning model specializing in web development. Use DEEP THINKING, WEB SEARCH CONTEXT, and SEQUENTIAL THINKING to create executable HTML/CSS/JavaScript code.

User Request: {user_message}
{search_context}

## DEEP THINKING + SEQUENTIAL THINKING PROCESS:

### 1. DEEP UNDERSTANDING:
- What exactly does the user want to create?
- What are the core functional requirements?
- What web technologies are needed?
- What should the user experience be?

### 2. WEB SEARCH INTEGRATION:
- How can I incorporate the latest web development practices from the search results?
- What modern approaches should I use?
- Are there any recent best practices to follow?

### 3. SEQUENTIAL PLANNING:
- Step 1: HTML structure planning
- Step 2: CSS styling approach
- Step 3: JavaScript functionality design
- Step 4: Integration and testing considerations

### 4. DEEP IMPLEMENTATION REASONING:
- What's the most efficient code structure?
- How to ensure cross-browser compatibility?
- What modern web standards should I use?
- How to make it responsive and accessible?

## CRITICAL REQUIREMENT: GENERATE ACTUAL WORKING CODE
DO NOT provide analysis, explanations, or architectural guidance.
DO NOT provide pseudocode or theoretical solutions.
ONLY generate complete, executable HTML files with embedded CSS and JavaScript.

## FINAL OUTPUT REQUIREMENTS:
You MUST generate a COMPLETE, WORKING HTML file that:
- Contains ALL code needed to run immediately in a browser
- Has embedded CSS and JavaScript (no external dependencies)
- Works when copy-pasted and opened in any browser
- Implements exactly what the user requested
- Includes modern styling and functionality

## MANDATORY RESPONSE FORMAT:
Start your response with the complete HTML code block:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your App Title</title>
    <style>
        /* Complete CSS styling here */
    </style>
</head>
<body>
    <!-- Complete HTML structure here -->
    
    <script>
        // Complete JavaScript functionality here
    </script>
</body>
</html>
```

GENERATE THE COMPLETE WORKING CODE NOW!
"""
        
        self.logger.info("🧠 DeepSeek R1: Deep thinking + Sequential thinking + Web search for web coding...")
        code_response = self._call_deepseek_r1(deepseek_prompt, max_tokens=10000)
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ DeepSeek web coding completed in {processing_time:.2f}s")
        
        return {
            'response': code_response,
            'processing_time': processing_time,
            'mode': 'deepseek_coding_web',
            'request_type': 'web_coding',
            'models_used': ['deepseek-r1-0528'],
            'workflow': 'deepseek_deep_thinking_sequential_web_search',
            'is_executable': True,
            'code_type': 'html_css_js',
            'search_results': search_results if search_results else None
        }
    
    def _process_general_coding(self, user_message: str, start_time: float) -> Dict[str, Any]:
        """Process general coding requests with deep analysis"""
        
        # Step 1: Web search for relevant coding information
        search_query = f"{user_message} programming code example best practices 2024"
        search_results = self._web_search(search_query, max_results=3)
        
        search_context = ""
        if search_results:
            search_context = "\n\n🔍 **Recent Programming Information:**\n"
            for result in search_results:
                search_context += f"- {result['title']}: {result['description']}\n"
        
        # Step 2: DeepSeek R1 with deep thinking & sequential thinking
        deepseek_prompt = f"""
You are DeepSeek R1, an advanced reasoning model specializing in software engineering. Use DEEP THINKING, WEB SEARCH CONTEXT, and SEQUENTIAL THINKING to analyze this coding request.

User Coding Request: {user_message}
{search_context}

## DEEP THINKING + SEQUENTIAL THINKING PROCESS:

### 1. DEEP UNDERSTANDING:
- What exactly is the user asking about?
- What programming concepts are involved?
- What are the technical challenges?
- What solutions exist in the current landscape?

### 2. WEB SEARCH INTEGRATION:
- What recent developments or best practices can I incorporate?
- Are there new approaches or tools mentioned in the search results?
- How do current industry practices address this?

### 3. SEQUENTIAL ANALYSIS:
- Step 1: Problem breakdown and requirements analysis
- Step 2: Technical approach evaluation
- Step 3: Implementation strategy design
- Step 4: Best practices and optimization considerations

### 4. DEEP TECHNICAL REASONING:
- What are the pros and cons of different approaches?
- What are the performance, security, and scalability implications?
- How does this fit into modern software architecture?
- What are the potential pitfalls and how to avoid them?

## CRITICAL REQUIREMENT: PROVIDE WORKING CODE EXAMPLES
Focus on generating PRACTICAL, EXECUTABLE code examples rather than just theoretical analysis.

## RESPONSE REQUIREMENTS:
You MUST provide:
1. **Working Code Examples**: Complete, runnable code that demonstrates the solution
2. **Practical Implementation**: Real code the user can copy-paste and use
3. **Setup Instructions**: Exact commands to install dependencies and run the code
4. **Working Examples**: Functional code snippets with proper imports and structure

## MANDATORY FORMAT:
Start with working code examples in proper code blocks:

```python
# Complete working Python code here
```

```javascript  
// Complete working JavaScript code here
```

```bash
# Setup commands here
```

Then provide brief explanations and best practices.

GENERATE WORKING CODE EXAMPLES NOW!
"""
        
        self.logger.info("🧠 DeepSeek R1: Deep thinking + Sequential thinking + Web search for general coding...")
        coding_response = self._call_deepseek_r1(deepseek_prompt, max_tokens=8000)
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ DeepSeek general coding completed in {processing_time:.2f}s")
        
        return {
            'response': coding_response,
            'processing_time': processing_time,
            'mode': 'deepseek_coding_general',
            'request_type': 'general_coding',
            'models_used': ['deepseek-r1-0528'],
            'workflow': 'deepseek_deep_thinking_sequential_web_search',
            'is_executable': False,
            'search_results': search_results if search_results else None
        }
    
    def is_available(self) -> bool:
        """Check if the system is available"""
        return bool(self.openrouter_api_key)