import asyncio
import json
import os
import time
import threading
import requests
from collections import deque
from typing import Dict, Any, Optional, List
import struct
import re

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

# Configuration
ASR_MODEL = os.getenv('ASR_MODEL', 'small')
ASR_DEVICE = os.getenv('ASR_DEVICE', 'cpu')
ASR_BEAM = int(os.getenv('ASR_BEAM', '5'))
ASR_VAD = os.getenv('ASR_VAD', 'true').lower() == 'true'
SAMPLE_RATE = int(os.getenv('SAMPLE_RATE', '16000'))
CHUNK_MS = int(os.getenv('CHUNK_MS', '40'))

# Behavior analysis configuration
BEHAVIOR_PAUSE_MS = int(os.getenv('BEHAVIOR_PAUSE_MS', '2000'))
BEHAVIOR_WPM_LOW = int(os.getenv('BEHAVIOR_WPM_LOW', '80'))
BEHAVIOR_SERVICE_URL = os.getenv('BEHAVIOR_SERVICE_URL', 'http://behavior:8008')

# Streaming configuration
WINDOW_DURATION = 3.0  # seconds - sliding window size
SILENCE_THRESHOLD = 0.01  # RMS threshold for silence detection
SILENCE_DURATION = 0.6  # seconds of silence before final
TRANSCRIPTION_INTERVAL = 0.4  # seconds between transcriptions
MIN_AUDIO_DURATION = 0.5  # minimum audio duration before transcription

# Calculate buffer sizes
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_MS / 1000)  # samples per chunk
WINDOW_SIZE = int(SAMPLE_RATE * WINDOW_DURATION)  # sliding window size
SILENCE_SAMPLES = int(SAMPLE_RATE * SILENCE_DURATION)  # silence detection
MIN_AUDIO_SAMPLES = int(SAMPLE_RATE * MIN_AUDIO_DURATION)  # minimum audio

app = FastAPI()

# Global model instance
model = None

def load_model():
    global model
    if model is None:
        print(f"Loading Whisper model: {ASR_MODEL} on {ASR_DEVICE}")
        model = WhisperModel(ASR_MODEL, device=ASR_DEVICE, compute_type="int8")
        print("Model loaded successfully")

class BehaviorAnalyzer:
    """Анализатор поведения речи"""
    
    def __init__(self):
        self.filler_patterns = [
            r'\bэ-э\b', r'\bмм\b', r'\bа-а\b', r'\bну\b', r'\bвот\b',
            r'\buh\b', r'\bum\b', r'\ber\b', r'\buhm\b'
        ]
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.filler_patterns]
        
    def count_fillers(self, text: str) -> int:
        """Подсчет заполнителей в тексте"""
        count = 0
        for pattern in self.compiled_patterns:
            count += len(pattern.findall(text))
        return count
    
    def calculate_wpm(self, text: str, duration_ms: float) -> float:
        """Вычисление слов в минуту"""
        if duration_ms <= 0:
            return 0
        words = len(text.split())
        minutes = duration_ms / (1000 * 60)
        return words / minutes if minutes > 0 else 0
    
    def analyze_speech_patterns(self, text: str, duration_ms: float, 
                              word_timestamps: List[Dict] = None) -> Dict[str, Any]:
        """Анализ паттернов речи"""
        filler_count = self.count_fillers(text)
        wpm = self.calculate_wpm(text, duration_ms)
        
        # Анализ пауз между словами
        max_pause_ms = 0
        if word_timestamps:
            for i in range(1, len(word_timestamps)):
                pause = word_timestamps[i]['start'] - word_timestamps[i-1]['end']
                max_pause_ms = max(max_pause_ms, pause)
        
        return {
            'filler_count': filler_count,
            'wpm': wpm,
            'max_pause_ms': max_pause_ms,
            'duration_ms': duration_ms,
            'word_count': len(text.split())
        }
    
    async def emit_behavior_event(self, session_id: str, event_type: str, 
                                score: float, evidence: Dict[str, Any]):
        """Отправка события поведения в сервис"""
        try:
            event_data = {
                'type': event_type,
                'score': score,
                'timestamp': time.time(),
                'session_id': session_id,
                'evidence': evidence
            }
            
            response = requests.post(
                f"{BEHAVIOR_SERVICE_URL}/events",
                json=event_data,
                timeout=5
            )
            
            if response.status_code != 200:
                print(f"Failed to emit behavior event: {response.status_code}")
                
        except Exception as e:
            print(f"Error emitting behavior event: {e}")

