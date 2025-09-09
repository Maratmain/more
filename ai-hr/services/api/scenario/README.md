# AI-HR Scenario System

Система управления сценариями интервью для различных ролевых профилей.

## Структура файлов

```
scenario/
├── role_profiles.yaml     # Профили ролей и веса блоков
├── schema.py             # Pydantic модели для валидации
├── selector.py           # Логика выбора следующего вопроса
├── generator.py          # Генератор fallback сценариев
├── examples/             # Примеры JSON сценариев
│   └── python_backend.json
└── README.md            # Эта документация
```

## Как читать YAML профили

Файл `role_profiles.yaml` содержит:

- **profiles**: Словарь ролевых профилей
- **block_weights**: Веса компетенций (0.0-1.0)
- **drill_threshold**: Порог для углубленных вопросов
- **rationale**: Обоснование весов на основе JD

### Пример использования

```python
import yaml

with open('role_profiles.yaml', 'r', encoding='utf-8') as f:
    profiles = yaml.safe_load(f)

ba_profile = profiles['profiles']['ba_anti_fraud']
weights = ba_profile['block_weights']
```

## JSON сценарии

JSON файлы сценариев находятся в папке `examples/` и содержат:

- **nodes**: Вопросы с критериями успеха
- **start_id**: ID начального вопроса
- **policy**: Параметры сценария

## Интеграция с системой

Сценарии автоматически загружаются через:
- Dialog Manager (`services/dm/main.py`)
- Main API (`services/api/main.py`)
- Admin UI для управления

## Добавление новых профилей

1. Добавить профиль в `role_profiles.yaml`
2. Создать JSON сценарий в `examples/`
3. Обновить `scenario_mapping`
4. Протестировать через Admin UI
