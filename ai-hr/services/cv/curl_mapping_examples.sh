#!/bin/bash

# CV Mapping API - curl Examples
# This script demonstrates how to use the CV mapping endpoints

BASE_URL="http://localhost:8007"

echo "🚀 CV Mapping API - curl Examples"
echo "=================================="

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

# Test 2: List CVs
print_step "Testing CV list endpoint"
curl -s -X GET "${BASE_URL}/cvs/list" | jq '.' || print_error "CV list failed"
echo ""

# Test 3: BA Mapping (if CVs exist)
print_step "Testing BA mapping (first CV)"
CV_ID=$(curl -s -X GET "${BASE_URL}/cvs/list" | jq -r '.cv_ids[0]' 2>/dev/null)

if [ "$CV_ID" != "null" ] && [ -n "$CV_ID" ]; then
    curl -s -X GET "${BASE_URL}/map/${CV_ID}?role_type=ba" | jq '.' || print_error "BA mapping failed"
else
    print_warning "No CVs found - upload a CV first"
fi
echo ""

# Test 4: IT Mapping (if CVs exist)
print_step "Testing IT mapping (first CV)"
if [ "$CV_ID" != "null" ] && [ -n "$CV_ID" ]; then
    curl -s -X GET "${BASE_URL}/map/${CV_ID}?role_type=it" | jq '.' || print_error "IT mapping failed"
else
    print_warning "No CVs found - upload a CV first"
fi
echo ""

# Test 5: POST Mapping (if CVs exist)
print_step "Testing POST mapping endpoint"
if [ "$CV_ID" != "null" ] && [ -n "$CV_ID" ]; then
    curl -s -X POST "${BASE_URL}/map" \
        -H "Content-Type: application/json" \
        -d "{\"cv_id\": \"${CV_ID}\", \"role_type\": \"ba\"}" | jq '.' || print_error "POST mapping failed"
else
    print_warning "No CVs found - upload a CV first"
fi
echo ""

# Test 6: Error handling - invalid CV ID
print_step "Testing error handling (invalid CV ID)"
curl -s -X GET "${BASE_URL}/map/invalid-cv-id?role_type=ba" | jq '.' || print_error "Error handling test failed"
echo ""

# Test 7: Error handling - invalid role type
print_step "Testing error handling (invalid role type)"
if [ "$CV_ID" != "null" ] && [ -n "$CV_ID" ]; then
    curl -s -X GET "${BASE_URL}/map/${CV_ID}?role_type=invalid" | jq '.' || print_error "Error handling test failed"
else
    print_warning "No CVs found - skipping error test"
fi
echo ""

# Test 8: Upload sample CV for testing
print_step "Uploading sample CV for testing"
if [ -f "samples/cv1.txt" ]; then
    UPLOAD_RESPONSE=$(curl -s -F "file=@samples/cv1.txt" "${BASE_URL}/ingest")
    NEW_CV_ID=$(echo "${UPLOAD_RESPONSE}" | jq -r '.cv_id' 2>/dev/null)
    
    if [ "$NEW_CV_ID" != "null" ] && [ -n "$NEW_CV_ID" ]; then
        print_success "CV uploaded successfully: ${NEW_CV_ID}"
        
        # Test mapping on the new CV
        print_step "Testing mapping on uploaded CV"
        curl -s -X GET "${BASE_URL}/map/${NEW_CV_ID}?role_type=ba" | jq '.' || print_error "Mapping on new CV failed"
    else
        print_error "Failed to upload CV"
    fi
else
    print_warning "Sample CV file not found: samples/cv1.txt"
fi
echo ""

print_success "All curl examples completed!"
echo ""
echo "📝 Usage Notes:"
echo "  - Upload a CV first using: curl -F file=@your_cv.pdf ${BASE_URL}/ingest"
echo "  - Get CV ID from: curl ${BASE_URL}/cvs/list"
echo "  - Map to BA: curl ${BASE_URL}/map/{cv_id}?role_type=ba"
echo "  - Map to IT: curl ${BASE_URL}/map/{cv_id}?role_type=it"
echo "  - Use 'jq' for pretty JSON output (install with: apt-get install jq)"
echo ""
echo "🔧 API Endpoints:"
echo "  GET  /map/{cv_id}?role_type={ba|it}  - Simple mapping"
echo "  POST /map                             - Full mapping with request body"
echo "  GET  /cvs/list                       - List all CV IDs"
echo "  POST /ingest                         - Upload new CV"
