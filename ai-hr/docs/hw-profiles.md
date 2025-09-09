# Hardware Profiles for AI-HR System

Comprehensive hardware profiles and configuration recommendations for different deployment scenarios.

## Overview

The AI-HR system supports three main hardware profiles, each optimized for different performance requirements and budget constraints:

1. **CPU-Only Profile** - Minimal hardware requirements
2. **Mid-GPU Profile** - Balanced performance with single GPU
3. **Big GPU Profile** - High-performance deployment with powerful GPUs

## Profile 1: CPU-Only

### Hardware Requirements
- **CPU**: 8+ cores (Intel i7/AMD Ryzen 7 or better)
- **RAM**: 16GB+ (32GB recommended)
- **Storage**: 50GB+ free space
- **GPU**: Not required

### Model Configuration
```bash
# Recommended Models
LLM_MODEL=Qwen2.5-3B-Instruct-Q4_K_M.gguf  # 2.1GB
LLM_MODEL=Qwen2.5-7B-Instruct-Q4_K_M.gguf  # 4.1GB (better quality)

# Alternative: Llama-3.1-8B
LLM_MODEL=llama-3.1-8b-instruct-q4_k_m.gguf  # 4.1GB
```

### Performance Settings
```bash
# CPU-Only Configuration
LLM_GPU_LAYERS=0
LLM_THREADS=8
LLM_PARALLEL=2
LLM_CTX=4096
LLM_BATCH_SIZE=256
LLM_UBATCH_SIZE=256

# SLA Compliance
LLM_MAX_TOKENS=64  # Reduced for CPU performance
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.9
```

### Expected Performance
- **Speed**: 6-10 tokens/sec
- **Response Time**: 30-50 tokens ≈ 3-5 seconds
- **SLA Compliance**: ⚠️ Close to 5s limit
- **Backchannel**: **REQUIRED** for good UX

### Backchannel Configuration
```yaml
# config/backchannel.yaml
common:
  generic_positive: ["Понимаю.", "Хорошо.", "Продолжайте."]
  generic_neutral: ["Уточните, пожалуйста.", "Понял, но нужны детали."]
  generic_negative: ["Понял, но это не совсем то, что нужно."]
selection:
  positive_threshold: 0.7
  negative_threshold: 0.3
  backchannel_delay_ms: 1000  # Play backchannel after 1s
```

### Docker Compose Configuration
```yaml
services:
  llm-local:
    build: ./services/llm-local
    ports: ["8080:8080"]
    env_file: ./services/llm-local/env.example
    volumes:
      - llm_models:/app/models
    environment:
      - LLM_GPU_LAYERS=0
      - LLM_THREADS=8
      - LLM_PARALLEL=2
      - LLM_MAX_TOKENS=64
    restart: unless-stopped
```

### Use Cases
- **Development/Testing**: Local development environments
- **Budget Constraints**: Cost-effective deployment
- **Edge Deployment**: Remote locations with limited hardware
- **Proof of Concept**: Initial system validation

## Profile 2: Mid-GPU (8-16GB)

### Hardware Requirements
- **GPU**: RTX 3060 Ti, RTX 4060 Ti, RTX 3070, RTX 4070 (8-16GB VRAM)
- **CPU**: 6+ cores (Intel i5/AMD Ryzen 5 or better)
- **RAM**: 16GB+ (32GB recommended)
- **Storage**: 50GB+ free space

### Model Configuration
```bash
# Recommended Models
LLM_MODEL=Qwen2.5-7B-Instruct-Q5_K_M.gguf  # 5.1GB (recommended)
LLM_MODEL=Qwen2.5-7B-Instruct-Q8_0.gguf    # 8.1GB (higher quality)

# Alternative: Llama-3.1-8B
LLM_MODEL=llama-3.1-8b-instruct-q5_k_m.gguf  # 5.1GB
LLM_MODEL=llama-3.1-8b-instruct-q8_0.gguf    # 8.1GB
```

### Performance Settings
```bash
# Mid-GPU Configuration
LLM_GPU_LAYERS=auto
LLM_THREADS=8
LLM_PARALLEL=4
LLM_CTX=8192
LLM_BATCH_SIZE=512
LLM_UBATCH_SIZE=512

# SLA Compliance
LLM_MAX_TOKENS=96  # Standard for good performance
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.9
```

### Expected Performance
- **Speed**: 20-60 tokens/sec (depending on GPU)
- **Response Time**: 50-80 tokens ≈ 1-3 seconds
- **SLA Compliance**: ✅ Well within 5s limit
- **Backchannel**: Optional (for enhanced UX)

