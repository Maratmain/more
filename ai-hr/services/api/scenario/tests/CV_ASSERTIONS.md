# CV Assertions for Interview Scenarios

## Business Analyst (Anti-fraud) - CV Assertions

| Тезис из CV | Ожидаемые узлы | Ожидаемый уровень | Обоснование |
|-------------|----------------|-------------------|-------------|
| **3 года опыта с антифрод-системами** | `afr_l1_intro` | L2 (0.8) | Прямой опыт настройки правил |
| **Снижение FPR на 25%** | `afr_l2_cases` | L3 (0.9) | Конкретные метрики и результаты |
| **ML-модели и анализ паттернов** | `afr_l3_metrics` | L3 (0.85) | Опыт с машинным обучением |
| **BPMN/Camunda моделирование** | `req_l1_core` | L2 (0.9) | Прямой опыт с требованиями |
| **Сложные интеграции** | `req_l2_complex` | L2 (0.8) | Опыт декомпозиции требований |
| **Jira/Confluence проекты** | `proj_l1_participation` | L2 (0.85) | Активное участие в проектах |
| **Работа с бизнесом** | `proj_l2_conflicts` | L1 (0.7) | Опыт медиации конфликтов |
| **Тест-кейсы для антифрод** | `test_l1_cases` | L2 (0.9) | Прямой опыт разработки тестов |
| **Python автоматизация** | `test_l2_automation` | L1 (0.75) | Опыт с автоматизацией |
| **ДБО ЮЛ и платежные системы** | `pay_l1_systems` | L2 (0.9) | Специфические знания |
| **ПОД-ФТ и регуляторы** | `pay_l2_compliance` | L2 (0.85) | Знание регуляторных требований |

### Ожидаемый общий результат:
- **Общий балл**: 0.85
- **Сильные стороны**: AntiFraud_Rules, Requirements_Engineering, Testing_UAT, Payment_Systems_Rules
- **Слабые стороны**: Отсутствуют
- **Критические компетенции**: Все пройдены успешно

---

## IT Data Center Operations - CV Assertions

| Тезис из CV | Ожидаемые узлы | Ожидаемый уровень | Обоснование |
|-------------|----------------|-------------------|-------------|
| **Монтаж/демонтаж серверов** | `hw_l1_install` | L2 (0.9) | Прямой опыт работы с оборудованием |
| **RAID контроллеры (базовые)** | `hw_l2_raid_bmc` | L1 (0.6) | Ограниченный опыт с RAID/BMC |
| **Service Desk инциденты** | `hw_l3_incidents` | L2 (0.85) | Опыт обработки инцидентов |
| **Сетевое оборудование** | `net_l1_lan_san` | L2 (0.8) | Опыт работы с LAN |
| **Диагностика сетей** | `net_l2_troubleshooting` | L1 (0.75) | Базовые навыки диагностики |
| **Кабельные системы** | `cable_l1_scs` | L1 (0.7) | Базовые знания СКС |
| **Порядок в серверных** | `cable_l2_maintenance` | L2 (0.8) | Опыт поддержания порядка |
| **WDS и образы ОС** | `sys_l1_os_imaging` | L2 (0.9) | Прямой опыт с WDS |
| **AD/DNS/DHCP/GPO** | `sys_l2_ad_gpo` | L3 (0.95) | Глубокий опыт с AD |
| **CMDB/DCIM (базовые)** | `cmdb_l1_systems` | L1 (0.7) | Ограниченный опыт |
| **Excel/Visio отчеты** | `cmdb_l2_analytics` | L1 (0.6) | Базовые навыки аналитики |

### Ветки эквивалентности:

| Условие | Альтернативный путь | Компенсация | Ожидаемый балл |
|---------|-------------------|-------------|----------------|
| **Нет опыта RAID/BMC** | `sys_l1_os_imaging` | Опыт с WDS и образами ОС | 0.8 |
| **Ограниченный SAN опыт** | `sys_l2_ad_gpo` | Глубокие знания AD/GPO | 0.85 |
| **Слабые навыки аналитики** | `sys_l2_ad_gpo` | Сильный опыт с AD | 0.8 |

