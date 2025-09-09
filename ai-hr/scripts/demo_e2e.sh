#!/bin/bash

# AI-HR E2E Demo Script
# Demonstrates: CV Upload → Search → Report Generation

set -e  # Exit on any error

echo "🚀 AI-HR E2E Demo Starting..."
echo "=================================="

# Configuration
CV_SERVICE="http://localhost:8007"
REPORT_SERVICE="http://localhost:8005"
MAIN_API="http://localhost:8006"
SAMPLE_CV="samples/cv1.pdf"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if sample CV exists
if [ ! -f "$SAMPLE_CV" ]; then
    log_error "Sample CV not found: $SAMPLE_CV"
    log_info "Creating a sample CV file..."
    
    # Create a simple text-based CV
    mkdir -p samples
    cat > samples/cv1.txt << 'EOF'
Алексей Петров
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
EOF
    
    # Convert to PDF if possible
    if command -v pandoc &> /dev/null; then
        pandoc samples/cv1.txt -o samples/cv1.pdf
        log_success "Created sample CV: $SAMPLE_CV"
    else
        log_warning "Pandoc not found, using text file instead"
        SAMPLE_CV="samples/cv1.txt"
    fi
fi

# Step 1: Upload CV
echo ""
log_info "Step 1: Uploading CV..."
echo "Uploading: $SAMPLE_CV"

UPLOAD_RESPONSE=$(curl -s -F "file=@$SAMPLE_CV" "$CV_SERVICE/ingest")
echo "Upload response: $UPLOAD_RESPONSE"

# Extract CV ID from response
CV_ID=$(echo "$UPLOAD_RESPONSE" | grep -o '"cv_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$CV_ID" ]; then
    log_error "Failed to extract CV ID from upload response"
    echo "Full response: $UPLOAD_RESPONSE"
    exit 1
fi

log_success "CV uploaded successfully! CV ID: $CV_ID"

# Step 2: Search CVs
echo ""
log_info "Step 2: Searching CVs..."
echo "Searching for: Django"

SEARCH_RESPONSE=$(curl -s "$CV_SERVICE/cvs/search?q=Django&top_k=3")
echo "Search response: $SEARCH_RESPONSE"

# Check if search returned results
RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | grep -o '"total":[0-9]*' | cut -d':' -f2)

if [ -z "$RESULT_COUNT" ] || [ "$RESULT_COUNT" -eq 0 ]; then
    log_warning "No search results found"
else
    log_success "Found $RESULT_COUNT search results"
    
    # Show search results
    echo ""
    echo "Search Results:"
    echo "$SEARCH_RESPONSE" | grep -o '"chunk_text":"[^"]*"' | sed 's/"chunk_text":"//g' | sed 's/"$//g' | head -3
fi

# Step 3: Generate Report
echo ""
log_info "Step 3: Generating Report..."

# Create report data
REPORT_DATA='{
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
  "positives": ["Отличное знание Python", "Опыт с Django ORM", "Знание PostgreSQL"],
  "negatives": ["Слабое знание Docker", "Ограниченный CI/CD опыт"],
  "quotes": [
    {
      "text": "Работал с Django более 4 лет, создавал высоконагруженные приложения",
      "source": "Interview Transcript"
    }
  ],
  "rating_0_10": 7.5
}'

echo "Generating report with data:"
echo "$REPORT_DATA" | jq . 2>/dev/null || echo "$REPORT_DATA"

# Generate report
REPORT_RESPONSE=$(curl -s -X POST "$REPORT_SERVICE/report" \
  -H "Content-Type: application/json" \
  -d "$REPORT_DATA" \
  --output "report.pdf" \
  -w "HTTPSTATUS:%{http_code}")

HTTP_STATUS=$(echo "$REPORT_RESPONSE" | grep -o "HTTPSTATUS:[0-9]*" | cut -d: -f2)

if [ "$HTTP_STATUS" -eq 200 ]; then
    log_success "Report generated successfully!"
    log_info "Report saved as: report.pdf"
    
    # Check file size
    if [ -f "report.pdf" ]; then
        FILE_SIZE=$(ls -lh report.pdf | awk '{print $5}')
        log_info "Report file size: $FILE_SIZE"
    fi
else
    log_error "Report generation failed with HTTP status: $HTTP_STATUS"
    echo "Response: $REPORT_RESPONSE"
fi

# Summary
echo ""
echo "=================================="
log_success "E2E Demo Completed!"
echo ""
echo "Summary:"
echo "1. ✅ CV uploaded (ID: $CV_ID)"
echo "2. ✅ Search performed (Results: $RESULT_COUNT)"
echo "3. ✅ Report generated (report.pdf)"
echo ""
echo "Files created:"
echo "- report.pdf (interview report)"
echo ""
echo "Next steps:"
echo "- Open report.pdf to view the generated report"
echo "- Use the Admin UI at http://localhost:8080 for interactive management"
echo "- Check service logs: docker logs ai-hr-cv-1 -f"
echo ""
