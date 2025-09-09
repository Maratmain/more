#!/usr/bin/env python3
"""
Test script for PDF Report Service
"""

import requests
import json
from datetime import datetime

def test_report_generation():
    """Test PDF report generation with sample data"""
    
    # Sample interview data
    report_data = {
        "candidate": {
            "name": "Алексей Петров",
            "email": "alexey.petrov@example.com",
            "experience": "5 лет Python разработки",
            "location": "Москва"
        },
        "vacancy": {
            "title": "Senior Python Developer",
            "department": "Backend Development",
            "level": "Senior",
            "location": "Москва",
            "salary_range": "200,000 - 300,000 руб"
        },
        "blocks": [
            {"name": "Python", "score": 0.9, "weight": 0.3},
            {"name": "Django", "score": 0.8, "weight": 0.25},
            {"name": "Database", "score": 0.7, "weight": 0.2},
            {"name": "API Design", "score": 0.6, "weight": 0.15},
            {"name": "Testing", "score": 0.5, "weight": 0.1}
        ],
        "positives": [
            "Отличное знание Python и современных практик",
            "Глубокий опыт работы с Django ORM",
            "Хорошие навыки проектирования API",
            "Опыт работы с PostgreSQL и Redis"
        ],
        "negatives": [
            "Ограниченный опыт с микросервисной архитектурой",
            "Слабое знание Docker и контейнеризации",
            "Недостаточный опыт с CI/CD пайплайнами"
        ],
        "quotes": [
            {
                "text": "Я работал с Django более 4 лет, создавал высоконагруженные приложения для e-commerce платформы",
                "source": "Interview Transcript"
            },
            {
                "text": "В моем последнем проекте я оптимизировал запросы к базе данных, что снизило время отклика на 40%",
                "source": "CV Summary"
            },
            {
                "text": "Я использую pytest для тестирования, но хотел бы изучить более продвинутые техники тестирования",
                "source": "Interview Transcript"
            }
        ],
        "rating_0_10": 7.5
    }
    
    print("=== Testing PDF Report Generation ===\n")
    
    # Test health endpoint
    try:
        response = requests.get("http://localhost:8005/health")
        if response.status_code == 200:
            print("✓ Health check passed")
        else:
            print(f"✗ Health check failed: {response.status_code}")
            return
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to report service. Make sure it's running on port 8005")
        return
    
    # Test PDF generation
    try:
        print("Generating PDF report...")
        response = requests.post(
            "http://localhost:8005/report",
            json=report_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            # Save PDF file
            filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ PDF report generated successfully: {filename}")
            print(f"  File size: {len(response.content)} bytes")
        else:
            print(f"✗ PDF generation failed: {response.status_code}")
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"✗ PDF generation error: {e}")
    
    # Test HTML fallback
    try:
        print("\nTesting HTML fallback...")
        response = requests.post(
            "http://localhost:8005/report/html",
            json=report_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ HTML report generated: {filename}")
        else:
            print(f"✗ HTML generation failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ HTML generation error: {e}")

def test_edge_cases():
    """Test edge cases and validation"""
    
    print("\n=== Testing Edge Cases ===\n")
    
    # Test with minimal data
    minimal_data = {
        "candidate": {"name": "Test Candidate"},
        "vacancy": {"title": "Test Position"},
        "blocks": [{"name": "Test", "score": 0.5, "weight": 1.0}],
        "positives": [],
        "negatives": [],
        "quotes": [],
        "rating_0_10": 5.0
    }
    
    try:
        response = requests.post(
            "http://localhost:8005/report/html",
            json=minimal_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✓ Minimal data test passed")
        else:
            print(f"✗ Minimal data test failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Minimal data test error: {e}")
    
    # Test with invalid data
    invalid_data = {
        "candidate": {"name": "Test"},
        "vacancy": {"title": "Test"},
        "blocks": [{"name": "Test", "score": 1.5, "weight": 1.0}],  # Invalid score > 1.0
        "rating_0_10": 5.0
    }
    
    try:
        response = requests.post(
            "http://localhost:8005/report/html",
            json=invalid_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 422:  # Validation error
            print("✓ Validation test passed (correctly rejected invalid data)")
        else:
            print(f"✗ Validation test failed: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Validation test error: {e}")

if __name__ == "__main__":
    test_report_generation()
    test_edge_cases()
    
    print("\n=== Test Complete ===")
    print("To run the report service:")
    print("  docker compose up -d report")
    print("  # or locally: uvicorn main:app --port 8005")
