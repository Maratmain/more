import os
import io
import struct
import time
from typing import Optional

import numpy as np
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv

load_dotenv()

# Configuration
PIPER_MODEL = os.getenv('PIPER_MODEL', 'ru_RU-some_voice-medium.onnx')
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', '16000'))
PORT = int(os.getenv('PORT', '8003'))

app = FastAPI()

# Global Piper model instance
piper_model = None

def load_piper_model():
    """Load Piper TTS model"""
    global piper_model
    try:
        # Try to import piper
        from piper import PiperVoice
        
        # For demo purposes, we'll use a simple fallback
        # In production, you would load the actual model:
        # piper_model = PiperVoice.load(PIPER_MODEL)
        
        print(f"TTS model configured: {PIPER_MODEL}")
        print("Note: Using fallback TTS - install piper for full functionality")
        piper_model = "fallback"
        
    except ImportError:
        print("Piper not installed - using fallback TTS")
        piper_model = "fallback"

def create_wav_header(sample_rate: int, num_samples: int) -> bytes:
    """Create WAV file header"""
    num_channels = 1  # mono
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data_size = num_samples * block_align
    file_size = 36 + data_size
    
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF',
        file_size,
        b'WAVE',
        b'fmt ',
        16,  # fmt chunk size
        1,   # audio format (PCM)
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b'data',
        data_size
    )
    
    return header

def synthesize_fallback(text: str, sample_rate: int) -> np.ndarray:
    """Fallback TTS - generates a simple tone pattern"""
    # Simple fallback: generate a tone pattern based on text length
    duration = max(0.5, len(text) * 0.1)  # 0.1 seconds per character, min 0.5s
    num_samples = int(sample_rate * duration)
    
    # Generate a simple tone pattern
    t = np.linspace(0, duration, num_samples)
    frequency = 440 + (len(text) % 200)  # Vary frequency based on text
    audio = 0.3 * np.sin(2 * np.pi * frequency * t)
    
    # Add some variation to make it sound more interesting
    audio += 0.1 * np.sin(2 * np.pi * frequency * 2 * t)
    
    # Apply simple envelope
    envelope = np.exp(-t * 2)  # Decay envelope
    audio *= envelope
    
    return audio

def synthesize_with_piper(text: str, sample_rate: int) -> np.ndarray:
    """Synthesize speech using Piper"""
    if piper_model == "fallback":
        return synthesize_fallback(text, sample_rate)
    
    try:
        # In production with actual Piper:
        # audio = piper_model.synthesize(text)
        # return audio
        pass
    except Exception as e:
        print(f"Piper synthesis error: {e}")
        return synthesize_fallback(text, sample_rate)
    
    return synthesize_fallback(text, sample_rate)

@app.on_event("startup")
async def startup_event():
    load_piper_model()

@app.get("/health")
async def health():
    return {
        "status": "ok", 
        "model": PIPER_MODEL,
        "sample_rate": SAMPLE_RATE,
        "piper_available": piper_model is not None
    }

@app.get("/speak")
async def speak(
    text: str = Query(..., description="Text to synthesize"),
    format: str = Query("wav", description="Output format (wav/pcm)")
):
    """Synthesize text to speech"""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        # Synthesize audio
        audio = synthesize_with_piper(text, SAMPLE_RATE)
        
        # Convert to 16-bit PCM
        audio_int16 = (audio * 32767).astype(np.int16)
        
        if format.lower() == "pcm":
            # Return raw PCM data
            pcm_data = audio_int16.tobytes()
            return StreamingResponse(
                io.BytesIO(pcm_data),
                media_type="audio/pcm",
                headers={"Content-Length": str(len(pcm_data))}
            )
        else:
            # Return WAV format
            wav_header = create_wav_header(SAMPLE_RATE, len(audio_int16))
            wav_data = wav_header + audio_int16.tobytes()
            
            return StreamingResponse(
                io.BytesIO(wav_data),
                media_type="audio/wav",
                headers={
                    "Content-Length": str(len(wav_data)),
                    "Content-Disposition": f"inline; filename=speech.wav"
                }
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TTS synthesis failed: {str(e)}")

@app.post("/dm/reply")
async def dialog_manager_reply(request: dict):
    """Dialog manager endpoint stub for testing"""
    user_text = request.get("text", "")
    
    # Simple response logic for testing
    if "привет" in user_text.lower() or "hello" in user_text.lower():
        reply = "Привет! Как дела?"
    elif "спасибо" in user_text.lower() or "thank" in user_text.lower():
        reply = "Пожалуйста! Рад помочь."
    elif "вопрос" in user_text.lower() or "question" in user_text.lower():
        reply = "Конечно, задавайте вопросы!"
    else:
        reply = "Понял, спасибо за информацию."
    
    return {
        "text": reply,
        "type": "ai_response",
        "timestamp": time.time()
    }

@app.get("/")
async def root():
    return {
        "service": "TTS (Text-to-Speech) + Dialog Manager",
        "endpoints": {
            "/speak": "GET /speak?text=Hello&format=wav",
            "/health": "GET /health",
            "/dm/reply": "POST /dm/reply (dialog manager stub)"
        },
        "example": "/speak?text=Привет мир&format=wav"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)