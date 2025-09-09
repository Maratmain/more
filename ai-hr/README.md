# AI-HR Production System

Полнофункциональная система AI-HR для проведения интервью с использованием искусственного интеллекта, real-time коммуникаций и Telegram бота.

## Архитектура

- **LiveKit** - Real-time коммуникации с TURN сервером
- **Caddy** - Reverse proxy с автоматическим HTTPS
- **LLM Local** - Локальная модель Qwen2.5-7B через llama.cpp
- **Token Server** - Сервер для генерации токенов доступа
- **Telegram Bot** - Бот с Local Bot API для больших файлов
- **AI Services** - ASR, TTS, DM, CV, Report, Metrics

## Быстрый запуск

### 1. Настройка DNS
Укажите в DNS записи:
- `app.<ваш-домен>` → ваш публичный IP
- `video.<ваш-домен>` → ваш публичный IP

### 2. Конфигурация
```bash
# Скопируйте и заполните переменные
cp env.example .env

# Обязательно заполните:
# - DOMAIN=your-domain.com
# - TELEGRAM_BOT_TOKEN=ваш_токен
# - TELEGRAM_ADMINS=ваш_telegram_id
```

### 3. Запуск сервисов
```bash
# Основные сервисы
docker compose up -d livekit caddy llm-local token-server realtime-client

# AI сервисы
docker compose up -d api report asr tts dm cv metrics

# Telegram бот
docker compose up -d bot-api tg-bot
```

### 4. Проверка работоспособности
```bash
# HTTPS фронт
curl -I https://app.<ваш-домен>/

# Токен-сервер
curl https://app.<ваш-домен>/api/health

# Генерация токена
curl "https://app.<ваш-домен>/api/token?identity=test&room=demo"
```

## Первый звонок

### 1. Откройте интервью
```
https://app.<ваш-домен>/?room=demo&name=Я
```

### 2. Пригласите участника
Отправьте ссылку коллеге или откройте на другом устройстве:
```
https://app.<ваш-домен>/?room=demo&name=Кандидат
```

### 3. Разрешите доступ
- **Камера/микрофон** - HTTPS обязателен для доступа к медиа
- **Проверьте**: слышите/видите друг друга
- **Активный спикер** подсвечивается автоматически

### 4. Тест AI
- Скажите пару фраз
- Увидите backchannel реакции (≤2 сек)
- Получите итоговый ответ AI (≤5 сек)

### 5. Troubleshooting медиа
Если звук/видео не работает:
- **Откройте порты**: WSS:443, TURN/TLS:443, TURN/UDP:3478
- **Корпоративные сети**: разрешите UDP 50000–60000
- **Проверьте TURN**: `curl https://video.<домен>/api/turn`

## Чек-лист

1. **Разрешить доступ к камере/микрофону** в браузере
2. **Обе вкладки видят/слышат друг друга** - видео и аудио работают
3. **«Говорящий» подсвечивается** - активный участник выделен синим цветом
4. **Если не слышно** — проверить:
   - Вкладка активна (не в фоне)
   - Системный mute отключен
   - LiveKit сервер поднят (`curl http://localhost:7880`)

## Telegram бот

### Админ команды
```
/admin - Админ меню (только для TELEGRAM_ADMINS)
/candidate <id> - Профиль кандидата
/links <id> - Deep links для быстрого доступа
/broadcast <сегмент> - Рассылка по сегментам
/conferences - Список конференций
```

### Функции
- **PDF отчёт** - генерация и отправка отчетов
- **Оценки по вопросам** - пагинированный просмотр ответов
- **Deep links** - быстрый доступ к профилям кандидатов
- **Рассылка** - сегментированные уведомления
- **Большие файлы** - поддержка до 2GB через Local Bot API

### Настройка
```bash
# В .env укажите:
TELEGRAM_BOT_TOKEN=ваш_токен_от_BotFather
TELEGRAM_ADMINS=ваш_telegram_id
TELEGRAM_USE_LOCAL_BOT_API=true
```

## Troubleshooting

### Проверка контейнеров

```bash
docker ps                    # проверить запущенные контейнеры
docker logs ai-hr-livekit-1  # логи LiveKit
docker logs ai-hr-token-server-1  # логи token-server
```

### Проверка CORS и портов

