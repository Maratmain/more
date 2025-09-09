# Сервис метрик AI-HR
import os
import time
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI-HR Metrics")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
METRICS_STORAGE_PATH = Path(__file__).parent / "data"
METRICS_STORAGE_PATH.mkdir(exist_ok=True)
SLA_TARGETS = {
    "asr_latency_ms": 2000,
    "dm_latency_ms": 1000,
    "tts_latency_ms": 1500,
    "total_turn_s": 5.0,
    "backchannel_s": 2.0,
}
COST_CONFIG = {
    "llm": {
        "openrouter": {
            "claude-3.5-sonnet": 0.003,  # $0.003 per 1K tokens
            "gpt-4": 0.03,               # $0.03 per 1K tokens
            "default": 0.01,             # $0.01 per 1K tokens
        },
        "openai": {
            "gpt-4": 0.03,               # $0.03 per 1K tokens
            "gpt-3.5-turbo": 0.002,      # $0.002 per 1K tokens
            "default": 0.01,             # $0.01 per 1K tokens
        }
    },
    "asr": {
        "whisper": 0.006,                # $0.006 per minute
        "faster-whisper": 0.003,         # $0.003 per minute (local)
        "default": 0.005,                # $0.005 per minute
    },
    "tts": {
        "piper": 0.001,                  # $0.001 per minute (local)
        "elevenlabs": 0.18,              # $0.18 per 1K characters
        "default": 0.01,                 # $0.01 per minute
    },
    "storage": {
        "qdrant": 0.0001,                # $0.0001 per MB per month
        "embeddings": 0.00005,           # $0.00005 per embedding
        "default": 0.0001,               # $0.0001 per MB per month
    }
}

@dataclass
class LatencyMetric:
    """Latency measurement for a service"""
    service: str
    latency_ms: float
    timestamp: datetime
    session_id: str
    turn_id: str
    success: bool = True
    error_message: Optional[str] = None

@dataclass
class CostMetric:
    """Cost measurement for a service"""
    service: str
    cost_usd: float
    timestamp: datetime
    session_id: str
    turn_id: str
    units: int = 1
    unit_type: str = "request"
    details: Dict[str, Any] = None

@dataclass
class TurnMetric:
    """Complete turn measurement"""
    session_id: str
    turn_id: str
    timestamp: datetime
    asr_latency_ms: float
    dm_latency_ms: float
    tts_latency_ms: float
    total_turn_s: float
    backchannel_s: float
    total_cost_usd: float
    sla_compliant: bool
    services_used: List[str]

# Pydantic models for API
class LatencyRequest(BaseModel):
    service: str
    latency_ms: float
    session_id: str
    turn_id: str
    success: bool = True
    error_message: Optional[str] = None

class CostRequest(BaseModel):
    service: str
    cost_usd: float
    session_id: str
    turn_id: str
    units: int = 1
    unit_type: str = "request"
    details: Optional[Dict[str, Any]] = None

class TurnRequest(BaseModel):
    session_id: str
    turn_id: str
    asr_latency_ms: float
    dm_latency_ms: float
    tts_latency_ms: float
    total_turn_s: float
    backchannel_s: float
    total_cost_usd: float
    services_used: List[str]

class CostAnalysisRequest(BaseModel):
    session_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_breakdown: bool = True

class CostAnalysisResponse(BaseModel):
    total_cost_usd: float
    total_turns: int
    avg_cost_per_turn: float
    cost_breakdown: Dict[str, float]
    sla_compliance: Dict[str, float]
    hr_salary_comparison: Dict[str, Any]
    recommendations: List[str]

# Storage functions
def save_metric_to_csv(metric: Any, filename: str):
    """Save metric to CSV file"""
    csv_path = METRICS_STORAGE_PATH / f"{filename}.csv"
    file_exists = csv_path.exists()
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            # Write header
            if hasattr(metric, '__dataclass_fields__'):
                writer.writerow(metric.__dataclass_fields__.keys())
            else:
                writer.writerow(metric.keys())
        
        # Write data
        if hasattr(metric, '__dataclass_fields__'):
            writer.writerow(asdict(metric).values())
        else:
            writer.writerow(metric.values())

