# LLM Gateway Service

Gateway service for integrating with various Large Language Model providers through OpenRouter or OpenAI-compatible endpoints.

## Features

- **Multi-Provider Support**: OpenRouter, OpenAI, and compatible APIs
- **Model Selection**: Easy switching between different LLM models
- **Request Routing**: Intelligent routing to appropriate providers
- **Response Caching**: Optional response caching for cost optimization
- **Rate Limiting**: Built-in rate limiting and quota management
- **Error Handling**: Robust error handling and fallback mechanisms

## Configuration

### Environment Variables

```bash
# Provider selection
LLM_PROVIDER=openrouter  # openrouter | openai_compatible

# OpenRouter Configuration
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_HEADERS_X_TITLE=AI-HR
OPENROUTER_HEADERS_REFERER=http://localhost:5173

# Model selection
LLM_MODEL=anthropic/claude-3.5-sonnet:beta
```

### OpenRouter Setup

1. **Create Account**: Sign up at [OpenRouter](https://openrouter.ai/)
2. **Get API Key**: Generate API key from [Keys page](https://openrouter.ai/keys)
3. **Configure Model**: Select model from available options

#### OpenRouter API Details

- **Base URL**: `https://openrouter.ai/api/v1`
- **Authentication**: `Authorization: Bearer YOUR_API_KEY`
- **Optional Headers**:
  - `HTTP-Referer`: Your application URL
  - `X-Title`: Your application name

**Reference**: [OpenRouter Documentation](https://openrouter.ai/docs)

#### Available Models

Popular models available through OpenRouter:

```bash
# Anthropic Claude
LLM_MODEL=anthropic/claude-3.5-sonnet:beta
LLM_MODEL=anthropic/claude-3-haiku:beta

# OpenAI GPT
LLM_MODEL=openai/gpt-4o
LLM_MODEL=openai/gpt-4o-mini

# Meta Llama
LLM_MODEL=meta-llama/llama-3.1-405b-instruct
LLM_MODEL=meta-llama/llama-3.1-70b-instruct

# Google Gemini
LLM_MODEL=google/gemini-pro-1.5
LLM_MODEL=google/gemini-pro-1.5-flash
```

## API Usage

### Basic Request

```python
import requests

headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5173",
    "X-Title": "AI-HR"
}

data = {
    "model": "anthropic/claude-3.5-sonnet:beta",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ]
}

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers=headers,
    json=data
)
```

### Service Integration

```python
# Example service call
async def generate_response(prompt: str) -> str:
    response = await llm_gateway.chat_completion(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000,
        temperature=0.7
    )
    return response.choices[0].message.content
```

## Service Architecture

### Request Flow

```
Client Request → LLM Gateway → Provider API → Response Processing → Client
```

### Provider Selection

```python
if LLM_PROVIDER == "openrouter":
    provider = OpenRouterProvider(
        api_key=OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        headers={
            "HTTP-Referer": OPENROUTER_HEADERS_REFERER,
            "X-Title": OPENROUTER_HEADERS_X_TITLE
        }
    )
elif LLM_PROVIDER == "openai_compatible":
    provider = OpenAICompatibleProvider(
        base_url=OPENAI_COMPATIBLE_URL,
        api_key=OPENAI_COMPATIBLE_KEY
    )
```

## Development

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export OPENROUTER_API_KEY=your_key
export LLM_MODEL=anthropic/claude-3.5-sonnet:beta

# Run service
uvicorn main:app --port 8008
```

### Testing

```bash
# Test OpenRouter connection
curl -X POST "http://localhost:8008/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3.5-sonnet:beta",
    "messages": [{"role": "user", "content": "Hello"}]
  }'

# Check service health
curl "http://localhost:8008/health"
```

## Cost Optimization

### Response Caching

```python
# Enable caching for repeated requests
CACHE_ENABLED=true
CACHE_TTL=3600  # 1 hour
```

### Model Selection

- **Development**: Use faster, cheaper models (Claude Haiku, GPT-4o-mini)
- **Production**: Use higher-quality models (Claude Sonnet, GPT-4o)
- **Testing**: Use free tier models when available

### Rate Limiting

```python
# Configure rate limits
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_TOKENS_PER_MINUTE=100000
```

## Error Handling

### Common Errors

1. **Authentication Failed**:
   - Check API key validity
   - Verify provider configuration

2. **Model Not Available**:
   - Check model name spelling
   - Verify model availability in region

3. **Rate Limit Exceeded**:
   - Implement exponential backoff
   - Consider request queuing

4. **Network Issues**:
   - Implement retry logic
   - Use fallback providers

### Fallback Strategy

```python
async def chat_with_fallback(prompt: str) -> str:
    try:
        return await primary_provider.chat_completion(prompt)
    except Exception as e:
        logger.warning(f"Primary provider failed: {e}")
        return await fallback_provider.chat_completion(prompt)
```

## Monitoring

### Metrics

- **Request Count**: Total requests per provider
- **Response Time**: Average response latency
- **Error Rate**: Failed requests percentage
- **Token Usage**: Tokens consumed per request
- **Cost Tracking**: Estimated costs per provider

### Health Checks

```bash
# Service health
GET /health

# Provider status
GET /providers/status

# Model availability
GET /models/available
```

## Security

- **API Key Management**: Secure storage and rotation
- **Request Validation**: Input sanitization and validation
- **Rate Limiting**: Protection against abuse
- **Logging**: Audit trail for all requests
- **CORS**: Proper CORS configuration

## Troubleshooting

### Debug Mode

```bash
# Enable debug logging
DEBUG=true
LOG_LEVEL=DEBUG
```

### Common Issues

1. **OpenRouter API Key Issues**:
   - Verify key is active
   - Check account balance
   - Ensure proper permissions

2. **Model Selection**:
   - Use exact model names
   - Check model availability
   - Verify region restrictions

3. **Network Connectivity**:
   - Test direct API calls
   - Check firewall settings
   - Verify DNS resolution

### Logs

```bash
# View service logs
docker logs ai-hr-llm-gw-1 -f

# Check specific provider logs
grep "OpenRouter" logs/app.log
```
