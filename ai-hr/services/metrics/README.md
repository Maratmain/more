# AI-HR Metrics Service

Comprehensive metrics tracking and cost analysis for the AI-HR system. Monitors latency, costs, and SLA compliance across all services.

## Features

- **Latency Tracking**: Monitor ASR, DM, TTS, and total turn times
- **Cost Analysis**: Track LLM, ASR, TTS, and storage costs
- **SLA Monitoring**: Real-time compliance tracking with configurable targets
- **ROI Analysis**: Compare AI costs vs HR salary costs
- **Cost Optimization**: Automated recommendations for cost reduction
- **Real-time Reporting**: Live metrics dashboard and alerts

## SLA Targets

| Metric | Target | Description |
|--------|--------|-------------|
| ASR Latency | ≤ 2 seconds | Speech-to-text processing time |
| DM Latency | ≤ 1 second | Dialog Manager response time |
| TTS Latency | ≤ 1.5 seconds | Text-to-speech generation time |
| Total Turn | ≤ 5 seconds | Complete turn processing time |
| Backchannel | ≤ 2 seconds | Quick response time |

## Cost Configuration

### LLM Costs (per 1K tokens)
- **OpenRouter**: $0.003 (Claude 3.5 Sonnet), $0.03 (GPT-4)
- **OpenAI**: $0.03 (GPT-4), $0.002 (GPT-3.5 Turbo)
- **Default**: $0.01 per 1K tokens

### ASR Costs (per minute)
- **Whisper**: $0.006 per minute
- **Faster-Whisper**: $0.003 per minute (local)
- **Default**: $0.005 per minute

### TTS Costs
- **Piper**: $0.001 per minute (local)
- **ElevenLabs**: $0.18 per 1K characters
- **Default**: $0.01 per minute

### Storage Costs
- **Qdrant**: $0.0001 per MB per month
- **Embeddings**: $0.00005 per embedding
- **Default**: $0.0001 per MB per month

## API Endpoints

### Record Metrics

#### `POST /latency`
Record latency metric for a service.

```json
{
  "service": "asr",
  "latency_ms": 1500,
  "session_id": "session_123",
  "turn_id": "turn_456",
  "success": true,
  "error_message": null
}
```

#### `POST /cost`
Record cost metric for a service.

```json
{
  "service": "llm",
  "cost_usd": 0.05,
  "session_id": "session_123",
  "turn_id": "turn_456",
  "units": 1000,
  "unit_type": "tokens",
  "details": {
    "model": "claude-3.5-sonnet",
    "provider": "openrouter"
  }
}
```

#### `POST /turn`
Record complete turn metric.

```json
{
  "session_id": "session_123",
  "turn_id": "turn_456",
  "asr_latency_ms": 1500,
  "dm_latency_ms": 800,
  "tts_latency_ms": 1200,
  "total_turn_s": 4.5,
  "backchannel_s": 1.8,
  "total_cost_usd": 0.08,
  "services_used": ["asr", "dm", "tts"]
}
```

### Analysis & Reporting

#### `POST /cost-analysis`
Get comprehensive cost analysis.

```json
{
  "session_id": "session_123",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "include_breakdown": true
}
```

**Response:**
```json
{
  "total_cost_usd": 25.50,
  "total_turns": 150,
  "avg_cost_per_turn": 0.17,
  "cost_breakdown": {
    "llm": 18.50,
    "asr": 4.20,
    "tts": 2.80
  },
  "sla_compliance": {
    "asr_latency": 95.5,
    "dm_latency": 98.2,
    "tts_latency": 92.1,
    "total_turn": 94.8,
    "backchannel": 96.3,
    "overall": 91.2
  },
  "hr_salary_comparison": {
    "hr_hourly_rate_usd": 50.0,
    "avg_turn_duration_minutes": 4.2,
    "hr_cost_per_turn_usd": 3.50,
    "ai_cost_per_turn_usd": 0.17,
    "cost_savings_per_turn_usd": 3.33,
    "cost_savings_percentage": 95.1
  },
  "recommendations": [
    "✅ Excellent cost savings - consider scaling up",
    "🔧 SLA compliance below 90% - investigate performance issues"
  ]
}
```

