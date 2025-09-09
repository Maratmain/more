#!/bin/bash

# AI-HR Metrics Service - curl Examples
# This script demonstrates the metrics API endpoints

BASE_URL="http://localhost:8010"

echo "📊 AI-HR Metrics Service - curl Examples"
echo "========================================"

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
print_step "Testing health check endpoint"
curl -s -X GET "${BASE_URL}/health" | jq '.' || print_error "Health check failed"
echo ""

# Test 2: SLA Targets
print_step "Testing SLA targets endpoint"
curl -s -X GET "${BASE_URL}/sla-targets" | jq '.' || print_error "SLA targets failed"
echo ""

# Test 3: Cost Configuration
print_step "Testing cost configuration endpoint"
curl -s -X GET "${BASE_URL}/cost-config" | jq '.config.llm' || print_error "Cost config failed"
echo ""

# Test 4: Record Latency Metrics
print_step "Testing latency recording"
curl -s -X POST "${BASE_URL}/latency" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "asr",
    "latency_ms": 1500,
    "session_id": "test_session_123",
    "turn_id": "turn_456",
    "success": true,
    "error_message": null
  }' | jq '.status' || print_error "Latency recording failed"
echo ""

# Test 5: Record Cost Metrics
print_step "Testing cost recording"
curl -s -X POST "${BASE_URL}/cost" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "llm",
    "cost_usd": 0.05,
    "session_id": "test_session_123",
    "turn_id": "turn_456",
    "units": 1000,
    "unit_type": "tokens",
    "details": {
      "model": "claude-3.5-sonnet",
      "provider": "openrouter"
    }
  }' | jq '.status' || print_error "Cost recording failed"
echo ""

# Test 6: Record Complete Turn
print_step "Testing turn recording"
curl -s -X POST "${BASE_URL}/turn" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_123",
    "turn_id": "turn_456",
    "asr_latency_ms": 1500,
    "dm_latency_ms": 800,
    "tts_latency_ms": 1200,
    "total_turn_s": 4.5,
    "backchannel_s": 1.8,
    "total_cost_usd": 0.08,
    "services_used": ["asr", "dm", "tts"]
  }' | jq '.status' || print_error "Turn recording failed"
echo ""

# Test 7: Cost Analysis
print_step "Testing cost analysis"
curl -s -X POST "${BASE_URL}/cost-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_session_123",
    "include_breakdown": true
  }' | jq '.total_cost_usd' || print_error "Cost analysis failed"
echo ""

# Test 8: Metrics Summary
print_step "Testing metrics summary"
curl -s -X GET "${BASE_URL}/metrics/summary" | jq '.turns' || print_error "Metrics summary failed"
echo ""

# Test 9: Multiple Latency Records
print_step "Testing multiple latency records"
for i in {1..5}; do
  curl -s -X POST "${BASE_URL}/latency" \
    -H "Content-Type: application/json" \
    -d "{
      \"service\": \"asr\",
      \"latency_ms\": $((1000 + i * 100)),
      \"session_id\": \"batch_test_$i\",
      \"turn_id\": \"turn_$i\",
      \"success\": true
    }" > /dev/null
done
print_success "Recorded 5 latency metrics"
echo ""

# Test 10: Error Handling
print_step "Testing error handling"
curl -s -X POST "${BASE_URL}/latency" \
  -H "Content-Type: application/json" \
  -d '{
    "service": "asr",
    "latency_ms": 5000,
    "session_id": "error_test",
    "turn_id": "turn_error",
    "success": false,
    "error_message": "Timeout error"
  }' | jq '.status' || print_error "Error handling test failed"
echo ""

# Test 11: Cost Analysis with Date Range
print_step "Testing cost analysis with date range"
curl -s -X POST "${BASE_URL}/cost-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-12-31T23:59:59",
    "include_breakdown": true
  }' | jq '.total_turns' || print_error "Date range analysis failed"
echo ""

# Test 12: Performance Test
print_step "Testing performance with multiple requests"
start_time=$(date +%s)
for i in {1..10}; do
  curl -s -X POST "${BASE_URL}/latency" \
    -H "Content-Type: application/json" \
    -d "{
      \"service\": \"perf_test\",
      \"latency_ms\": $((500 + i * 50)),
      \"session_id\": \"perf_session_$i\",
      \"turn_id\": \"perf_turn_$i\",
      \"success\": true
    }" > /dev/null
done
end_time=$(date +%s)
duration=$((end_time - start_time))
print_success "Recorded 10 metrics in ${duration} seconds"
echo ""

print_success "All curl examples completed!"
echo ""
echo "📝 Usage Notes:"
echo "  - Start metrics service: python main.py"
echo "  - Test individual endpoints with the examples above"
echo "  - Use 'jq' for pretty JSON output (install with: apt-get install jq)"
echo "  - Check data directory for CSV files with recorded metrics"
echo ""
echo "🔧 API Endpoints:"
echo "  POST /latency                    - Record latency metric"
echo "  POST /cost                       - Record cost metric"
echo "  POST /turn                       - Record complete turn metric"
echo "  POST /cost-analysis              - Get cost analysis"
echo "  GET  /health                     - Service health check"
echo "  GET  /sla-targets                - Get SLA targets"
echo "  GET  /cost-config                - Get cost configuration"
echo "  GET  /metrics/summary            - Get metrics summary"
echo ""
echo "💡 Key Features:"
echo "  - Real-time latency tracking"
echo "  - Cost analysis and ROI calculation"
echo "  - SLA compliance monitoring"
echo "  - HR salary comparison"
echo "  - Automated recommendations"
echo "  - CSV data storage"
echo ""
echo "🚀 Next Steps:"
echo "  1. Start the metrics service: python main.py"
echo "  2. Run the cost analysis script: python ../../scripts/cost_check.py"
echo "  3. Integrate metrics in your services using the client library"
echo "  4. Monitor SLA compliance and costs"
echo "  5. Optimize based on recommendations"
