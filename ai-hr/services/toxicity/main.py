"""
Сервис детекции токсичности для AI-HR
Использует модель unbiased-toxic-roberta для анализа текста
"""
import os
import time
from typing import Dict, Any, List
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI-HR Toxicity Detection")

# Configuration
TOXICITY_MODEL = os.getenv("TOXICITY_MODEL", "unbiased-toxic-roberta")
TOXICITY_THRESHOLD_WARN = float(os.getenv("BEHAVIOR_TOXICITY_WARN", "0.75"))
TOXICITY_THRESHOLD_HI = float(os.getenv("BEHAVIOR_TOXICITY_HI", "0.90"))
HUGGINGFACE_API_URL = "https://api-inference.huggingface.co/models"

class ToxicityRequest(BaseModel):
    text: str = Field(..., description="Текст для анализа на токсичность")
    session_id: str = Field(..., description="ID сессии интервью")

class ToxicityResponse(BaseModel):
    toxicity: float = Field(..., ge=0.0, le=1.0, description="Уровень токсичности (0-1)")
    labels: List[str] = Field(default_factory=list, description="Обнаруженные категории токсичности")
    threshold_warn: float = Field(..., description="Порог предупреждения")
    threshold_hi: float = Field(..., description="Критический порог")
    needs_action: bool = Field(..., description="Требуется ли действие")
    action_level: str = Field(..., description="Уровень действия: none, warn, critical")

class ToxicityAnalyzer:
    """Анализатор токсичности текста"""
    
    def __init__(self):
        self.model_name = TOXICITY_MODEL
        self.api_url = f"{HUGGINGFACE_API_URL}/{self.model_name}"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('HUGGINGFACE_API_TOKEN', '')}"
        }
        
        # Fallback patterns for basic toxicity detection
        self.toxicity_patterns = [
            r'\b(идиот|дурак|тупой|дебил)\b',
            r'\b(блять|сука|пизда|хуй)\b',
            r'\b(убить|убийство|смерть)\b',
            r'\b(ненавижу|ненависть)\b',
            r'\b(уйди|пошёл|вали)\b'
        ]
        
        self.toxicity_labels = [
            "insult", "threat", "identity_attack", "profanity", "severe_toxicity"
        ]
    
    async def analyze_text(self, text: str) -> Dict[str, Any]:
        """Анализ текста на токсичность"""
        try:
            # Try Hugging Face API first
            if os.getenv('HUGGINGFACE_API_TOKEN'):
                result = await self._analyze_with_hf_api(text)
                if result:
                    return result
            
            # Fallback to pattern matching
            return await self._analyze_with_patterns(text)
            
        except Exception as e:
            print(f"Toxicity analysis error: {e}")
            return await self._analyze_with_patterns(text)
    
    async def _analyze_with_hf_api(self, text: str) -> Dict[str, Any]:
        """Анализ через Hugging Face API"""
        try:
            payload = {
                "inputs": text,
                "parameters": {
                    "return_all_scores": True,
                    "function_to_apply": "sigmoid"
                }
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                
                # Extract toxicity score and labels
                toxicity_score = 0.0
                detected_labels = []
                
                for result in results:
                    if isinstance(result, list):
                        for item in result:
                            label = item.get('label', '')
                            score = item.get('score', 0.0)
                            
                            if 'toxic' in label.lower() or 'toxicity' in label.lower():
                                toxicity_score = max(toxicity_score, score)
                            
                            if score > 0.5:  # Threshold for label detection
                                detected_labels.append(label)
                
                return {
                    'toxicity': toxicity_score,
                    'labels': detected_labels,
                    'model': self.model_name
                }
            
        except Exception as e:
            print(f"HF API error: {e}")
        
        return None
    
    async def _analyze_with_patterns(self, text: str) -> Dict[str, Any]:
        """Fallback анализ через паттерны"""
        import re
        
        toxicity_score = 0.0
        detected_labels = []
        
        text_lower = text.lower()
        
        # Check for toxicity patterns
        for i, pattern in enumerate(self.toxicity_patterns):
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                toxicity_score += 0.2
                detected_labels.append(self.toxicity_labels[i % len(self.toxicity_labels)])
        
        # Cap at 1.0
        toxicity_score = min(toxicity_score, 1.0)
        
        return {
            'toxicity': toxicity_score,
            'labels': detected_labels,
            'model': 'pattern_fallback'
        }
    
    def determine_action_level(self, toxicity_score: float) -> str:
        """Определение уровня действия по оценке токсичности"""
        if toxicity_score >= TOXICITY_THRESHOLD_HI:
            return "critical"
        elif toxicity_score >= TOXICITY_THRESHOLD_WARN:
            return "warn"
        else:
            return "none"

analyzer = ToxicityAnalyzer()

@app.post("/score", response_model=ToxicityResponse)
async def score_toxicity(request: ToxicityRequest) -> ToxicityResponse:
    """Анализ текста на токсичность"""
    try:
        # Analyze text
        analysis = await analyzer.analyze_text(request.text)
        
        # Determine action level
        action_level = analyzer.determine_action_level(analysis['toxicity'])
        needs_action = action_level in ["warn", "critical"]
        
        return ToxicityResponse(
            toxicity=analysis['toxicity'],
            labels=analysis['labels'],
            threshold_warn=TOXICITY_THRESHOLD_WARN,
            threshold_hi=TOXICITY_THRESHOLD_HI,
            needs_action=needs_action,
            action_level=action_level
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Toxicity analysis failed: {str(e)}")

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "ok",
        "model": TOXICITY_MODEL,
        "thresholds": {
            "warn": TOXICITY_THRESHOLD_WARN,
            "hi": TOXICITY_THRESHOLD_HI
        }
    }

@app.get("/config")
async def get_config():
    """Получение конфигурации"""
    return {
        "model": TOXICITY_MODEL,
        "thresholds": {
            "warn": TOXICITY_THRESHOLD_WARN,
            "hi": TOXICITY_THRESHOLD_HI
        },
        "labels": analyzer.toxicity_labels
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