#### `GET /metrics/summary`
Get summary of recent metrics (last 24 hours).

#### `GET /sla-targets`
Get current SLA targets.

#### `GET /cost-config`
Get cost configuration.

#### `GET /health`
Health check endpoint.

## Client Library

### Basic Usage

```python
from metrics.client import record_latency, record_cost, time_operation

# Record latency
record_latency("asr", 1500, "session_123", "turn_456")

# Record cost
record_cost("llm", 0.05, "session_123", "turn_456", 
           units=1000, unit_type="tokens")

# Time an operation
with time_operation("asr", "session_123", "turn_456"):
    result = process_audio(audio_data)
```

### Service-Specific Metrics

```python
from metrics.client import asr_metrics, dm_metrics, tts_metrics

# ASR service
with asr_metrics.time_operation(session_id, turn_id):
    transcript = process_audio(audio_data)

# Dialog Manager
with dm_metrics.time_operation(session_id, turn_id):
    response = generate_response(transcript)

# TTS service
with tts_metrics.time_operation(session_id, turn_id):
    audio = generate_speech(response)
```

### Decorators

```python
from metrics.client import time_function, time_async_function

# Sync function
@time_function("asr", session_id, turn_id)
def process_audio(audio_data):
    return transcript

# Async function
@time_async_function("dm", session_id, turn_id)
async def generate_response(transcript):
    return response
```

## Cost Analysis Script

### Usage

```bash
# Basic cost analysis
python scripts/cost_check.py

# Analyze specific session
python scripts/cost_check.py --session-id session_123

# Analyze date range
python scripts/cost_check.py --start-date 2024-01-01 --end-date 2024-01-31

# Custom HR salary rate
python scripts/cost_check.py --hr-salary 75.0

# Save report to file
python scripts/cost_check.py --output cost_report.json

# Quiet mode (JSON only)
python scripts/cost_check.py --quiet
```

### Sample Output

```
================================================================================
🤖 AI-HR COST ANALYSIS REPORT
================================================================================
Generated: 2024-01-15 14:30:25

📊 SUMMARY
----------------------------------------
Total Turns: 150
Total AI Cost: $25.50
Average Cost per Turn: $0.1700

💰 ROI ANALYSIS
----------------------------------------
HR Salary Rate: $50.00/hour
Average Turn Duration: 4.2 minutes
AI Cost per Turn: $0.1700
HR Cost per Turn: $3.50
Savings per Turn: $3.33
Total Savings: $499.50
Savings Percentage: 95.1%
ROI: 1958.8%
Break-even Point: 1 turns

💸 COST BREAKDOWN
----------------------------------------
LLM            : $18.50 (72.5%)
ASR            : $4.20 (16.5%)
TTS            : $2.80 (11.0%)

⏱️ SLA COMPLIANCE
----------------------------------------
ASR Latency    :  95.5% ✅ (target: 2000)
DM Latency     :  98.2% ✅ (target: 1000)
TTS Latency    :  92.1% ⚠️ (target: 1500)
Total Turn     :  94.8% ✅ (target: 5.0)
Backchannel    :  96.3% ✅ (target: 2.0)
Overall        :  91.2% ⚠️ (target: All metrics)

💡 RECOMMENDATIONS
----------------------------------------
1. ✅ Excellent cost savings - consider scaling up
2. 🔧 SLA compliance below 90% - investigate performance issues
3. 🔊 TTS latency issues - consider local TTS or caching

📈 COST EFFICIENCY RATING
----------------------------------------
Rating: 🟢 EXCELLENT
Savings: 95.1%

================================================================================
```

## Integration Examples

### ASR Service Integration

