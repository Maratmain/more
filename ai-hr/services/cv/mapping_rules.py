"""
CV Mapping Rules for Role Categories

This module contains rule-based mapping logic to categorize CV content
into specific role blocks for BA (Anti-fraud) and IT (Data Center) positions.
"""

from typing import Dict, List, Set, Tuple
import re

# BA (Anti-fraud) Role Categories and Keywords
BA_CATEGORIES = {
    "AntiFraud_Rules": {
        "keywords": [
            "антифрод", "антифрод-правила", "антифрод правила", "anti-fraud", "antifraud",
            "мошенничество", "fraud", "мошенничество", "выявление мошенничества",
            "фрод", "fraud detection", "fraud prevention", "fraud monitoring",
            "ложноположительные", "false positive", "false negative", "FPR", "TPR",
            "правила", "rules", "rule engine", "rule management",
            "риск", "risk", "risk assessment", "risk management",
            "подозрительные операции", "suspicious transactions", "suspicious activity"
        ],
        "description": "Знание антифрод-правил и методов выявления мошенничества"
    },
    
    "Requirements_Engineering": {
        "keywords": [
            "требования", "requirements", "постановка требований", "requirements engineering",
            "функциональные требования", "functional requirements", "нефункциональные требования",
            "техническое задание", "ТЗ", "technical specification", "specification",
            "анализ требований", "requirements analysis", "сбор требований",
            "стейкхолдеры", "stakeholders", "заказчики", "customers", "business users",
            "интервью", "interviews", "workshop", "воркшоп", "мозговой штурм"
        ],
        "description": "Опыт постановки требований к системам"
    },
    
    "Stakeholders_Communication": {
        "keywords": [
            "коммуникация", "communication", "взаимодействие", "interaction",
            "презентация", "presentation", "доклад", "reporting", "отчеты",
            "координация", "coordination", "управление проектами", "project management",
            "команда", "team", "командная работа", "teamwork", "collaboration",
            "заказчики", "customers", "клиенты", "clients", "пользователи", "users",
            "менеджмент", "management", "руководство", "leadership"
        ],
        "description": "Взаимодействие с заказчиками и командой"
    },
    
    "Testing_UAT": {
        "keywords": [
            "тестирование", "testing", "тесты", "tests", "тест-кейсы", "test cases",
            "UAT", "user acceptance testing", "приемочное тестирование",
            "функциональное тестирование", "functional testing", "интеграционное тестирование",
            "регрессионное тестирование", "regression testing", "smoke testing",
            "качество", "quality", "QA", "quality assurance", "контроль качества",
            "баг", "bug", "дефект", "defect", "ошибка", "error", "issue"
        ],
        "description": "Тестирование и приемочное тестирование"
    },
    
    "Payment_Systems_Rules": {
        "keywords": [
            "платежные системы", "payment systems", "платежи", "payments",
            "ДБО ЮЛ", "ДБО", "корпоративные карты", "corporate cards", "корпоративные карточки",
            "ПОД", "ФТ", "ПОД-ФТ", "AML", "KYC", "противодействие отмыванию",
            "регуляторика", "regulatory", "регулирование", "compliance", "соответствие",
            "банковские системы", "banking systems", "финтех", "fintech",
            "переводы", "transfers", "операции", "transactions", "расчеты"
        ],
        "description": "Знание платежных систем и регуляторики"
    },
    
    "SQL_DB_Basics": {
        "keywords": [
            "SQL", "база данных", "database", "БД", "СУБД", "DBMS",
            "PostgreSQL", "MySQL", "Oracle", "SQL Server", "MongoDB",
            "запросы", "queries", "SELECT", "INSERT", "UPDATE", "DELETE",
            "индексы", "indexes", "схема", "schema", "таблицы", "tables",
            "связи", "relations", "JOIN", "WHERE", "GROUP BY", "ORDER BY"
        ],
        "description": "Знание принципов работы СУБД и SQL"
    },
    
    "Documentation": {
        "keywords": [
            "документация", "documentation", "документы", "documents",
            "процессы", "processes", "процедуры", "procedures", "инструкции",
            "регламенты", "regulations", "стандарты", "standards",
            "Confluence", "Wiki", "Jira", "Trello", "Asana",
            "техническая документация", "technical documentation", "пользовательская документация",
            "API документация", "API documentation", "спецификации", "specifications"
        ],
        "description": "Ведение документации и процессов"
    }
}

