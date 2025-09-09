#!/usr/bin/env python3
"""
AI-HR Cost Analysis Script

Analyzes costs and provides comparison with HR salary costs.
Generates reports on cost efficiency and recommendations.
"""

import os
import sys
import json
import requests
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Configuration
METRICS_SERVICE_URL = os.getenv("METRICS_SERVICE_URL", "http://localhost:8010")
DEFAULT_HR_SALARY = 50.0  # $50/hour default HR rate

class CostAnalyzer:
    """Cost analysis and reporting"""
    
    def __init__(self, metrics_url: str = METRICS_SERVICE_URL):
        self.metrics_url = metrics_url
        self.session = requests.Session()
    
    def get_cost_analysis(self, session_id: Optional[str] = None, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Get cost analysis from metrics service"""
        try:
            payload = {
                "session_id": session_id,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "include_breakdown": True
            }
            
            response = self.session.post(
                f"{self.metrics_url}/cost-analysis",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching cost analysis: {e}")
            return {}
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get metrics summary from service"""
        try:
            response = self.session.get(f"{self.metrics_url}/metrics/summary", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching metrics summary: {e}")
            return {}
    
    def get_sla_targets(self) -> Dict[str, Any]:
        """Get SLA targets from service"""
        try:
            response = self.session.get(f"{self.metrics_url}/sla-targets", timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching SLA targets: {e}")
            return {}
    
    def calculate_roi(self, analysis: Dict[str, Any], hr_salary_override: Optional[float] = None) -> Dict[str, Any]:
        """Calculate ROI and cost savings"""
        hr_salary = hr_salary_override or DEFAULT_HR_SALARY
        hr_comparison = analysis.get("hr_salary_comparison", {})
        
        total_turns = analysis.get("total_turns", 0)
        total_cost = analysis.get("total_cost_usd", 0)
        avg_cost_per_turn = analysis.get("avg_cost_per_turn", 0)
        
        if total_turns == 0:
            return {"error": "No data available for ROI calculation"}
        
        # Calculate HR costs
        avg_turn_duration_minutes = hr_comparison.get("avg_turn_duration_minutes", 0)
        hr_cost_per_turn = (avg_turn_duration_minutes / 60) * hr_salary
        total_hr_cost = hr_cost_per_turn * total_turns
        
        # Calculate savings
        total_savings = total_hr_cost - total_cost
        savings_percentage = (total_savings / total_hr_cost * 100) if total_hr_cost > 0 else 0
        
        # Calculate ROI
        roi_percentage = (total_savings / total_cost * 100) if total_cost > 0 else 0
        
        return {
            "hr_salary_per_hour": hr_salary,
            "total_turns": total_turns,
            "avg_turn_duration_minutes": avg_turn_duration_minutes,
            "ai_total_cost": total_cost,
            "hr_total_cost": total_hr_cost,
            "total_savings": total_savings,
            "savings_percentage": savings_percentage,
            "roi_percentage": roi_percentage,
            "break_even_turns": int(total_cost / hr_cost_per_turn) if hr_cost_per_turn > 0 else 0,
            "cost_per_turn_ai": avg_cost_per_turn,
            "cost_per_turn_hr": hr_cost_per_turn,
            "savings_per_turn": hr_cost_per_turn - avg_cost_per_turn
        }
    
    def generate_recommendations(self, analysis: Dict[str, Any], roi: Dict[str, Any]) -> List[str]:
        """Generate cost optimization recommendations"""
        recommendations = []
        
        # Cost efficiency recommendations
        if roi.get("savings_percentage", 0) < 0:
            recommendations.append("🚨 AI costs exceed HR costs - immediate optimization needed")
        elif roi.get("savings_percentage", 0) < 20:
            recommendations.append("⚠️ Low cost savings - consider optimizing AI usage")
        elif roi.get("savings_percentage", 0) > 80:
            recommendations.append("✅ Excellent cost savings - consider scaling up")
        
        # SLA compliance recommendations
        sla_compliance = analysis.get("sla_compliance", {})
        if sla_compliance.get("overall", 0) < 90:
            recommendations.append("🔧 SLA compliance below 90% - investigate performance issues")
        
        if sla_compliance.get("asr_latency", 0) < 95:
            recommendations.append("🎤 ASR latency issues - consider faster models or local processing")
        
        if sla_compliance.get("dm_latency", 0) < 95:
            recommendations.append("💬 Dialog Manager latency issues - optimize response generation")
        
        if sla_compliance.get("tts_latency", 0) < 95:
            recommendations.append("🔊 TTS latency issues - consider local TTS or caching")
        
        # Cost breakdown recommendations
        cost_breakdown = analysis.get("cost_breakdown", {})
        if cost_breakdown.get("llm", 0) > analysis.get("total_cost_usd", 0) * 0.7:
            recommendations.append("🤖 LLM costs >70% of total - consider model optimization")
        
        if cost_breakdown.get("asr", 0) > analysis.get("total_cost_usd", 0) * 0.3:
            recommendations.append("🎤 ASR costs >30% of total - consider local processing")
        
        if cost_breakdown.get("tts", 0) > analysis.get("total_cost_usd", 0) * 0.2:
            recommendations.append("🔊 TTS costs >20% of total - consider local TTS")
        
        # Volume recommendations
        total_turns = analysis.get("total_turns", 0)
        if total_turns > 1000:
            recommendations.append("📈 High volume usage - consider bulk pricing or dedicated infrastructure")
        elif total_turns < 10:
            recommendations.append("📉 Low volume usage - consider pay-per-use models")
        
        return recommendations
    
    def print_cost_report(self, analysis: Dict[str, Any], roi: Dict[str, Any], 
                         sla_targets: Dict[str, Any], recommendations: List[str]):
        """Print formatted cost report"""
        print("=" * 80)
        print("🤖 AI-HR COST ANALYSIS REPORT")
        print("=" * 80)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Summary
        print("📊 SUMMARY")
        print("-" * 40)
        print(f"Total Turns: {analysis.get('total_turns', 0):,}")
        print(f"Total AI Cost: ${analysis.get('total_cost_usd', 0):.2f}")
        print(f"Average Cost per Turn: ${analysis.get('avg_cost_per_turn', 0):.4f}")
        print()
        
        # ROI Analysis
        print("💰 ROI ANALYSIS")
        print("-" * 40)
        print(f"HR Salary Rate: ${roi.get('hr_salary_per_hour', 0):.2f}/hour")
        print(f"Average Turn Duration: {roi.get('avg_turn_duration_minutes', 0):.1f} minutes")
        print(f"AI Cost per Turn: ${roi.get('cost_per_turn_ai', 0):.4f}")
        print(f"HR Cost per Turn: ${roi.get('cost_per_turn_hr', 0):.2f}")
        print(f"Savings per Turn: ${roi.get('savings_per_turn', 0):.2f}")
        print(f"Total Savings: ${roi.get('total_savings', 0):.2f}")
        print(f"Savings Percentage: {roi.get('savings_percentage', 0):.1f}%")
        print(f"ROI: {roi.get('roi_percentage', 0):.1f}%")
        print(f"Break-even Point: {roi.get('break_even_turns', 0)} turns")
        print()
        
        # Cost Breakdown
        print("💸 COST BREAKDOWN")
        print("-" * 40)
        cost_breakdown = analysis.get("cost_breakdown", {})
        total_cost = analysis.get("total_cost_usd", 0)
        
        for service, cost in cost_breakdown.items():
            percentage = (cost / total_cost * 100) if total_cost > 0 else 0
            print(f"{service.upper():<15}: ${cost:.2f} ({percentage:.1f}%)")
        print()
        
        # SLA Compliance
        print("⏱️ SLA COMPLIANCE")
        print("-" * 40)
        sla_compliance = analysis.get("sla_compliance", {})
        targets = sla_targets.get("targets", {})
        
        sla_metrics = [
            ("ASR Latency", "asr_latency", "asr_latency_ms"),
            ("DM Latency", "dm_latency", "dm_latency_ms"),
            ("TTS Latency", "tts_latency", "tts_latency_ms"),
            ("Total Turn", "total_turn", "total_turn_s"),
            ("Backchannel", "backchannel", "backchannel_s"),
            ("Overall", "overall", None)
        ]
        
        for name, key, target_key in sla_metrics:
            compliance = sla_compliance.get(key, 0)
            target = targets.get(target_key, "N/A") if target_key else "All metrics"
            status = "✅" if compliance >= 95 else "⚠️" if compliance >= 90 else "❌"
            print(f"{name:<15}: {compliance:5.1f}% {status} (target: {target})")
        print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 40)
        if recommendations:
            for i, rec in enumerate(recommendations, 1):
                print(f"{i}. {rec}")
        else:
            print("No specific recommendations at this time.")
        print()
        
        # Cost Efficiency Rating
        savings_pct = roi.get("savings_percentage", 0)
        if savings_pct >= 80:
            rating = "🟢 EXCELLENT"
        elif savings_pct >= 60:
            rating = "🟡 GOOD"
        elif savings_pct >= 40:
            rating = "🟠 FAIR"
        elif savings_pct >= 0:
            rating = "🔴 POOR"
        else:
            rating = "🚨 CRITICAL"
        
        print("📈 COST EFFICIENCY RATING")
        print("-" * 40)
        print(f"Rating: {rating}")
        print(f"Savings: {savings_pct:.1f}%")
        print()
        
        print("=" * 80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="AI-HR Cost Analysis Tool")
    parser.add_argument("--session-id", help="Specific session ID to analyze")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--hr-salary", type=float, help="HR salary per hour (default: $50)")
    parser.add_argument("--metrics-url", default=METRICS_SERVICE_URL, help="Metrics service URL")
    parser.add_argument("--output", help="Output file for JSON report")
    parser.add_argument("--quiet", action="store_true", help="Quiet mode (JSON output only)")
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid start date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
        except ValueError:
            print("Error: Invalid end date format. Use YYYY-MM-DD")
            sys.exit(1)
    
    # Initialize analyzer
    analyzer = CostAnalyzer(args.metrics_url)
    
    # Get data
    print("Fetching cost analysis data..." if not args.quiet else "", end="")
    analysis = analyzer.get_cost_analysis(args.session_id, start_date, end_date)
    
    if not analysis:
        print("Error: Could not fetch cost analysis data")
        sys.exit(1)
    
    print("✓" if not args.quiet else "", end="")
    
    # Get SLA targets
    print("Fetching SLA targets..." if not args.quiet else "", end="")
    sla_targets = analyzer.get_sla_targets()
    print("✓" if not args.quiet else "", end="")
    
    # Calculate ROI
    print("Calculating ROI..." if not args.quiet else "", end="")
    roi = analyzer.calculate_roi(analysis, args.hr_salary)
    print("✓" if not args.quiet else "", end="")
    
    # Generate recommendations
    print("Generating recommendations..." if not args.quiet else "", end="")
    recommendations = analyzer.generate_recommendations(analysis, roi)
    print("✓" if not args.quiet else "", end="")
    
    # Prepare report data
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis,
        "roi": roi,
        "sla_targets": sla_targets,
        "recommendations": recommendations
    }
    
    # Output
    if args.quiet:
        # JSON output only
        print(json.dumps(report_data, indent=2))
    else:
        # Full report
        analyzer.print_cost_report(analysis, roi, sla_targets, recommendations)
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"Report saved to: {args.output}")

if __name__ == "__main__":
    main()