- **CORS_ORIGIN**: должен совпадать с URL клиента (`http://localhost:5173`)
- **Порт 3001**: token-server должен отвечать
- **Порт 7880**: LiveKit должен отвечать

### Подключение извне

⚠️ **Важно**: Без STUN/TURN серверов в локальной сети возможны проблемы с подключением. Для продакшена потребуются дополнительные порты и настройка STUN/TURN серверов.

### Порты

- **3001**: Token Server
- **5173**: Realtime Client (статический сервер)
- **7880**: LiveKit Server
- **8002**: ASR Service
- **8003**: TTS Service
- **8004**: Dialog Manager
- **8005**: PDF Report Service
- **8006**: Main API (unified endpoints)
- **8007**: CV Processing Service
- **8008**: LLM Gateway Service
- **8009**: Telegram Bot (no external port)
- **8080**: Admin UI (static server)

### ASR без ресемплинга

Если ресемплинг в браузере не работает, можно временно отправить аудио в исходном формате (обычно 48 kHz):

```javascript
// В audio.js закомментировать ресемплинг:
// const resampledData = this.resample(float32Data, this.sourceSampleRate, this.targetSampleRate);
// this.ws.send(int16Data.buffer);

// И отправить напрямую:
const int16Data = this.float32ToInt16(float32Data);
this.ws.send(int16Data.buffer);
```

⚠️ **Важно**: В этом случае сервер ASR должен принять 48 kHz и сам выполнить ресемплинг к 16 kHz.

### WAV Batch Fallback

Если стриминг не работает, можно использовать батч-режим (больше задержка, но проще):

```javascript
// В audio.js - собирать WAV и слать батчем раз в 2-3 секунды
class WAVBatchCapture {
  constructor() {
    this.audioBuffer = [];
    this.batchInterval = 3000; // 3 seconds
    this.startBatchTimer();
  }
  
  addAudioChunk(float32Data) {
    this.audioBuffer.push(...float32Data);
  }
  
  startBatchTimer() {
    setInterval(() => {
      if (this.audioBuffer.length > 0) {
        this.sendWAVBatch();
        this.audioBuffer = [];
      }
    }, this.batchInterval);
  }
  
  sendWAVBatch() {
    // Convert to WAV format and send to ASR
    const wavBlob = this.createWAVBlob(this.audioBuffer);
    fetch('/api/asr/batch', {
      method: 'POST',
      body: wavBlob
    });
  }
}
```

**Минусы батч-режима:**
- Задержка 2-3 секунды вместо реального времени
- Больше нагрузка на сервер (обработка больших файлов)
- Менее отзывчивый интерфейс
- Сложнее обработка ошибок

## TTS Service

### Запуск без Docker

```bash
cd services/tts
pip install -r requirements.txt
uvicorn server:app --port 8003
```

### Готовые модели Piper