class StreamingSession:
    def __init__(self, websocket: WebSocket, session_id: str = None):
        self.websocket = websocket
        self.session_id = session_id or f"session_{int(time.time())}"
        self.ring_buffer = deque(maxlen=WINDOW_SIZE)
        self.last_audio_time = 0
        self.last_transcription_time = 0
        self.silence_start_time = 0
        self.is_silent = False
        self.lock = threading.Lock()
        self.running = True
        
        # Behavior analysis
        self.behavior_analyzer = BehaviorAnalyzer()
        self.speech_segments = []  # История сегментов речи
        self.last_word_timestamp = 0
        
    def add_audio_chunk(self, audio_data: np.ndarray):
        """Add audio chunk to ring buffer"""
        with self.lock:
            self.ring_buffer.extend(audio_data)
            self.last_audio_time = time.time()
            
            # Check for silence
            rms = np.sqrt(np.mean(audio_data ** 2))
            if rms < SILENCE_THRESHOLD:
                if not self.is_silent:
                    self.is_silent = True
                    self.silence_start_time = self.last_audio_time
            else:
                self.is_silent = False
                self.silence_start_time = 0
    
    def should_transcribe(self) -> bool:
        """Check if it's time for transcription"""
        current_time = time.time()
        
        # Check transcription interval
        if current_time - self.last_transcription_time < TRANSCRIPTION_INTERVAL:
            return False
            
        # Check minimum audio duration
        with self.lock:
            if len(self.ring_buffer) < MIN_AUDIO_SAMPLES:
                return False
                
        return True
    
    def should_finalize(self) -> bool:
        """Check if we should send final result"""
        if not self.is_silent:
            return False
            
        current_time = time.time()
        silence_duration = current_time - self.silence_start_time
        
        return silence_duration >= SILENCE_DURATION
    
    def get_audio_window(self) -> Optional[np.ndarray]:
        """Get current audio window for transcription"""
        with self.lock:
            if len(self.ring_buffer) < MIN_AUDIO_SAMPLES:
                return None
            return np.array(self.ring_buffer)
    
    def clear_buffer(self):
        """Clear the ring buffer"""
        with self.lock:
            self.ring_buffer.clear()
    
    async def transcribe_audio(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """Transcribe audio and return text with behavior analysis"""
        try:
            segments, info = model.transcribe(
                audio_data,
                vad_filter=ASR_VAD,
                beam_size=ASR_BEAM,
                language=None,  # auto-detect
                no_speech_threshold=0.6,
                log_prob_threshold=-1.0,
                condition_on_previous_text=False,
                word_timestamps=True
            )
            
            # Collect all text segments and timestamps
            text_parts = []
            word_timestamps = []
            total_duration = 0
            
            for segment in segments:
                if segment.text.strip():
                    text_parts.append(segment.text.strip())
                    total_duration = max(total_duration, segment.end * 1000)  # Convert to ms
                    
                    # Collect word timestamps
                    if hasattr(segment, 'words'):
                        for word in segment.words:
                            word_timestamps.append({
                                'word': word.word,
                                'start': word.start * 1000,
                                'end': word.end * 1000
                            })
            
            full_text = " ".join(text_parts)
            
            # Behavior analysis
            if full_text:
                duration_ms = total_duration
                speech_analysis = self.behavior_analyzer.analyze_speech_patterns(
                    full_text, duration_ms, word_timestamps
                )
                
                # Check for nervous freeze
                if (speech_analysis['max_pause_ms'] >= BEHAVIOR_PAUSE_MS or 
                    speech_analysis['wpm'] < BEHAVIOR_WPM_LOW):
                    
                    score = 0.7  # Base score for nervous freeze
                    if speech_analysis['max_pause_ms'] >= BEHAVIOR_PAUSE_MS:
                        score += 0.2
                    if speech_analysis['wpm'] < BEHAVIOR_WPM_LOW:
                        score += 0.1
                    
                    await self.behavior_analyzer.emit_behavior_event(
                        self.session_id,
                        "nervous_freeze",
                        min(score, 1.0),
                        speech_analysis
                    )
                
                # Store segment for history
                self.speech_segments.append({
                    'text': full_text,
                    'timestamp': time.time(),
                    'analysis': speech_analysis
                })
                
                # Keep only last 10 segments
                if len(self.speech_segments) > 10:
                    self.speech_segments.pop(0)
            
            return {
                'text': full_text,
                'word_timestamps': word_timestamps,
                'duration_ms': total_duration,
                'analysis': speech_analysis if full_text else None
            }
            
        except Exception as e:
            print(f"Transcription error: {e}")
            return {'text': '', 'word_timestamps': [], 'duration_ms': 0, 'analysis': None}

@app.on_event("startup")
async def startup_event():
    load_model()

@app.get("/health")
async def health():
    return {"status": "ok", "model": ASR_MODEL, "device": ASR_DEVICE}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Get session_id from query params if provided
    session_id = websocket.query_params.get("session_id")
    session = StreamingSession(websocket, session_id)
    
    async def transcription_worker():
        """Background worker for transcription"""
        while session.running:
            try:
                # Check if we should transcribe
                if session.should_transcribe():
                    audio_window = session.get_audio_window()
                    if audio_window is not None:
                        # Transcribe audio with behavior analysis
                        result = await session.transcribe_audio(audio_window)
                        
                        if result['text']:
                            # Send partial result
                            response = {
                                "type": "partial",
                                "text": result['text'],
                                "timestamp": time.time(),
                                "analysis": result['analysis']
                            }
                            await websocket.send_text(json.dumps(response))
                        
                        session.last_transcription_time = time.time()
                
                # Check if we should finalize
                if session.should_finalize():
                    audio_window = session.get_audio_window()
                    if audio_window is not None:
                        # Final transcription with behavior analysis
                        result = await session.transcribe_audio(audio_window)
                        
                        if result['text']:
                            # Send final result
                            response = {
                                "type": "final",
                                "text": result['text'],
                                "timestamp": time.time(),
                                "analysis": result['analysis'],
                                "word_timestamps": result['word_timestamps']
                            }
                            await websocket.send_text(json.dumps(response))
                        
                        # Clear buffer after final
                        session.clear_buffer()
                        session.last_transcription_time = time.time()
                
                # Small delay to prevent busy waiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Transcription worker error: {e}")
                break
    
    # Start transcription worker
    worker_task = asyncio.create_task(transcription_worker())
    
    try:
        while True:
            # Receive audio data
            data = await websocket.receive_bytes()
            
            # Convert bytes to numpy array (Int16 LE mono)
            audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Add to session buffer
            session.add_audio_chunk(audio_chunk)
                
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        # Cleanup
        session.running = False
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)