# IT (Data Center) Role Categories and Keywords
IT_CATEGORIES = {
    "DC_HW_x86_RAID_BMC": {
        "keywords": [
            "x86", "серверы", "servers", "серверное оборудование", "server hardware",
            "BIOS", "UEFI", "настройка BIOS", "BIOS configuration",
            "BMC", "IPMI", "удаленное управление", "remote management",
            "RAID", "RAID-контроллер", "RAID controller", "RAID массив", "RAID array",
            "жесткие диски", "hard drives", "SSD", "HDD", "storage", "хранилище",
            "процессоры", "processors", "CPU", "память", "memory", "RAM"
        ],
        "description": "Опыт работы с серверным оборудованием x86, RAID, BMC"
    },
    
    "LAN_SAN_Networking": {
        "keywords": [
            "LAN", "локальная сеть", "local area network", "сеть", "network",
            "SAN", "storage area network", "сетевое хранилище", "network storage",
            "коммутаторы", "switches", "маршрутизаторы", "routers",
            "Cisco", "MikroTik", "Juniper", "HP", "Dell", "сетевое оборудование",
            "VLAN", "виртуальные сети", "virtual networks", "подсети", "subnets",
            "IP", "TCP/IP", "протоколы", "protocols", "сетевые протоколы"
        ],
        "description": "Знание сетевых технологий LAN/SAN"
    },
    
    "SCS_Cabling_Optics": {
        "keywords": [
            "СКС", "структурированная кабельная система", "structured cabling",
            "оптика", "optical", "оптоволокно", "fiber optic", "оптические кабели",
            "монтаж", "installation", "установка", "подключение", "connection",
            "патч-панели", "patch panels", "розетки", "outlets", "разъемы", "connectors",
            "кабели", "cables", "витая пара", "twisted pair", "UTP", "STP",
            "кросс", "cross-connect", "коммутационный шкаф", "rack", "стойка"
        ],
        "description": "Монтаж СКС, работа с оптикой"
    },
    
    "Incident_Handling": {
        "keywords": [
            "инциденты", "incidents", "аварии", "outages", "сбои", "failures",
            "обработка инцидентов", "incident handling", "incident management",
            "мониторинг", "monitoring", "Nagios", "Zabbix", "Prometheus",
            "логи", "logs", "логирование", "logging", "анализ логов",
            "диагностика", "diagnostics", "устранение неисправностей", "troubleshooting",
            "MTTR", "MTBF", "SLA", "время восстановления", "recovery time"
        ],
        "description": "Обработка инцидентов и аварий"
    },
    
    "DC_Housekeeping": {
        "keywords": [
            "порядок", "order", "организация", "organization", "чистота", "cleanliness",
            "серверная", "server room", "дата-центр", "data center", "ЦОД",
            "охлаждение", "cooling", "кондиционирование", "air conditioning",
            "электропитание", "power", "UPS", "ИБП", "генераторы", "generators",
            "пожарная безопасность", "fire safety", "безопасность", "security",
            "доступ", "access", "контроль доступа", "access control"
        ],
        "description": "Поддержание порядка в серверных"
    },
    
    "CMDB_DCIM_Reporting": {
        "keywords": [
            "CMDB", "configuration management database", "база конфигураций",
            "DCIM", "data center infrastructure management", "управление инфраструктурой",
            "отчеты", "reports", "отчетность", "reporting", "аналитика", "analytics",
            "инвентаризация", "inventory", "учет", "accounting", "активы", "assets",
            "конфигурация", "configuration", "изменения", "changes", "change management",
            "документирование", "documentation", "схемы", "diagrams", "топология"
        ],
        "description": "Работа с CMDB, DCIM, отчетность"
    },
    
    "OS_Imaging_GPO_AD": {
        "keywords": [
            "Windows", "Linux", "операционные системы", "operating systems", "ОС",
            "Active Directory", "AD", "домен", "domain", "доменные службы",
            "GPO", "групповые политики", "group policies", "политики", "policies",
            "imaging", "образы", "развертывание", "deployment", "WDS", "MDT",
            "пользователи", "users", "группы", "groups", "права доступа", "permissions",
            "DNS", "DHCP", "службы", "services", "роли", "roles"
        ],
        "description": "Настройка ОС, групповые политики, Active Directory"
    },
    
    "Tooling_Excel_Visio": {
        "keywords": [
            "Excel", "таблицы", "spreadsheets", "формулы", "formulas", "макросы", "macros",
            "Visio", "диаграммы", "diagrams", "схемы", "flowcharts", "блок-схемы",
            "PowerShell", "скрипты", "scripts", "автоматизация", "automation",
            "мониторинг", "monitoring", "графики", "charts", "дашборды", "dashboards",
            "документация", "documentation", "инструкции", "instructions", "руководства"
        ],
        "description": "Работа с инструментами (Excel, Visio)"
    }
}

