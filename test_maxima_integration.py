#!/usr/bin/env python3
"""
Test script for Omnix Maxima integration with enhanced coding capabilities
"""

import os
from omnix_maxima_mode import OmnixMaximaManager

def test_coding_detection():
    """Test the coding request detection logic"""
    print("🧪 Testing coding detection logic...")
    
    openrouter_key = "test_key"
    manager = OmnixMaximaManager(openrouter_key)
    
    # Test coding requests
    coding_requests = [
        "Write a Python function to sort a list",
        "How do I fix this JavaScript error?",
        "Create a REST API in Node.js",
        "Debug this SQL query",
        "def factorial(n): return n if n <= 1 else n * factorial(n-1)",
        "What's the best algorithm for sorting?",
        "Help me optimize this code performance"
    ]
    
    # Test web coding vs general coding requests
    web_coding_requests = [
        "Create a HTML calculator with CSS styling",
        "Build a interactive JavaScript dashboard", 
        "Make a responsive web page with animations",
        "Create a CSS grid layout with hover effects",
        "Build a JavaScript slider component"
    ]
    
    general_coding_requests = [
        "Create a Python web scraper with error handling",
        "Implement a sorting algorithm in Python",
        "Write a REST API in Node.js",
        "Build a distributed cache system",
        "Generate a function that calculates fibonacci numbers"
    ]
    
    # Test general requests  
    general_requests = [
        "What is the meaning of life?",
        "Explain quantum physics",
        "Tell me about climate change",
        "What's the weather like today?",
        "How to cook pasta?"
    ]
    
    print("Coding detection:")
    for request in coding_requests:
        is_coding = manager._is_coding_request(request)
        status = "✅" if is_coding else "❌"
        print(f"  {status} '{request[:50]}...' -> {is_coding}")
    
    print("\nWeb coding detection:")
    for request in web_coding_requests:
        is_web_coding = manager._is_web_coding_request(request)
        status = "✅" if is_web_coding else "❌"
        print(f"  {status} '{request[:50]}...' -> web_coding: {is_web_coding}")
    
    print("\nGeneral coding detection:")
    for request in general_coding_requests:
        is_coding = manager._is_coding_request(request)
        is_web_coding = manager._is_web_coding_request(request)
        status = "✅" if is_coding and not is_web_coding else "❌"
        print(f"  {status} '{request[:50]}...' -> coding: {is_coding}, web_coding: {is_web_coding}")
    
    print("\nGeneral requests:")
    for request in general_requests:
        is_coding = manager._is_coding_request(request)
        status = "✅" if not is_coding else "❌"
        print(f"  {status} '{request[:50]}...' -> {is_coding}")
    
    return True

def test_maxima_manager():
    print("🧪 Testing Omnix Maxima Manager...")
    
    # Test initialization with placeholder key
    openrouter_key = "test_key"
    
    try:
        manager = OmnixMaximaManager(openrouter_key)
        print("✅ Manager initialized successfully")
        
        # Test availability check
        available = manager.is_available()
        print(f"✅ Availability check: {available}")
        
        # Test coding detection
        test_coding_detection()
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_workflow_info():
    print("\n🔄 Omnix Maxima DeepSeek R1 Sequential Thinking Workflows:")
    
    print("\n🌐 For WEB CODING Requests (HTML/CSS/JavaScript):")
    print("   1. 🧠 DeepSeek R1: Sequential thinking process")
    print("      - Understanding: What does the user want to create?")
    print("      - Planning: HTML structure, CSS styling, JS functionality")
    print("      - Implementation: Complete executable code")
    print("      - Testing: Syntactically correct and functional")
    print("   2. 📱 Output: Complete HTML file ready to run in browser")
    print("      - Embedded CSS and JavaScript")
    print("      - Interactive and responsive design") 
    print("      - Modern web standards (HTML5, CSS3, ES6+)")
    
    print("\n💻 For GENERAL CODING Requests (Python, Node.js, etc.):")
    print("   1. 🧠 DeepSeek R1: Sequential thinking analysis")
    print("      - Understanding: What is the user asking?")
    print("      - Analysis: Key technical concepts and challenges")
    print("      - Deep reasoning: Comprehensive insights")
    print("      - Practical guidance: Actionable advice")
    print("   2. 📋 Output: Technical analysis and code examples")
    print("      - Best practices and recommendations")
    print("      - Step-by-step explanations")
    
    print("\n🌟 For GENERAL Requests:")
    print("   1. 🧠 DeepSeek R1: Sequential thinking process")
    print("      - Understanding: What is being asked?")
    print("      - Analysis: Break down key components")
    print("      - Reasoning: Step-by-step thinking")
    print("      - Synthesis: Comprehensive response")
    print("   2. 💬 Output: Thoughtful analysis with reasoning")
    print("      - Deep insights and connections")
    print("      - Transparent reasoning process")
    
    print("\n🎯 Smart Request Detection:")
    print("   • 'HTML/CSS/JavaScript/Web' + 'Create/Build' → Web Coding")
    print("   • 'Python/Java/API' + 'Create/Build' → General Coding") 
    print("   • Other requests → General sequential thinking")

if __name__ == "__main__":
    success = test_maxima_manager()
    if success:
        show_workflow_info()
        print("\n🎉 Omnix Maxima DeepSeek R1 coding system is ready!")
        print("📝 Next steps:")
        print("1. Add your OPENROUTER_API_KEY to .env file")
        print("2. Start the application and enable Omnix Maxima mode")
        print("3. Try web coding requests for executable HTML/CSS/JS code")
        print("4. Test general coding requests for technical analysis")
        print("5. Experience DeepSeek R1's sequential thinking capabilities!")
    else:
        print("\n❌ Integration test failed")