class AudioCapture {
  constructor() {
    this.audioContext = null;
    this.workletNode = null;
    this.mediaStream = null;
    this.ws = null;
    this.isCapturing = false;
    this.targetSampleRate = 16000;
    this.sourceSampleRate = 48000; // Browser default
    
    // Backchannel timing controls
    this.lastBackchannelTime = 0;
    this.backchannelInterval = 2000; // 2 seconds minimum between backchannels
    this.backchannelPhrases = [
      "Понимаю…",
      "Слушаю…", 
      "Понятно…",
      "Хорошо…",
      "Продолжайте…"
    ];
    this.backchannelIndex = 0;
  }

  async initialize() {
    try {
      // Create AudioContext
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      
      // Add AudioWorklet module
      await this.audioContext.audioWorklet.addModule('./worklet.js');
      
      // Get microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: this.sourceSampleRate,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true
        }
      });
      
      console.log('Audio initialized successfully');
      return true;
    } catch (error) {
      console.error('Failed to initialize audio:', error);
      return false;
    }
  }

  connectToASR() {
    try {
      this.ws = new WebSocket('ws://localhost:8002/ws');
      
      this.ws.onopen = () => {
        console.log('Connected to ASR service');
      };
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('ASR result:', data);
        
        // Handle different message types
        if (data.type === 'partial') {
          // Show partial result "on the fly"
          this.displayTranscription(data);
          
          // Trigger backchannel if text is long enough and enough time has passed
          if (data.text && data.text.length > 3) {
            this.handleBackchannel();
          }
        } else if (data.type === 'final') {
          // Send final result to backend dialog manager
          this.handleFinalResult(data);
        } else if (data.type === 'error') {
          this.displayError(data);
        }
      };
      
      this.ws.onerror = (error) => {
        console.error('ASR WebSocket error:', error);
      };
      
      this.ws.onclose = () => {
        console.log('ASR WebSocket closed');
      };
      
      return true;
    } catch (error) {
      console.error('Failed to connect to ASR:', error);
      return false;
    }
  }

  startCapture() {
    if (this.isCapturing) return;
    
    try {
      // Create AudioWorkletNode
      this.workletNode = new AudioWorkletNode(this.audioContext, 'mic-capture-processor');
      
      // Connect microphone to worklet
      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      source.connect(this.workletNode);
      
      // Handle audio data from worklet
      this.workletNode.port.onmessage = (event) => {
        if (event.data.type === 'audioData') {
          this.processAudioData(event.data.data);
        }
      };
      
      this.isCapturing = true;
      console.log('Audio capture started');
    } catch (error) {
      console.error('Failed to start capture:', error);
    }
  }

  stopCapture() {
    if (!this.isCapturing) return;
    
    try {
      if (this.workletNode) {
        this.workletNode.disconnect();
        this.workletNode = null;
      }
      
      this.isCapturing = false;
      console.log('Audio capture stopped');
    } catch (error) {
      console.error('Failed to stop capture:', error);
    }
  }

  processAudioData(float32Data) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
    
    try {
      // Resample from 48kHz to 16kHz (simple linear interpolation)
      const resampledData = this.resample(float32Data, this.sourceSampleRate, this.targetSampleRate);
      
      // Convert Float32 to Int16
      const int16Data = this.float32ToInt16(resampledData);
      
      // Send binary data to ASR service
      this.ws.send(int16Data.buffer);
    } catch (error) {
      console.error('Failed to process audio data:', error);
    }
  }

  resample(inputData, inputSampleRate, outputSampleRate) {
    const ratio = inputSampleRate / outputSampleRate;
    const outputLength = Math.floor(inputData.length / ratio);
    const output = new Float32Array(outputLength);
    
    for (let i = 0; i < outputLength; i++) {
      const inputIndex = i * ratio;
      const index = Math.floor(inputIndex);
      const fraction = inputIndex - index;
      
      if (index + 1 < inputData.length) {
        // Linear interpolation
        output[i] = inputData[index] * (1 - fraction) + inputData[index + 1] * fraction;
      } else {
        output[i] = inputData[index];
      }
    }
    
    return output;
  }

  float32ToInt16(float32Data) {
    const int16Data = new Int16Array(float32Data.length);
    
    for (let i = 0; i < float32Data.length; i++) {
      // Clamp to [-1, 1] and convert to 16-bit integer
      const sample = Math.max(-1, Math.min(1, float32Data[i]));
      int16Data[i] = Math.round(sample * 32767);
    }
    
    return int16Data;
  }

  displayTranscription(data) {
    const transcriptionEl = document.getElementById('transcription');
    if (!transcriptionEl) return;
    
    transcriptionEl.innerHTML = `<strong>Говорите:</strong> ${data.text}`;
    transcriptionEl.style.color = '#666';
  }

  handleBackchannel() {
    const currentTime = Date.now();
    
    // Check if enough time has passed since last backchannel
    if (currentTime - this.lastBackchannelTime < this.backchannelInterval) {
      return;
    }
    
    // Get next backchannel phrase
    const phrase = this.backchannelPhrases[this.backchannelIndex];
    this.backchannelIndex = (this.backchannelIndex + 1) % this.backchannelPhrases.length;
    
    // Play backchannel immediately
    this.playTTS(phrase);
    this.lastBackchannelTime = currentTime;
    
    console.log('Backchannel:', phrase);
  }

  async handleFinalResult(data) {
    const transcriptionEl = document.getElementById('transcription');
    if (!transcriptionEl) return;
    
    // Display final result
    transcriptionEl.innerHTML = `<strong>Результат:</strong> ${data.text}`;
    transcriptionEl.style.color = '#000';
    
    console.log('Final transcription:', data.text);
    
    try {
      // Send to dialog manager and get response
      const reply = await this.sendToDialogManager(data);
      
      if (reply && reply.text) {
        // Play the AI response
        await this.playTTS(reply.text);
      }
    } catch (error) {
      console.error('Dialog manager error:', error);
      // Fallback response
      await this.playTTS("Понял, спасибо за информацию.");
    }
  }

  displayError(data) {
    const transcriptionEl = document.getElementById('transcription');
    if (!transcriptionEl) return;
    
    transcriptionEl.innerHTML = `<strong>Ошибка:</strong> ${data.message}`;
    transcriptionEl.style.color = '#f00';
  }

  async sendToDialogManager(data) {
    try {
      console.log('Sending to dialog manager:', data);
      
      const response = await fetch('http://localhost:8004/reply', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json' 
        },
        body: JSON.stringify({
          node: {
            id: "intro_1",
            category: "introduction",
            order: 1,
            question: "Расскажите о себе",
            weight: 1.0,
            success_criteria: ["опыт", "навыки", "образование"],
            followups: ["Что вас мотивирует?"],
            next_if_fail: "intro_2",
            next_if_pass: "experience_1"
          },
          transcript: data.text,
          scores: {},
          context: {}
        })
      });
      
      if (!response.ok) {
        throw new Error(`Dialog manager error: ${response.status}`);
      }
      
      const reply = await response.json();
      console.log('Dialog manager reply:', reply);
      return reply;
      
    } catch (error) {
      console.error('Dialog manager request failed:', error);
      
      // Return fallback response
      return {
        text: "Понял, спасибо за информацию.",
        type: "fallback"
      };
    }
  }

  async playTTS(text) {
    if (!text || !text.trim()) {
      console.warn('TTS: Empty text provided');
      return;
    }

    try {
      const response = await fetch(`http://localhost:8003/speak?text=${encodeURIComponent(text)}&format=wav`);
      
      if (!response.ok) {
        throw new Error(`TTS request failed: ${response.status}`);
      }

      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Create and play audio element
      const audio = new Audio(audioUrl);
      audio.preload = 'auto';
      
      // Clean up object URL after playing
      audio.onended = () => {
        URL.revokeObjectURL(audioUrl);
      };
      
      audio.onerror = (error) => {
        console.error('TTS playback error:', error);
        URL.revokeObjectURL(audioUrl);
      };

      await audio.play();
      console.log('TTS: Playing speech for:', text);
      
    } catch (error) {
      console.error('TTS error:', error);
      // Fallback: show text in console or display area
      this.displayTTSFallback(text);
    }
  }

  displayTTSFallback(text) {
    const transcriptionEl = document.getElementById('transcription');
    if (!transcriptionEl) return;
    
    const originalContent = transcriptionEl.innerHTML;
    transcriptionEl.innerHTML = `<strong>TTS (fallback):</strong> ${text}`;
    transcriptionEl.style.color = '#0066cc';
    
    // Restore original content after 3 seconds
    setTimeout(() => {
      transcriptionEl.innerHTML = originalContent;
      transcriptionEl.style.color = '#000';
    }, 3000);
  }

  async cleanup() {
    this.stopCapture();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
      this.mediaStream = null;
    }
    
    if (this.audioContext) {
      await this.audioContext.close();
      this.audioContext = null;
    }
  }
}