def normalize_text(text: str) -> str:
    """Normalize text for keyword matching"""
    # Convert to lowercase and remove extra whitespace
    text = re.sub(r'\s+', ' ', text.lower().strip())
    # Remove special characters but keep letters, numbers, and spaces
    text = re.sub(r'[^\w\s\-]', ' ', text)
    return text

def find_keywords_in_text(text: str, keywords: List[str]) -> List[str]:
    """Find which keywords are present in the text"""
    normalized_text = normalize_text(text)
    found_keywords = []
    
    for keyword in keywords:
        # Check for exact match (case insensitive)
        if keyword.lower() in normalized_text:
            found_keywords.append(keyword)
        # Check for partial match (word boundaries)
        elif re.search(r'\b' + re.escape(keyword.lower()) + r'\b', normalized_text):
            found_keywords.append(keyword)
    
    return found_keywords

def map_cv_to_ba_categories(text: str) -> Dict[str, Dict[str, any]]:
    """Map CV text to BA (Anti-fraud) categories"""
    detected_blocks = {}
    missing_blocks = []
    
    for category, config in BA_CATEGORIES.items():
        found_keywords = find_keywords_in_text(text, config["keywords"])
        
        if found_keywords:
            detected_blocks[category] = {
                "description": config["description"],
                "found_keywords": found_keywords,
                "keyword_count": len(found_keywords),
                "coverage_score": len(found_keywords) / len(config["keywords"]),
                "status": "covered"
            }
        else:
            missing_blocks.append(category)
            detected_blocks[category] = {
                "description": config["description"],
                "found_keywords": [],
                "keyword_count": 0,
                "coverage_score": 0.0,
                "status": "not_covered"
            }
    
    return {
        "detected_blocks": detected_blocks,
        "missing_blocks": missing_blocks,
        "total_categories": len(BA_CATEGORIES),
        "covered_categories": len(detected_blocks) - len(missing_blocks)
    }

def map_cv_to_it_categories(text: str) -> Dict[str, Dict[str, any]]:
    """Map CV text to IT (Data Center) categories"""
    detected_blocks = {}
    missing_blocks = []
    
    for category, config in IT_CATEGORIES.items():
        found_keywords = find_keywords_in_text(text, config["keywords"])
        
        if found_keywords:
            detected_blocks[category] = {
                "description": config["description"],
                "found_keywords": found_keywords,
                "keyword_count": len(found_keywords),
                "coverage_score": len(found_keywords) / len(config["keywords"]),
                "status": "covered"
            }
        else:
            missing_blocks.append(category)
            detected_blocks[category] = {
                "description": config["description"],
                "found_keywords": [],
                "keyword_count": 0,
                "coverage_score": 0.0,
                "status": "not_covered"
            }
    
    return {
        "detected_blocks": detected_blocks,
        "missing_blocks": missing_blocks,
        "total_categories": len(IT_CATEGORIES),
        "covered_categories": len(detected_blocks) - len(missing_blocks)
    }

def map_cv_to_role_categories(text: str, role_type: str) -> Dict[str, any]:
    """Map CV text to role-specific categories"""
    if role_type.lower() == "ba":
        return map_cv_to_ba_categories(text)
    elif role_type.lower() == "it":
        return map_cv_to_it_categories(text)
    else:
        raise ValueError(f"Unsupported role type: {role_type}. Supported: 'ba', 'it'")

def get_role_priority_level(mapping_result: Dict[str, any]) -> str:
    """Determine priority level based on coverage"""
    covered_ratio = mapping_result["covered_categories"] / mapping_result["total_categories"]
    
    if covered_ratio >= 0.8:
        return "L3"  # High coverage - can start with advanced questions
    elif covered_ratio >= 0.5:
        return "L2"  # Medium coverage - start with intermediate questions
    else:
        return "L1"  # Low coverage - start with basic questions

def analyze_cv_mapping(text: str, role_type: str) -> Dict[str, any]:
    """Complete CV mapping analysis"""
    mapping_result = map_cv_to_role_categories(text, role_type)
    priority_level = get_role_priority_level(mapping_result)
    
    return {
        "role_type": role_type,
        "priority_level": priority_level,
        "mapping_result": mapping_result,
        "recommendations": {
            "start_level": priority_level,
            "focus_areas": [cat for cat in mapping_result["missing_blocks"][:3]],  # Top 3 missing areas
            "strengths": [cat for cat, data in mapping_result["detected_blocks"].items() 
                         if data["status"] == "covered" and data["coverage_score"] > 0.3]
        }
    }
