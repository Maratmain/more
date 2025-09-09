# AI-HR LLM Services Documentation

Comprehensive guide to local LLM services for the AI-HR system, including llama.cpp and vLLM integration.

## Overview

The AI-HR system supports multiple LLM backends for flexible deployment:

1. **llama.cpp** - Local inference with Qwen2.5-7B-Instruct (recommended)
2. **vLLM** - GPU-accelerated inference with Meta-Llama-3.1-8B-Instruct
3. **OpenRouter** - Cloud API with multiple models
4. **OpenAI-Compatible** - Local or cloud OpenAI-compatible APIs

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Dialog        │    │   LLM Gateway   │    │   Local LLM     │
│   Manager       │───▶│   Service       │───▶│   Services      │
│   (DM)          │    │   (llm-gw)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   OpenRouter    │    │   llama.cpp     │
                       │   (Cloud API)   │    │   (Local)       │
                       └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │   vLLM          │
                                               │   (GPU)         │
                                               └─────────────────┘
```

## Service Configuration

### Port Mapping

| Service | Port | Description |
|---------|------|-------------|
| llm-local | 8080 | llama.cpp server |
| llm-vllm | 8009 | vLLM server |
| llm-gw | 8008 | LLM Gateway |
| dm | 8004 | Dialog Manager |

### Environment Variables

```bash
# LLM Provider Selection
LLM_PROVIDER=llama.cpp                    # llama.cpp | openai_compatible | openrouter
LLM_ENGINE=llama.cpp                      # llama.cpp | openai_compatible

# Local LLM Configuration
LLM_BASE_URL=http://llm-local:8080/v1     # llama.cpp service URL
LLM_MODEL=qwen2.5-7b-instruct            # Model name

# vLLM Configuration
VLLM_BASE_URL=http://llm-vllm:8000/v1     # vLLM service URL
VLLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct

# OpenRouter Configuration
OPENROUTER_API_KEY=your_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet:beta

# OpenAI-Compatible Configuration
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_KEY=ollama
OPENAI_MODEL=gpt-4
```

## llama.cpp Service (llm-local)

### Features

- **Qwen2.5-7B-Instruct**: Multilingual model with excellent Russian support
- **GGUF Quantization**: Efficient model formats (Q4_K_M, Q5_K_M, Q8_0, F16)
- **GPU Acceleration**: CUDA and OpenCL support
- **JSON Schema Enforcement**: Structured output with grammar constraints
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API
- **Streaming Support**: Real-time response streaming

### Model Options

| Model | Size | Quality | Speed | Memory | Use Case |
|-------|------|---------|-------|--------|----------|
| Q4_K_M | ~4.1GB | Good | Fast | Low | Development/Testing |
| Q5_K_M | ~5.1GB | Better | Medium | Medium | **Recommended** |
| Q8_0 | ~8.1GB | Excellent | Slower | High | Production |
| F16 | ~13.4GB | Best | Slowest | Highest | Maximum Quality |

### Configuration

```bash
# Model Configuration
LLM_MODEL=Qwen2.5-7B-Instruct-Q5_K_M.gguf
LLM_MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf

# Performance Settings
LLM_CTX=8192                    # Context window size
LLM_THREADS=8                   # CPU threads
LLM_GPU_LAYERS=auto            # GPU layers (auto, -1, 0, or number)
LLM_PARALLEL=4                 # Parallel requests

# JSON Schema Enforcement
LLM_JSON_SCHEMA_ENFORCE=true   # Enable JSON grammar
```

### Usage Examples

#### Basic Chat Completion

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct",
    "messages": [
      {"role": "system", "content": "Ты интервьюер. Отвечай коротко."},
      {"role": "user", "content": "Расскажи о своем опыте работы с Python."}
    ],
    "stream": false,
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

#### JSON Schema Enforcement

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct",
    "messages": [
      {"role": "system", "content": "Ты интервьюер. Верни JSON: {reply, next_node_id, scoring_update:{block,delta,score}, red_flags[]}."},
      {"role": "user", "content": "node:..., transcript:..., current_scores:..., role_profile:..."}
    ],
    "stream": false,
    "temperature": 0.1,
    "response_format": {"type": "json_object"}
  }'
```

#### Streaming Response

```bash
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct",
    "messages": [
      {"role": "user", "content": "Расскажи о своем опыте работы с Python."}
    ],
    "stream": true,
    "temperature": 0.7
  }'
```

