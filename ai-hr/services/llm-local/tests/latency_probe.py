#!/usr/bin/env python3
"""
Latency Probe for LLM Local Service
Tests response times and automatically adjusts configuration for SLA compliance.
"""

import os
import sys
import time
import json
import csv
import statistics
import requests
import argparse
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LatencyProbe:
    def __init__(self, base_url: str = "http://localhost:8080", num_runs: int = 10):
        self.base_url = base_url
        self.num_runs = num_runs
        self.results = []
        self.csv_file = "latency_results.csv"
        
        # Test prompts (short for latency testing)
        self.test_prompts = [
            "Привет! Как дела?",
            "Расскажи о своем опыте работы с Python.",
            "Что такое машинное обучение?",
            "Опиши процесс разработки ПО.",
            "Какие у тебя навыки в области данных?"
        ]
    
    def test_single_request(self, prompt: str, max_tokens: int = 50) -> Dict[str, Any]:
        """Test a single request and measure latency"""
        payload = {
            "model": "qwen2.5-7b-instruct",
            "messages": [
                {"role": "system", "content": "Ты интервьюер. Отвечай коротко."},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "temperature": 0.7,
            "max_tokens": max_tokens
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                content = data.get('choices', [{}])[0].get('message', {}).get('content', '')
                token_count = len(content.split())  # Approximate token count
                
                return {
                    "success": True,
                    "latency_ms": latency_ms,
                    "token_count": token_count,
                    "content_length": len(content),
                    "status_code": response.status_code,
                    "error": None
                }
            else:
                return {
                    "success": False,
                    "latency_ms": latency_ms,
                    "token_count": 0,
                    "content_length": 0,
                    "status_code": response.status_code,
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            return {
                "success": False,
                "latency_ms": latency_ms,
                "token_count": 0,
                "content_length": 0,
                "status_code": 0,
                "error": str(e)
            }
    
    def run_latency_test(self, max_tokens: int = 50) -> List[Dict[str, Any]]:
        """Run latency test with multiple prompts"""
        print(f"🚀 Starting latency test with {self.num_runs} runs, max_tokens={max_tokens}")
        print(f"📡 Testing against: {self.base_url}")
        print()
        
        results = []
        
        for i in range(self.num_runs):
            prompt = self.test_prompts[i % len(self.test_prompts)]
            print(f"Run {i+1}/{self.num_runs}: {prompt[:30]}...")
            
            result = self.test_single_request(prompt, max_tokens)
            result["run"] = i + 1
            result["prompt"] = prompt
            result["max_tokens"] = max_tokens
            result["timestamp"] = datetime.now().isoformat()
            
            results.append(result)
            
            if result["success"]:
                print(f"  ✅ {result['latency_ms']:.1f}ms, {result['token_count']} tokens")
            else:
                print(f"  ❌ {result['latency_ms']:.1f}ms, Error: {result['error']}")
            
            # Small delay between requests
            time.sleep(0.5)
        
        return results
    
    def calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate latency statistics"""
        successful_results = [r for r in results if r["success"]]
        
        if not successful_results:
            return {
                "p50": 0,
                "p95": 0,
                "p99": 0,
                "mean": 0,
                "min": 0,
                "max": 0,
                "success_rate": 0
            }
        
        latencies = [r["latency_ms"] for r in successful_results]
        latencies.sort()
        
        n = len(latencies)
        
        return {
            "p50": latencies[int(n * 0.5)],
            "p95": latencies[int(n * 0.95)],
            "p99": latencies[int(n * 0.99)],
            "mean": statistics.mean(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "success_rate": len(successful_results) / len(results) * 100
        }
    
    def save_results_to_csv(self, results: List[Dict[str, Any]], stats: Dict[str, float]):
        """Save results to CSV file"""
        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'run', 'timestamp', 'prompt', 'max_tokens', 'success', 
                'latency_ms', 'token_count', 'content_length', 'status_code', 'error'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow(result)
        
        # Append statistics
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([])  # Empty row
            writer.writerow(['STATISTICS'])
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['P50 (ms)', f"{stats['p50']:.1f}"])
            writer.writerow(['P95 (ms)', f"{stats['p95']:.1f}"])
            writer.writerow(['P99 (ms)', f"{stats['p99']:.1f}"])
            writer.writerow(['Mean (ms)', f"{stats['mean']:.1f}"])
            writer.writerow(['Min (ms)', f"{stats['min']:.1f}"])
            writer.writerow(['Max (ms)', f"{stats['max']:.1f}"])
            writer.writerow(['Success Rate (%)', f"{stats['success_rate']:.1f}"])
        
        print(f"📊 Results saved to: {self.csv_file}")
    
    def check_sla_compliance(self, stats: Dict[str, float]) -> Tuple[bool, str]:
        """Check if performance meets SLA requirements"""
        sla_target_ms = 5000  # 5 seconds
        
        if stats["p95"] > sla_target_ms:
            return False, f"P95 latency {stats['p95']:.1f}ms exceeds SLA target {sla_target_ms}ms"
        
        if stats["success_rate"] < 95:
            return False, f"Success rate {stats['success_rate']:.1f}% below 95% threshold"
        
        return True, "SLA compliance achieved"
    
    def suggest_optimizations(self, stats: Dict[str, float]) -> List[str]:
        """Suggest configuration optimizations based on results"""
        suggestions = []
        
        if stats["p95"] > 5000:  # 5 seconds
            suggestions.append("⚠️  P95 > 5s: Reduce max_tokens to 32-48")
            suggestions.append("⚠️  Consider using Q4_K_M quantization")
            suggestions.append("⚠️  Enable backchannel for better UX")
        
        elif stats["p95"] > 3000:  # 3 seconds
            suggestions.append("⚡ P95 > 3s: Consider reducing max_tokens to 64")
            suggestions.append("⚡ Monitor performance under load")
        
        if stats["success_rate"] < 95:
            suggestions.append("🔧 Low success rate: Check service health")
            suggestions.append("🔧 Verify GPU/CPU resources")
        
        if stats["mean"] < 1000:  # 1 second
            suggestions.append("✅ Excellent performance! Consider increasing max_tokens")
        
        return suggestions
    
    def run_adaptive_test(self) -> Dict[str, Any]:
        """Run adaptive test with automatic configuration adjustment"""
        print("🔍 Running adaptive latency test...")
        print()
        
        # Test with different max_tokens values
        max_tokens_options = [96, 64, 48, 32]
        best_config = None
        
        for max_tokens in max_tokens_options:
            print(f"🧪 Testing with max_tokens={max_tokens}")
            results = self.run_latency_test(max_tokens)
            stats = self.calculate_statistics(results)
            
            print(f"📈 Results: P50={stats['p50']:.1f}ms, P95={stats['p95']:.1f}ms, Success={stats['success_rate']:.1f}%")
            
            sla_compliant, message = self.check_sla_compliance(stats)
            print(f"🎯 SLA: {'✅' if sla_compliant else '❌'} {message}")
            
            if sla_compliant:
                best_config = {
                    "max_tokens": max_tokens,
                    "stats": stats,
                    "results": results
                }
                print(f"✅ Found SLA-compliant configuration: max_tokens={max_tokens}")
                break
            else:
                print(f"❌ Configuration not SLA-compliant, trying smaller max_tokens...")
            
            print()
        
        if best_config:
            # Save best configuration results
            self.save_results_to_csv(best_config["results"], best_config["stats"])
            
            # Print final recommendations
            print("🎉 ADAPTIVE TEST COMPLETE")
            print("=" * 50)
            print(f"✅ Recommended max_tokens: {best_config['max_tokens']}")
            print(f"📊 P95 latency: {best_config['stats']['p95']:.1f}ms")
            print(f"📊 Success rate: {best_config['stats']['success_rate']:.1f}%")
            
            suggestions = self.suggest_optimizations(best_config["stats"])
            if suggestions:
                print("\n💡 Recommendations:")
                for suggestion in suggestions:
                    print(f"   {suggestion}")
            
            return best_config
        else:
            print("❌ No SLA-compliant configuration found!")
            print("💡 Consider:")
            print("   - Using smaller model (Qwen2.5-3B)")
            print("   - Enabling backchannel")
            print("   - Upgrading hardware")
            return None

def main():
    parser = argparse.ArgumentParser(description="LLM Latency Probe")
    parser.add_argument("--url", default="http://localhost:8080", help="LLM service URL")
    parser.add_argument("--runs", type=int, default=10, help="Number of test runs")
    parser.add_argument("--max-tokens", type=int, default=50, help="Max tokens per request")
    parser.add_argument("--adaptive", action="store_true", help="Run adaptive test")
    parser.add_argument("--output", default="latency_results.csv", help="Output CSV file")
    
    args = parser.parse_args()
    
    probe = LatencyProbe(base_url=args.url, num_runs=args.runs)
    probe.csv_file = args.output
    
    if args.adaptive:
        result = probe.run_adaptive_test()
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        # Single test run
        results = probe.run_latency_test(args.max_tokens)
        stats = probe.calculate_statistics(results)
        
        print("\n📊 LATENCY TEST RESULTS")
        print("=" * 30)
        print(f"P50: {stats['p50']:.1f}ms")
        print(f"P95: {stats['p95']:.1f}ms")
        print(f"P99: {stats['p99']:.1f}ms")
        print(f"Mean: {stats['mean']:.1f}ms")
        print(f"Min: {stats['min']:.1f}ms")
        print(f"Max: {stats['max']:.1f}ms")
        print(f"Success Rate: {stats['success_rate']:.1f}%")
        
        sla_compliant, message = probe.check_sla_compliance(stats)
        print(f"\n🎯 SLA Compliance: {'✅' if sla_compliant else '❌'} {message}")
        
        suggestions = probe.suggest_optimizations(stats)
        if suggestions:
            print("\n💡 Recommendations:")
            for suggestion in suggestions:
                print(f"   {suggestion}")
        
        probe.save_results_to_csv(results, stats)

if __name__ == "__main__":
    main()
