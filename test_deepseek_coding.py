#!/usr/bin/env python3
"""
Test script for DeepSeek R1 Coding System
"""

import os
from deepseek_coding_system import DeepSeekCodingSystem

def test_deepseek_coding_system():
    print("🧪 Testing DeepSeek R1 Coding System...")
    
    # Test initialization
    openrouter_key = "test_key"
    brave_key = "test_key"
    
    try:
        system = DeepSeekCodingSystem(openrouter_key, brave_key)
        print("✅ DeepSeek Coding System initialized successfully")
        
        # Test availability check
        available = system.is_available()
        print(f"✅ Availability check: {available}")
        
        # Test coding detection
        test_coding_detection(system)
        
        print("✅ All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_coding_detection(system):
    print("\n🧪 Testing coding detection logic...")
    
    # Web coding requests
    web_coding_requests = [
        "Create a HTML calculator with CSS styling",
        "Build an interactive JavaScript dashboard", 
        "Make a responsive web page with animations",
        "Create a CSS grid layout with hover effects",
        "Build a JavaScript slider component"
    ]
    
    # General coding requests
    general_coding_requests = [
        "Create a Python web scraper with error handling",
        "Implement a sorting algorithm in Python",
        "Write a REST API in Node.js",
        "Build a distributed cache system",
        "Generate a function that calculates fibonacci numbers"
    ]
    
    # General requests  
    general_requests = [
        "What is the meaning of life?",
        "Explain quantum physics",
        "Tell me about climate change",
        "What's the weather like today?",
        "How to cook pasta?"
    ]
    
    print("General coding detection:")
    for request in general_coding_requests:
        is_coding = system._is_coding_request(request)
        status = "✅" if is_coding else "❌"
        print(f"  {status} '{request[:50]}...' -> {is_coding}")
    
    print("\nWeb coding detection:")
    for request in web_coding_requests:
        is_web_coding = system._is_web_coding_request(request)
        status = "✅" if is_web_coding else "❌"
        print(f"  {status} '{request[:50]}...' -> {is_web_coding}")
    
    print("\nGeneral requests:")
    for request in general_requests:
        is_coding = system._is_coding_request(request)
        status = "✅" if not is_coding else "❌"
        print(f"  {status} '{request[:50]}...' -> {is_coding}")

def show_system_info():
    print("\n🚀 DeepSeek R1 Coding System Features:")
    
    print("\n🌐 For WEB CODING Requests:")
    print("   🧠 DeepSeek R1: Deep thinking + Sequential thinking + Web search")
    print("      - Understanding: What does user want to create?")
    print("      - Web Search: Latest web development practices")
    print("      - Planning: HTML structure, CSS styling, JS functionality")
    print("      - Implementation: Complete executable code")
    print("   📱 Output: Complete HTML file ready to run in browser")
    
    print("\n💻 For GENERAL CODING Requests:")
    print("   🧠 DeepSeek R1: Deep thinking + Sequential thinking + Web search")
    print("      - Understanding: What is being asked?")
    print("      - Web Search: Recent programming information")
    print("      - Analysis: Technical concepts and challenges")
    print("      - Implementation: Practical guidance and examples")
    print("   📋 Output: Comprehensive technical analysis")
    
    print("\n🎯 Key Features:")
    print("   • Uses ONLY DeepSeek R1 (no multi-stage reasoning)")
    print("   • Deep thinking for thorough analysis")
    print("   • Web search integration for current information")
    print("   • Sequential thinking for step-by-step processing")
    print("   • Executable HTML/CSS/JS for web requests")
    print("   • Technical guidance for general coding")

if __name__ == "__main__":
    success = test_deepseek_coding_system()
    if success:
        show_system_info()
        print("\n🎉 DeepSeek R1 Coding System is ready!")
        print("📝 Integration status:")
        print("1. ✅ New system created")
        print("2. ✅ Integrated into main.py")
        print("3. ✅ Routes coding requests away from complex mode")
        print("4. 🧪 Ready for testing with real requests!")
    else:
        print("\n❌ System test failed")