```python
# In your ASR service
from metrics.client import asr_metrics, time_operation

class ASRService:
    def process_audio(self, audio_data, session_id, turn_id):
        with asr_metrics.time_operation(session_id, turn_id):
            # Your ASR processing code
            transcript = self.whisper_model.transcribe(audio_data)
            
            # Record cost if using paid service
            if self.using_paid_service:
                cost = self.calculate_cost(len(audio_data))
                asr_metrics.record_cost(
                    cost_usd=cost,
                    session_id=session_id,
                    turn_id=turn_id,
                    units=len(audio_data),
                    unit_type="seconds",
                    details={"model": "whisper", "provider": "openai"}
                )
            
            return transcript
```

### Dialog Manager Integration

```python
# In your Dialog Manager
from metrics.client import dm_metrics, time_operation

class DialogManager:
    def generate_response(self, transcript, context, session_id, turn_id):
        with dm_metrics.time_operation(session_id, turn_id):
            # Your DM processing code
            response = self.llm_client.generate(transcript, context)
            
            # Record LLM cost
            if self.llm_client.cost > 0:
                dm_metrics.record_cost(
                    cost_usd=self.llm_client.cost,
                    session_id=session_id,
                    turn_id=turn_id,
                    units=self.llm_client.tokens_used,
                    unit_type="tokens",
                    details={
                        "model": self.llm_client.model,
                        "provider": self.llm_client.provider
                    }
                )
            
            return response
```

### TTS Service Integration

```python
# In your TTS service
from metrics.client import tts_metrics, time_operation

class TTSService:
    def generate_speech(self, text, session_id, turn_id):
        with tts_metrics.time_operation(session_id, turn_id):
            # Your TTS processing code
            audio = self.tts_engine.synthesize(text)
            
            # Record cost
            cost = self.calculate_cost(len(text))
            tts_metrics.record_cost(
                cost_usd=cost,
                session_id=session_id,
                turn_id=turn_id,
                units=len(text),
                unit_type="characters",
                details={"service": "piper", "voice": self.voice_name}
            )
            
            return audio
```

## Docker Deployment

```bash
# Build and run metrics service
cd services/metrics
docker build -t ai-hr-metrics .
docker run -d -p 8010:8010 --name metrics ai-hr-metrics

# Or use docker-compose
docker-compose up metrics
```

## Environment Variables

```bash
# Metrics service configuration
METRICS_SERVICE_URL=http://localhost:8010
METRICS_STORAGE_PATH=/app/data

# Cost configuration (optional overrides)
LLM_COST_OPENROUTER_CLAUDE=0.003
LLM_COST_OPENAI_GPT4=0.03
ASR_COST_WHISPER=0.006
TTS_COST_PIPER=0.001
STORAGE_COST_QDRANT=0.0001

# SLA targets (optional overrides)
SLA_ASR_LATENCY_MS=2000
SLA_DM_LATENCY_MS=1000
SLA_TTS_LATENCY_MS=1500
SLA_TOTAL_TURN_S=5.0
SLA_BACKCHANNEL_S=2.0
```

## Monitoring & Alerts

### SLA Monitoring
- Real-time compliance tracking
- Automatic alerts for SLA violations
- Performance trend analysis

### Cost Monitoring
- Daily/weekly/monthly cost reports
- Cost per turn analysis
- ROI tracking vs HR costs

### Performance Monitoring
- Latency distribution analysis
- Service performance comparison
- Bottleneck identification

## Data Storage

Metrics are stored in CSV files in the `data/` directory:
- `latency.csv` - Latency measurements
- `cost.csv` - Cost measurements  
- `turns.csv` - Complete turn metrics

## Troubleshooting

### Common Issues

1. **Metrics not recording**: Check metrics service URL and connectivity
2. **High latency**: Review service performance and network conditions
3. **Cost spikes**: Analyze usage patterns and optimize model usage
4. **SLA violations**: Investigate service bottlenecks and scaling needs

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for metrics client
logger = logging.getLogger('metrics.client')
logger.setLevel(logging.DEBUG)
```

## Contributing

1. Add new metric types in `main.py`
2. Update cost configuration as needed
3. Add new SLA targets for new services
4. Extend client library for new use cases
5. Update documentation and examples
