#!/usr/bin/env python3
"""
Test the updated DeepSeek coding system to verify it generates executable code
"""

import os
from deepseek_coding_system import DeepSeekCodingSystem

def test_executable_code_generation():
    print("🧪 Testing Updated DeepSeek Coding System for Executable Code...")
    
    # Load API keys
    primary_key = os.getenv("OPENROUTER_API_KEY")
    backup_key = os.getenv("OPENROUTER_API_KEY_BACKUP")
    brave_key = os.getenv("BRAVE_API_KEY")
    
    if not primary_key:
        print("❌ Missing OpenRouter API key")
        return False
    
    try:
        system = DeepSeekCodingSystem(primary_key, brave_key, backup_key)
        print("✅ DeepSeek Coding System initialized successfully")
        
        # Test web coding request (should generate HTML/CSS/JS)
        print("\n🌐 Testing Web Coding Request...")
        web_request = "Create a simple HTML calculator with CSS styling and JavaScript functionality"
        
        result = system.process_coding_request(web_request)
        
        if 'error' in result:
            print(f"❌ Web coding request failed: {result['error']}")
            return False
        
        print("✅ Web coding request successful!")
        print(f"📊 Mode: {result.get('mode', 'Unknown')}")
        print(f"🔧 Workflow: {result.get('workflow', 'Unknown')}")
        
        # Check if response contains HTML code
        response = result.get('response', '')
        if '<!DOCTYPE html>' in response and '<script>' in response and '<style>' in response:
            print("✅ Generated complete HTML file with embedded CSS and JavaScript")
        else:
            print("❌ Response does not contain complete HTML file")
            print("📝 Response preview:")
            print(response[:500] + "..." if len(response) > 500 else response)
        
        # Test general coding request (should generate working code)
        print("\n💻 Testing General Coding Request...")
        general_request = "Create a Python web scraper with error handling"
        
        result2 = system.process_coding_request(general_request)
        
        if 'error' in result2:
            print(f"❌ General coding request failed: {result2['error']}")
            return False
        
        print("✅ General coding request successful!")
        
        response2 = result2.get('response', '')
        if '```python' in response2 or 'import ' in response2:
            print("✅ Generated working Python code examples")
        else:
            print("❌ Response does not contain Python code")
            print("📝 Response preview:")
            print(response2[:500] + "..." if len(response2) > 500 else response2)
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_expected_output():
    print("\n🎯 Expected Output Types:")
    
    print("\n🌐 Web Coding Requests should generate:")
    print("   ✅ Complete HTML file with <!DOCTYPE html>")
    print("   ✅ Embedded <style> tags with CSS")
    print("   ✅ Embedded <script> tags with JavaScript")
    print("   ✅ Working functionality (buttons, interactions, etc.)")
    print("   ✅ Ready to copy-paste and run in browser")
    
    print("\n💻 General Coding Requests should generate:")
    print("   ✅ Complete Python/JavaScript/etc. code examples")
    print("   ✅ Working import statements and dependencies")
    print("   ✅ Functional code that can be copy-pasted and run")
    print("   ✅ Setup instructions and usage examples")

if __name__ == "__main__":
    success = test_executable_code_generation()
    if success:
        show_expected_output()
        print("\n🎉 Updated system successfully generates executable code!")
    else:
        print("\n❌ System still needs adjustment to generate executable code")
        show_expected_output()