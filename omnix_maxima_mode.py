#!/usr/bin/env python3
"""
Omnix Maxima Mode - DeepSeek R1 Coding System
Features:
- DeepSeek R1 for sequential thinking and code generation via OpenRouter
- Focus on executable HTML/CSS/JavaScript code only
- Advanced chain-of-thought processing for coding
- Web search integration for up-to-date information
"""

import asyncio
import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
import requests


class OmnixMaximaManager:
    """DeepSeek R1 only system for Omnix Maxima mode with executable code generation"""
    
    def __init__(self, openrouter_api_key: str, google_api_key: str = None):
        self.openrouter_api_key = openrouter_api_key
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
            'make', 'write', 'implement', 'generate', 'interactive', 'dynamic', 'animation'
        ]
        
        self.logger.info("✅ Omnix Maxima Manager initialized with DeepSeek R1 for executable code generation")
    
    def _call_deepseek_r1(self, prompt: str, max_tokens: int = 4000) -> str:
        """Call DeepSeek R1 via OpenRouter for deep reasoning"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_api_key}",
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
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                self.logger.error(f"DeepSeek R1 API error: {response.status_code} - {response.text}")
                return f"Error calling DeepSeek R1: {response.status_code}"
                
        except Exception as e:
            self.logger.error(f"DeepSeek R1 call failed: {e}")
            return f"Error calling DeepSeek R1: {str(e)}"
    
    
    def _is_coding_request(self, user_message: str) -> bool:
        """Detect if the user request is related to coding/programming"""
        message_lower = user_message.lower()
        
        # Check for coding keywords
        keyword_match = any(keyword in message_lower for keyword in self.coding_keywords)
        
        # Check for code patterns (function definitions, imports, etc.)
        code_patterns = [
            'def ', 'function ', 'class ', 'import ', 'from ', '#!/',
            'console.log', 'print(', 'return ', 'if (', 'for (', 'while (',
            '```', 'const ', 'var ', 'let ', 'public ', 'private ', 'static '
        ]
        pattern_match = any(pattern in message_lower for pattern in code_patterns)
        
        return keyword_match or pattern_match
    
    def _is_web_coding_request(self, user_message: str) -> bool:
        """Detect if user wants web code (HTML/CSS/JS) that can run in browser"""
        message_lower = user_message.lower()
        
        # Specific web coding keywords - more precise
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
        
        # Implementation keywords - user wants actual code
        implementation_keywords = [
            'create', 'build', 'make', 'write', 'implement', 'code',
            'develop', 'program', 'script', 'generate', 'show me the code',
            'give me code', 'write code', 'build me', 'create a', 'make a'
        ]
        
        web_match = any(keyword in message_lower for keyword in web_keywords)
        non_web_match = any(keyword in message_lower for keyword in non_web_keywords)
        implementation_match = any(keyword in message_lower for keyword in implementation_keywords)
        
        # Must have web keywords and implementation keywords, but no non-web keywords
        return web_match and implementation_match and not non_web_match
    
    def process_maxima_request(self, user_message: str, search_context: str = "", sources: List = None) -> Dict[str, Any]:
        """
        Process a request using DeepSeek R1 for sequential thinking and executable code generation
        
        For Web Coding Tasks:
        1. DeepSeek R1 uses sequential thinking to understand the request
        2. Generates complete, executable HTML/CSS/JavaScript code
        3. Code runs directly in the browser with interactive features
        
        For General Tasks:
        1. DeepSeek R1 performs deep reasoning and sequential thinking
        2. Provides comprehensive analysis and insights
        """
        if sources is None:
            sources = []
            
        is_web_coding = self._is_web_coding_request(user_message)
        is_general_coding = self._is_coding_request(user_message) and not is_web_coding
        
        if is_web_coding:
            request_type = "web_coding"
        elif is_general_coding:
            request_type = "general_coding"
        else:
            request_type = "general"
        
        self.logger.info(f"🎯 Processing Maxima {request_type} request: {user_message[:100]}...")
        start_time = time.time()
        
        try:
            if is_web_coding:
                return self._process_web_coding_request(user_message, search_context, sources, start_time)
            elif is_general_coding:
                return self._process_general_coding_request(user_message, search_context, sources, start_time)
            else:
                return self._process_general_request(user_message, search_context, sources, start_time)
                
        except Exception as e:
            self.logger.error(f"Maxima processing failed: {e}")
            return {
                'error': f'Omnix Maxima processing error: {str(e)}',
                'fallback_response': 'I apologize, but there was an error with the advanced processing. Please try again.'
            }
    
    def _process_web_coding_request(self, user_message: str, search_context: str, sources: List, start_time: float) -> Dict[str, Any]:
        """Process web coding requests with DeepSeek R1 for executable HTML/CSS/JS code"""
        
        deepseek_web_coding_prompt = f"""
You are DeepSeek R1, an advanced reasoning model specializing in web development. The user wants EXECUTABLE HTML/CSS/JavaScript code that runs directly in the browser.

User Web Coding Request: {user_message}
{search_context}

IMPORTANT: Use sequential thinking to understand the request and generate COMPLETE, WORKING, EXECUTABLE code.