### Hardware-Specific Tuning

#### RTX 4060 Ti (8GB)
```bash
LLM_GPU_LAYERS=auto
LLM_PARALLEL=4
LLM_CTX=8192
LLM_BATCH_SIZE=512
# Expected: ~25 tokens/sec
```

#### RTX 3070 (8GB)
```bash
LLM_GPU_LAYERS=auto
LLM_PARALLEL=4
LLM_CTX=8192
LLM_BATCH_SIZE=512
# Expected: ~40 tokens/sec
```

#### RTX 4070 (12GB)
```bash
LLM_GPU_LAYERS=auto
LLM_PARALLEL=6
LLM_CTX=8192
LLM_BATCH_SIZE=768
# Expected: ~60 tokens/sec
```

### Docker Compose Configuration
```yaml
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
    environment:
      - LLM_GPU_LAYERS=auto
      - LLM_PARALLEL=4
      - LLM_MAX_TOKENS=96
    restart: unless-stopped
```

### Use Cases
- **Production Deployment**: Balanced performance and cost
- **Small-Medium Teams**: 10-50 concurrent users
- **Hybrid Environments**: Mix of local and cloud processing
- **Cost-Conscious Production**: Good performance without premium hardware

## Profile 3: Big GPU

### Hardware Requirements
- **GPU**: RTX 4090, RTX 4080, RTX 3090, A100, H100 (16GB+ VRAM)
- **CPU**: 8+ cores (Intel i7/AMD Ryzen 7 or better)
- **RAM**: 32GB+ (64GB recommended)
- **Storage**: 100GB+ free space

### Model Configuration

#### Option A: vLLM Service (Recommended)
```bash
# vLLM Configuration
VLLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
VLLM_MODEL=google/gemma-2-9b-it
VLLM_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct  # If 40GB+ VRAM

# Service Configuration
LLM_PROVIDER=openai_compatible
OPENAI_BASE_URL=http://llm-vllm:8000/v1
LLM_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct
```

#### Option B: llama.cpp with Large Models
```bash
# Large Models (if VRAM allows)
LLM_MODEL=Qwen2.5-7B-Instruct-F16.gguf  # 13.4GB
LLM_MODEL=llama-3.1-8b-instruct-f16.gguf  # 16.4GB
LLM_MODEL=llama-3.1-70b-instruct-q4_k_m.gguf  # 39.5GB (RTX 4090 24GB)
```

### Performance Settings
```bash
# Big GPU Configuration
LLM_GPU_LAYERS=auto
LLM_THREADS=16
LLM_PARALLEL=8
LLM_CTX=8192
LLM_BATCH_SIZE=1024
LLM_UBATCH_SIZE=1024

# SLA Compliance
LLM_MAX_TOKENS=128  # Higher limit for premium hardware
LLM_TEMPERATURE=0.7
LLM_TOP_P=0.9
```

### Expected Performance
- **Speed**: 100-200+ tokens/sec
- **Response Time**: 50-100 tokens ≈ 0.5-1 second
- **SLA Compliance**: ✅ Excellent performance
- **Backchannel**: Not required (fast enough)

### Hardware-Specific Tuning

#### RTX 4090 (24GB)
```bash
# vLLM Configuration
VLLM_GPU_MEMORY_UTILIZATION=0.9
VLLM_MAX_NUM_SEQS=16
VLLM_MAX_MODEL_LEN=8192
# Expected: ~150-200 tokens/sec
```

#### RTX 4080 (16GB)
```bash
# vLLM Configuration
VLLM_GPU_MEMORY_UTILIZATION=0.85
VLLM_MAX_NUM_SEQS=12
VLLM_MAX_MODEL_LEN=8192
# Expected: ~100-150 tokens/sec
```

#### RTX 3090 (24GB)
```bash
# vLLM Configuration
VLLM_GPU_MEMORY_UTILIZATION=0.9
VLLM_MAX_NUM_SEQS=16
VLLM_MAX_MODEL_LEN=8192
# Expected: ~80-120 tokens/sec
```

### Docker Compose Configuration
```yaml
services:
  llm-vllm:
    image: vllm/vllm-openai:latest
    command: [
      "--model", "meta-llama/Meta-Llama-3.1-8B-Instruct",
      "--max-model-len", "8192",
      "--gpu-memory-utilization", "0.9",
      "--max-num-seqs", "16",
      "--host", "0.0.0.0",
      "--port", "8000"
    ]
    ports: ["8009:8000"]
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: ["gpu"]
    restart: unless-stopped

  # Alternative: Large llama.cpp model
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
    environment:
      - LLM_GPU_LAYERS=auto
      - LLM_PARALLEL=8
      - LLM_MAX_TOKENS=128
    restart: unless-stopped
```

