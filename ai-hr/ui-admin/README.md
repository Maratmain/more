# AI-HR Admin Panel

Простая веб-панель для управления резюме, поиска и генерации отчётов в системе AI-HR.

## Возможности

- **📋 Управление резюме**: Просмотр списка загруженных CV
- **🔍 Семантический поиск**: Поиск по содержимому резюме через Qdrant
- **📊 Генерация отчётов**: Создание PDF отчётов с результатами интервью
- **🔧 Мониторинг**: Проверка статуса всех сервисов AI-HR

## Быстрый старт

### 1. Запуск сервисов

Убедитесь, что все сервисы AI-HR запущены:

```bash
# Запуск всех сервисов
docker compose up -d

# Или отдельно
docker compose up -d cv report api
```

### 2. Запуск веб-панели

#### Вариант 1: Простой HTTP сервер
```bash
cd ui-admin
python -m http.server 8080
# Откройте http://localhost:8080
```

#### Вариант 2: Node.js сервер
```bash
cd ui-admin
npx serve -p 8080
# Откройте http://localhost:8080
```

#### Вариант 3: PHP сервер
```bash
cd ui-admin
php -S localhost:8080
# Откройте http://localhost:8080
```

### 3. Использование

1. **Просмотр резюме**: Нажмите "Обновить список" для загрузки CV
2. **Поиск**: Введите запрос и нажмите "Поиск"
3. **Генерация отчёта**: Заполните форму и нажмите "Сформировать отчёт"
4. **Мониторинг**: Нажмите "Проверить сервисы" для проверки статуса

## API Endpoints

### CV Service (http://localhost:8007)

#### GET /cvs/list
Получить список всех CV ID:
```bash
curl "http://localhost:8007/cvs/list"
```

#### GET /cvs/search
Поиск по резюме:
```bash
curl "http://localhost:8007/cvs/search?q=Python%20разработка&top_k=5"
```

#### GET /cvs
Получить детальную информацию о CV:
```bash
curl "http://localhost:8007/cvs"
```

#### DELETE /cvs/{cv_id}
Удалить резюме:
```bash
curl -X DELETE "http://localhost:8007/cvs/abc123-def456"
```

#### GET /health
Проверка статуса сервиса:
```bash
curl "http://localhost:8007/health"
```

### Report Service (http://localhost:8005)

#### POST /report
Генерация PDF отчёта:
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
      {"name": "Python", "score": 0.8, "weight": 0.4},
      {"name": "Django", "score": 0.7, "weight": 0.35},
      {"name": "Database", "score": 0.6, "weight": 0.25}
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
Генерация HTML отчёта (fallback):
```bash
curl -X POST "http://localhost:8005/report/html" \
  -H "Content-Type: application/json" \
  -d '{...}' \
  --output report.html
```

#### GET /health
Проверка статуса сервиса:
```bash
curl "http://localhost:8005/health"
```

### Main API (http://localhost:8006)

#### GET /health
Проверка статуса главного API:
```bash
curl "http://localhost:8006/health"
```

#### GET /stats
Статистика использования:
```bash
curl "http://localhost:8006/stats"
```

## Ручное тестирование API

### 1. Проверка сервисов
```bash
# CV Service
curl "http://localhost:8007/health"

# Report Service  
curl "http://localhost:8005/health"

# Main API
curl "http://localhost:8006/health"
```

### 2. Загрузка резюме
```bash
# Через Telegram бота (если настроен)
# Или напрямую через CV service
curl -X POST "http://localhost:8007/ingest" \
  -F "file=@resume.pdf"
```

### 3. Поиск по резюме
```bash
# Поиск по навыкам
curl "http://localhost:8007/cvs/search?q=Python%20Django&top_k=3"

# Поиск по опыту
curl "http://localhost:8007/cvs/search?q=опыт%20разработки&top_k=5"

# Поиск по технологиям
curl "http://localhost:8007/cvs/search?q=PostgreSQL%20база%20данных&top_k=3"
```

### 4. Генерация отчёта
```bash
# Создать JSON файл с данными отчёта
cat > report_data.json << EOF
{
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
    {"name": "Python", "score": 0.8, "weight": 0.4},
    {"name": "Django", "score": 0.7, "weight": 0.35},
    {"name": "Database", "score": 0.6, "weight": 0.25}
  ],
  "positives": ["Отличное знание Python", "Опыт с Django ORM"],
  "negatives": ["Слабое знание Docker"],
  "quotes": [
    {
      "text": "Работал с Django более 4 лет",
      "source": "Interview"
    }
  ],
  "rating_0_10": 7.5
}
EOF

# Генерировать PDF отчёт
curl -X POST "http://localhost:8005/report" \
  -H "Content-Type: application/json" \
  -d @report_data.json \
  --output interview_report.pdf
```

## Структура файлов

```
ui-admin/
├── index.html          # Главная страница с интерфейсом
├── app.js             # JavaScript для API взаимодействий
└── README.md          # Документация
```

## Настройка

### Изменение API URLs

Отредактируйте `app.js` и измените `API_CONFIG`:

```javascript
const API_CONFIG = {
    CV_SERVICE: 'http://your-cv-service:8007',
    REPORT_SERVICE: 'http://your-report-service:8005',
    MAIN_API: 'http://your-main-api:8006'
};
```

### CORS настройки

Если возникают проблемы с CORS, добавьте в сервисы:

```python
# В FastAPI приложениях
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Проблемы с подключением

1. **Сервисы недоступны**:
   ```bash
   # Проверить статус контейнеров
   docker ps
   
   # Проверить логи
   docker logs ai-hr-cv-1
   docker logs ai-hr-report-1
   ```

2. **CORS ошибки**:
   - Убедитесь, что CORS настроен в сервисах
   - Проверьте, что URL в `app.js` правильные

3. **Файлы не загружаются**:
   - Проверьте, что CV service запущен
   - Убедитесь, что Qdrant настроен правильно

### Отладка

1. **Открыть Developer Tools** (F12)
2. **Проверить Console** на ошибки JavaScript
3. **Проверить Network** на неудачные API запросы
4. **Проверить логи сервисов**:
   ```bash
   docker logs ai-hr-cv-1 -f
   docker logs ai-hr-report-1 -f
   ```

## Безопасность

⚠️ **Важно**: Эта панель предназначена для внутреннего использования.

- Не размещайте в публичном доступе
- Используйте аутентификацию в продакшене
- Ограничьте доступ по IP или VPN
- Регулярно обновляйте зависимости

## Разработка

### Добавление новых функций

1. **Новый API endpoint**: Добавьте в соответствующий сервис
2. **UI элемент**: Добавьте в `index.html`
3. **JavaScript функция**: Добавьте в `app.js`
4. **Документация**: Обновите `README.md`

### Тестирование

```bash
# Тест API endpoints
curl "http://localhost:8007/health"
curl "http://localhost:8005/health"
curl "http://localhost:8006/health"

# Тест поиска
curl "http://localhost:8007/cvs/search?q=test&top_k=1"

# Тест генерации отчёта
curl -X POST "http://localhost:8005/report" -H "Content-Type: application/json" -d '{"candidate":{"name":"Test"},"vacancy":{"title":"Test"},"blocks":[],"positives":[],"negatives":[],"quotes":[],"rating_0_10":5.0}' --output test.pdf
```
