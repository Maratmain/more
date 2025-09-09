#!/usr/bin/env python3
"""
Test script for AI-HR Metrics Service

Demonstrates metrics recording, cost analysis, and SLA monitoring.
"""

import requests
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Configuration
METRICS_URL = "http://localhost:8010"

def test_metrics_service():
    """Test the metrics service endpoints"""
    print("🧪 Testing AI-HR Metrics Service")
    print("=" * 50)
    
    # Test health check
    print("Testing health check...")
    try:
        response = requests.get(f"{METRICS_URL}/health", timeout=5)
        response.raise_for_status()
        health_data = response.json()
        print(f"✅ Health check passed: {health_data['status']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Test SLA targets
    print("\nTesting SLA targets...")
    try:
        response = requests.get(f"{METRICS_URL}/sla-targets", timeout=5)
        response.raise_for_status()
        sla_data = response.json()
        print("✅ SLA targets retrieved:")
        for metric, target in sla_data['targets'].items():
            print(f"  {metric}: {target}")
    except Exception as e:
        print(f"❌ SLA targets failed: {e}")
    
    # Test cost config
    print("\nTesting cost configuration...")
    try:
        response = requests.get(f"{METRICS_URL}/cost-config", timeout=5)
        response.raise_for_status()
        cost_data = response.json()
        print("✅ Cost configuration retrieved")
        print(f"  LLM providers: {list(cost_data['config']['llm'].keys())}")
    except Exception as e:
        print(f"❌ Cost config failed: {e}")
    
    return True

def record_sample_metrics():
    """Record sample metrics for testing"""
    print("\n📊 Recording sample metrics...")
    
    session_id = f"test_session_{int(time.time())}"
    turn_id = f"turn_{int(time.time())}"
    
    # Record latency metrics
    latency_metrics = [
        {"service": "asr", "latency_ms": 1500, "success": True},
        {"service": "dm", "latency_ms": 800, "success": True},
        {"service": "tts", "latency_ms": 1200, "success": True},
        {"service": "asr", "latency_ms": 2500, "success": False, "error_message": "Timeout"}
    ]
    
    for metric in latency_metrics:
        try:
            payload = {
                "service": metric["service"],
                "latency_ms": metric["latency_ms"],
                "session_id": session_id,
                "turn_id": turn_id,
                "success": metric["success"],
                "error_message": metric.get("error_message")
            }
            
            response = requests.post(f"{METRICS_URL}/latency", json=payload, timeout=5)
            response.raise_for_status()
            print(f"✅ Recorded {metric['service']} latency: {metric['latency_ms']}ms")
        except Exception as e:
            print(f"❌ Failed to record {metric['service']} latency: {e}")
    
    # Record cost metrics
    cost_metrics = [
        {"service": "llm", "cost_usd": 0.05, "units": 1000, "unit_type": "tokens", "details": {"model": "claude-3.5-sonnet"}},
        {"service": "asr", "cost_usd": 0.02, "units": 60, "unit_type": "seconds", "details": {"model": "whisper"}},
        {"service": "tts", "cost_usd": 0.01, "units": 500, "unit_type": "characters", "details": {"service": "piper"}}
    ]
    
    for metric in cost_metrics:
        try:
            payload = {
                "service": metric["service"],
                "cost_usd": metric["cost_usd"],
                "session_id": session_id,
                "turn_id": turn_id,
                "units": metric["units"],
                "unit_type": metric["unit_type"],
                "details": metric["details"]
            }
            
            response = requests.post(f"{METRICS_URL}/cost", json=payload, timeout=5)
            response.raise_for_status()
            print(f"✅ Recorded {metric['service']} cost: ${metric['cost_usd']:.3f}")
        except Exception as e:
            print(f"❌ Failed to record {metric['service']} cost: {e}")
    
    # Record complete turn
    try:
        payload = {
            "session_id": session_id,
            "turn_id": turn_id,
            "asr_latency_ms": 1500,
            "dm_latency_ms": 800,
            "tts_latency_ms": 1200,
            "total_turn_s": 4.5,
            "backchannel_s": 1.8,
            "total_cost_usd": 0.08,
            "services_used": ["asr", "dm", "tts"]
        }
        
        response = requests.post(f"{METRICS_URL}/turn", json=payload, timeout=5)
        response.raise_for_status()
        print(f"✅ Recorded complete turn: {payload['total_turn_s']}s, ${payload['total_cost_usd']:.3f}")
    except Exception as e:
        print(f"❌ Failed to record turn: {e}")
    
    return session_id

def test_cost_analysis(session_id: str):
    """Test cost analysis functionality"""
    print(f"\n💰 Testing cost analysis for session: {session_id}")
    
    try:
        payload = {
            "session_id": session_id,
            "include_breakdown": True
        }
        
        response = requests.post(f"{METRICS_URL}/cost-analysis", json=payload, timeout=10)
        response.raise_for_status()
        analysis = response.json()
        
        print("✅ Cost analysis completed:")
        print(f"  Total cost: ${analysis['total_cost_usd']:.3f}")
        print(f"  Total turns: {analysis['total_turns']}")
        print(f"  Avg cost per turn: ${analysis['avg_cost_per_turn']:.4f}")
        
        print("\n  Cost breakdown:")
        for service, cost in analysis['cost_breakdown'].items():
            print(f"    {service}: ${cost:.3f}")
        
        print("\n  SLA compliance:")
        for metric, compliance in analysis['sla_compliance'].items():
            status = "✅" if compliance >= 95 else "⚠️" if compliance >= 90 else "❌"
            print(f"    {metric}: {compliance:.1f}% {status}")
        
        print("\n  HR comparison:")
        hr_data = analysis['hr_salary_comparison']
        print(f"    HR cost per turn: ${hr_data['hr_cost_per_turn_usd']:.2f}")
        print(f"    AI cost per turn: ${hr_data['ai_cost_per_turn_usd']:.4f}")
        print(f"    Savings per turn: ${hr_data['cost_savings_per_turn_usd']:.2f}")
        print(f"    Savings percentage: {hr_data['cost_savings_percentage']:.1f}%")
        
        print("\n  Recommendations:")
        for i, rec in enumerate(analysis['recommendations'], 1):
            print(f"    {i}. {rec}")
        
    except Exception as e:
        print(f"❌ Cost analysis failed: {e}")

def test_metrics_summary():
    """Test metrics summary"""
    print("\n📈 Testing metrics summary...")
    
    try:
        response = requests.get(f"{METRICS_URL}/metrics/summary", timeout=5)
        response.raise_for_status()
        summary = response.json()
        
        print("✅ Metrics summary retrieved:")
        print(f"  Period: {summary['period']}")
        print(f"  Turns: {summary['turns']}")
        print(f"  Latency measurements: {summary['latency_measurements']}")
        print(f"  Cost measurements: {summary['cost_measurements']}")
        print(f"  Total cost: ${summary['total_cost_usd']:.3f}")
        
        print("\n  SLA compliance:")
        for metric, compliance in summary['sla_compliance'].items():
            status = "✅" if compliance >= 95 else "⚠️" if compliance >= 90 else "❌"
            print(f"    {metric}: {compliance:.1f}% {status}")
        
    except Exception as e:
        print(f"❌ Metrics summary failed: {e}")

def test_client_library():
    """Test the metrics client library"""
    print("\n🔧 Testing metrics client library...")
    
    try:
        # Import the client library
        import sys
        import os
        sys.path.append(os.path.dirname(__file__))
        
        from client import record_latency, record_cost, time_operation, get_metrics_client
        
        # Test basic recording
        session_id = f"client_test_{int(time.time())}"
        turn_id = f"turn_{int(time.time())}"
        
        # Record latency
        success = record_latency("test_service", 1000, session_id, turn_id)
        print(f"✅ Client latency recording: {'success' if success else 'failed'}")
        
        # Record cost
        success = record_cost("test_service", 0.01, session_id, turn_id)
        print(f"✅ Client cost recording: {'success' if success else 'failed'}")
        
        # Test context manager
        with time_operation("test_service", session_id, turn_id):
            time.sleep(0.1)  # Simulate work
        print("✅ Client context manager: success")
        
        # Test client instance
        client = get_metrics_client()
        print(f"✅ Client instance: {type(client).__name__}")
        
    except Exception as e:
        print(f"❌ Client library test failed: {e}")

def main():
    """Main test function"""
    print("🚀 AI-HR Metrics Service Test Suite")
    print("=" * 60)
    
    # Test basic service functionality
    if not test_metrics_service():
        print("❌ Basic service tests failed. Make sure metrics service is running.")
        return
    
    # Record sample metrics
    session_id = record_sample_metrics()
    
    # Test cost analysis
    test_cost_analysis(session_id)
    
    # Test metrics summary
    test_metrics_summary()
    
    # Test client library
    test_client_library()
    
    print("\n" + "=" * 60)
    print("🏁 All tests completed!")
    print("\n💡 Usage Notes:")
    print("  - Start metrics service: python main.py")
    print("  - Run cost analysis: python ../../scripts/cost_check.py")
    print("  - Check metrics: curl http://localhost:8010/health")
    print("  - View data: Check data/ directory for CSV files")

if __name__ == "__main__":
    main()
