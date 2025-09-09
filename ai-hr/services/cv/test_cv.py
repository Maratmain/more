#!/usr/bin/env python3
"""
Test script for CV Processing Service
"""

import requests
import json
import os
from pathlib import Path

API_BASE = "http://localhost:8007"

def create_sample_cv():
    """Create a sample CV file for testing"""
    sample_cv_content = """
    АЛЕКСЕЙ ПЕТРОВ
    Senior Python Developer
    
    КОНТАКТНАЯ ИНФОРМАЦИЯ:
    Email: alexey.petrov@example.com
    Телефон: +7 (999) 123-45-67
    Местоположение: Москва, Россия
    
    ПРОФЕССИОНАЛЬНЫЙ ОПЫТ:
    
    Senior Python Developer | TechCorp | 2021 - настоящее время
    • Разработка высоконагруженных веб-приложений на Django и FastAPI
    • Оптимизация производительности баз данных PostgreSQL
    • Внедрение микросервисной архитектуры
    • Наставничество junior разработчиков
    
    Python Developer | StartupXYZ | 2019 - 2021
    • Создание REST API для мобильных приложений
    • Интеграция с внешними сервисами через API
    • Разработка автоматизированных тестов
    
    ТЕХНИЧЕСКИЕ НАВЫКИ:
    • Python, Django, FastAPI, Flask
    • PostgreSQL, Redis, MongoDB
    • Docker, Kubernetes, AWS
    • Git, CI/CD, pytest
    • React, JavaScript (базовые знания)
    
    ОБРАЗОВАНИЕ:
    Магистр информатики | МГУ | 2017-2019
    Бакалавр программирования | МГУ | 2013-2017
    
    ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:
    • Опыт работы с машинным обучением (scikit-learn, pandas)
    • Знание английского языка (Upper-Intermediate)
    • Участие в open-source проектах
    """
    
    # Create sample CV file
    sample_file = Path("sample_cv.txt")
    sample_file.write_text(sample_cv_content, encoding='utf-8')
    return sample_file

def test_health():
    """Test health check endpoint"""
    print("=== Testing Health Check ===")
    try:
        response = requests.get(f"{API_BASE}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Health check passed: {data['status']}")
            print(f"  Service: {data['service']}")
            print(f"  Embedder model: {data['embedder_model']}")
            print(f"  Qdrant status: {data['qdrant_status']}")
            print(f"  Collection: {data['collection']}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False

def test_cv_ingest():
    """Test CV ingestion"""
    print("\n=== Testing CV Ingestion ===")
    
    # Create sample CV
    sample_file = create_sample_cv()
    
    try:
        with open(sample_file, 'rb') as f:
            files = {'file': ('sample_cv.txt', f, 'text/plain')}
            response = requests.post(f"{API_BASE}/ingest", files=files)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ CV ingested successfully")
            print(f"  CV ID: {data['cv_id']}")
            print(f"  Filename: {data['filename']}")
            print(f"  Chunks created: {data['chunks_created']}")
            print(f"  Total text length: {data['total_text_length']}")
            print(f"  Processing time: {data['processing_time']:.2f}s")
            return data['cv_id']
        else:
            print(f"✗ CV ingestion failed: {response.status_code}")
            print(f"  Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"✗ CV ingestion error: {e}")
        return None
    finally:
        # Clean up sample file
        if sample_file.exists():
            sample_file.unlink()

def test_cv_search(cv_id: str):
    """Test CV search functionality"""
    print("\n=== Testing CV Search ===")
    
    search_queries = [
        "Python разработка Django",
        "база данных PostgreSQL",
        "микросервисы архитектура",
        "машинное обучение",
        "Docker Kubernetes"
    ]
    
    for query in search_queries:
        try:
            search_data = {
                "query": query,
                "limit": 3,
                "score_threshold": 0.5
            }
            
            response = requests.post(f"{API_BASE}/search", json=search_data)
            
            if response.status_code == 200:
                results = response.json()
                print(f"✓ Search for '{query}': {len(results)} results")
                for i, result in enumerate(results[:2]):  # Show top 2
                    print(f"  {i+1}. Score: {result['score']:.3f}")
                    print(f"     Text: {result['chunk_text'][:100]}...")
            else:
                print(f"✗ Search failed for '{query}': {response.status_code}")
                
        except Exception as e:
            print(f"✗ Search error for '{query}': {e}")

def test_cv_list():
    """Test CV listing"""
    print("\n=== Testing CV List ===")
    
    try:
        response = requests.get(f"{API_BASE}/cvs")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ CV list retrieved: {data['total']} CVs")
            for cv in data['cvs']:
                print(f"  - {cv['filename']}: {cv['chunks_count']} chunks")
        else:
            print(f"✗ CV list failed: {response.status_code}")
    except Exception as e:
        print(f"✗ CV list error: {e}")

def test_cv_stats():
    """Test statistics endpoint"""
    print("\n=== Testing Statistics ===")
    
    try:
        response = requests.get(f"{API_BASE}/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Statistics retrieved")
            print(f"  Collection: {data['collection_name']}")
            print(f"  Total points: {data['total_points']}")
            print(f"  Vector size: {data['vector_size']}")
            print(f"  Distance metric: {data['distance_metric']}")
            print(f"  Embedder model: {data['embedder_model']}")
        else:
            print(f"✗ Statistics failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Statistics error: {e}")

def test_cv_delete(cv_id: str):
    """Test CV deletion"""
    print("\n=== Testing CV Deletion ===")
    
    if not cv_id:
        print("⚠ No CV ID provided, skipping deletion test")
        return
    
    try:
        response = requests.delete(f"{API_BASE}/cvs/{cv_id}")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ CV deleted successfully")
            print(f"  CV ID: {data['cv_id']}")
            print(f"  Deleted points: {data['deleted_points']}")
        else:
            print(f"✗ CV deletion failed: {response.status_code}")
    except Exception as e:
        print(f"✗ CV deletion error: {e}")

def main():
    """Run all tests"""
    print("CV Processing Service Test Suite")
    print("=" * 50)
    
    # Check if service is running
    if not test_health():
        print("\n❌ CV service is not running. Please start it first:")
        print("  docker compose up -d cv")
        print("  # or locally: uvicorn main:app --port 8007")
        print("\n⚠ Make sure to configure .env file with Qdrant credentials!")
        return
    
    # Run tests
    cv_id = test_cv_ingest()
    if cv_id:
        test_cv_search(cv_id)
        test_cv_list()
        test_cv_stats()
        test_cv_delete(cv_id)
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\nAPI Documentation:")
    print(f"  Swagger UI: {API_BASE}/docs")
    print(f"  ReDoc: {API_BASE}/redoc")

if __name__ == "__main__":
    main()
