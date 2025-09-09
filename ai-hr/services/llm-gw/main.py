"""
LLM Gateway Service

Provides a unified interface for LLM providers (OpenRouter, OpenAI-compatible).
Supports both streaming and non-streaming responses.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="LLM Gateway Service",
    description="Unified interface for LLM providers",
    version="1.0.0"
)

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_HEADERS_X_TITLE = os.getenv("OPENROUTER_HEADERS_X_TITLE", "AI-HR")
OPENROUTER_HEADERS_REFERER = os.getenv("OPENROUTER_HEADERS_REFERER", "http://localhost:5173")

# OpenAI-compatible configuration
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")  # Default to Ollama
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")  # Ollama doesn't require real API key

# Default model
DEFAULT_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet:beta")

# Request/Response models
class GenerateRequest(BaseModel):
    system: Optional[str] = Field(None, description="System prompt")
    prompt: str = Field(..., description="User prompt")
    model: str = Field("env_default", description="Model to use (or 'env_default' for default)")
    stream: bool = Field(False, description="Whether to stream the response")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Sampling temperature")

class GenerateResponse(BaseModel):
    content: str
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None

# Provider classes
class OpenRouterProvider:
    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required for OpenRouter provider")
        
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_HEADERS_REFERER,
            "X-Title": OPENROUTER_HEADERS_X_TITLE
        }
    
    async def generate(self, request: GenerateRequest, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Generate response using OpenRouter"""
        model = request.model if request.model != "env_default" else DEFAULT_MODEL
        
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": request.stream
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.temperature:
            payload["temperature"] = request.temperature
        
        logger.info(f"OpenRouter request: model={model}, stream={request.stream}")
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60.0
        )
        
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"OpenRouter error: {response.status_code} - {error_text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenRouter API error: {error_text}"
            )
        
        return response.json()
    
    async def generate_stream(self, request: GenerateRequest, client: httpx.AsyncClient) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenRouter"""
        model = request.model if request.model != "env_default" else DEFAULT_MODEL
        
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.temperature:
            payload["temperature"] = request.temperature
        
        logger.info(f"OpenRouter stream request: model={model}")
        
        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60.0
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                logger.error(f"OpenRouter stream error: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenRouter API error: {error_text.decode()}"
                )
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield f"data: {data}\n\n"
                    except json.JSONDecodeError:
                        continue

class OpenAICompatibleProvider:
    def __init__(self):
        self.base_url = OPENAI_BASE_URL
        self.api_key = OPENAI_API_KEY
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def generate(self, request: GenerateRequest, client: httpx.AsyncClient) -> Dict[str, Any]:
        """Generate response using OpenAI-compatible API"""
        model = request.model if request.model != "env_default" else DEFAULT_MODEL
        
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": request.stream
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.temperature:
            payload["temperature"] = request.temperature
        
        logger.info(f"OpenAI-compatible request: model={model}, stream={request.stream}")
        
        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60.0
        )
        
        if response.status_code != 200:
            error_text = response.text
            logger.error(f"OpenAI-compatible error: {response.status_code} - {error_text}")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"OpenAI-compatible API error: {error_text}"
            )
        
        return response.json()
    
    async def generate_stream(self, request: GenerateRequest, client: httpx.AsyncClient) -> AsyncGenerator[str, None]:
        """Generate streaming response using OpenAI-compatible API"""
        model = request.model if request.model != "env_default" else DEFAULT_MODEL
        
        messages = []
        if request.system:
            messages.append({"role": "system", "content": request.system})
        messages.append({"role": "user", "content": request.prompt})
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True
        }
        
        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens
        if request.temperature:
            payload["temperature"] = request.temperature
        
        logger.info(f"OpenAI-compatible stream request: model={model}")
        
        async with client.stream(
            "POST",
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload,
            timeout=60.0
        ) as response:
            if response.status_code != 200:
                error_text = await response.aread()
                logger.error(f"OpenAI-compatible stream error: {response.status_code} - {error_text}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"OpenAI-compatible API error: {error_text.decode()}"
                )
            
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove "data: " prefix
                    if data.strip() == "[DONE]":
                        break
                    try:
                        yield f"data: {data}\n\n"
                    except json.JSONDecodeError:
                        continue

# Initialize provider
try:
    if LLM_PROVIDER == "openrouter":
        provider = OpenRouterProvider()
        logger.info("Initialized OpenRouter provider")
    elif LLM_PROVIDER == "openai_compatible":
        provider = OpenAICompatibleProvider()
        logger.info("Initialized OpenAI-compatible provider")
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
except Exception as e:
    logger.error(f"Failed to initialize provider: {e}")
    provider = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "provider": LLM_PROVIDER,
        "provider_initialized": provider is not None
    }

@app.get("/models")
async def list_models():
    """List available models"""
    if not provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    
    return {
        "provider": LLM_PROVIDER,
        "default_model": DEFAULT_MODEL,
        "available_models": [
            DEFAULT_MODEL,
            "env_default"  # Special value to use default
        ]
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """Generate text using the configured LLM provider"""
    if not provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    
    if request.stream:
        raise HTTPException(
            status_code=400, 
            detail="Use /generate/stream endpoint for streaming responses"
        )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await provider.generate(request, client)
            
            # Extract content from response
            if "choices" in response and len(response["choices"]) > 0:
                choice = response["choices"][0]
                content = choice["message"]["content"]
                finish_reason = choice.get("finish_reason")
            else:
                raise HTTPException(status_code=500, detail="Invalid response format")
            
            return GenerateResponse(
                content=content,
                model=response.get("model", request.model),
                usage=response.get("usage"),
                finish_reason=finish_reason
            )
            
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Request timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Request error: {str(e)}")
        except Exception as e:
            logger.error(f"Generation error: {e}")
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@app.post("/generate/stream")
async def generate_stream(request: GenerateRequest):
    """Generate streaming text using the configured LLM provider"""
    if not provider:
        raise HTTPException(status_code=503, detail="Provider not initialized")
    
    async def stream_generator():
        async with httpx.AsyncClient() as client:
            try:
                async for chunk in provider.generate_stream(request, client):
                    yield chunk
            except httpx.TimeoutException:
                yield f"data: {json.dumps({'error': 'Request timeout'})}\n\n"
            except httpx.RequestError as e:
                yield f"data: {json.dumps({'error': f'Request error: {str(e)}'})}\n\n"
            except Exception as e:
                logger.error(f"Stream generation error: {e}")
                yield f"data: {json.dumps({'error': f'Generation failed: {str(e)}'})}\n\n"
    
    return StreamingResponse(
        stream_generator(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.get("/")
async def root():
    """Root endpoint with service information"""
    return {
        "service": "LLM Gateway",
        "version": "1.0.0",
        "provider": LLM_PROVIDER,
        "endpoints": {
            "generate": "/generate",
            "generate_stream": "/generate/stream",
            "health": "/health",
            "models": "/models"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)