// Global instance
window.audioCapture = new AudioCapture();

// Initialize ASR controls when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  const startBtn = document.getElementById('startASR');
  const stopBtn = document.getElementById('stopASR');
  const statusEl = document.getElementById('asrStatus');
  const ttsTextInput = document.getElementById('ttsText');
  const testTTSBtn = document.getElementById('testTTS');
  
  if (startBtn && stopBtn && statusEl) {
    startBtn.addEventListener('click', async () => {
      try {
        const initialized = await window.audioCapture.initialize();
        if (initialized) {
          const connected = window.audioCapture.connectToASR();
          if (connected) {
            window.audioCapture.startCapture();
            startBtn.disabled = true;
            stopBtn.disabled = false;
            statusEl.textContent = 'активен';
            statusEl.classList.add('active');
          }
        }
      } catch (error) {
        console.error('Failed to start ASR:', error);
        alert('Ошибка запуска ASR: ' + error.message);
      }
    });
    
    stopBtn.addEventListener('click', async () => {
      try {
        await window.audioCapture.cleanup();
        startBtn.disabled = false;
        stopBtn.disabled = true;
        statusEl.textContent = 'отключен';
        statusEl.classList.remove('active');
      } catch (error) {
        console.error('Failed to stop ASR:', error);
      }
    });
  }

  // TTS test functionality
  if (testTTSBtn && ttsTextInput) {
    testTTSBtn.addEventListener('click', async () => {
      const text = ttsTextInput.value.trim();
      if (!text) {
        alert('Введите текст для озвучки');
        return;
      }
      
      try {
        testTTSBtn.disabled = true;
        testTTSBtn.textContent = 'Озвучивание...';
        await window.audioCapture.playTTS(text);
      } catch (error) {
        console.error('TTS test failed:', error);
        alert('Ошибка TTS: ' + error.message);
      } finally {
        testTTSBtn.disabled = false;
        testTTSBtn.textContent = 'Тест TTS';
      }
    });

    // Allow Enter key to trigger TTS
    ttsTextInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        testTTSBtn.click();
      }
    });
  }
});
