#!/usr/bin/env python3
"""
Test script for updated Dialog Manager functionality

This script demonstrates the role-based interview responses
with backchannel-ready formulations and confidence scoring.
"""

import requests
import json
from typing import Dict, Any

# Configuration
DM_URL = "http://localhost:8004"

def test_ba_interview():
    """Test BA (Anti-fraud) interview responses"""
    print("🧪 Testing BA (Anti-fraud) Interview")
    print("=" * 50)
    
    # Sample BA node
    ba_node = {
        "id": "afr_l1_intro",
        "category": "AntiFraud_Rules",
        "order": 1,
        "question": "Опишите опыт настройки антифрод-правил и снижение ложноположительных срабатываний.",
        "weight": 0.4,
        "success_criteria": ["правила", "метрики", "FPR/TPR", "кейсы", "оптимизация"],
        "followups": ["Приведите пример оптимизации правила и результат в цифрах"],
        "next_if_fail": "req_l1_core",
        "next_if_pass": "afr_l2_cases"
    }
    
    # Test cases for BA
    test_cases = [
        {
            "name": "Good BA Response",
            "transcript": "Я работал с антифрод-правилами 3 года. Настраивал правила для выявления мошенничества, оптимизировал FPR до 2%, TPR был 95%. Использовал метрики качества для оценки эффективности.",
            "expected_score": "high"
        },
        {
            "name": "Medium BA Response", 
            "transcript": "Работал с правилами, настраивал параметры, снижал ложные срабатывания. Были хорошие результаты.",
            "expected_score": "medium"
        },
        {
            "name": "Poor BA Response",
            "transcript": "Да, работал с системами, что-то настраивал, но не помню детали.",
            "expected_score": "low"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 {test_case['name']}")
        print(f"Transcript: {test_case['transcript'][:50]}...")
        
        payload = {
            "node": ba_node,
            "transcript": test_case["transcript"],
            "scores": {"AntiFraud_Rules": 0.0},
            "role_profile": "ba_anti_fraud",
            "block_weights": {"AntiFraud_Rules": 0.95}
        }
        
        try:
            response = requests.post(f"{DM_URL}/reply", json=payload)
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Response: {result['reply']}")
            print(f"   Score: {result['scoring_update']['score']:.2f}")
            print(f"   Delta: {result['delta_score']:.2f}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Next Node: {result['next_node_id']}")
            print(f"   Red Flags: {result['red_flags']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def test_it_interview():
    """Test IT (Data Center) interview responses"""
    print("\n\n💻 Testing IT (Data Center) Interview")
    print("=" * 50)
    
    # Sample IT node
    it_node = {
        "id": "hw_l2_raid_bmc",
        "category": "DC_HW_x86_RAID_BMC",
        "order": 2,
        "question": "Расскажите о первичной настройке BIOS, BMC и RAID-контроллеров. Какие параметры критичны?",
        "weight": 0.6,
        "success_criteria": ["BIOS", "BMC", "RAID", "настройка", "параметры"],
        "followups": ["Какие настройки безопасности обязательны для новых серверов?"],
        "next_if_fail": "hw_l3_incidents",
        "next_if_pass": "hw_l3_incidents"
    }
    
    # Test cases for IT
    test_cases = [
        {
            "name": "Good IT Response",
            "transcript": "Настраивал BIOS для новых серверов, конфигурировал BMC для удаленного управления, настраивал RAID-массивы. Критичные параметры: загрузка с SSD, включение виртуализации, настройка IPMI.",
            "expected_score": "high"
        },
        {
            "name": "Medium IT Response",
            "transcript": "Работал с серверами, настраивал BIOS и RAID, что-то с BMC делал, но не все помню.",
            "expected_score": "medium"
        },
        {
            "name": "Poor IT Response",
            "transcript": "Да, видел серверы, но не настраивал сам.",
            "expected_score": "low"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n📝 {test_case['name']}")
        print(f"Transcript: {test_case['transcript'][:50]}...")
        
        payload = {
            "node": it_node,
            "transcript": test_case["transcript"],
            "scores": {"DC_HW_x86_RAID_BMC": 0.0},
            "role_profile": "it_dc_ops",
            "block_weights": {"DC_HW_x86_RAID_BMC": 0.95}
        }
        
        try:
            response = requests.post(f"{DM_URL}/reply", json=payload)
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Response: {result['reply']}")
            print(f"   Score: {result['scoring_update']['score']:.2f}")
            print(f"   Delta: {result['delta_score']:.2f}")
            print(f"   Confidence: {result['confidence']:.2f}")
            print(f"   Next Node: {result['next_node_id']}")
            print(f"   Red Flags: {result['red_flags']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")

def test_health_endpoints():
    """Test health and configuration endpoints"""
    print("\n\n🔍 Testing Health Endpoints")
    print("=" * 50)
    
    endpoints = [
        ("/health", "Health Check"),
        ("/config/backchannel", "Backchannel Config"),
        ("/roles", "Supported Roles")
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f"{DM_URL}{endpoint}")
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ {name}: OK")
            if endpoint == "/health":
                print(f"   Status: {result.get('status')}")
                print(f"   Config Loaded: {result.get('backchannel_config_loaded')}")
            elif endpoint == "/roles":
                print(f"   Roles: {result.get('roles')}")
                
        except Exception as e:
            print(f"❌ {name}: {e}")

def test_response_variations():
    """Test response variations for the same input"""
    print("\n\n🎲 Testing Response Variations")
    print("=" * 50)
    
    # Test the same input multiple times to see response variations
    node = {
        "id": "test_node",
        "category": "AntiFraud_Rules",
        "order": 1,
        "question": "Test question",
        "weight": 0.4,
        "success_criteria": ["правила", "метрики"],
        "followups": [],
        "next_if_fail": "next_fail",
        "next_if_pass": "next_pass"
    }
    
    transcript = "Работал с антифрод-правилами, настраивал метрики качества, снижал ложные срабатывания."
    
    payload = {
        "node": node,
        "transcript": transcript,
        "scores": {"AntiFraud_Rules": 0.0},
        "role_profile": "ba_anti_fraud"
    }
    
    print("Testing response variations (same input, multiple calls):")
    responses = []
    
    for i in range(5):
        try:
            response = requests.post(f"{DM_URL}/reply", json=payload)
            response.raise_for_status()
            result = response.json()
            responses.append(result['reply'])
            print(f"  {i+1}. {result['reply']}")
        except Exception as e:
            print(f"  {i+1}. Error: {e}")
    
    # Check for variations
    unique_responses = set(responses)
    print(f"\nUnique responses: {len(unique_responses)} out of {len(responses)}")
    if len(unique_responses) > 1:
        print("✅ Response variation working correctly")
    else:
        print("⚠️  No response variation detected")

def main():
    """Main test function"""
    print("🚀 Dialog Manager Test Suite")
    print("=" * 60)
    
    # Test health endpoints first
    test_health_endpoints()
    
    # Test BA interview
    test_ba_interview()
    
    # Test IT interview
    test_it_interview()
    
    # Test response variations
    test_response_variations()
    
    print("\n" + "=" * 60)
    print("🏁 All tests completed!")
    print("\n💡 Usage Notes:")
    print("  - Start DM service: docker compose up dm")
    print("  - Test with curl: curl -X POST http://localhost:8004/reply -d '{...}'")
    print("  - Check health: curl http://localhost:8004/health")

if __name__ == "__main__":
    main()
