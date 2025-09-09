"""
AI-HR Metrics Client Library

Easy-to-use client for recording metrics from other services.
Provides decorators and context managers for automatic timing.
"""

import time
import requests
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class MetricsClient:
    """Client for recording metrics to the metrics service"""
    
    def __init__(self, metrics_url: str = "http://localhost:8010"):
        self.metrics_url = metrics_url
        self.session = requests.Session()
        self.session.timeout = 5  # 5 second timeout for metrics
    
    def record_latency(self, service: str, latency_ms: float, session_id: str, 
                      turn_id: str, success: bool = True, error_message: Optional[str] = None):
        """Record latency metric"""
        try:
            payload = {
                "service": service,
                "latency_ms": latency_ms,
                "session_id": session_id,
                "turn_id": turn_id,
                "success": success,
                "error_message": error_message
            }
            
            response = self.session.post(f"{self.metrics_url}/latency", json=payload)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.warning(f"Failed to record latency metric: {e}")
            return False
    
    def record_cost(self, service: str, cost_usd: float, session_id: str, 
                   turn_id: str, units: int = 1, unit_type: str = "request",
                   details: Optional[Dict[str, Any]] = None):
        """Record cost metric"""
        try:
            payload = {
                "service": service,
                "cost_usd": cost_usd,
                "session_id": session_id,
                "turn_id": turn_id,
                "units": units,
                "unit_type": unit_type,
                "details": details or {}
            }
            
            response = self.session.post(f"{self.metrics_url}/cost", json=payload)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.warning(f"Failed to record cost metric: {e}")
            return False
    
    def record_turn(self, session_id: str, turn_id: str, asr_latency_ms: float,
                   dm_latency_ms: float, tts_latency_ms: float, total_turn_s: float,
                   backchannel_s: float, total_cost_usd: float, services_used: list):
        """Record complete turn metric"""
        try:
            payload = {
                "session_id": session_id,
                "turn_id": turn_id,
                "asr_latency_ms": asr_latency_ms,
                "dm_latency_ms": dm_latency_ms,
                "tts_latency_ms": tts_latency_ms,
                "total_turn_s": total_turn_s,
                "backchannel_s": backchannel_s,
                "total_cost_usd": total_cost_usd,
                "services_used": services_used
            }
            
            response = self.session.post(f"{self.metrics_url}/turn", json=payload)
            response.raise_for_status()
            return True
            
        except Exception as e:
            logger.warning(f"Failed to record turn metric: {e}")
            return False
    
    @contextmanager
    def time_operation(self, service: str, session_id: str, turn_id: str):
        """Context manager for timing operations"""
        start_time = time.time()
        success = True
        error_message = None
        
        try:
            yield
        except Exception as e:
            success = False
            error_message = str(e)
            raise
        finally:
            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000
            
            self.record_latency(
                service=service,
                latency_ms=latency_ms,
                session_id=session_id,
                turn_id=turn_id,
                success=success,
                error_message=error_message
            )
    
    def time_function(self, service: str, session_id: str = "default", turn_id: str = "default"):
        """Decorator for timing functions"""
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.time_operation(service, session_id, turn_id):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    async def time_async_function(self, service: str, session_id: str = "default", turn_id: str = "default"):
        """Decorator for timing async functions"""
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                success = True
                error_message = None
                
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    success = False
                    error_message = str(e)
                    raise
                finally:
                    end_time = time.time()
                    latency_ms = (end_time - start_time) * 1000
                    
                    self.record_latency(
                        service=service,
                        latency_ms=latency_ms,
                        session_id=session_id,
                        turn_id=turn_id,
                        success=success,
                        error_message=error_message
                    )
            return wrapper
        return decorator

# Global metrics client instance
_metrics_client = None

def get_metrics_client() -> MetricsClient:
    """Get global metrics client instance"""
    global _metrics_client
    if _metrics_client is None:
        _metrics_client = MetricsClient()
    return _metrics_client

def record_latency(service: str, latency_ms: float, session_id: str, 
                  turn_id: str, success: bool = True, error_message: Optional[str] = None):
    """Record latency metric using global client"""
    return get_metrics_client().record_latency(service, latency_ms, session_id, turn_id, success, error_message)

def record_cost(service: str, cost_usd: float, session_id: str, 
               turn_id: str, units: int = 1, unit_type: str = "request",
               details: Optional[Dict[str, Any]] = None):
    """Record cost metric using global client"""
    return get_metrics_client().record_cost(service, cost_usd, session_id, turn_id, units, unit_type, details)