### Use Cases
- **High-Performance Production**: 50+ concurrent users
- **Enterprise Deployment**: Mission-critical applications
- **Research & Development**: Advanced model experimentation
- **Premium Service**: Best possible user experience

## Performance Comparison

| Profile | Hardware | Model | Tokens/sec | Response Time | SLA | Cost | Use Case |
|---------|----------|-------|------------|---------------|-----|------|----------|
| CPU-Only | 8+ cores, 16GB RAM | Qwen2.5-3B Q4_K_M | 6-10 | 3-5s | ⚠️ | $ | Dev/Testing |
| CPU-Only | 8+ cores, 32GB RAM | Qwen2.5-7B Q4_K_M | 8-12 | 2-4s | ✅ | $$ | Budget Production |
| Mid-GPU | RTX 4060 Ti 8GB | Qwen2.5-7B Q5_K_M | 25 | 2-3s | ✅ | $$$ | Balanced Production |
| Mid-GPU | RTX 4070 12GB | Qwen2.5-7B Q8_0 | 60 | 1-2s | ✅ | $$$$ | High Performance |
| Big GPU | RTX 4090 24GB | Llama-3.1-8B (vLLM) | 150+ | 0.5-1s | ✅ | $$$$$ | Enterprise |
| Big GPU | RTX 4090 24GB | Llama-3.1-70B Q4_K_M | 100+ | 1-2s | ✅ | $$$$$ | Premium Enterprise |

## Migration Guide

### From CPU-Only to Mid-GPU
1. **Install GPU drivers** (NVIDIA CUDA)
2. **Update environment**:
   ```bash
   LLM_GPU_LAYERS=auto
   LLM_PARALLEL=4
   LLM_MAX_TOKENS=96
   ```
3. **Restart services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### From Mid-GPU to Big GPU
1. **Switch to vLLM**:
   ```bash
   LLM_PROVIDER=openai_compatible
   OPENAI_BASE_URL=http://llm-vllm:8000/v1
   ```
2. **Update docker-compose.yml** to include vLLM service
3. **Restart services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### From Big GPU to CPU-Only (Downgrade)
1. **Update environment**:
   ```bash
   LLM_GPU_LAYERS=0
   LLM_PARALLEL=2
   LLM_MAX_TOKENS=64
   LLM_MODEL=Qwen2.5-3B-Instruct-Q4_K_M.gguf
   ```
2. **Enable backchannel** in config
3. **Restart services**

## Troubleshooting

### Common Issues

#### 1. Out of Memory (OOM)
```bash
# Reduce model size
LLM_MODEL=Qwen2.5-3B-Instruct-Q4_K_M.gguf

# Reduce context size
LLM_CTX=4096

# Reduce batch size
LLM_BATCH_SIZE=256
```

#### 2. Slow Performance
```bash
# Enable GPU acceleration
LLM_GPU_LAYERS=auto

# Increase parallel requests
LLM_PARALLEL=4

# Use faster quantization
LLM_MODEL=Qwen2.5-7B-Instruct-Q4_K_M.gguf
```

#### 3. SLA Violations
```bash
# Reduce max tokens
LLM_MAX_TOKENS=64

# Enable backchannel
BACKCHANNEL_ENABLED=true

# Use smaller model
LLM_MODEL=Qwen2.5-3B-Instruct-Q4_K_M.gguf
```

### Performance Monitoring

#### Check GPU Usage
```bash
# NVIDIA GPU
nvidia-smi

# Check GPU layers
docker logs llm-local | grep "GPU layers"
```

#### Monitor Response Times
```bash
# Check metrics service
curl http://localhost:8010/metrics/summary

# Check DM health
curl http://localhost:8004/health
```

#### Latency Testing
```bash
# Run latency probe
cd services/llm-local/tests
python latency_probe.py

# Check results
cat latency_results.csv
```

## References

- [Qwen2.5-3B-Instruct Hugging Face](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)
- [Qwen2.5-7B-Instruct Hugging Face](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct)
- [Llama-3.1-8B-Instruct Hugging Face](https://huggingface.co/meta-llama/Meta-Llama-3.1-8B-Instruct)
- [vLLM Documentation](https://docs.vllm.ai/)
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [NVIDIA CUDA Toolkit](https://developer.nvidia.com/cuda-toolkit)
