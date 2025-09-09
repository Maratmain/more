// Realtime клиент для AI-HR интервью
import { Room, RoomEvent, RemoteParticipant, RemoteTrack } from 'livekit-client';

class AIHRRealtimeClient {
  constructor() {
    this.room = new Room();
    this.setupEventListeners();
    this.setupUI();
  }

  setupEventListeners() {
    this.room.on(RoomEvent.Connected, () => {
      console.log('Подключен к комнате');
      this.updateStatus('Подключен к комнате');
    });

    this.room.on(RoomEvent.Disconnected, () => {
      console.log('Отключен от комнаты');
      this.updateStatus('Отключен от комнаты');
    });

    this.room.on(RoomEvent.ParticipantConnected, (participant) => {
      console.log('Участник подключился:', participant.identity);
      this.addParticipant(participant);
    });

    this.room.on(RoomEvent.ParticipantDisconnected, (participant) => {
      console.log('Участник отключился:', participant.identity);
      this.removeParticipant(participant);
    });

    this.room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      console.log('Трек подписан:', track.kind, participant.identity);
      this.attachTrack(track, participant);
    });
  }

  setupUI() {
    // Получение параметров из URL
    const urlParams = new URLSearchParams(window.location.search);
    const roomName = urlParams.get('room') || 'demo';
    const userName = urlParams.get('name') || 'Участник';

    // Заполнение полей
    document.getElementById('roomName').value = roomName;
    document.getElementById('userName').value = decodeURIComponent(userName);

    // Обработчики событий
    document.getElementById('joinBtn').addEventListener('click', () => this.joinRoom());
    document.getElementById('leaveBtn').addEventListener('click', () => this.leaveRoom());
    document.getElementById('copyInviteBtn').addEventListener('click', () => this.copyInviteLink());
  }

  async joinRoom() {
    const roomName = document.getElementById('roomName').value;
    const userName = document.getElementById('userName').value;

    if (!roomName || !userName) {
      alert('Заполните название комнаты и имя');
      return;
    }

    try {
      this.updateStatus('Получение токена...');
      
      // Получение токена от сервера
      const response = await fetch(`/api/token?room=${roomName}&identity=${encodeURIComponent(userName)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Ошибка получения токена');
      }

      this.updateStatus('Подключение к комнате...');

      // Подключение к комнате
      await this.room.connect(data.wsUrl, data.token);
      
      // Включение камеры и микрофона
      await this.room.localParticipant.enableCameraAndMicrophone();
      
      this.updateStatus('Подключен! Включите камеру и микрофон');
      this.toggleButtons(true);

    } catch (error) {
      console.error('Ошибка подключения:', error);
      this.updateStatus(`Ошибка: ${error.message}`);
    }
  }

  async leaveRoom() {
    await this.room.disconnect();
    this.toggleButtons(false);
    this.updateStatus('Отключен от комнаты');
  }

  copyInviteLink() {
    const roomName = document.getElementById('roomName').value;
    const userName = document.getElementById('userName').value;
    
    const inviteUrl = `${window.location.origin}?room=${roomName}&name=${encodeURIComponent(userName)}`;
    
    navigator.clipboard.writeText(inviteUrl).then(() => {
      alert('Ссылка-приглашение скопирована в буфер обмена!');
    }).catch(() => {
      // Fallback для старых браузеров
      const textArea = document.createElement('textarea');
      textArea.value = inviteUrl;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert('Ссылка-приглашение скопирована!');
    });
  }

  addParticipant(participant) {
    const participantsDiv = document.getElementById('participants');
    const participantDiv = document.createElement('div');
    participantDiv.id = `participant-${participant.identity}`;
    participantDiv.className = 'participant';
    participantDiv.innerHTML = `
      <h3>${participant.identity}</h3>
      <div class="video-container" id="video-${participant.identity}"></div>
    `;
    participantsDiv.appendChild(participantDiv);
  }

  removeParticipant(participant) {
    const participantDiv = document.getElementById(`participant-${participant.identity}`);
    if (participantDiv) {
      participantDiv.remove();
    }
  }

  attachTrack(track, participant) {
    const videoContainer = document.getElementById(`video-${participant.identity}`);
    if (!videoContainer) return;

    if (track.kind === 'video') {
      const videoElement = track.attach();
      videoElement.className = 'remote-video';
      videoContainer.appendChild(videoElement);
    } else if (track.kind === 'audio') {
      track.attach();
    }
  }

  updateStatus(message) {
    document.getElementById('status').textContent = message;
  }

  toggleButtons(connected) {
    document.getElementById('joinBtn').disabled = connected;
    document.getElementById('leaveBtn').disabled = !connected;
    document.getElementById('copyInviteBtn').disabled = !connected;
  }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
  new AIHRRealtimeClient();
});