## Sequential Thinking Process:
1. **Understanding**: What exactly does the user want to create?
2. **Planning**: What HTML structure, CSS styling, and JavaScript functionality is needed?
3. **Implementation**: Write the complete code that works immediately when opened in a browser
4. **Testing**: Ensure the code is syntactically correct and functional

## Code Generation Requirements:
- Generate a COMPLETE HTML file with embedded CSS and JavaScript
- The code must be immediately executable in any modern browser
- Include all necessary HTML structure, CSS styling, and JavaScript functionality
- Make it interactive, responsive, and visually appealing
- Add proper comments explaining the code
- Use modern web standards (HTML5, CSS3, ES6+)

## Response Format:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your App Title</title>
    <style>
        /* Your CSS here */
    </style>
</head>
<body>
    <!-- Your HTML here -->
    
    <script>
        // Your JavaScript here
    </script>
</body>
</html>
```

## Key Features to Include:
- Modern, clean design
- Interactive elements
- Responsive layout
- Smooth animations/transitions
- Error handling in JavaScript
- Accessibility features

Generate the COMPLETE, WORKING code that the user can copy-paste and run immediately!
"""
        
        self.logger.info("🧠 DeepSeek R1: Sequential thinking for web code generation...")
        code_response = self._call_deepseek_r1(deepseek_web_coding_prompt, max_tokens=8000)
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Maxima web coding completed in {processing_time:.2f}s")
        
        response_data = {
            'response': code_response,
            'processing_time': processing_time,
            'mode': 'omnix_maxima_web_coding',
            'request_type': 'web_coding',
            'models_used': ['deepseek-r1-0528'],
            'workflow': 'deepseek_sequential_thinking_code_generation',
            'is_executable': True,
            'code_type': 'html_css_js'
        }
        
        if sources:
            response_data['sources'] = sources
            
        return response_data
    
    def _process_general_coding_request(self, user_message: str, search_context: str, sources: List, start_time: float) -> Dict[str, Any]:
        """Process general coding requests (non-web) with DeepSeek R1"""
        
        deepseek_general_coding_prompt = f"""
You are DeepSeek R1, an advanced reasoning model specializing in software engineering. The user has a coding-related request that is not specifically for web development.

User Coding Request: {user_message}
{search_context}

## Sequential Thinking Process:
1. **Understanding**: What exactly is the user asking about?
2. **Analysis**: What are the key technical concepts, challenges, or solutions involved?
3. **Deep Reasoning**: Provide comprehensive analysis and insights
4. **Practical Guidance**: Offer actionable advice and examples

## Response Requirements:
- Provide thorough technical analysis
- Include code examples when relevant (but note they won't be executable in the browser)
- Explain concepts clearly with step-by-step reasoning
- Offer best practices and recommendations
- Consider edge cases and potential issues

Focus on providing deep technical insights and practical guidance.
"""
        
        self.logger.info("🧠 DeepSeek R1: Sequential thinking for general coding...")
        coding_response = self._call_deepseek_r1(deepseek_general_coding_prompt, max_tokens=6000)
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Maxima general coding completed in {processing_time:.2f}s")
        
        response_data = {
            'response': coding_response,
            'processing_time': processing_time,
            'mode': 'omnix_maxima_general_coding',
            'request_type': 'general_coding',
            'models_used': ['deepseek-r1-0528'],
            'workflow': 'deepseek_sequential_thinking_analysis',
            'is_executable': False
        }
        
        if sources:
            response_data['sources'] = sources
            
        return response_data
    
    def _process_general_request(self, user_message: str, search_context: str, sources: List, start_time: float) -> Dict[str, Any]:
        """Process general (non-coding) requests with DeepSeek R1 sequential thinking"""
        
        deepseek_prompt = f"""
You are DeepSeek R1, an advanced reasoning model with powerful sequential thinking capabilities. Analyze the following user request with deep reasoning and provide a comprehensive response.

User Request: {user_message}
{search_context}

## Sequential Thinking Process:
1. **Understanding**: What exactly is the user asking about?
2. **Analysis**: Break down the request and identify key components, implications, and nuances
3. **Reasoning**: Show your step-by-step thinking process
4. **Insights**: Identify the most important insights and connections
5. **Synthesis**: Provide a comprehensive, well-structured response

## Response Requirements:
- Use deep reasoning and sequential thinking
- Provide thorough analysis and insights
- Be comprehensive yet clear and engaging
- Include practical advice when applicable
- Show your reasoning process transparently
- Maintain a helpful and intelligent tone

Provide a complete, thoughtful response that demonstrates advanced reasoning capabilities.
"""

        self.logger.info("🧠 DeepSeek R1: Sequential thinking for general request...")
        final_response = self._call_deepseek_r1(deepseek_prompt, max_tokens=6000)
        
        processing_time = time.time() - start_time
        self.logger.info(f"✅ Maxima general processing completed in {processing_time:.2f}s")
        
        response_data = {
            'response': final_response,
            'processing_time': processing_time,
            'mode': 'omnix_maxima_general',
            'request_type': 'general',
            'models_used': ['deepseek-r1-0528'],
            'workflow': 'deepseek_sequential_thinking'
        }
        
        if sources:
            response_data['sources'] = sources
            
        return response_data
    
    def is_available(self) -> bool:
        """Check if OpenRouter API is available"""
        return bool(self.openrouter_api_key)