Для полной функциональности скачайте модели:
- **Русские голоса**: [rhasspy/piper-voices](https://github.com/rhasspy/piper-voices)
- **Английские голоса**: [rhasspy/piper-voices](https://github.com/rhasspy/piper-voices)
- **Бинарники**: [rhasspy/piper](https://github.com/rhasspy/piper/releases)

### Временная заглушка

Если Piper не установлен, используется fallback TTS (простой тон). Для тестирования можно добавить статические MP3 файлы:

```javascript
// В audio.js - временная заглушка
async playTTSFallback(text) {
  const audio = new Audio('/static/speech.mp3');
  await audio.play();
}
```

## Timing SLA (Service Level Agreement)

Для обеспечения ощущения низкой задержки (<1-2 секунды) система использует двухуровневый подход:

### Backchannel (Немедленная обратная связь)

- **Триггер**: При получении `partial` ASR результата с длиной текста > 3 символов
- **Время отклика**: ≤ 500 мс
- **Фразы**: "Понимаю…", "Слушаю…", "Понятно…", "Хорошо…", "Продолжайте…"
- **Частота**: Не чаще 1 раза в 2 секунды
- **Цель**: Показать, что система "слушает" и понимает речь

### Final Response (Основной ответ)

- **Триггер**: При получении `final` ASR результата
- **Время отклика**: ≤ 2-3 секунды
- **Процесс**: 
  1. Отправка в dialog manager (`/dm/reply`)
  2. Получение AI ответа
  3. TTS синтез и воспроизведение
- **Цель**: Предоставить содержательный ответ

### Общее SLA

- **Суммарное время до "смыслового ответа"**: ≤ 5 секунд
- **Backchannel**: ≤ 500 мс (немедленная обратная связь)
- **Final TTS**: ≤ 2-3 с (содержательный ответ)

### Fallback режим

Если backchannel не работает, система переходит в режим только final-ответов:

```javascript
// Отключить backchannel в audio.js
this.backchannelInterval = 0; // Отключить
```

### LiveKit интеграция (опционально)

Для отправки системных событий в комнату можно использовать LiveKit JS SDK:

```javascript
// Отправка события в комнату
room.localParticipant.publishData(
  new TextEncoder().encode(JSON.stringify({
    type: 'backchannel',
    text: 'Понимаю...'
  }))
);
```

## Dialog Manager Service

### Запуск без Docker

```bash
cd services/dm
pip install -r requirements.txt
uvicorn main:app --port 8004
```

### Тестирование API

```bash
curl -X POST "http://localhost:8004/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "node": {
      "id": "intro_1",
      "category": "introduction", 
      "order": 1,
      "question": "Расскажите о себе",
      "weight": 1.0,
      "success_criteria": ["опыт", "навыки", "образование"],
      "followups": ["Что вас мотивирует?"],
      "next_if_fail": "intro_2",
      "next_if_pass": "experience_1"
    },
    "transcript": "У меня есть опыт работы в IT более 5 лет",
    "scores": {},
    "context": {}
  }'
```

### Автодокументация

- **Swagger UI**: http://localhost:8004/docs
- **ReDoc**: http://localhost:8004/redoc

## Scenario System

### Структура сценариев

Сценарии интервью хранятся в JSON формате с поддержкой:
- **Узлы вопросов** (L1-L4 уровни сложности)
- **Критерии успеха** для каждого вопроса
- **Логика ветвления** (drill-down vs next)
- **Политики оценки** (пороги, веса)

### Тестирование сценариев

```bash
cd services/api/scenario
python test_scenario.py
```

### Пример сценария

```json
{
  "schema_version": "0.1",
  "policy": {"drill_threshold": 0.7},
  "start_id": "django_l1_intro",
  "nodes": [
    {
      "id": "django_l1_intro",
      "category": "python_backend",
      "order": 1,
      "question": "Расскажите о вашем опыте работы с Django",
      "weight": 1.0,
      "success_criteria": ["django", "python", "веб-разработка"],
      "next_if_fail": "django_l2_basics",
      "next_if_pass": "django_l3_advanced"
    }
  ]
}
```

### Fallback генератор

Если сценарий не найден, система автоматически генерирует 3-узловую цепочку:

```python
from scenario import generate_fallback_scenario
scenario = generate_fallback_scenario("react_frontend")
```

## BARS Scoring System

### Behavioral Anchored Rating Scales

Система оценки с поведенческими якорями (BARS) для объективной оценки кандидатов:

- **0.0**: Нет доказательств / Плохая производительность
- **0.3**: Ниже ожиданий / Ограниченные доказательства  
- **0.7**: Соответствует ожиданиям / Хорошие доказательства
- **1.0**: Превышает ожидания / Отличные доказательства

### Взвешенная агрегация

```python
from services.api.scoring import QAnswer, score_block, score_overall

# Ответы по вопросам
answers = [
    QAnswer("q1", "Django", 1.0, 0.5),  # отличный ответ, важный вопрос
    QAnswer("q2", "Django", 0.7, 0.5),  # хороший ответ, важный вопрос
    QAnswer("q3", "React", 0.3, 0.8),   # слабый ответ, критичный вопрос
]

# Оценка блока
django_score = score_block(answers, "Django")  # 0.85

# Общая оценка
block_scores = {"Django": 0.85, "React": 0.3}
block_weights = {"Django": 0.6, "React": 0.4}
overall = score_overall(block_scores, block_weights)  # 0.63
```

### Формула итогового матча

```python
from services.api.scoring import calculate_match_score

candidate_scores = {"Django": 0.8, "React": 0.6}
job_requirements = {"Django": 0.7, "React": 0.5}
block_weights = {"Django": 0.6, "React": 0.4}

match_score = calculate_match_score(
    candidate_scores, job_requirements, block_weights
)  # 1.0 (perfect match)
```

### Тестирование

```bash
cd services/api/scoring/tests
python test_bars.py
```

### Анализ производительности

```python
from services.api.scoring import analyze_performance

analysis = analyze_performance(answers, block_weights)
print(analysis["overall_score"])      # 0.63
print(analysis["overall_level"])      # "Meets expectations"
print(analysis["strengths"])          # ["Django"]
print(analysis["weaknesses"])         # ["React"]
```

## PDF Report Service

### WeasyPrint-based Report Generation

Сервис генерации профессиональных PDF-отчётов из результатов интервью:

- **Общий %-match**: Взвешенная оценка соответствия
- **Таблица блоков**: Детальная разбивка по навыкам
- **Плюсы/минусы**: Сильные и слабые стороны
- **Цитаты-доказательства**: Подтверждения из CV/транскриптов
- **Рекомендации**: Итоговая оценка 0-10

### Запуск

```bash
# Docker
docker compose up -d report

# Локально (требует системные зависимости)
pip install -r services/report/requirements.txt
uvicorn services.report.main:app --port 8005
```

### API Endpoints

#### POST /report
Генерирует PDF-отчёт из данных интервью:

```bash
curl -X POST "http://localhost:8005/report" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate": {
      "name": "Алексей Петров",
      "experience": "5 лет Python разработки",
      "location": "Москва"
    },
    "vacancy": {
      "title": "Senior Python Developer",
      "department": "Backend Development",
      "level": "Senior"
    },
    "blocks": [
      {"name": "Python", "score": 0.9, "weight": 0.3},
      {"name": "Django", "score": 0.8, "weight": 0.25},
      {"name": "Database", "score": 0.7, "weight": 0.2}
    ],
    "positives": ["Отличное знание Python", "Опыт с Django ORM"],
    "negatives": ["Слабое знание Docker", "Ограниченный CI/CD опыт"],
    "quotes": [
      {
        "text": "Работал с Django более 4 лет, создавал высоконагруженные приложения",
        "source": "Interview Transcript"
      }
    ],
    "rating_0_10": 7.5
  }' \
  --output report.pdf
```

#### POST /report/html
Генерирует HTML-версию (fallback если PDF не работает):

```bash
curl -X POST "http://localhost:8005/report/html" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  --output report.html
```

### Тестирование

```bash
cd services/report
python test_report.py
```

### Системные зависимости (для локального запуска)

#### Ubuntu/Debian:
```bash
sudo apt-get install libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 \
  libfontconfig1 libcairo2 libgdk-pixbuf2.0-0 libglib2.0-0 \
  libgtk-3-0 libgstreamer1.0-0 libgstreamer-plugins-base1.0-0
```

#### macOS:
```bash
brew install cairo pango gdk-pixbuf libffi
```

#### Windows:
```bash
# Установить через conda или использовать Docker
conda install -c conda-forge cairo pango gdk-pixbuf
```

### Структура отчёта

1. **Заголовок**: Название, %-match, рейтинг 0-10
2. **Информация о кандидате**: Имя, позиция, опыт
3. **Требования к вакансии**: Должность, отдел, уровень
4. **Таблица навыков**: Блоки с оценками и весами
5. **Сильные стороны**: Плюсы >0.7
6. **Области для улучшения**: Минусы <0.7
7. **Доказательства**: Цитаты из интервью/CV
8. **Подвал**: Дата генерации, ID отчёта

### WeasyPrint преимущества

- **Нативный HTML/CSS → PDF**: Без внешних браузеров
- **Профессиональное качество**: Подходит для отчётов и инвойсов
- **Быстрая генерация**: Оптимизирован для серверного использования
- **CSS поддержка**: Полная поддержка современных стилей

## Main API Service

### Unified API Endpoints

Главный API сервис предоставляет единую точку входа для всех операций:

- **POST /scenario/load**: Загрузка и сохранение сценариев
- **POST /score/aggregate**: Агрегация оценок с BARS
- **POST /report/render**: Генерация PDF отчётов
- **GET /scenario/list**: Список доступных сценариев
- **GET /stats**: Статистика использования

### Запуск

```bash
# Docker
docker compose up -d api

# Локально
cd services/api
pip install -r requirements.txt
uvicorn main:app --port 8006
```

### API Endpoints

#### POST /scenario/load
Загружает и сохраняет сценарий в `data/scenarios/<id>.json`:

```bash
curl -X POST "http://localhost:8006/scenario/load" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "python_backend",
    "schema_version": "0.1",
    "policy": {"drill_threshold": 0.7},
    "start_id": "python_l1_intro",
    "nodes": [
      {
        "id": "python_l1_intro",
        "category": "python_backend",
        "order": 1,
        "question": "Расскажите о вашем опыте работы с Python",
        "weight": 1.0,
        "success_criteria": ["python", "опыт", "проекты"],
        "next_if_fail": "python_l2_basics",
        "next_if_pass": "python_l3_advanced"
      }
    ]
  }'
```

#### POST /score/aggregate
Агрегирует оценки с использованием BARS системы:

```bash
curl -X POST "http://localhost:8006/score/aggregate" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": "q1", "block": "Python", "score": 0.9, "weight": 0.5},
      {"question_id": "q2", "block": "Django", "score": 0.8, "weight": 0.6}
    ],
    "block_weights": {
      "Python": 0.4,
      "Django": 0.35,
      "Database": 0.25
    }
  }'
```

#### POST /report/render
Генерирует PDF отчёт через проксирование в сервис отчётов:

```bash
curl -X POST "http://localhost:8006/report/render" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate": {"name": "Алексей Петров", "experience": "5 лет Python"},
    "vacancy": {"title": "Senior Python Developer", "department": "Backend"},
    "blocks": [
      {"name": "Python", "score": 0.8, "weight": 0.4},
      {"name": "Django", "score": 0.7, "weight": 0.35}
    ],
    "positives": ["Отличное знание Python"],
    "negatives": ["Слабое знание Docker"],
    "quotes": [{"text": "Работал с Django 4 года", "source": "Interview"}],
    "rating_0_10": 7.5
  }'
```

#### GET /scenario/list
Получает список всех загруженных сценариев:

```bash
curl "http://localhost:8006/scenario/list"
```

#### GET /stats
Получает статистику использования API:

```bash
curl "http://localhost:8006/stats"
```

### Тестирование

```bash
cd services/api
python test_api.py
```

### Интеграция с другими сервисами

- **BARS Scoring**: Использует модуль `services/api/scoring/`
- **Report Service**: Проксирует запросы на `http://report:8005`
- **Data Storage**: Сохраняет сценарии в `data/scenarios/`
- **Scenario System**: Интегрирован с `services/api/scenario/`

### Структура данных

#### Scenario Format
```json
{
  "id": "scenario_id",
  "schema_version": "0.1",
  "policy": {"drill_threshold": 0.7},
  "start_id": "first_node_id",
  "nodes": [
    {
      "id": "node_id",
      "category": "skill_category",
      "order": 1,
      "question": "Question text",
      "weight": 1.0,
      "success_criteria": ["keyword1", "keyword2"],
      "next_if_fail": "next_node_id",
      "next_if_pass": "next_node_id"
    }
  ]
}
```

#### Score Aggregation Response
```json
{
  "block_scores": {"Python": 0.8, "Django": 0.7},
  "overall": 0.75,
  "overall_percentage": 75.0,
  "analysis": {
    "strengths": ["Python"],
    "weaknesses": ["Database"],
    "overall_level": "Meets expectations"
  },
  "summary": {
    "total_questions": 5,
    "blocks_assessed": 2,
    "average_score": 0.75
  }
}
```

## CV Processing Service

### Vector Database Integration

Сервис обработки резюме с извлечением текста, генерацией эмбеддингов и хранением в Qdrant:

- **Извлечение текста**: PDF, DOCX, TXT файлы
- **Семантический поиск**: Поиск по смыслу с Sentence Transformers
- **Векторная база**: Qdrant Cloud (1 GB free tier)
- **Chunking**: Разбивка на фрагменты с перекрытием

### Настройка Qdrant Cloud

1. **Регистрация**: [Qdrant Cloud](https://cloud.qdrant.io/)
2. **Создание кластера**: 1 GB free tier
3. **Получение данных**: URL и API ключ

### Конфигурация

```bash
# Скопировать env.example в .env
cp services/cv/env.example services/cv/.env
```

```env
QDRANT_URL=https://your-cluster-url.qdrant.tech
QDRANT_API_KEY=your-api-key-here
QDRANT_COLLECTION=cv_chunks
EMBEDDER=sentence-transformers/all-MiniLM-L6-v2
```

### Запуск

```bash
# Docker
docker compose up -d cv

# Локально
cd services/cv
pip install -r requirements.txt
uvicorn main:app --port 8007
```

### API Endpoints

#### POST /ingest
Загрузить и обработать резюме:

```bash
curl -X POST "http://localhost:8007/ingest" \
  -F "file=@resume.pdf"
```

#### POST /search
Семантический поиск:

```bash
curl -X POST "http://localhost:8007/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python разработка Django",
    "limit": 5,
    "score_threshold": 0.7
  }'
```

#### GET /cvs
Список всех резюме:

```bash
curl "http://localhost:8007/cvs"
```

### Технические детали

- **Модель**: all-MiniLM-L6-v2 (384-мерные векторы)
- **Chunking**: 800 символов с перекрытием 100
- **Метрика**: Cosine similarity
- **Производительность**: ~1000 предложений/сек

### Тестирование

```bash
cd services/cv
python test_cv.py
```

### Интеграция с другими сервисами

```python
# Поиск релевантных фрагментов для контекста интервью
cv_context = requests.post('http://cv:8007/search', json={
    'query': current_question,
    'limit': 3
}).json()
```

## Telegram Bot Service

### CV Upload via Telegram

Telegram бот для удобной загрузки резюме в систему AI-HR:

- **Загрузка файлов**: PDF, DOCX, DOC, TXT
- **Автоматическая обработка**: Передача в CV Processing Service
- **Уведомления**: Статус обработки в реальном времени
- **Мониторинг**: Проверка состояния AI-HR сервисов

### Настройка бота

1. **Создание бота**:
   - Найдите [@BotFather](https://t.me/BotFather) в Telegram
   - Отправьте `/newbot` и следуйте инструкциям
   - Сохраните полученный токен

2. **Конфигурация**:
   ```bash
   cp services/tg-bot/env.example services/tg-bot/.env
   ```

   ```env
   TELEGRAM_BOT_TOKEN=your-bot-token-here
   CV_SERVICE_URL=http://cv:8007
   MAX_FILE_SIZE_MB=20
   BOT_USERNAME=your_bot_username
   ```

### Запуск

```bash
# Docker
docker compose up -d tg-bot

# Локально
cd services/tg-bot
pip install -r requirements.txt
python main.py
```

### Использование

#### Команды бота:
- `/start` - Приветствие и инструкции
- `/help` - Подробная справка
- `/status` - Проверка состояния AI-HR сервиса

#### Загрузка резюме:
1. Отправьте файл резюме в чат с ботом
2. Бот проверит формат и размер
3. Файл будет обработан автоматически
4. Вы получите уведомление о результате

### Ограничения

#### Размер файла: 20 MB
- **Причина**: Ограничение Telegram Bot API
- **Решение**: Для больших файлов используйте Pyrogram/Telethon

#### Альтернативы для больших файлов:

**Pyrogram (рекомендуется):**
```python
from pyrogram import Client
app = Client("my_account")
with app:
    app.send_document("chat_id", "large_file.pdf")
```

**Telethon:**
```python
from telethon import TelegramClient
client = TelegramClient('session', api_id, api_hash)
await client.send_file("chat_id", "large_file.pdf")
```

### Тестирование

```bash
cd services/tg-bot
python test_bot.py
```

### Архитектура

```
Telegram User → Telegram Bot → CV Processing Service → Qdrant
```

### Безопасность

- **Токен бота**: Храните в `.env` файле
- **Временные файлы**: Автоматически удаляются
- **Данные**: Передаются только в CV Processing Service

## Admin UI

### Веб-панель управления

Простая веб-панель для администрирования системы AI-HR:

- **📋 Управление резюме**: Просмотр и удаление загруженных CV
- **🔍 Семантический поиск**: Поиск по содержимому резюме
- **📊 Генерация отчётов**: Создание PDF отчётов
- **🔧 Мониторинг**: Проверка статуса всех сервисов

### Запуск

```bash
# Перейти в директорию
cd ui-admin

# Запустить простой HTTP сервер
python -m http.server 8080
# или
npx serve -p 8080
# или
php -S localhost:8080

# Открыть http://localhost:8080
```

### Возможности

#### Управление резюме
- Просмотр списка всех загруженных CV
- Удаление резюме по ID
- Автоматическое обновление списка

#### Семантический поиск
- Поиск по ключевым словам
- Настройка количества результатов
- Отображение релевантности

#### Генерация отчётов
- Заполнение данных кандидата
- Настройка оценок и комментариев
- Скачивание PDF отчёта

#### Мониторинг сервисов
- Проверка статуса CV Service
- Проверка статуса Report Service
- Проверка статуса Main API

### API Endpoints

#### CV Service
```bash
# Список CV
curl "http://localhost:8007/cvs/list"

# Поиск
curl "http://localhost:8007/cvs/search?q=Python&top_k=5"

# Удаление
curl -X DELETE "http://localhost:8007/cvs/{cv_id}"
```

#### Report Service
```bash
# Генерация PDF
curl -X POST "http://localhost:8005/report" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  --output report.pdf
```

### Структура

```
ui-admin/
├── index.html          # Главная страница
├── app.js             # JavaScript логика
└── README.md          # Документация
```

### Настройка

Отредактируйте `app.js` для изменения API URLs:

```javascript
const API_CONFIG = {
    CV_SERVICE: 'http://localhost:8007',
    REPORT_SERVICE: 'http://localhost:8005',
    MAIN_API: 'http://localhost:8006'
};
```

## Demo Flow

### E2E Demo Script

Полный демонстрационный скрипт, показывающий весь workflow: загрузка CV → поиск → генерация отчёта.

#### Запуск демо

```bash
# Bash версия (Linux/macOS)
chmod +x scripts/demo_e2e.sh
./scripts/demo_e2e.sh

# Python версия (все платформы)
python scripts/demo_e2e.py
```

#### Что делает демо

1. **Загрузка CV**: Создаёт sample CV и загружает в систему
2. **Поиск**: Ищет по ключевому слову "Django" 
3. **Отчёт**: Генерирует PDF отчёт с результатами

#### Результат

- `report.pdf` - сгенерированный отчёт
- `demo_e2e.log` - подробный лог (Python версия)
- Вывод в консоль с результатами каждого шага

#### Ручной запуск шагов

```bash
# 1. Загрузка CV
curl -F file=@samples/cv1.pdf http://localhost:8007/ingest

# 2. Поиск
curl "http://localhost:8007/cvs/search?q=Django&top_k=3"

# 3. Генерация отчёта
curl -X POST http://localhost:8005/report \
  -H "Content-Type: application/json" \
  -d '{
    "candidate": {"name": "Алексей Петров"},
    "vacancy": {"title": "Senior Python Developer"},
    "blocks": [{"name": "Python", "score": 0.8, "weight": 0.4}],
    "positives": ["Отличное знание Python"],
    "negatives": ["Слабое знание Docker"],
    "quotes": [{"text": "Работал с Django 4 года", "source": "Interview"}],
    "rating_0_10": 7.5
  }' \
  --output report.pdf
```

## System Startup

### Полный запуск системы

```bash
# 1. Клонировать репозиторий
git clone <repository-url>
cd ai-hr

# 2. Настроить переменные окружения
cp .env.example .env
# Отредактировать .env файл с вашими ключами

# 3. Запустить все сервисы
docker compose up -d

# 4. Проверить статус
docker compose ps
```

### Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните необходимые ключи:

```bash
# Основные сервисы
cp .env.example .env
```

#### Обязательные ключи:

1. **Telegram Bot**:
   - Получите токен от [@BotFather](https://t.me/BotFather)
   - `TELEGRAM_BOT_TOKEN=your_bot_token_here`

2. **OpenRouter (LLM)**:
   - Зарегистрируйтесь на [OpenRouter](https://openrouter.ai/)
   - Получите API ключ: `OPENROUTER_API_KEY=your_api_key`

3. **Qdrant Cloud**:
   - Создайте кластер на [Qdrant Cloud](https://cloud.qdrant.io/)
   - Скопируйте URL и API ключ:
     - `QDRANT_URL=https://your-cluster.qdrant.io:6333`
     - `QDRANT_API_KEY=your_qdrant_key`

#### Опциональные настройки:

- **LiveKit**: Используйте `devkey/secret` для разработки
- **Модели**: Выберите LLM модель в `LLM_MODEL`
- **Файлы**: Настройте лимиты в `MAX_FILE_SIZE_MB`

### Документация по сервисам

Каждый сервис имеет подробную документацию:

- **Telegram Bot**: [`services/tg-bot/README.md`](services/tg-bot/README.md) - Настройка бота, лимиты файлов, Local Bot API
- **LLM Gateway**: [`services/llm-gw/README.md`](services/llm-gw/README.md) - OpenRouter, OpenAI-compatible, streaming
- **Vector Service**: [`services/vector/README.md`](services/vector/README.md) - Qdrant Cloud, embedding модели
- **Token Server**: [`services/token-server/README.md`](services/token-server/README.md) - LiveKit токены, JWT

### Порядок проверки сервисов

```bash
# 1. Проверить базовые сервисы
curl http://localhost:6333/health          # Qdrant
curl http://localhost:8007/health          # CV Service
curl http://localhost:8005/health          # Report Service

# 2. Проверить AI сервисы
curl http://localhost:8002/health          # ASR Service
curl http://localhost:8003/health          # TTS Service
curl http://localhost:8004/health          # Dialog Manager

# 3. Проверить интеграции
curl http://localhost:8006/health          # Main API
curl http://localhost:3001/health          # Token Server
curl http://localhost:7880/health          # LiveKit

# 4. Запустить демо
python scripts/demo_e2e.py
```

### Локальный запуск без Docker

Если Docker недоступен, можно запустить сервисы локально:

```bash
# 1. Qdrant (требует Docker)
docker run -p 6333:6333 qdrant/qdrant:latest

# 2. CV Service
cd services/cv
pip install -r requirements.txt
uvicorn main:app --port 8007

# 3. Report Service  
cd services/report
pip install -r requirements.txt
uvicorn main:app --port 8005

# 4. ASR Service
cd services/asr
pip install -r requirements.txt
uvicorn server:app --port 8002

# 5. TTS Service
cd services/tts
pip install -r requirements.txt
uvicorn main:app --port 8003

# 6. Dialog Manager
cd services/dm
pip install -r requirements.txt
uvicorn main:app --port 8004

# 7. Main API
cd services/api
pip install -r requirements.txt
uvicorn main:app --port 8006

# 8. Token Server
cd services/token-server
npm install
npm start

# 9. LiveKit (требует Docker)
docker run -p 7880:7880 livekit/livekit-server:latest --dev --bind 0.0.0.0
```

### Таблица портов

| Порт | Сервис | Описание |
|------|--------|----------|
| 3001 | Token Server | JWT токены для LiveKit |
| 6333 | Qdrant | Векторная база данных |
| 7880 | LiveKit | WebRTC сервер |
| 8002 | ASR Service | Распознавание речи |
| 8003 | TTS Service | Синтез речи |
| 8004 | Dialog Manager | Управление диалогом |
| 8005 | Report Service | Генерация PDF отчётов |
| 8006 | Main API | Унифицированные API |
| 8007 | CV Service | Обработка резюме |
| 8080 | Admin UI | Веб-панель управления |

## Ресурсы и лимиты

### Qdrant

- **Бесплатный план**: 1 GB storage
- **Ёмкость**: ~1 млн векторов 768d
- **Прототип**: Отлично подходит для демо
- **Документация**: [qdrant.tech](https://qdrant.tech)

### Embedding модели

- **all-MiniLM-L6-v2**: 384d, ~5x быстрее топовых моделей
- **Качество**: Приемлемое для большинства задач
- **Размер**: ~80 MB
- **Документация**: [sbert.net](https://www.sbert.net)

### Telegram Bot API

- **Лимит файлов**: 20 MB
- **Обход**: Использование file_id для больших файлов
- **Альтернативы**: Pyrogram, Telethon для больших файлов
- **Документация**: [GitHub](https://github.com/python-telegram-bot/python-telegram-bot)

### Рекомендуемые ресурсы

#### Минимальные требования
- **RAM**: 4 GB
- **CPU**: 2 cores
- **Storage**: 10 GB
- **Network**: Стабильное подключение

#### Рекомендуемые требования
- **RAM**: 8 GB
- **CPU**: 4 cores
- **Storage**: 50 GB SSD
- **Network**: Высокоскоростное подключение

### Мониторинг ресурсов

```bash
# Проверка использования ресурсов
docker stats

# Проверка логов
docker compose logs -f

# Проверка места на диске
docker system df

# Очистка неиспользуемых ресурсов
docker system prune
```
