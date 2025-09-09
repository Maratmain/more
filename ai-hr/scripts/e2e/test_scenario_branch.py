#!/usr/bin/env python3
"""
E2E Scenario Branch Testing
Tests a single scenario branch (3 nodes) locally with full integration.
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

class ScenarioBranchTester:
    def __init__(self, 
                 dm_url: str = "http://localhost:8004",
                 llm_url: str = "http://localhost:8080",
                 metrics_url: str = "http://localhost:8010"):
        self.dm_url = dm_url
        self.llm_url = llm_url
        self.metrics_url = metrics_url
        self.session_id = f"test_session_{int(time.time())}"
        self.turn_id = 0
        
        # Test scenario data
        self.test_scenarios = {
            "ba_anti_fraud": {
                "role_profile": "ba_anti_fraud",
                "nodes": [
                    {
                        "id": "afr_l1_intro",
                        "category": "AntiFraud_Rules",
                        "order": 1,
                        "weight": 0.4,
                        "question": "Опишите опыт настройки антифрод-правил и снижение ложноположительных срабатываний.",
                        "success_criteria": ["правила", "метрики", "FPR/TPR", "кейсы", "оптимизация"],
                        "followups": ["Приведите пример оптимизации правила и результат в цифрах"],
                        "next_if_fail": "req_l1_core",
                        "next_if_pass": "afr_l2_cases"
                    },
                    {
                        "id": "afr_l2_cases",
                        "category": "AntiFraud_Rules",
                        "order": 2,
                        "weight": 0.6,
                        "question": "Расскажите о конкретных кейсах мошенничества, с которыми вы работали.",
                        "success_criteria": ["кейсы", "мошенничество", "анализ", "решение", "результат"],
                        "followups": ["Как вы анализировали подозрительные транзакции?"],
                        "next_if_fail": "req_l1_core",
                        "next_if_pass": "req_l1_core"
                    },
                    {
                        "id": "req_l1_core",
                        "category": "Requirements_Engineering",
                        "order": 3,
                        "weight": 0.5,
                        "question": "Опишите процесс сбора и анализа требований для антифрод-систем.",
                        "success_criteria": ["требования", "анализ", "стейкхолдеры", "документация", "валидация"],
                        "followups": ["Как вы работали с бизнес-пользователями?"],
                        "next_if_fail": "test_l1_basics",
                        "next_if_pass": "test_l1_basics"
                    }
                ]
            },
            "it_dc_ops": {
                "role_profile": "it_dc_ops",
                "nodes": [
                    {
                        "id": "hw_l1_intro",
                        "category": "DC_HW_x86_RAID_BMC",
                        "order": 1,
                        "weight": 0.4,
                        "question": "Расскажите о вашем опыте работы с серверным оборудованием x86.",
                        "success_criteria": ["x86", "серверы", "BIOS", "BMC", "RAID", "настройка"],
                        "followups": ["Какие модели серверов вы настраивали?"],
                        "next_if_fail": "net_l1_basics",
                        "next_if_pass": "hw_l2_raid_bmc"
                    },
                    {
                        "id": "hw_l2_raid_bmc",
                        "category": "DC_HW_x86_RAID_BMC",
                        "order": 2,
                        "weight": 0.6,
                        "question": "Расскажите о первичной настройке BIOS, BMC и RAID-контроллеров. Какие параметры критичны?",
                        "success_criteria": ["BIOS", "BMC", "RAID", "настройка", "параметры"],
                        "followups": ["Какие настройки безопасности обязательны для новых серверов?"],
                        "next_if_fail": "hw_l3_incidents",
                        "next_if_pass": "hw_l3_incidents"
                    },
                    {
                        "id": "net_l1_basics",
                        "category": "LAN_SAN_Networking",
                        "order": 3,
                        "weight": 0.5,
                        "question": "Опишите ваш опыт настройки сетевого оборудования в ЦОД.",
                        "success_criteria": ["сеть", "LAN", "SAN", "Cisco", "MikroTik", "настройка"],
                        "followups": ["Какие протоколы вы использовали?"],
                        "next_if_fail": "inc_l1_basics",
                        "next_if_pass": "inc_l1_basics"
                    }
                ]
            }
        }
    
    def check_service_health(self) -> Dict[str, bool]:
        """Check health of all required services"""
        print("🔍 Checking service health...")
        
        health_status = {}
        
        # Check DM service
        try:
            response = requests.get(f"{self.dm_url}/health", timeout=5)
            health_status["dm"] = response.status_code == 200
            if health_status["dm"]:
                print("✅ Dialog Manager: OK")
            else:
                print("❌ Dialog Manager: Failed")
        except Exception as e:
            health_status["dm"] = False
            print(f"❌ Dialog Manager: Error - {e}")
        
        # Check LLM service
        try:
            response = requests.get(f"{self.llm_url}/health", timeout=5)
            health_status["llm"] = response.status_code == 200
            if health_status["llm"]:
                print("✅ LLM Service: OK")
            else:
                print("❌ LLM Service: Failed")
        except Exception as e:
            health_status["llm"] = False
            print(f"❌ LLM Service: Error - {e}")
        
        # Check Metrics service
        try:
            response = requests.get(f"{self.metrics_url}/health", timeout=5)
            health_status["metrics"] = response.status_code == 200
            if health_status["metrics"]:
                print("✅ Metrics Service: OK")
            else:
                print("❌ Metrics Service: Failed")
        except Exception as e:
            health_status["metrics"] = False
            print(f"❌ Metrics Service: Error - {e}")
        
        return health_status
    
    def simulate_candidate_response(self, node: Dict[str, Any], role_profile: str) -> str:
        """Simulate candidate response based on node and role profile"""
        
        # Role-specific response templates
        responses = {
            "ba_anti_fraud": {
                "AntiFraud_Rules": [
                    "Я работал с антифрод-правилами 3 года. Настраивал метрики FPR и TPR, оптимизировал правила для снижения ложноположительных срабатываний. У нас было несколько кейсов с карточным мошенничеством, которые мы успешно выявили.",
                    "В моей практике было много работы с антифрод-системами. Я настраивал правила, анализировал метрики FPR/TPR, работал с кейсами мошенничества. Особенно эффективно получилось снизить ложноположительные срабатывания на 30%.",
                    "Опыт работы с антифродом - 2 года. Настраивал правила, работал с метриками, анализировал кейсы мошенничества. Понимаю важность баланса между выявлением мошенничества и ложными срабатываниями."
                ],
                "Requirements_Engineering": [
                    "Собирал требования для антифрод-систем, работал с бизнес-пользователями, анализировал их потребности. Документировал требования, проводил валидацию с заказчиками.",
                    "Опыт сбора требований - 3 года. Работал со стейкхолдерами, анализировал бизнес-процессы, документировал требования. Проводил интервью, валидировал требования с пользователями.",
                    "Собирал требования для различных систем, включая антифрод. Работал с документацией, анализировал потребности пользователей, проводил валидацию требований."
                ]
            },
            "it_dc_ops": {
                "DC_HW_x86_RAID_BMC": [
                    "Работал с серверным оборудованием x86 4 года. Настраивал BIOS, BMC, RAID-контроллеры. Знаю критические параметры безопасности, настройки производительности.",
                    "Опыт работы с x86 серверами - 3 года. Настраивал BIOS, BMC, RAID. Понимаю важность правильной настройки параметров безопасности и производительности.",
                    "Работал с серверным оборудованием, настраивал BIOS, BMC, RAID-контроллеры. Знаю основные параметры настройки и безопасности."
                ],
                "LAN_SAN_Networking": [
                    "Настраивал сетевое оборудование в ЦОД 3 года. Работал с Cisco, MikroTik, настраивал LAN и SAN сети. Использовал различные протоколы, включая BGP, OSPF.",
                    "Опыт настройки сетей в ЦОД - 2 года. Работал с Cisco оборудованием, настраивал LAN/SAN, знаю протоколы маршрутизации и коммутации.",
                    "Настраивал сетевое оборудование, работал с LAN и SAN сетями. Знаю основные протоколы и принципы настройки сетевого оборудования."
                ]
            }
        }
        
        # Get appropriate response based on role and category
        role_responses = responses.get(role_profile, {})
        category_responses = role_responses.get(node["category"], [
            f"У меня есть опыт работы с {node['category']}. Могу рассказать подробнее."
        ])
        
        # Return a random response from the category
        import random
        return random.choice(category_responses)
    
    def test_single_node(self, node: Dict[str, Any], role_profile: str, scores: Dict[str, float]) -> Dict[str, Any]:
        """Test a single interview node"""
        self.turn_id += 1
        
        print(f"\n🎯 Testing Node: {node['id']} ({node['category']})")
        print(f"📝 Question: {node['question']}")
        
        # Simulate candidate response
        candidate_response = self.simulate_candidate_response(node, role_profile)
        print(f"💬 Candidate: {candidate_response}")
        
        # Prepare DM request
        dm_request = {
            "node": node,
            "transcript": candidate_response,
            "scores": scores,
            "role_profile": role_profile
        }
        
        # Measure DM response time
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.dm_url}/reply",
                json=dm_request,
                timeout=30
            )
            
            end_time = time.time()
            dm_latency_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                dm_response = response.json()
                
                print(f"🤖 DM Response: {dm_response.get('reply', 'No reply')}")
                print(f"📊 Next Node: {dm_response.get('next_node_id', 'None')}")
                print(f"📈 Score Update: {dm_response.get('scoring_update', {})}")
                print(f"🚩 Red Flags: {dm_response.get('red_flags', [])}")
                print(f"⏱️  DM Latency: {dm_latency_ms:.1f}ms")
                
                # Record metrics
                self.record_metrics(dm_latency_ms, dm_response)
                
                return {
                    "success": True,
                    "node_id": node["id"],
                    "dm_response": dm_response,
                    "dm_latency_ms": dm_latency_ms,
                    "candidate_response": candidate_response,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "node_id": node["id"],
                    "dm_response": None,
                    "dm_latency_ms": dm_latency_ms,
                    "candidate_response": candidate_response,
                    "error": f"HTTP {response.status_code}: {response.text}"
                }
                
        except Exception as e:
            end_time = time.time()
            dm_latency_ms = (end_time - start_time) * 1000
            
            return {
                "success": False,
                "node_id": node["id"],
                "dm_response": None,
                "dm_latency_ms": dm_latency_ms,
                "candidate_response": candidate_response,
                "error": str(e)
            }
    
    def record_metrics(self, dm_latency_ms: float, dm_response: Dict[str, Any]):
        """Record metrics to metrics service"""
        try:
            # Record DM latency
            metrics_request = {
                "service": "dm",
                "latency_ms": dm_latency_ms,
                "session_id": self.session_id,
                "turn_id": str(self.turn_id)
            }
            
            requests.post(
                f"{self.metrics_url}/latency",
                json=metrics_request,
                timeout=5
            )
            
            # Record turn metrics
            turn_request = {
                "session_id": self.session_id,
                "turn_id": str(self.turn_id),
                "total_turn_s": dm_latency_ms / 1000
            }
            
            requests.post(
                f"{self.metrics_url}/turn",
                json=turn_request,
                timeout=5
            )
            
        except Exception as e:
            print(f"⚠️  Failed to record metrics: {e}")
    
    def test_scenario_branch(self, scenario_name: str) -> Dict[str, Any]:
        """Test a complete scenario branch (3 nodes)"""
        print(f"🚀 Starting E2E test for scenario: {scenario_name}")
        print("=" * 60)
        
        if scenario_name not in self.test_scenarios:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        scenario = self.test_scenarios[scenario_name]
        role_profile = scenario["role_profile"]
        nodes = scenario["nodes"]
        
        print(f"👤 Role Profile: {role_profile}")
        print(f"📋 Nodes to test: {len(nodes)}")
        print()
        
        # Initialize scores
        scores = {}
        results = []
        total_start_time = time.time()
        
        # Test each node in sequence
        for i, node in enumerate(nodes):
            print(f"📍 Step {i+1}/{len(nodes)}")
            
            result = self.test_single_node(node, role_profile, scores)
            results.append(result)
            
            if not result["success"]:
                print(f"❌ Node test failed: {result['error']}")
                break
            
            # Update scores based on DM response
            scoring_update = result["dm_response"].get("scoring_update", {})
            if scoring_update:
                block = scoring_update.get("block")
                score = scoring_update.get("score", 0.0)
                if block:
                    scores[block] = score
            
            # Determine next node
            next_node_id = result["dm_response"].get("next_node_id")
            if next_node_id and i < len(nodes) - 1:
                # Find next node in our test sequence
                next_node = next((n for n in nodes if n["id"] == next_node_id), None)
                if next_node:
                    # Reorder nodes to follow the path
                    nodes = [next_node] + [n for n in nodes if n["id"] != next_node_id]
        
        total_end_time = time.time()
        total_duration_s = total_end_time - total_start_time
        
        # Calculate summary statistics
        successful_tests = [r for r in results if r["success"]]
        total_dm_latency = sum(r["dm_latency_ms"] for r in successful_tests)
        avg_dm_latency = total_dm_latency / len(successful_tests) if successful_tests else 0
        
        summary = {
            "scenario_name": scenario_name,
            "role_profile": role_profile,
            "total_duration_s": total_duration_s,
            "nodes_tested": len(results),
            "successful_tests": len(successful_tests),
            "success_rate": len(successful_tests) / len(results) * 100 if results else 0,
            "avg_dm_latency_ms": avg_dm_latency,
            "total_dm_latency_ms": total_dm_latency,
            "final_scores": scores,
            "results": results
        }
        
        return summary
    
    def print_summary(self, summary: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 E2E TEST SUMMARY")
        print("=" * 60)
        print(f"🎭 Scenario: {summary['scenario_name']}")
        print(f"👤 Role Profile: {summary['role_profile']}")
        print(f"⏱️  Total Duration: {summary['total_duration_s']:.1f}s")
        print(f"📋 Nodes Tested: {summary['nodes_tested']}")
        print(f"✅ Successful Tests: {summary['successful_tests']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⚡ Avg DM Latency: {summary['avg_dm_latency_ms']:.1f}ms")
        print(f"📊 Total DM Latency: {summary['total_dm_latency_ms']:.1f}ms")
        
        print(f"\n🎯 Final Scores:")
        for block, score in summary['final_scores'].items():
            print(f"   {block}: {score:.2f}")
        
        # SLA compliance check
        sla_compliant = summary['avg_dm_latency_ms'] <= 5000  # 5 seconds
        print(f"\n🎯 SLA Compliance: {'✅' if sla_compliant else '❌'} {'Compliant' if sla_compliant else 'Violated'}")
        
        if not sla_compliant:
            print("💡 Recommendations:")
            print("   - Reduce max_tokens in DM configuration")
            print("   - Enable backchannel for better UX")
            print("   - Consider hardware upgrade")
    
    def save_results(self, summary: Dict[str, Any], output_file: str):
        """Save test results to JSON file"""
        # Add metadata
        summary["test_metadata"] = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "dm_url": self.dm_url,
            "llm_url": self.llm_url,
            "metrics_url": self.metrics_url
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Results saved to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="E2E Scenario Branch Testing")
    parser.add_argument("--scenario", choices=["ba_anti_fraud", "it_dc_ops"], 
                       default="ba_anti_fraud", help="Scenario to test")
    parser.add_argument("--dm-url", default="http://localhost:8004", help="DM service URL")
    parser.add_argument("--llm-url", default="http://localhost:8080", help="LLM service URL")
    parser.add_argument("--metrics-url", default="http://localhost:8010", help="Metrics service URL")
    parser.add_argument("--output", default="e2e_test_results.json", help="Output JSON file")
    parser.add_argument("--skip-health-check", action="store_true", help="Skip service health check")
    
    args = parser.parse_args()
    
    tester = ScenarioBranchTester(
        dm_url=args.dm_url,
        llm_url=args.llm_url,
        metrics_url=args.metrics_url
    )
    
    try:
        # Check service health
        if not args.skip_health_check:
            health_status = tester.check_service_health()
            if not all(health_status.values()):
                print("\n❌ Some services are not healthy. Use --skip-health-check to proceed anyway.")
                sys.exit(1)
            print()
        
        # Run scenario test
        summary = tester.test_scenario_branch(args.scenario)
        
        # Print summary
        tester.print_summary(summary)
        
        # Save results
        tester.save_results(summary, args.output)
        
        # Exit with appropriate code
        if summary['success_rate'] == 100 and summary['avg_dm_latency_ms'] <= 5000:
            print("\n🎉 All tests passed!")
            sys.exit(0)
        else:
            print("\n⚠️  Some tests failed or SLA violated")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