def load_metrics_from_csv(filename: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict]:
    """Load metrics from CSV file with optional date filtering"""
    csv_path = METRICS_STORAGE_PATH / f"{filename}.csv"
    
    if not csv_path.exists():
        return []
    
    metrics = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert timestamp if present
            if 'timestamp' in row and row['timestamp']:
                try:
                    row['timestamp'] = datetime.fromisoformat(row['timestamp'])
                    # Apply date filtering
                    if start_date and row['timestamp'] < start_date:
                        continue
                    if end_date and row['timestamp'] > end_date:
                        continue
                except ValueError:
                    pass
            
            metrics.append(row)
    
    return metrics

# Cost calculation functions
def calculate_llm_cost(model: str, tokens: int, provider: str = "openrouter") -> float:
    """Calculate LLM cost based on model and tokens"""
    cost_per_1k = COST_CONFIG["llm"].get(provider, {}).get(model, COST_CONFIG["llm"][provider]["default"])
    return (tokens / 1000) * cost_per_1k

def calculate_asr_cost(service: str, duration_minutes: float) -> float:
    """Calculate ASR cost based on service and duration"""
    cost_per_minute = COST_CONFIG["asr"].get(service, COST_CONFIG["asr"]["default"])
    return duration_minutes * cost_per_minute

def calculate_tts_cost(service: str, duration_minutes: float, characters: int = 0) -> float:
    """Calculate TTS cost based on service and duration/characters"""
    if service == "elevenlabs" and characters > 0:
        cost_per_1k_chars = COST_CONFIG["tts"][service]
        return (characters / 1000) * cost_per_1k_chars
    else:
        cost_per_minute = COST_CONFIG["tts"].get(service, COST_CONFIG["tts"]["default"])
        return duration_minutes * cost_per_minute

def calculate_storage_cost(service: str, size_mb: float, duration_days: float = 30) -> float:
    """Calculate storage cost based on service, size, and duration"""
    cost_per_mb_per_month = COST_CONFIG["storage"].get(service, COST_CONFIG["storage"]["default"])
    return size_mb * cost_per_mb_per_month * (duration_days / 30)

# SLA compliance functions
def check_sla_compliance(metric: TurnMetric) -> bool:
    """Check if a turn meets SLA requirements"""
    return (
        metric.asr_latency_ms <= SLA_TARGETS["asr_latency_ms"] and
        metric.dm_latency_ms <= SLA_TARGETS["dm_latency_ms"] and
        metric.tts_latency_ms <= SLA_TARGETS["tts_latency_ms"] and
        metric.total_turn_s <= SLA_TARGETS["total_turn_s"] and
        metric.backchannel_s <= SLA_TARGETS["backchannel_s"]
    )

def calculate_sla_compliance(metrics: List[Dict]) -> Dict[str, float]:
    """Calculate SLA compliance percentages"""
    if not metrics:
        return {}
    
    total_turns = len(metrics)
    compliance = {
        "asr_latency": 0,
        "dm_latency": 0,
        "tts_latency": 0,
        "total_turn": 0,
        "backchannel": 0,
        "overall": 0
    }
    
    for metric in metrics:
        if float(metric.get('asr_latency_ms', 0)) <= SLA_TARGETS["asr_latency_ms"]:
            compliance["asr_latency"] += 1
        if float(metric.get('dm_latency_ms', 0)) <= SLA_TARGETS["dm_latency_ms"]:
            compliance["dm_latency"] += 1
        if float(metric.get('tts_latency_ms', 0)) <= SLA_TARGETS["tts_latency_ms"]:
            compliance["tts_latency"] += 1
        if float(metric.get('total_turn_s', 0)) <= SLA_TARGETS["total_turn_s"]:
            compliance["total_turn"] += 1
        if float(metric.get('backchannel_s', 0)) <= SLA_TARGETS["backchannel_s"]:
            compliance["backchannel"] += 1
        
        # Overall compliance (all metrics must pass)
        if all([
            float(metric.get('asr_latency_ms', 0)) <= SLA_TARGETS["asr_latency_ms"],
            float(metric.get('dm_latency_ms', 0)) <= SLA_TARGETS["dm_latency_ms"],
            float(metric.get('tts_latency_ms', 0)) <= SLA_TARGETS["tts_latency_ms"],
            float(metric.get('total_turn_s', 0)) <= SLA_TARGETS["total_turn_s"],
            float(metric.get('backchannel_s', 0)) <= SLA_TARGETS["backchannel_s"]
        ]):
            compliance["overall"] += 1
    
    # Convert to percentages
    for key in compliance:
        compliance[key] = (compliance[key] / total_turns) * 100
    
    return compliance