## vLLM Service (llm-vllm)

### Features

- **Meta-Llama-3.1-8B-Instruct**: High-quality multilingual model
- **GPU Acceleration**: Optimized for NVIDIA GPUs
- **High Throughput**: Parallel request processing
- **OpenAI-Compatible API**: Standard OpenAI API format
- **Memory Efficient**: Optimized GPU memory usage

### Configuration

```bash
# vLLM Configuration
VLLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
VLLM_MAX_MODEL_LEN=8192
VLLM_GPU_MEMORY_UTILIZATION=0.9
VLLM_MAX_NUM_SEQS=16
```

### Usage Examples

#### Basic Chat Completion

```bash
curl -X POST http://localhost:8009/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "messages": [
      {"role": "system", "content": "Ты интервьюер. Отвечай коротко."},
      {"role": "user", "content": "Расскажи о своем опыте работы с Python."}
    ],
    "stream": false,
    "temperature": 0.7,
    "max_tokens": 512
  }'
```

#### JSON Schema Enforcement

```bash
curl -X POST http://localhost:8009/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "messages": [
      {"role": "system", "content": "Ты интервьюер. Верни JSON: {reply, next_node_id, scoring_update:{block,delta,score}, red_flags[]}."},
      {"role": "user", "content": "node:..., transcript:..., current_scores:..., role_profile:..."}
    ],
    "stream": false,
    "temperature": 0.1,
    "response_format": {"type": "json_object"}
  }'
```

## Dialog Manager Integration

### LLM Response Generation

The Dialog Manager automatically integrates with configured LLM services:

```python
def generate_llm_response(node, transcript, scores, role_profile):
    """Generate LLM response for interview node"""
    
    # Create system prompt
    system_prompt = f"""Ты интервьюер для роли {role_profile or 'общей'}. 
    Отвечай коротко и структурированно. 
    Верни JSON: {{"reply": "краткий ответ", "next_node_id": "следующий_узел", "scoring_update": {{"block": "категория", "delta": 0.1, "score": 0.8}}, "red_flags": []}}."""
    
    # Create user prompt
    user_prompt = f"""node: {node.category}, transcript: {transcript}, current_scores: {scores}, role_profile: {role_profile}"""
    
    # Call LLM with JSON schema enforcement
    llm_response = call_local_llm(system_prompt, user_prompt, stream=False)
    
    return llm_response
```

### Response Format

The LLM returns structured JSON responses:

```json
{
  "reply": "Понял кейс, уточните метрику FPR/TPR.",
  "next_node_id": "afr_l2_cases",
  "scoring_update": {
    "block": "AntiFraud_Rules",
    "delta": 0.7,
    "score": 0.8
  },
  "red_flags": []
}
```

### Fallback Mechanism

If LLM services are unavailable, the Dialog Manager falls back to heuristic scoring:

```python
# Try LLM-based response first
if LLM_ENGINE in ["llama.cpp", "openai_compatible"]:
    llm_response = generate_llm_response(...)
    if "error" not in llm_response:
        return llm_response

# Fallback to heuristic scoring
score = heuristic_score(transcript, criteria)
confidence = calculate_confidence(transcript, criteria, score)
reply_text = get_role_specific_response(role_profile, score, confidence)
```

## Performance Comparison

### Benchmarks

| Service | Model | Hardware | Tokens/sec | Memory | Latency |
|---------|-------|----------|------------|--------|---------|
| llama.cpp | Q5_K_M | RTX 4090 | ~150 | 8GB | ~50ms |
| llama.cpp | Q5_K_M | RTX 3080 | ~100 | 8GB | ~80ms |
| llama.cpp | Q4_K_M | RTX 3060 | ~60 | 6GB | ~120ms |
| llama.cpp | Q5_K_M | CPU (16 cores) | ~20 | 8GB | ~300ms |
| vLLM | Llama-3.1-8B | RTX 4090 | ~200 | 12GB | ~40ms |
| vLLM | Llama-3.1-8B | RTX 3080 | ~120 | 12GB | ~70ms |

### Cost Analysis

