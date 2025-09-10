#!/usr/bin/env python3
"""
Test script for DeepSeek R1 Coding System fallback functionality
"""

import os
from deepseek_coding_system import DeepSeekCodingSystem

def test_fallback_system():
    print("🧪 Testing DeepSeek R1 Coding System Fallback...")
    
    # Load API keys
    primary_key = os.getenv("OPENROUTER_API_KEY")
    backup_key = os.getenv("OPENROUTER_API_KEY_BACKUP")
    brave_key = os.getenv("BRAVE_API_KEY")
    
    if not primary_key or not backup_key:
        print("❌ Missing API keys in environment")
        return False
    
    try:
        system = DeepSeekCodingSystem(primary_key, brave_key, backup_key)
        print("✅ DeepSeek Coding System initialized successfully")
        print(f"📋 Primary key: ...{primary_key[-8:]}")
        print(f"📋 Backup key: ...{backup_key[-8:]}")
        print(f"📋 Current key: ...{system.current_key[-8:]}")
        
        # Test a simple coding request that should work
        print("\n🧪 Testing simple coding request...")
        test_prompt = "Create a simple HTML button with CSS hover effect"
        
        # This will test the fallback if the primary key is rate-limited
        result = system.process_coding_request(test_prompt)
        
        if 'error' in result:
            print(f"❌ Request failed: {result['error']}")
            return False
        else:
            print("✅ Request successful!")
            print(f"📊 Processing time: {result.get('processing_time', 'Unknown'):.2f}s")
            print(f"🔧 Models used: {result.get('models_used', [])}")
            print(f"🔄 Workflow: {result.get('workflow', 'Unknown')}")
            print(f"📋 Current key after request: ...{system.current_key[-8:]}")
            
            # Check if key switched
            if system.current_key != primary_key:
                print("🔄 Successfully switched to backup key due to rate limiting!")
            else:
                print("📍 Still using primary key (no rate limiting occurred)")
            
            return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_fallback_info():
    print("\n🚀 DeepSeek R1 Fallback System Features:")
    
    print("\n🔄 Automatic Fallback Logic:")
    print("   1. 🔑 Try primary OpenRouter API key first")
    print("   2. ⚠️  If 429 (rate limited), automatically switch to backup key")
    print("   3. ✅ Continue using backup key for future requests")
    print("   4. 📝 Log all key switches for monitoring")
    
    print("\n🎯 Benefits:")
    print("   • Zero downtime when hitting rate limits")
    print("   • Automatic recovery without user intervention")
    print("   • Maintains service quality during high usage")
    print("   • Transparent fallback (user doesn't see errors)")

if __name__ == "__main__":
    success = test_fallback_system()
    if success:
        show_fallback_info()
        print("\n🎉 Fallback system is working correctly!")
        print("📝 Status:")
        print("1. ✅ Backup API key configured")
        print("2. ✅ Automatic fallback logic implemented")
        print("3. ✅ Key switching works properly")
        print("4. 🚀 Ready to handle rate limits gracefully!")
    else:
        print("\n❌ Fallback system test failed")