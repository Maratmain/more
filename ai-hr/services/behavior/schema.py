"""
Схема событий поведения для AI-HR системы
"""
from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime

# Типы событий поведения
BehaviorEventType = Literal[
    "toxicity",           # Токсичность речи
    "nervous_freeze",     # Нервное замирание/ступор
    "irritability",       # Раздражительность
    "low_truthfulness"    # Низкая достоверность ответов
]

class BehaviorEvent(BaseModel):
    """Событие поведения кандидата"""
    type: BehaviorEventType = Field(..., description="Тип события поведения")
    score: float = Field(..., ge=0.0, le=1.0, description="Оценка события (0-1)")
    timestamp: float = Field(..., description="Unix timestamp события")
    session_id: str = Field(..., description="ID сессии интервью")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Доказательства события")
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "type": "toxicity",
                    "score": 0.85,
                    "timestamp": 1703123456.789,
                    "session_id": "session_123",
                    "evidence": {
                        "text": "Вы идиоты!",
                        "labels": ["insult", "threat"],
                        "model": "unbiased-toxic-roberta"
                    }
                },
                {
                    "type": "nervous_freeze",
                    "score": 0.7,
                    "timestamp": 1703123456.789,
                    "session_id": "session_123",
                    "evidence": {
                        "max_pause_ms": 3500,
                        "wpm": 45,
                        "filler_count": 8,
                        "duration_ms": 10000
                    }
                },
                {
                    "type": "irritability",
                    "score": 0.6,
                    "timestamp": 1703123456.789,
                    "session_id": "session_123",
                    "evidence": {
                        "anger_score": 0.7,
                        "prosody_features": {
                            "pitch_variance": 0.8,
                            "energy_high": 0.9
                        }
                    }
                },
                {
                    "type": "low_truthfulness",
                    "score": 0.8,
                    "timestamp": 1703123456.789,
                    "session_id": "session_123",
                    "evidence": {
                        "contradictions": ["CV: 5 лет опыта", "Ответ: 3 года"],
                        "evasive_responses": 3,
                        "confidence_drop": 0.4
                    }
                }
            ]
        }

class BehaviorPolicy(BaseModel):
    """Политика реагирования на события поведения"""
    action: Literal["continue", "micro_backchannel", "pause_offer", "warning", "end"] = Field(
        ..., description="Действие для выполнения"
    )
    phrase: str = Field(..., description="Фраза для произнесения")
    severity: Literal["low", "medium", "high", "critical"] = Field(
        ..., description="Уровень серьезности"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "action": "warning",
                    "phrase": "Давайте соблюдаем деловой тон. Если продолжится, завершим разговор.",
                    "severity": "high"
                },
                {
                    "action": "pause_offer",
                    "phrase": "Предлагаю сделать короткую паузу на 2 минуты — продолжим?",
                    "severity": "medium"
                },
                {
                    "action": "micro_backchannel",
                    "phrase": "Понимаю, продолжайте…",
                    "severity": "low"
                },
                {
                    "action": "end",
                    "phrase": "Вынужден завершить интервью. Мы свяжемся позже.",
                    "severity": "critical"
                }
            ]
        }

class BehaviorIncident(BaseModel):
    """Инцидент поведения для админ-уведомлений"""
    session_id: str = Field(..., description="ID сессии")
    candidate_id: Optional[str] = Field(None, description="ID кандидата")
    event_type: BehaviorEventType = Field(..., description="Тип события")
    severity: str = Field(..., description="Уровень серьезности")
    timestamp: datetime = Field(..., description="Время инцидента")
    evidence: Dict[str, Any] = Field(..., description="Доказательства")
    action_taken: str = Field(..., description="Предпринятое действие")
    phrase_used: str = Field(..., description="Использованная фраза")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "session_123",
                "candidate_id": "candidate_456",
                "event_type": "toxicity",
                "severity": "high",
                "timestamp": "2023-12-21T10:30:00Z",
                "evidence": {
                    "text": "Вы идиоты!",
                    "score": 0.85
                },
                "action_taken": "warning",
                "phrase_used": "Давайте соблюдаем деловой тон..."
            }
        }
