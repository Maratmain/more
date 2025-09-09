#!/usr/bin/env python3
"""
Test script for AI-HR Main API
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8006"

def test_health():
    """Test health check endpoint"""
    print("=== Testing Health Check ===")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data['status']}")
            print(f"  Service: {data['service']}")
            print(f"  Scenarios dir: {data['scenarios_dir']}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_scenario_management():
    """Test scenario loading and listing"""
    print("\n=== Testing Scenario Management ===")
    
    # Test scenario loading
    scenario_data = {
        "id": "test_python_backend",
        "schema_version": "0.1",
        "policy": {"drill_threshold": 0.7},
        "start_id": "python_l1_intro",
        "nodes": [
            {
                "id": "python_l1_intro",
                "category": "python_backend",
                "order": 1,
                "question": "Расскажите о вашем опыте работы с Python",
                "weight": 1.0,
                "success_criteria": ["python", "опыт", "проекты"],
                "next_if_fail": "python_l2_basics",
                "next_if_pass": "python_l3_advanced"
            },
            {
                "id": "python_l2_basics",
                "category": "python_backend", 
                "order": 2,
                "question": "Объясните основные концепции Python",
                "weight": 0.8,
                "success_criteria": ["основы", "концепции"],
                "next_if_fail": "python_l3_advanced",
                "next_if_pass": "python_l3_advanced"
            }
        ]
    }
    
    try:
        response = requests.post(f"{API_BASE}/scenario/load", json=scenario_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Scenario loaded: {data['id']}")
            print(f"  Nodes: {data['nodes_count']}")
        else:
            print(f"✗ Scenario loading failed: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Scenario loading error: {e}")
    
    # Test scenario listing
    try:
        response = requests.get(f"{API_BASE}/scenario/list")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Scenarios listed: {data['total']} found")
            for scenario in data['scenarios']:
                print(f"  - {scenario['id']}: {scenario['nodes_count']} nodes")
        else:
            print(f"✗ Scenario listing failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Scenario listing error: {e}")
    
    # Test scenario retrieval
    try:
        response = requests.get(f"{API_BASE}/scenario/test_python_backend")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Scenario retrieved: {data['id']}")
        else:
            print(f"✗ Scenario retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Scenario retrieval error: {e}")

def test_scoring():
    """Test score aggregation"""
    print("\n=== Testing Score Aggregation ===")
    
    scoring_data = {
        "answers": [
            {"question_id": "q1", "block": "Python", "score": 0.9, "weight": 0.5},
            {"question_id": "q2", "block": "Python", "score": 0.7, "weight": 0.5},
            {"question_id": "q3", "block": "Django", "score": 0.8, "weight": 0.6},
            {"question_id": "q4", "block": "Django", "score": 0.6, "weight": 0.4},
            {"question_id": "q5", "block": "Database", "score": 0.5, "weight": 0.8}
        ],
        "block_weights": {
            "Python": 0.4,
            "Django": 0.35,
            "Database": 0.25
        }
    }
    
    try:
        response = requests.post(f"{API_BASE}/score/aggregate", json=scoring_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Score aggregation successful")
            print(f"  Overall: {data['overall']} ({data['overall_percentage']}%)")
            print(f"  Block scores: {data['block_scores']}")
            print(f"  Strengths: {data['analysis']['strengths']}")
            print(f"  Weaknesses: {data['analysis']['weaknesses']}")
        else:
            print(f"✗ Score aggregation failed: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ Score aggregation error: {e}")

def test_report_generation():
    """Test report generation"""
    print("\n=== Testing Report Generation ===")
    
    report_data = {
        "candidate": {
            "name": "Алексей Петров",
            "experience": "5 лет Python разработки",
            "location": "Москва"
        },
        "vacancy": {
            "title": "Senior Python Developer",
            "department": "Backend Development",
            "level": "Senior"
        },
        "blocks": [
            {"name": "Python", "score": 0.8, "weight": 0.4},
            {"name": "Django", "score": 0.7, "weight": 0.35},
            {"name": "Database", "score": 0.5, "weight": 0.25}
        ],
        "positives": ["Отличное знание Python", "Опыт с Django ORM"],
        "negatives": ["Слабое знание Docker", "Ограниченный CI/CD опыт"],
        "quotes": [
            {
                "text": "Работал с Django более 4 лет, создавал высоконагруженные приложения",
                "source": "Interview Transcript"
            }
        ],
        "rating_0_10": 7.5
    }
    
    # Test PDF generation
    try:
        response = requests.post(f"{API_BASE}/report/render", json=report_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✓ PDF report generated: {data['size_bytes']} bytes")
            else:
                print(f"⚠ PDF generation failed: {data.get('error')}")
                if "fallback" in data:
                    print(f"  Fallback: {data['fallback']}")
        else:
            print(f"✗ PDF report generation failed: {response.status_code}")
    except Exception as e:
        print(f"✗ PDF report generation error: {e}")
    
    # Test HTML fallback
    try:
        response = requests.post(f"{API_BASE}/report/html", json=report_data)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print(f"✓ HTML report generated: {data['size_bytes']} bytes")
            else:
                print(f"⚠ HTML generation failed: {data.get('error')}")
        else:
            print(f"✗ HTML report generation failed: {response.status_code}")
    except Exception as e:
        print(f"✗ HTML report generation error: {e}")

def test_stats():
    """Test statistics endpoint"""
    print("\n=== Testing Statistics ===")
    
    try:
        response = requests.get(f"{API_BASE}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Statistics retrieved")
            print(f"  Scenarios loaded: {data['scenarios_loaded']}")
            print(f"  API version: {data['api_version']}")
            print(f"  Report service URL: {data['report_service_url']}")
        else:
            print(f"✗ Statistics failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Statistics error: {e}")

def main():
    """Run all tests"""
    print("AI-HR Main API Test Suite")
    print("=" * 50)
    
    # Check if API is running
    if not test_health():
        print("\n❌ API is not running. Please start it first:")
        print("  docker compose up -d api")
        print("  # or locally: uvicorn services.api.main:app --port 8006")
        return
    
    # Run all tests
    test_scenario_management()
    test_scoring()
    test_report_generation()
    test_stats()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\nAPI Documentation:")
    print(f"  Swagger UI: {API_BASE}/docs")
    print(f"  ReDoc: {API_BASE}/redoc")

if __name__ == "__main__":
    main()
