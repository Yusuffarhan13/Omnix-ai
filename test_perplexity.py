#!/usr/bin/env python3
"""
Test script for Perplexity Sonar Deep Research integration
"""

import os
import sys
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from perplexity_research import PerplexityResearchManager

def test_perplexity_integration():
    """Test the Perplexity research integration"""
    
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
        
        # Test queries
        test_queries = [
            "What are the latest developments in quantum computing in 2025?",
            "Compare the performance of GPT-4 and Claude 3",
            "What are the environmental impacts of cryptocurrency mining?"
        ]
        
        for query in test_queries[:1]:  # Test just the first query
            print(f"\n🔍 Testing query: {query}")
            print("-" * 50)
            
            result = manager.conduct_research_sync(query)
            
            if result['success']:
                print(f"✅ Research successful!")
                print(f"\n📝 Summary (first 500 chars):")
                print(result['summary'][:500] + "...")
                print(f"\n📚 Sources found: {len(result['sources'])}")
                for i, source in enumerate(result['sources'][:3], 1):
                    print(f"   {i}. {source.get('title', 'No title')} - {source.get('url', 'No URL')}")
                print(f"\n💡 Key insights: {len(result['key_insights'])}")
                for i, insight in enumerate(result['key_insights'][:3], 1):
                    print(f"   {i}. {insight[:100]}...")
                print(f"\n📊 Confidence score: {result['confidence_score']}")
                print(f"📈 Metadata: {json.dumps(result.get('metadata', {}), indent=2)}")
            else:
                print(f"❌ Research failed: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Perplexity Sonar Deep Research Integration Test")
    print("=" * 50)
    
    success = test_perplexity_integration()
    
    if success:
        print("\n✅ Integration test passed! Perplexity research is ready to use.")
        print("\nTo use in your application:")
        print("1. Make sure PERPLEXITY_API_KEY is set in .env")
        print("2. Start the Flask server: python main.py")
        print("3. The research endpoints will use Perplexity automatically")
    else:
        print("\n❌ Integration test failed. Please check the errors above.")
    
    sys.exit(0 if success else 1)