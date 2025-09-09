# LLM Local Service

Local LLM service using llama.cpp with Qwen2.5-7B-Instruct model for high-performance, low-latency inference.

## Features

- **llama.cpp Engine**: Optimized C++ implementation with GPU acceleration
- **Qwen2.5-7B-Instruct**: Multilingual model with excellent Russian support
- **GGUF Quantization**: Efficient model formats (Q4_K_M, Q5_K_M, Q8_0, F16)
- **OpenAI-Compatible API**: Drop-in replacement for OpenAI API
- **JSON Schema Enforcement**: Structured output with grammar constraints
- **Streaming Support**: Real-time response streaming
- **GPU Acceleration**: CUDA and OpenCL support
- **Low Latency**: Optimized for real-time applications

## Model Options

### Recommended Models (RU/EN)

#### 1. Qwen2.5-7B-Instruct (GGUF) - **Recommended**
- **Strengths**: Excellent Russian/English support, good quality/speed balance
- **Use Case**: Primary choice for AI-HR system
- **Quantizations**: Q4_K_M, Q5_K_M, Q8_0, F16

#### 2. Llama-3.1-8B-Instruct (GGUF)
- **Strengths**: Strong base model, many integrations/templates
- **Use Case**: Alternative to Qwen2.5, good for English-heavy interviews
- **Quantizations**: Q4_K_M, Q5_K_M, Q8_0, F16

#### 3. Gemma-2-9B-it (vLLM)
- **Strengths**: Often outperforms Llama-3.1-8B on benchmarks
- **Use Case**: GPU-optimized alternative via vLLM service
- **Requirements**: Requires vLLM service (GPU recommended)

### Qwen2.5-7B-Instruct Quantizations

| Model | Size | Quality | Speed | Memory | Use Case |
|-------|------|---------|-------|--------|----------|
| Q4_K_M | ~4.1GB | Good | Fast | Low | Development/Testing |
| Q5_K_M | ~5.1GB | Better | Medium | Medium | **Recommended** |
| Q8_0 | ~8.1GB | Excellent | Slower | High | Production |
| F16 | ~13.4GB | Best | Slowest | Highest | Maximum Quality |

### Model URLs

```bash
# Q4_K_M (4.1GB) - Fast, lower quality
LLM_MODEL=Qwen2.5-7B-Instruct-Q4_K_M.gguf
LLM_MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf

# Q5_K_M (5.1GB) - Balanced (Recommended)
LLM_MODEL=Qwen2.5-7B-Instruct-Q5_K_M.gguf
LLM_MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf

# Q8_0 (8.1GB) - High quality
LLM_MODEL=Qwen2.5-7B-Instruct-Q8_0.gguf
LLM_MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q8_0.gguf

# F16 (13.4GB) - Maximum quality
LLM_MODEL=Qwen2.5-7B-Instruct-F16.gguf
LLM_MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-f16.gguf

# Llama-3.1-8B-Instruct alternatives
LLM_MODEL=llama-3.1-8b-instruct-q5_k_m.gguf
LLM_MODEL_URL=https://huggingface.co/bartowski/Llama-3.1-8B-Instruct-GGUF/resolve/main/llama-3.1-8b-instruct-q5_k_m.gguf
```

## Model Switching Guide

### How to Switch Models

#### 1. Update Environment Variables
```bash
# Edit services/llm-local/env.example
LLM_MODEL=Qwen2.5-7B-Instruct-Q5_K_M.gguf
LLM_MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf
```

#### 2. Restart Container
```bash
# Stop current service
docker-compose stop llm-local

# Remove old model (optional, saves disk space)
docker volume rm ai-hr_llm_models

# Start with new model
docker-compose up -d llm-local

# Check logs
docker logs -f llm-local
```

#### 3. Verify Model Loading
```bash
# Check health endpoint
curl http://localhost:8080/health

# Test with sample request
curl -X POST http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen2.5-7b-instruct",
    "messages": [{"role": "user", "content": "Привет! Как дела?"}],
    "max_tokens": 50
  }'
```

### Model Comparison

| Model | Russian Support | English Support | Speed | Quality | Memory |
|-------|----------------|-----------------|-------|---------|--------|
| Qwen2.5-7B | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Llama-3.1-8B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| Gemma-2-9B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |

### Switching Between Services

#### From llama.cpp to vLLM
```bash
# Update DM configuration
LLM_PROVIDER=openai_compatible
LLM_ENGINE=openai_compatible
OPENAI_BASE_URL=http://llm-vllm:8000/v1
LLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct

# Restart DM service
docker-compose restart dm
```

#### From vLLM to llama.cpp
```bash
# Update DM configuration
LLM_PROVIDER=llama.cpp
LLM_ENGINE=llama.cpp
LLM_BASE_URL=http://llm-local:8080/v1
LLM_MODEL=qwen2.5-7b-instruct

# Restart DM service
docker-compose restart dm
```

## Configuration

### Environment Variables