| Service | Setup Cost | Running Cost | Quality | Speed |
|---------|------------|--------------|---------|-------|
| llama.cpp | Free | Free | High | Fast |
| vLLM | Free | Free | High | Very Fast |
| OpenRouter | Free | $0.003-0.03/1K tokens | Very High | Fast |
| OpenAI | Free | $0.002-0.03/1K tokens | Very High | Fast |

## Deployment Options

### Option 1: Local llama.cpp (Recommended)

```yaml
# docker-compose.yml
services:
  llm-local:
    build: ./services/llm-local
    ports: ["8080:8080"]
    env_file: ./services/llm-local/env.example
    volumes:
      - llm_models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: ["gpu"]
```

**Pros:**
- Free to run
- High performance
- Multilingual support
- JSON schema enforcement
- Low latency

**Cons:**
- Requires local hardware
- Model download time
- GPU memory requirements

### Option 2: vLLM (GPU-optimized)

```yaml
# docker-compose.yml
services:
  llm-vllm:
    image: vllm/vllm-openai:latest
    command: [
      "--model", "meta-llama/Meta-Llama-3.1-8B-Instruct",
      "--max-model-len", "8192",
      "--gpu-memory-utilization", "0.9",
      "--max-num-seqs", "16"
    ]
    ports: ["8009:8000"]
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: ["gpu"]
```

**Pros:**
- Highest throughput
- Optimized for GPUs
- OpenAI-compatible
- Parallel processing

**Cons:**
- Requires powerful GPU
- Higher memory usage
- More complex setup

### Option 3: OpenRouter (Cloud)

```bash
# Environment
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_api_key
OPENROUTER_MODEL=anthropic/claude-3.5-sonnet:beta
```

**Pros:**
- No local hardware required
- Access to premium models
- High quality responses
- Easy setup

**Cons:**
- Ongoing costs
- Internet dependency
- Data privacy concerns

## Troubleshooting

### Common Issues

#### 1. Model Download Fails

```bash
# Check network connectivity
curl -I https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf

# Manual download
wget -O models/qwen2.5-7b-instruct-q5_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf
```

#### 2. GPU Not Detected

```bash
# Check NVIDIA GPU
nvidia-smi

# Check OpenCL
clinfo

# Force CPU mode
LLM_GPU_LAYERS=0
```

#### 3. Out of Memory

```bash
# Reduce context size
LLM_CTX=4096

# Use smaller model
LLM_MODEL=Qwen2.5-7B-Instruct-Q4_K_M.gguf

# Reduce parallel requests
LLM_PARALLEL=2
```

#### 4. LLM Service Unavailable

```bash
# Check service status
curl http://localhost:8080/health

# Check logs
docker logs llm-local

# Restart service
docker-compose restart llm-local
```

#### 5. JSON Schema Issues

```bash
# Verify JSON schema enforcement
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct",
    "messages": [{"role": "user", "content": "Return JSON: {test: true}"}],
    "response_format": {"type": "json_object"}
  }'
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check LLM configuration
print(f"LLM Engine: {LLM_ENGINE}")
print(f"LLM Provider: {LLM_PROVIDER}")
print(f"LLM Base URL: {LLM_BASE_URL}")
print(f"LLM Model: {LLM_MODEL}")
```

## Best Practices

### 1. Model Selection

- **Development**: Use Q4_K_M for fast iteration
- **Production**: Use Q5_K_M for balanced performance
- **High Quality**: Use Q8_0 or F16 for maximum quality

### 2. Performance Optimization

- **GPU Memory**: Use `LLM_GPU_LAYERS=auto` for automatic detection
- **Context Size**: Reduce `LLM_CTX` for lower memory usage
- **Parallel Requests**: Increase `LLM_PARALLEL` for higher throughput

### 3. Cost Optimization

- **Local Models**: Use llama.cpp or vLLM for zero ongoing costs
- **Cloud Models**: Use OpenRouter for premium quality when needed
- **Hybrid Approach**: Use local for development, cloud for production

### 4. Security

- **Local Models**: Keep sensitive data on-premises
- **Cloud Models**: Use for non-sensitive applications
- **API Keys**: Store securely in environment variables

### 5. Monitoring

- **Health Checks**: Monitor service availability
- **Performance**: Track response times and throughput
- **Costs**: Monitor usage and costs for cloud services

## References

- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [vLLM Documentation](https://docs.vllm.ai/)
- [Qwen2.5-7B-Instruct Hugging Face](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [OpenRouter API](https://openrouter.ai/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