# API Endpoints
@app.post("/latency")
async def record_latency(request: LatencyRequest, background_tasks: BackgroundTasks):
    """Record latency metric"""
    metric = LatencyMetric(
        service=request.service,
        latency_ms=request.latency_ms,
        timestamp=datetime.now(),
        session_id=request.session_id,
        turn_id=request.turn_id,
        success=request.success,
        error_message=request.error_message
    )
    
    background_tasks.add_task(save_metric_to_csv, metric, "latency")
    
    return {"status": "recorded", "metric": asdict(metric)}

@app.post("/cost")
async def record_cost(request: CostRequest, background_tasks: BackgroundTasks):
    """Record cost metric"""
    metric = CostMetric(
        service=request.service,
        cost_usd=request.cost_usd,
        timestamp=datetime.now(),
        session_id=request.session_id,
        turn_id=request.turn_id,
        units=request.units,
        unit_type=request.unit_type,
        details=request.details or {}
    )
    
    background_tasks.add_task(save_metric_to_csv, metric, "cost")
    
    return {"status": "recorded", "metric": asdict(metric)}

@app.post("/turn")
async def record_turn(request: TurnRequest, background_tasks: BackgroundTasks):
    """Record complete turn metric"""
    turn_metric = TurnMetric(
        session_id=request.session_id,
        turn_id=request.turn_id,
        timestamp=datetime.now(),
        asr_latency_ms=request.asr_latency_ms,
        dm_latency_ms=request.dm_latency_ms,
        tts_latency_ms=request.tts_latency_ms,
        total_turn_s=request.total_turn_s,
        backchannel_s=request.backchannel_s,
        total_cost_usd=request.total_cost_usd,
        sla_compliant=check_sla_compliance(TurnMetric(
            session_id=request.session_id,
            turn_id=request.turn_id,
            timestamp=datetime.now(),
            asr_latency_ms=request.asr_latency_ms,
            dm_latency_ms=request.dm_latency_ms,
            tts_latency_ms=request.tts_latency_ms,
            total_turn_s=request.total_turn_s,
            backchannel_s=request.backchannel_s,
            total_cost_usd=request.total_cost_usd,
            sla_compliant=True,
            services_used=request.services_used
        )),
        services_used=request.services_used
    )
    
    background_tasks.add_task(save_metric_to_csv, turn_metric, "turns")
    
    return {"status": "recorded", "metric": asdict(turn_metric)}

