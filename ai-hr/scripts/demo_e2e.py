#!/usr/bin/env python3
"""
AI-HR E2E Demo Script (Python Version)
Demonstrates: CV Upload → Search → Report Generation

This script provides detailed logging and error handling for the complete
AI-HR workflow demonstration.
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('demo_e2e.log')
    ]
)
logger = logging.getLogger(__name__)

# Configuration
CONFIG = {
    'cv_service': 'http://localhost:8007',
    'report_service': 'http://localhost:8005',
    'main_api': 'http://localhost:8006',
    'sample_cv': 'samples/cv1.pdf',
    'timeout': 30
}

class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'  # No Color

def log_info(message: str):
    """Log info message with blue color"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.NC}")
    logger.info(message)

def log_success(message: str):
    """Log success message with green color"""
    print(f"{Colors.GREEN}✅ {message}{Colors.NC}")
    logger.info(f"SUCCESS: {message}")

def log_warning(message: str):
    """Log warning message with yellow color"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.NC}")
    logger.warning(message)

def log_error(message: str):
    """Log error message with red color"""
    print(f"{Colors.RED}❌ {message}{Colors.NC}")
    logger.error(message)

def log_step(step: str, message: str):
    """Log step with purple color"""
    print(f"{Colors.PURPLE}🔄 {step}: {message}{Colors.NC}")
    logger.info(f"STEP {step}: {message}")

def create_sample_cv() -> str:
    """Create a sample CV file for demo purposes"""
    samples_dir = Path('samples')
    samples_dir.mkdir(exist_ok=True)
    
    cv_text = """Алексей Петров
Senior Python Developer

ОПЫТ РАБОТЫ:
- 5 лет разработки на Python
- 4 года работы с Django и Django REST Framework
- Опыт с PostgreSQL, Redis, Celery
- Знание Docker, Kubernetes
- Опыт с CI/CD (GitLab CI, GitHub Actions)
- Работа с микросервисной архитектурой

НАВЫКИ:
- Python, Django, FastAPI
- PostgreSQL, Redis, MongoDB
- Docker, Kubernetes
- Git, GitLab, GitHub
- Linux, Bash scripting
- REST API, GraphQL

ОБРАЗОВАНИЕ:
- МГУ, Факультет ВМК, 2018

ПРОЕКТЫ:
- Разработка высоконагруженного API для e-commerce
- Микросервисная архитектура для банковского приложения
- Система аналитики в реальном времени