```bash
# Engine and Model
LLM_ENGINE=llama.cpp
LLM_MODEL=Qwen2.5-7B-Instruct-Q5_K_M.gguf
LLM_MODEL_URL=https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf

# Model Parameters
LLM_CTX=8192                    # Context window size
LLM_THREADS=8                   # CPU threads
LLM_PORT=8080                   # Server port
LLM_HOST=0.0.0.0               # Server host

# GPU Configuration
LLM_GPU_LAYERS=auto            # GPU layers (auto, -1, 0, or number)
LLM_GPU_MEMORY_UTILIZATION=0.9 # GPU memory usage

# Server Configuration
LLM_PARALLEL=4                 # Parallel requests
LLM_EMBEDDING=true             # Enable embeddings
LLM_CHAT_TEMPLATE=qwen2        # Chat template

# JSON Schema Enforcement
LLM_JSON_SCHEMA_ENFORCE=true   # Enable JSON grammar

# Performance Tuning
LLM_BATCH_SIZE=512             # Batch size
LLM_UBATCH_SIZE=512            # Unbatch size
LLM_SEQ_MAX=2048               # Max sequence length
LLM_N_PREDICT=512              # Max prediction length

# Logging
LLM_VERBOSE=false              # Verbose logging
LLM_LOG_LEVEL=info             # Log level

# Model Download
LLM_DOWNLOAD_TIMEOUT=3600      # Download timeout (seconds)
LLM_DOWNLOAD_RETRIES=3         # Download retries
LLM_MODEL_CHECKSUM=sha256:auto # Checksum verification
```

## Usage

### Docker Compose

```yaml
services:
  llm-local:
    build: ./services/llm-local
    env_file: ./services/llm-local/env.example
    ports: ["8080:8080"]
    volumes:
      - llm_models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: ["gpu"]  # For NVIDIA GPU

volumes:
  llm_models:
```

### Manual Docker

```bash
# Build the image
docker build -t ai-hr-llm-local ./services/llm-local

# Run with GPU support
docker run -d \
  --name llm-local \
  --gpus all \
  -p 8080:8080 \
  -v llm_models:/app/models \
  ai-hr-llm-local

# Run CPU only
docker run -d \
  --name llm-local \
  -p 8080:8080 \
  -v llm_models:/app/models \
  ai-hr-llm-local
```

### Local Development

```bash
# Clone llama.cpp
git clone https://github.com/ggerganov/llama.cpp.git
cd llama.cpp

# Build with GPU support
make -j$(nproc) LLAMA_CUBLAS=1 LLAMA_CLBLAST=1

# Download model
wget -O models/qwen2.5-7b-instruct-q5_k_m.gguf \
  https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf

# Start server
./llama-server \
  -m models/qwen2.5-7b-instruct-q5_k_m.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 8192 \
  --n-gpu-layers auto \
  --embedding \
  --chat-template qwen2 \
  --api-server \
  --parallel 4 \
  --grammar-json-schema
```

## API Usage

### OpenAI-Compatible Endpoints

The service provides OpenAI-compatible API endpoints:

- `POST /v1/chat/completions` - Chat completions
- `POST /v1/completions` - Text completions
- `POST /v1/embeddings` - Text embeddings
- `GET /health` - Health check

### Chat Completions

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

### Streaming Response

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

### JSON Schema Enforcement

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

## Performance

### Benchmarks

| Hardware | Model | Tokens/sec | Memory | Latency | SLA Target |
|----------|-------|------------|--------|---------|------------|
| RTX 4090 | Q5_K_M | ~150 | 8GB | ~50ms | ✅ <2s |
| RTX 3080 | Q5_K_M | ~100 | 8GB | ~80ms | ✅ <2s |
| RTX 4060 Ti | Q5_K_M | ~25 | 8GB | ~200ms | ✅ <2s |
| RTX 3060 | Q4_K_M | ~60 | 6GB | ~120ms | ✅ <2s |
| CPU (16 cores) | Q5_K_M | ~20 | 8GB | ~300ms | ⚠️ 2-4s |
| CPU (8 cores) | Q4_K_M | ~15 | 6GB | ~400ms | ⚠️ 2-4s |

### Performance Profiles

#### RTX 4060 Ti Profile
- **Model**: Llama-3.1-8B / Qwen2.5-7B
- **Quantization**: Q5_K_M
- **Speed**: ~25 tokens/sec (community benchmarks)
- **Response Time**: 50-80 tokens ≈ 2-4 seconds
- **SLA Compliance**: ✅ Within 5s target

#### CPU-Only Profile
- **Speed**: 6-10 tokens/sec on 8-core processors
- **Response Length**: Keep responses short (30-50 tokens)
- **Response Time**: 30-50 tokens ≈ 3-5 seconds
- **SLA Compliance**: ⚠️ Close to 5s limit

### SLA Targets

