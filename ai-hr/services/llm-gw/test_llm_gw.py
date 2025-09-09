#!/usr/bin/env python3
"""
Test script for LLM Gateway Service

This script demonstrates how to use the LLM Gateway service
with both OpenRouter and OpenAI-compatible providers.
"""

import requests
import json
import time
import os
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8008"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")

def test_health():
    """Test health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print(f"✅ Health check passed: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_models():
    """Test models endpoint"""
    print("\n🔍 Testing models endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/models")
        response.raise_for_status()
        print(f"✅ Models endpoint: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Models endpoint failed: {e}")
        return False

def test_generate_openrouter():
    """Test generation with OpenRouter"""
    if not OPENROUTER_API_KEY:
        print("\n⚠️  Skipping OpenRouter test - no API key provided")
        return False
    
    print("\n🔍 Testing OpenRouter generation...")
    
    payload = {
        "system": "You are a helpful AI assistant for HR interviews.",
        "prompt": "What are the key skills for a Python developer?",
        "model": "env_default",
        "stream": False,
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ OpenRouter generation successful:")
        print(f"   Model: {result.get('model')}")
        print(f"   Content: {result.get('content', '')[:100]}...")
        print(f"   Usage: {result.get('usage')}")
        return True
    except Exception as e:
        print(f"❌ OpenRouter generation failed: {e}")
        return False

def test_generate_openai_compatible():
    """Test generation with OpenAI-compatible provider"""
    print("\n🔍 Testing OpenAI-compatible generation...")
    
    payload = {
        "system": "You are a helpful AI assistant.",
        "prompt": "Hello, how are you?",
        "model": "env_default",
        "stream": False,
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        result = response.json()
        print(f"✅ OpenAI-compatible generation successful:")
        print(f"   Model: {result.get('model')}")
        print(f"   Content: {result.get('content', '')[:100]}...")
        return True
    except Exception as e:
        print(f"❌ OpenAI-compatible generation failed: {e}")
        return False

def test_streaming():
    """Test streaming generation"""
    print("\n🔍 Testing streaming generation...")
    
    payload = {
        "system": "You are a helpful AI assistant.",
        "prompt": "Count from 1 to 5, one number per line.",
        "model": "env_default",
        "stream": True,
        "max_tokens": 50,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/generate/stream",
            json=payload,
            stream=True,
            timeout=30
        )
        response.raise_for_status()
        
        print("✅ Streaming response:")
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data = line_str[6:]  # Remove 'data: ' prefix
                    if data.strip() == '[DONE]':
                        break
                    try:
                        chunk = json.loads(data)
                        if 'choices' in chunk and len(chunk['choices']) > 0:
                            delta = chunk['choices'][0].get('delta', {})
                            if 'content' in delta:
                                print(f"   {delta['content']}", end='', flush=True)
                    except json.JSONDecodeError:
                        continue
        print("\n✅ Streaming completed")
        return True
    except Exception as e:
        print(f"❌ Streaming generation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 LLM Gateway Service Test Suite")
    print("=" * 50)
    
    # Test basic endpoints
    health_ok = test_health()
    models_ok = test_models()
    
    if not health_ok:
        print("\n❌ Service is not healthy. Please check if the service is running.")
        return
    
    # Test generation based on provider
    provider = os.getenv("LLM_PROVIDER", "openrouter")
    print(f"\n🔧 Testing with provider: {provider}")
    
    if provider == "openrouter":
        test_generate_openrouter()
    elif provider == "openai_compatible":
        test_generate_openai_compatible()
    
    # Test streaming (works with both providers)
    test_streaming()
    
    print("\n" + "=" * 50)
    print("🏁 Test suite completed!")

if __name__ == "__main__":
    main()