ДОПОЛНИТЕЛЬНО:
- Участие в open-source проектах
- Выступления на конференциях
- Менторство junior разработчиков
"""
    
    # Create text file
    cv_txt_path = samples_dir / 'cv1.txt'
    cv_txt_path.write_text(cv_text, encoding='utf-8')
    
    # Try to create PDF if pandoc is available
    cv_pdf_path = samples_dir / 'cv1.pdf'
    try:
        import subprocess
        result = subprocess.run([
            'pandoc', str(cv_txt_path), '-o', str(cv_pdf_path)
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and cv_pdf_path.exists():
            log_success(f"Created sample CV: {cv_pdf_path}")
            return str(cv_pdf_path)
        else:
            log_warning("Pandoc failed, using text file")
            return str(cv_txt_path)
            
    except (subprocess.TimeoutExpired, FileNotFoundError, ImportError):
        log_warning("Pandoc not available, using text file")
        return str(cv_txt_path)

def check_service_health(service_url: str, service_name: str) -> bool:
    """Check if a service is healthy"""
    try:
        response = requests.get(f"{service_url}/health", timeout=5)
        if response.status_code == 200:
            log_success(f"{service_name} is healthy")
            return True
        else:
            log_error(f"{service_name} health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        log_error(f"{service_name} is not accessible: {e}")
        return False

def upload_cv(cv_path: str) -> Optional[str]:
    """Upload CV and return CV ID"""
    log_step("1", "Uploading CV")
    
    if not os.path.exists(cv_path):
        log_error(f"CV file not found: {cv_path}")
        return None
    
    log_info(f"Uploading: {cv_path}")
    
    try:
        with open(cv_path, 'rb') as f:
            files = {'file': (os.path.basename(cv_path), f, 'application/octet-stream')}
            response = requests.post(
                f"{CONFIG['cv_service']}/ingest",
                files=files,
                timeout=CONFIG['timeout']
            )
        
        response.raise_for_status()
        data = response.json()
        
        cv_id = data.get('cv_id')
        if not cv_id:
            log_error("No CV ID in response")
            logger.error(f"Upload response: {data}")
            return None
        
        log_success(f"CV uploaded successfully! CV ID: {cv_id}")
        log_info(f"Processing time: {data.get('processing_time_ms', 'N/A')}ms")
        log_info(f"Chunks created: {data.get('chunks_count', 'N/A')}")
        
        return cv_id
        
    except requests.exceptions.RequestException as e:
        log_error(f"CV upload failed: {e}")
        return None
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON response: {e}")
        return None

def search_cvs(query: str, top_k: int = 3) -> Optional[Dict[str, Any]]:
    """Search CVs and return results"""
    log_step("2", "Searching CVs")
    
    log_info(f"Searching for: {query}")
    
    try:
        response = requests.get(
            f"{CONFIG['cv_service']}/cvs/search",
            params={'q': query, 'top_k': top_k},
            timeout=CONFIG['timeout']
        )
        
        response.raise_for_status()
        data = response.json()
        
        total_results = data.get('total', 0)
        results = data.get('results', [])
        
        if total_results == 0:
            log_warning("No search results found")
            return data
        
        log_success(f"Found {total_results} search results")
        
        # Display results
        print(f"\n{Colors.CYAN}Search Results:{Colors.NC}")
        for i, result in enumerate(results[:3], 1):
            score = result.get('score', 0)
            filename = result.get('filename', 'Unknown')
            chunk_text = result.get('chunk_text', '')[:100] + "..."
            
            print(f"{Colors.WHITE}{i}. {filename} (Score: {score:.3f}){Colors.NC}")
            print(f"   {chunk_text}")
            print()
        
        return data
        
    except requests.exceptions.RequestException as e:
        log_error(f"Search failed: {e}")
        return None
    except json.JSONDecodeError as e:
        log_error(f"Invalid JSON response: {e}")
        return None

def generate_report() -> bool:
    """Generate interview report"""
    log_step("3", "Generating Report")
    
    report_data = {
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
        "positives": [
            "Отличное знание Python",
            "Опыт с Django ORM",
            "Знание PostgreSQL",
            "Опыт с микросервисами"
        ],
        "negatives": [
            "Слабое знание Docker",
            "Ограниченный CI/CD опыт"
        ],
        "quotes": [
            {
                "text": "Работал с Django более 4 лет, создавал высоконагруженные приложения",
                "source": "Interview Transcript"
            },
            {
                "text": "Имеет опыт работы с PostgreSQL и Redis в продакшене",
                "source": "Technical Assessment"
            }
        ],
        "rating_0_10": 7.5
    }
    
    log_info("Generating report with data:")
    print(json.dumps(report_data, indent=2, ensure_ascii=False))
    
    try:
        response = requests.post(
            f"{CONFIG['report_service']}/report",
            json=report_data,
            timeout=CONFIG['timeout']
        )
        
        response.raise_for_status()
        
        # Save PDF
        report_path = "report.pdf"
        with open(report_path, 'wb') as f:
            f.write(response.content)
        
        file_size = os.path.getsize(report_path)
        log_success(f"Report generated successfully!")
        log_info(f"Report saved as: {report_path}")
        log_info(f"Report file size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        return True
        
    except requests.exceptions.RequestException as e:
        log_error(f"Report generation failed: {e}")
        return False
    except Exception as e:
        log_error(f"Unexpected error during report generation: {e}")
        return False

def main():
    """Main demo function"""
    print(f"{Colors.PURPLE}🚀 AI-HR E2E Demo Starting...{Colors.NC}")
    print("=" * 50)
    
    # Check if sample CV exists
    cv_path = CONFIG['sample_cv']
    if not os.path.exists(cv_path):
        log_info("Sample CV not found, creating one...")
        cv_path = create_sample_cv()
    
    # Check service health
    log_info("Checking service health...")
    services_healthy = True
    
    if not check_service_health(CONFIG['cv_service'], "CV Service"):
        services_healthy = False
    
    if not check_service_health(CONFIG['report_service'], "Report Service"):
        services_healthy = False
    
    if not services_healthy:
        log_error("Some services are not healthy. Please check the services and try again.")
        return 1
    
    # Step 1: Upload CV
    cv_id = upload_cv(cv_path)
    if not cv_id:
        log_error("CV upload failed, stopping demo")
        return 1
    
    # Step 2: Search CVs
    search_results = search_cvs("Django", top_k=3)
    if search_results is None:
        log_error("Search failed, stopping demo")
        return 1
    
    # Step 3: Generate Report
    report_success = generate_report()
    if not report_success:
        log_error("Report generation failed")
        return 1
    
    # Summary
    print("\n" + "=" * 50)
    log_success("E2E Demo Completed Successfully!")
    print()
    print(f"{Colors.WHITE}Summary:{Colors.NC}")
    print(f"1. ✅ CV uploaded (ID: {cv_id})")
    print(f"2. ✅ Search performed (Results: {search_results.get('total', 0)})")
    print("3. ✅ Report generated (report.pdf)")
    print()
    print(f"{Colors.WHITE}Files created:{Colors.NC}")
    print("- report.pdf (interview report)")
    print("- demo_e2e.log (detailed log)")
    print()
    print(f"{Colors.WHITE}Next steps:{Colors.NC}")
    print("- Open report.pdf to view the generated report")
    print("- Use the Admin UI at http://localhost:8080 for interactive management")
    print("- Check service logs: docker logs ai-hr-cv-1 -f")
    print()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        log_warning("Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        logger.exception("Unexpected error in main")
        sys.exit(1)
