#!/bin/bash

# Dialog Manager API - curl Examples
# This script demonstrates the role-based interview responses

BASE_URL="http://localhost:8004"

echo "🚀 Dialog Manager API - curl Examples"
echo "====================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}🔍 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Test 1: Health Check
print_step "Testing health endpoint"
curl -s -X GET "${BASE_URL}/health" | jq '.' || print_error "Health check failed"
echo ""

# Test 2: Get supported roles
print_step "Testing roles endpoint"
curl -s -X GET "${BASE_URL}/roles" | jq '.' || print_error "Roles endpoint failed"
echo ""

# Test 3: Get backchannel config
print_step "Testing backchannel config endpoint"
curl -s -X GET "${BASE_URL}/config/backchannel" | jq '.config.roles | keys' || print_error "Config endpoint failed"
echo ""

# Test 4: BA Interview Response
print_step "Testing BA (Anti-fraud) interview response"
curl -s -X POST "${BASE_URL}/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "node": {
      "id": "afr_l1_intro",
      "category": "AntiFraud_Rules",
      "order": 1,
      "question": "Опишите опыт настройки антифрод-правил.",
      "weight": 0.4,
      "success_criteria": ["правила", "метрики", "FPR/TPR", "кейсы"],
      "followups": ["Приведите пример оптимизации правила"],
      "next_if_fail": "req_l1_core",
      "next_if_pass": "afr_l2_cases"
    },
    "transcript": "Я работал с антифрод-правилами 3 года. Настраивал правила для выявления мошенничества, оптимизировал FPR до 2%, TPR был 95%. Использовал метрики качества.",
    "scores": {"AntiFraud_Rules": 0.0},
    "role_profile": "ba_anti_fraud",
    "block_weights": {"AntiFraud_Rules": 0.95}
  }' | jq '.' || print_error "BA interview test failed"
echo ""

# Test 5: IT Interview Response
print_step "Testing IT (Data Center) interview response"
curl -s -X POST "${BASE_URL}/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "node": {
      "id": "hw_l2_raid_bmc",
      "category": "DC_HW_x86_RAID_BMC",
      "order": 2,
      "question": "Расскажите о настройке BIOS, BMC и RAID-контроллеров.",
      "weight": 0.6,
      "success_criteria": ["BIOS", "BMC", "RAID", "настройка", "параметры"],
      "followups": ["Какие настройки безопасности обязательны?"],
      "next_if_fail": "hw_l3_incidents",
      "next_if_pass": "hw_l3_incidents"
    },
    "transcript": "Настраивал BIOS для новых серверов, конфигурировал BMC для удаленного управления, настраивал RAID-массивы. Критичные параметры: загрузка с SSD, включение виртуализации.",
    "scores": {"DC_HW_x86_RAID_BMC": 0.0},
    "role_profile": "it_dc_ops",
    "block_weights": {"DC_HW_x86_RAID_BMC": 0.95}
  }' | jq '.' || print_error "IT interview test failed"
echo ""

# Test 6: Poor Response Test
print_step "Testing poor response handling"
curl -s -X POST "${BASE_URL}/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "node": {
      "id": "test_node",
      "category": "AntiFraud_Rules",
      "order": 1,
      "question": "Test question",
      "weight": 0.4,
      "success_criteria": ["правила", "метрики"],
      "followups": [],
      "next_if_fail": "next_fail",
      "next_if_pass": "next_pass"
    },
    "transcript": "Да, что-то работал, но не помню детали.",
    "scores": {"AntiFraud_Rules": 0.0},
    "role_profile": "ba_anti_fraud"
  }' | jq '.' || print_error "Poor response test failed"
echo ""

# Test 7: Response Variations (same input, multiple calls)
print_step "Testing response variations"
echo "Making 3 calls with same input to test response variety:"

for i in {1..3}; do
  echo "Call $i:"
  curl -s -X POST "${BASE_URL}/reply" \
    -H "Content-Type: application/json" \
    -d '{
      "node": {
        "id": "test_node",
        "category": "AntiFraud_Rules",
        "order": 1,
        "question": "Test question",
        "weight": 0.4,
        "success_criteria": ["правила", "метрики"],
        "followups": [],
        "next_if_fail": "next_fail",
        "next_if_pass": "next_pass"
      },
      "transcript": "Работал с антифрод-правилами, настраивал метрики качества.",
      "scores": {"AntiFraud_Rules": 0.0},
      "role_profile": "ba_anti_fraud"
    }' | jq -r '.reply' || print_error "Variation test failed"
done
echo ""

# Test 8: Without role profile (fallback)
print_step "Testing without role profile (fallback mode)"
curl -s -X POST "${BASE_URL}/reply" \
  -H "Content-Type: application/json" \
  -d '{
    "node": {
      "id": "test_node",
      "category": "TestCategory",
      "order": 1,
      "question": "Test question",
      "weight": 0.4,
      "success_criteria": ["test", "criteria"],
      "followups": [],
      "next_if_fail": "next_fail",
      "next_if_pass": "next_pass"
    },
    "transcript": "This is a test response with some test criteria mentioned.",
    "scores": {"TestCategory": 0.0}
  }' | jq '.' || print_error "Fallback test failed"
echo ""

print_success "All curl examples completed!"
echo ""
echo "📝 Usage Notes:"
echo "  - Start DM service: docker compose up dm"
echo "  - Test individual endpoints with the examples above"
echo "  - Use 'jq' for pretty JSON output (install with: apt-get install jq)"
echo ""
echo "🔧 API Endpoints:"
echo "  POST /reply                    - Main interview response endpoint"
echo "  GET  /health                   - Service health check"
echo "  GET  /roles                    - List supported role profiles"
echo "  GET  /config/backchannel       - Get backchannel configuration"
echo ""
echo "💡 Key Features:"
echo "  - Role-specific responses (BA vs IT)"
echo "  - Confidence scoring"
echo "  - Delta score calculation"
echo "  - Red flag detection"
echo "  - Response variation"
