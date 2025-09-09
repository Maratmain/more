#!/usr/bin/env python3
"""
Simple example of CV mapping functionality

This script demonstrates how to use the CV mapping rules
without requiring the full service to be running.
"""

import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from mapping_rules import analyze_cv_mapping, BA_CATEGORIES, IT_CATEGORIES

def main():
    """Main example function"""
    print("📝 CV Mapping Example")
    print("=" * 40)
    
    # Example BA CV content
    ba_cv = """
    Бизнес-аналитик с опытом работы в финтехе
    
    Опыт работы:
    - 3 года работы с антифрод-системами
    - Настройка антифрод-правил и снижение ложноположительных срабатываний
    - Постановка требований к платежным системам
    - Разработка тест-кейсов для UAT
    - Работа с заказчиками и стейкхолдерами
    - Знание SQL и работы с базами данных
    - Опыт работы с корпоративными картами и ДБО ЮЛ
    - Ведение документации в Confluence и Jira
    - Знание ПОД-ФТ и регуляторных требований
    
    Навыки:
    - Антифрод-системы, fraud detection
    - Requirements engineering
    - SQL, PostgreSQL, MySQL
    - Тестирование, UAT, test cases
    - Коммуникация с заказчиками
    - Документирование процессов
    """
    
    print("🔍 Analyzing BA CV...")
    ba_result = analyze_cv_mapping(ba_cv, "ba")
    
    print(f"Priority Level: {ba_result['priority_level']}")
    print(f"Coverage: {ba_result['mapping_result']['covered_categories']}/{ba_result['mapping_result']['total_categories']}")
    
    print("\nDetected Blocks:")
    for category, data in ba_result['mapping_result']['detected_blocks'].items():
        if data['status'] == 'covered':
            print(f"  ✅ {category}: {data['keyword_count']} keywords")
        else:
            print(f"  ❌ {category}: Not covered")
    
    print(f"\nMissing Blocks: {', '.join(ba_result['mapping_result']['missing_blocks'])}")
    
    # Example IT CV content
    it_cv = """
    Системный администратор с опытом работы в ЦОД
    
    Опыт работы:
    - 5 лет работы с серверным оборудованием x86
    - Настройка BIOS, BMC и RAID-контроллеров
    - Монтаж и настройка сетевого оборудования Cisco
    - Работа с LAN/SAN сетями
    - Монтаж СКС и работа с оптическими кабелями
    - Обработка инцидентов и аварий в ЦОД
    - Настройка Windows Server и Active Directory
    - Работа с групповыми политиками (GPO)
    - Использование Excel и Visio для документирования
    - Работа с CMDB и системами мониторинга
    
    Навыки:
    - Серверное оборудование x86, BIOS, BMC, RAID
    - Сетевые технологии LAN/SAN, Cisco, MikroTik
    - Windows Server, Linux, Active Directory, DNS, DHCP
    - Групповые политики, GPO, WDS
    - Мониторинг, логирование, обработка инцидентов
    - CMDB, DCIM, отчетность
    - Excel, Visio, PowerShell
    """
    
    print("\n\n💻 Analyzing IT CV...")
    it_result = analyze_cv_mapping(it_cv, "it")
    
    print(f"Priority Level: {it_result['priority_level']}")
    print(f"Coverage: {it_result['mapping_result']['covered_categories']}/{it_result['mapping_result']['total_categories']}")
    
    print("\nDetected Blocks:")
    for category, data in it_result['mapping_result']['detected_blocks'].items():
        if data['status'] == 'covered':
            print(f"  ✅ {category}: {data['keyword_count']} keywords")
        else:
            print(f"  ❌ {category}: Not covered")
    
    print(f"\nMissing Blocks: {', '.join(it_result['mapping_result']['missing_blocks'])}")
    
    print("\n🏁 Example completed!")

if __name__ == "__main__":
    main()