### Ожидаемый общий результат:
- **Общий балл**: 0.8
- **Сильные стороны**: OS_Imaging_GPO_AD, DC_Housekeeping, Incident_Handling
- **Слабые стороны**: CMDB_DCIM_Reporting
- **Критические компетенции**: Все пройдены успешно

---

## Тестовые сценарии

### BA Anti-fraud - Сильный кандидат
```
CV: Полный опыт по всем блокам
Ожидаемый путь: afr_l1_intro → afr_l2_cases → afr_l3_metrics → req_l1_core
Общий балл: 0.85
```

### BA Anti-fraud - Частичный опыт
```
CV: Без опыта с ML-моделями
Ожидаемый путь: afr_l1_intro → req_l1_core → req_l2_complex → proj_l1_participation
Общий балл: 0.75
Слабые стороны: AntiFraud_Rules
```

### IT DC Ops - Сильный кандидат
```
CV: Полный опыт по всем блокам
Ожидаемый путь: hw_l1_install → hw_l2_raid_bmc → hw_l3_incidents → net_l1_lan_san
Общий балл: 0.8
```

### IT DC Ops - RAID/BMC альтернатива
```
CV: Без опыта RAID/BMC, но с сильным AD/GPO
Ожидаемый путь: hw_l1_install → sys_l1_os_imaging → sys_l2_ad_gpo → cmdb_l1_systems
Общий балл: 0.75 (с эквивалентностью)
Слабые стороны: DC_HW_x86_RAID_BMC
```

### IT DC Ops - Service Desk фокус
```
CV: Фокус на Service Desk и инцидентах
Ожидаемый путь: hw_l1_install → hw_l3_incidents → cable_l2_maintenance → sys_l1_os_imaging
Общий балл: 0.7
Слабые стороны: LAN_SAN_Networking, CMDB_DCIM_Reporting
```

---

## Правила валидации

### BA Anti-fraud
- **Минимальный балл**: 0.7
- **Обязательные сильные стороны**: AntiFraud_Rules, Requirements_Engineering
- **Допустимые слабые стороны**: Soft_Skills_Clear_Speech
- **Критические провалы**: Payment_Systems_Rules

### IT DC Ops
- **Минимальный балл**: 0.6
- **Обязательные сильные стороны**: OS_Imaging_GPO_AD, DC_Housekeeping
- **Допустимые слабые стороны**: CMDB_DCIM_Reporting, Tooling_Excel_Visio
- **Критические провалы**: Incident_Handling
- **Порог эквивалентности**: 0.7

---

## Использование

### Запуск демо
```bash
# BA Anti-fraud
python run_demo.py ba_anti_fraud_v1 ba_anti_fraud_cv.assert.json

# IT DC Ops
python run_demo.py it_dc_ops_v1 it_dc_ops_cv.assert.json
```

### Ожидаемый вывод
```
🎯 Interview Scenario Demo Results
==================================================
📋 Scenario: ba_anti_fraud_v1
👤 Profile: ba_anti_fraud
🎚️  Threshold: 0.7

🛤️  Path Taken (First 3 Nodes):
  1. afr_l1_intro (Order: 1)
     Category: AntiFraud_Rules
     Question: Опишите опыт настройки антифрод-правил и снижение ложноположительных...

  2. afr_l2_cases (Order: 2)
     Category: AntiFraud_Rules
     Question: Расскажите о кейсах выявления мошенничества. Какие паттерны...

  3. afr_l3_metrics (Order: 3)
     Category: AntiFraud_Rules
     Question: Как вы балансируете между точностью детекции и количеством...

📊 Scores:
  🟢 afr_l1_intro: 0.80 (AntiFraud_Rules)
  🟢 afr_l2_cases: 0.90 (AntiFraud_Rules)
  🟢 afr_l3_metrics: 0.85 (AntiFraud_Rules)

📈 Block Scores:
  AntiFraud_Rules: 0.850

🎯 Overall Score: 0.850
📊 Performance Level: Meets expectations
💪 Strengths: AntiFraud_Rules
⚠️  Weaknesses: 
```
