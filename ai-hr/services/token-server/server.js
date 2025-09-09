const express = require('express');
const cors = require('cors');
const { AccessToken } = require('livekit-server-sdk');

const app = express();
const port = process.env.PORT || 3000;

// CORS для фронтенда
app.use(cors({
  origin: process.env.CORS_ORIGIN || 'http://localhost:5173',
  credentials: true
}));

app.use(express.json());

// Генерация токена для комнаты
app.get('/api/token', (req, res) => {
  try {
    const { room, identity } = req.query;
    
    if (!room || !identity) {
      return res.status(400).json({ 
        error: 'Требуются параметры room и identity' 
      });
    }

    const apiKey = process.env.LIVEKIT_API_KEY;
    const apiSecret = process.env.LIVEKIT_API_SECRET;
    const wsUrl = process.env.LIVEKIT_WS_URL;

    if (!apiKey || !apiSecret || !wsUrl) {
      return res.status(500).json({ 
        error: 'Не настроены переменные окружения LiveKit' 
      });
    }

    // Создание токена доступа
    const token = new AccessToken(apiKey, apiSecret, {
      identity: identity,
      ttl: '1h'
    });

    // Разрешения для участника
    token.addGrant({
      room: room,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
      canPublishData: true
    });

    const jwt = token.toJwt();

    res.json({
      token: jwt,
      wsUrl: wsUrl,
      room: room,
      identity: identity
    });

  } catch (error) {
    console.error('Ошибка генерации токена:', error);
    res.status(500).json({ 
      error: 'Ошибка генерации токена доступа' 
    });
  }
});

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'ok',
    wsUrl: process.env.LIVEKIT_WS_URL,
    timestamp: new Date().toISOString()
  });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Токен-сервер запущен на порту ${port}`);
  console.log(`CORS origin: ${process.env.CORS_ORIGIN}`);
  console.log(`LiveKit WS URL: ${process.env.LIVEKIT_WS_URL}`);
});