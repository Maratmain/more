# CV Processing Service

Сервис обработки резюме с извлечением текста, генерацией эмбеддингов и хранением в Qdrant.

## Возможности

- **Извлечение текста**: PDF, DOCX, TXT файлы
- **Семантический поиск**: Поиск по смыслу с использованием Sentence Transformers
- **Векторная база**: Хранение в Qdrant Cloud
- **Chunking**: Разбивка на фрагменты с перекрытием
- **REST API**: Полный набор эндпойнтов для управления

## Быстрый старт

### 1. Настройка Qdrant Cloud

1. Зарегистрируйтесь на [Qdrant Cloud](https://cloud.qdrant.io/)
2. Создайте кластер (1 GB free tier)
3. Получите URL и API ключ

### 2. Конфигурация

Скопируйте `env.example` в `.env` и заполните:

```bash
cp env.example .env
```

```env
# Qdrant Vector Database Configuration
QDRANT_URL=https://your-cluster-url.qdrant.tech
QDRANT_API_KEY=your-api-key-here
QDRANT_COLLECTION=cv_chunks

# Embedding Model Configuration
EMBEDDER=sentence-transformers/all-MiniLM-L6-v2

# Service Configuration
PORT=8007
CHUNK_SIZE=800
CHUNK_OVERLAP=100
```

### 3. Запуск

#### Docker (рекомендуется)
```bash
docker compose up -d cv
```

#### Локально
```bash
pip install -r requirements.txt
uvicorn main:app --port 8007
```

## API Endpoints

### POST /ingest
Загрузить и обработать резюме:

```bash
curl -X POST "http://localhost:8007/ingest" \
  -F "file=@resume.pdf"
```

**Поддерживаемые форматы**: PDF, DOCX, TXT

### POST /search
Семантический поиск по резюме:

```bash
curl -X POST "http://localhost:8007/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python разработка Django",
    "limit": 5,
    "score_threshold": 0.7
  }'
```

### GET /cvs
Список всех резюме:

```bash
curl "http://localhost:8007/cvs"
```

### GET /stats
Статистика базы данных:

```bash
curl "http://localhost:8007/stats"
```

### DELETE /cvs/{cv_id}
Удалить резюме:

```bash
curl -X DELETE "http://localhost:8007/cvs/{cv_id}"
```

## Тестирование

```bash
python test_cv.py
```

## Технические детали

### Модель эмбеддингов
- **all-MiniLM-L6-v2**: 384-мерные векторы
- **Скорость**: ~1000 предложений/сек
- **Качество**: Хорошо для семантического поиска

### Chunking стратегия
- **Размер чанка**: 800 символов (настраивается)
- **Перекрытие**: 100 символов
- **Разбивка**: По границам предложений

### Qdrant конфигурация
- **Метрика**: Cosine similarity
- **Размер вектора**: 384
- **Коллекция**: cv_chunks

## Troubleshooting

### Проблемы с PDF
Если PDF не читается, попробуйте:
1. Конвертировать в TXT
2. Использовать другой PDF reader
3. Проверить, что PDF не защищен паролем

### Проблемы с Qdrant
1. Проверьте URL и API ключ
2. Убедитесь, что кластер активен
3. Проверьте лимиты free tier

### Проблемы с памятью
Для больших файлов:
1. Уменьшите CHUNK_SIZE
2. Увеличьте CHUNK_OVERLAP
3. Используйте более мощный сервер

## Производительность

### Free Tier Qdrant
- **1 GB storage**
- **~1M векторов 768-d**
- **~2.6M векторов 384-d** (наш случай)

### Рекомендации
- **Малые резюме**: < 10 страниц
- **Средние резюме**: 10-50 страниц
- **Большие резюме**: > 50 страниц (требует оптимизации)

## Интеграция

### С Main API
```python
import requests

# Загрузить резюме
with open('resume.pdf', 'rb') as f:
    response = requests.post('http://cv:8007/ingest', files={'file': f})

# Поиск по резюме
search_response = requests.post('http://cv:8007/search', json={
    'query': 'Python Django опыт',
    'limit': 5
})
```

### С Dialog Manager
```python
# Получить релевантные фрагменты резюме для контекста
cv_context = requests.post('http://cv:8007/search', json={
    'query': current_question,
    'limit': 3
}).json()
```

## Мониторинг

### Health Check
```bash
curl "http://localhost:8007/health"
```

### Метрики
- Количество обработанных резюме
- Размер базы данных
- Время обработки
- Качество поиска

## Безопасность

- **API ключи**: Храните в .env файле
- **Файлы**: Временные файлы удаляются после обработки
- **Данные**: Эмбеддинги не содержат исходный текст
- **Доступ**: Ограничьте доступ к Qdrant кластеру