@app.post("/cost-analysis", response_model=CostAnalysisResponse)
async def analyze_costs(request: CostAnalysisRequest):
    """Analyze costs and provide recommendations"""
    # Load turn metrics
    turns = load_metrics_from_csv("turns", request.start_date, request.end_date)
    
    if request.session_id:
        turns = [t for t in turns if t.get('session_id') == request.session_id]
    
    if not turns:
        return CostAnalysisResponse(
            total_cost_usd=0.0,
            total_turns=0,
            avg_cost_per_turn=0.0,
            cost_breakdown={},
            sla_compliance={},
            hr_salary_comparison={},
            recommendations=[]
        )
    
    # Calculate totals
    total_cost = sum(float(t.get('total_cost_usd', 0)) for t in turns)
    total_turns = len(turns)
    avg_cost_per_turn = total_cost / total_turns if total_turns > 0 else 0
    
    # Cost breakdown by service
    cost_breakdown = {}
    for turn in turns:
        services = turn.get('services_used', '').split(',')
        for service in services:
            service = service.strip()
            if service:
                cost_breakdown[service] = cost_breakdown.get(service, 0) + float(turn.get('total_cost_usd', 0)) / len(services)
    
    # SLA compliance
    sla_compliance = calculate_sla_compliance(turns)
    
    # HR salary comparison (assuming $50/hour HR rate)
    hr_hourly_rate = 50.0
    avg_turn_duration_minutes = sum(float(t.get('total_turn_s', 0)) for t in turns) / (total_turns * 60) if total_turns > 0 else 0
    hr_cost_per_turn = (avg_turn_duration_minutes / 60) * hr_hourly_rate
    
    hr_salary_comparison = {
        "hr_hourly_rate_usd": hr_hourly_rate,
        "avg_turn_duration_minutes": avg_turn_duration_minutes,
        "hr_cost_per_turn_usd": hr_cost_per_turn,
        "ai_cost_per_turn_usd": avg_cost_per_turn,
        "cost_savings_per_turn_usd": hr_cost_per_turn - avg_cost_per_turn,
        "cost_savings_percentage": ((hr_cost_per_turn - avg_cost_per_turn) / hr_cost_per_turn * 100) if hr_cost_per_turn > 0 else 0
    }
    
    # Generate recommendations
    recommendations = []
    
    if avg_cost_per_turn > hr_cost_per_turn:
        recommendations.append("AI cost exceeds HR cost - consider optimizing model usage")
    
    if sla_compliance.get("overall", 0) < 90:
        recommendations.append("SLA compliance below 90% - investigate performance bottlenecks")
    
    if sla_compliance.get("asr_latency", 0) < 95:
        recommendations.append("ASR latency issues - consider faster models or local processing")
    
    if sla_compliance.get("dm_latency", 0) < 95:
        recommendations.append("Dialog Manager latency issues - optimize response generation")
    
    if sla_compliance.get("tts_latency", 0) < 95:
        recommendations.append("TTS latency issues - consider local TTS or caching")
    
    if total_cost > 100:  # Arbitrary threshold
        recommendations.append("High total costs - review usage patterns and optimize")
    
    return CostAnalysisResponse(
        total_cost_usd=total_cost,
        total_turns=total_turns,
        avg_cost_per_turn=avg_cost_per_turn,
        cost_breakdown=cost_breakdown,
        sla_compliance=sla_compliance,
        hr_salary_comparison=hr_salary_comparison,
        recommendations=recommendations
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "metrics",
        "sla_targets": SLA_TARGETS,
        "cost_config": COST_CONFIG,
        "storage_path": str(METRICS_STORAGE_PATH),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/sla-targets")
async def get_sla_targets():
    """Get SLA targets"""
    return {
        "targets": SLA_TARGETS,
        "description": {
            "asr_latency_ms": "ASR processing time in milliseconds",
            "dm_latency_ms": "Dialog Manager response time in milliseconds", 
            "tts_latency_ms": "TTS generation time in milliseconds",
            "total_turn_s": "Total turn time in seconds",
            "backchannel_s": "Backchannel response time in seconds"
        }
    }

@app.get("/cost-config")
async def get_cost_config():
    """Get cost configuration"""
    return {
        "config": COST_CONFIG,
        "description": "Cost per unit for different services and providers"
    }

@app.get("/metrics/summary")
async def get_metrics_summary():
    """Get summary of recent metrics"""
    # Load recent metrics (last 24 hours)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=1)
    
    turns = load_metrics_from_csv("turns", start_date, end_date)
    latency = load_metrics_from_csv("latency", start_date, end_date)
    costs = load_metrics_from_csv("cost", start_date, end_date)
    
    return {
        "period": f"{start_date.isoformat()} to {end_date.isoformat()}",
        "turns": len(turns),
        "latency_measurements": len(latency),
        "cost_measurements": len(costs),
        "sla_compliance": calculate_sla_compliance(turns),
        "total_cost_usd": sum(float(t.get('total_cost_usd', 0)) for t in turns)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
