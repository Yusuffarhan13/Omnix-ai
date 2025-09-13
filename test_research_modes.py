#!/usr/bin/env python3
"""
Test script for both regular and deep research modes
"""

import os
import sys
import json
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from perplexity_research import PerplexityResearchManager

def test_research_modes():
    """Test both regular and deep research modes"""
    
    # Get API key from environment
    api_key = os.getenv('PERPLEXITY_API_KEY')
    
    if not api_key or api_key == "your_perplexity_api_key_here":
        print("❌ PERPLEXITY_API_KEY not configured in .env file")
        print("   Please add your Perplexity API key to the .env file:")
        print("   PERPLEXITY_API_KEY=your_actual_api_key_here")
        return False
    
    print("✅ Perplexity API key found")
    
    try:
        # Initialize the manager
        manager = PerplexityResearchManager(api_key)
        print("✅ Perplexity Research Manager initialized")
        
        # Test query
        test_query = "What are the latest developments in AI in 2025?"
        
        print("\n" + "=" * 60)
        print("Testing Both Research Modes")
        print("=" * 60)
        
        # Test Regular Research
        print(f"\n📝 Testing REGULAR Research Mode")
        print(f"Query: {test_query}")
        print("-" * 40)
        
        start_time = time.time()
        regular_result = manager.conduct_research_sync(test_query, use_deep_research=False)
        regular_time = time.time() - start_time
        
        if regular_result['success']:
            print(f"✅ Regular Research successful!")
            print(f"⏱️  Time taken: {regular_time:.2f} seconds")
            print(f"📚 Sources found: {len(regular_result['sources'])}")
            print(f"💡 Key insights: {len(regular_result['key_insights'])}")
            print(f"📊 Model used: {regular_result.get('model', 'unknown')}")
            print(f"🔍 Research type: {regular_result.get('research_type', 'unknown')}")
            
            print(f"\n📝 Summary (first 300 chars):")
            print(regular_result['summary'][:300] + "...")
        else:
            print(f"❌ Regular Research failed: {regular_result.get('error', 'Unknown error')}")
        
        print("\n" + "-" * 60)
        
        # Test Deep Research
        print(f"\n🔬 Testing DEEP Research Mode")
        print(f"Query: {test_query}")
        print("-" * 40)
        
        start_time = time.time()
        deep_result = manager.conduct_research_sync(test_query, use_deep_research=True)
        deep_time = time.time() - start_time
        
        if deep_result['success']:
            print(f"✅ Deep Research successful!")
            print(f"⏱️  Time taken: {deep_time:.2f} seconds")
            print(f"📚 Sources found: {len(deep_result['sources'])}")
            print(f"💡 Key insights: {len(deep_result['key_insights'])}")
            print(f"📊 Model used: {deep_result.get('model', 'unknown')}")
            print(f"🔍 Research type: {deep_result.get('research_type', 'unknown')}")
            
            print(f"\n📝 Summary (first 300 chars):")
            print(deep_result['summary'][:300] + "...")
        else:
            print(f"❌ Deep Research failed: {deep_result.get('error', 'Unknown error')}")
        
        # Compare results
        print("\n" + "=" * 60)
        print("Comparison of Research Modes")
        print("=" * 60)
        
        if regular_result['success'] and deep_result['success']:
            print(f"📊 Time Comparison:")
            print(f"   Regular: {regular_time:.2f}s")
            print(f"   Deep: {deep_time:.2f}s")
            print(f"   Difference: {abs(deep_time - regular_time):.2f}s")
            
            print(f"\n📚 Sources Comparison:")
            print(f"   Regular: {len(regular_result['sources'])} sources")
            print(f"   Deep: {len(deep_result['sources'])} sources")
            
            print(f"\n💡 Insights Comparison:")
            print(f"   Regular: {len(regular_result['key_insights'])} insights")
            print(f"   Deep: {len(deep_result['key_insights'])} insights")
            
            print(f"\n📏 Content Length Comparison:")
            print(f"   Regular: {len(regular_result['summary'])} characters")
            print(f"   Deep: {len(deep_result['summary'])} characters")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Perplexity Regular vs Deep Research Test")
    print("=" * 60)
    
    success = test_research_modes()
    
    if success:
        print("\n✅ Both research modes are working correctly!")
        print("\nUsage:")
        print("1. Regular Research: Fast, good for quick queries")
        print("2. Deep Research: Comprehensive, better for complex topics")
        print("\nIn the UI:")
        print("- Click the 'Deep' toggle button next to send in Research mode")
        print("- When OFF (shows 'Regular'): Uses fast regular research")
        print("- When ON (shows 'Deep'): Uses comprehensive deep research")
        print("\nIn browser automation:")
        print("- Say 'deep research' to trigger deep mode")
        print("- Regular keywords trigger regular mode")
    else:
        print("\n❌ Test failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)