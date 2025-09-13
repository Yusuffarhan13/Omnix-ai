#!/usr/bin/env python3
"""
Test script for browser automation with research integration
"""

import requests
import json
import time

def test_browser_with_research():
    """Test browser automation with research"""
    
    base_url = "http://localhost:5000"
    
    # Test queries that should trigger research
    test_queries = [
        "Research and find the latest AI news on TechCrunch",
        "Look up information about quantum computing and visit IBM's quantum page",
        "Search for Python tutorials and open the best one",
        "Find out what is machine learning and visit a tutorial site"
    ]
    
    print("=" * 50)
    print("Browser Automation with Research Integration Test")
    print("=" * 50)
    
    for query in test_queries[:1]:  # Test just the first query
        print(f"\n🔍 Testing: {query}")
        print("-" * 50)
        
        # Send browser task request
        response = requests.post(
            f"{base_url}/browser",
            json={"task": query},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            print(f"✅ Task created with ID: {task_id}")
            
            # Poll for task status
            for i in range(30):  # Check for 30 seconds
                time.sleep(1)
                status_response = requests.get(f"{base_url}/task_status/{task_id}")
                if status_response.status_code == 200:
                    status = status_response.json()
                    print(f"   Status: {status.get('status', 'unknown')}")
                    if status.get('status') == 'completed':
                        print(f"   Result: {status.get('result', 'No result')[:200]}...")
                        break
                    elif status.get('status') == 'failed':
                        print(f"   Error: {status.get('error', 'Unknown error')}")
                        break
        else:
            print(f"❌ Failed to create task: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
    
    print("\n" + "=" * 50)
    print("Test completed!")
    print("\nNote: Check the Flask server logs to see:")
    print("1. '🔍 Using researcher mode to research and find answers...'")
    print("2. '✅ Research completed. Analyzed X sources. Now executing browser task...'")
    print("3. The enhanced task description with research results")

if __name__ == "__main__":
    test_browser_with_research()