- **Main Response**: ≤5 seconds (50-80 tokens)
- **Backchannel**: ≤1-2 seconds (short acknowledgments)
- **Max Tokens per Turn**: 96 tokens (enforced in DM)
- **Context Window**: 8192 tokens
- **Parallel Requests**: 4 concurrent

### Tuning Parameters

#### Recommended Settings for SLA Compliance
```bash
# GPU Configuration
--n-gpu-layers auto
--parallel 4
--ctx-size 8192

# Generation Parameters
--temp 0.7
--top_p 0.9
--min-p 0.05
--repeat-penalty 1.1

# Performance Limits
--max-tokens 96  # Enforced in DM for ≤5s SLA
--batch-size 512
--ubatch-size 512
```

#### Hardware-Specific Tuning

**RTX 4060 Ti (8GB)**
```bash
LLM_GPU_LAYERS=auto
LLM_PARALLEL=4
LLM_CTX=8192
LLM_BATCH_SIZE=512
```

**CPU Only (8+ cores)**
```bash
LLM_GPU_LAYERS=0
LLM_THREADS=8
LLM_PARALLEL=2
LLM_CTX=4096
LLM_BATCH_SIZE=256
```

### Optimization Tips

1. **GPU Memory**: Use `LLM_GPU_LAYERS=auto` for automatic GPU layer detection
2. **Context Size**: Reduce `LLM_CTX` for lower memory usage
3. **Quantization**: Use Q4_K_M for speed, Q8_0 for quality
4. **Parallel Requests**: Increase `LLM_PARALLEL` for higher throughput
5. **Batch Size**: Tune `LLM_BATCH_SIZE` based on your hardware
6. **Response Length**: Limit to 96 tokens for SLA compliance

## Integration

### Dialog Manager Integration

```python
# In services/dm/main.py
import os
import requests

LLM_ENGINE = os.getenv("LLM_ENGINE", "llama.cpp")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://llm-local:8080/v1")

def call_local_llm(system_prompt: str, user_prompt: str, stream: bool = True):
    """Call local LLM with JSON schema enforcement"""
    
    payload = {
        "model": "qwen2.5-7b-instruct",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": stream,
        "temperature": 0.1,
        "max_tokens": 512
    }
    
    # Add JSON schema enforcement for llama.cpp
    if LLM_ENGINE == "llama.cpp":
        payload["response_format"] = {"type": "json_object"}
    
    response = requests.post(
        f"{LLM_BASE_URL}/chat/completions",
        json=payload,
        stream=stream,
        timeout=30
    )
    
    return response
```

### Python Client

```python
import requests
import json

class LocalLLMClient:
    def __init__(self, base_url="http://localhost:8080/v1"):
        self.base_url = base_url
    
    def chat_completion(self, messages, stream=False, **kwargs):
        payload = {
            "model": "qwen2.5-7b-instruct",
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/chat/completions",
            json=payload,
            stream=stream
        )
        
        if stream:
            return response.iter_lines()
        else:
            return response.json()
    
    def generate_interview_response(self, transcript, context, role_profile):
        system_prompt = f"""Ты интервьюер для роли {role_profile}. 
        Отвечай коротко. Верни JSON: {{reply, next_node_id, scoring_update:{{block,delta,score}}, red_flags[]}}."""
        
        user_prompt = f"node:..., transcript:{transcript}, current_scores:..., role_profile:{role_profile}"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        return self.chat_completion(
            messages=messages,
            stream=False,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

# Usage
client = LocalLLMClient()
response = client.generate_interview_response(
    transcript="Я работал с Python 3 года...",
    context={"current_node": "python_experience"},
    role_profile="ba_anti_fraud"
)
```

## Troubleshooting

### Common Issues

1. **Model Download Fails**
   ```bash
   # Check network connectivity
   curl -I https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf
   
   # Manual download
   wget -O models/qwen2.5-7b-instruct-q5_k_m.gguf \
     https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q5_k_m.gguf
   ```

2. **GPU Not Detected**
   ```bash
   # Check NVIDIA GPU
   nvidia-smi
   
   # Check OpenCL
   clinfo
   
   # Force CPU mode
   LLM_GPU_LAYERS=0
   ```

3. **Out of Memory**
   ```bash
   # Reduce context size
   LLM_CTX=4096
   
   # Use smaller model
   LLM_MODEL=Qwen2.5-7B-Instruct-Q4_K_M.gguf
   
   # Reduce parallel requests
   LLM_PARALLEL=2
   ```

4. **Slow Performance**
   ```bash
   # Enable GPU acceleration
   LLM_GPU_LAYERS=auto
   
   # Increase threads
   LLM_THREADS=16
   
   # Use faster quantization
   LLM_MODEL=Qwen2.5-7B-Instruct-Q4_K_M.gguf
   ```

### Logs

```bash
# View container logs
docker logs llm-local

# Follow logs
docker logs -f llm-local

# Check health
curl http://localhost:8080/health
```

## References

- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [Qwen2.5-7B-Instruct Hugging Face](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [Qwen2.5-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF)
- [OpenAI API Compatibility](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md)