def record_turn(session_id: str, turn_id: str, asr_latency_ms: float,
               dm_latency_ms: float, tts_latency_ms: float, total_turn_s: float,
               backchannel_s: float, total_cost_usd: float, services_used: list):
    """Record complete turn metric using global client"""
    return get_metrics_client().record_turn(
        session_id, turn_id, asr_latency_ms, dm_latency_ms, tts_latency_ms,
        total_turn_s, backchannel_s, total_cost_usd, services_used
    )

@contextmanager
def time_operation(service: str, session_id: str, turn_id: str):
    """Context manager for timing operations using global client"""
    with get_metrics_client().time_operation(service, session_id, turn_id):
        yield

def time_function(service: str, session_id: str = "default", turn_id: str = "default"):
    """Decorator for timing functions using global client"""
    return get_metrics_client().time_function(service, session_id, turn_id)

def time_async_function(service: str, session_id: str = "default", turn_id: str = "default"):
    """Decorator for timing async functions using global client"""
    return get_metrics_client().time_async_function(service, session_id, turn_id)

# Example usage and integration helpers
class ServiceMetrics:
    """Helper class for service-specific metrics"""
    
    def __init__(self, service_name: str, metrics_client: Optional[MetricsClient] = None):
        self.service_name = service_name
        self.client = metrics_client or get_metrics_client()
    
    def time_operation(self, session_id: str, turn_id: str):
        """Time an operation for this service"""
        return self.client.time_operation(self.service_name, session_id, turn_id)
    
    def record_latency(self, latency_ms: float, session_id: str, turn_id: str, 
                      success: bool = True, error_message: Optional[str] = None):
        """Record latency for this service"""
        return self.client.record_latency(
            self.service_name, latency_ms, session_id, turn_id, success, error_message
        )
    
    def record_cost(self, cost_usd: float, session_id: str, turn_id: str,
                   units: int = 1, unit_type: str = "request", details: Optional[Dict[str, Any]] = None):
        """Record cost for this service"""
        return self.client.record_cost(
            self.service_name, cost_usd, session_id, turn_id, units, unit_type, details
        )

# Service-specific metric helpers
asr_metrics = ServiceMetrics("asr")
dm_metrics = ServiceMetrics("dm")
tts_metrics = ServiceMetrics("tts")
llm_metrics = ServiceMetrics("llm")
cv_metrics = ServiceMetrics("cv")
vector_metrics = ServiceMetrics("vector")

# Example integration for ASR service
def integrate_asr_metrics():
    """Example of how to integrate metrics in ASR service"""
    # In your ASR service code:
    """
    from metrics.client import asr_metrics, time_operation
    
    # Option 1: Context manager
    with asr_metrics.time_operation(session_id, turn_id):
        result = process_audio(audio_data)
    
    # Option 2: Manual timing
    start_time = time.time()
    try:
        result = process_audio(audio_data)
        success = True
        error = None
    except Exception as e:
        success = False
        error = str(e)
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000
        asr_metrics.record_latency(latency_ms, session_id, turn_id, success, error)
    
    # Option 3: Decorator
    @time_function("asr", session_id, turn_id)
    def process_audio(audio_data):
        # Your ASR processing code
        return result
    """

# Example integration for Dialog Manager
def integrate_dm_metrics():
    """Example of how to integrate metrics in Dialog Manager"""
    # In your DM service code:
    """
    from metrics.client import dm_metrics, time_operation
    
    # Time the response generation
    with dm_metrics.time_operation(session_id, turn_id):
        response = generate_response(transcript, context)
    
    # Record cost if using LLM
    if using_llm:
        dm_metrics.record_cost(
            cost_usd=llm_cost,
            session_id=session_id,
            turn_id=turn_id,
            units=tokens_used,
            unit_type="tokens",
            details={"model": model_name, "provider": provider}
        )
    """

# Example integration for TTS service
def integrate_tts_metrics():
    """Example of how to integrate metrics in TTS service"""
    # In your TTS service code:
    """
    from metrics.client import tts_metrics, time_operation
    
    # Time the TTS generation
    with tts_metrics.time_operation(session_id, turn_id):
        audio = generate_speech(text)
    
    # Record cost
    tts_metrics.record_cost(
        cost_usd=tts_cost,
        session_id=session_id,
        turn_id=turn_id,
        units=len(text),
        unit_type="characters",
        details={"service": "piper", "voice": voice_name}
    )
    """
