#!/bin/bash

# Telegram Bot API - curl Examples
# This script demonstrates how to interact with the Telegram Bot API
# for testing file uploads and bot functionality

# Configuration
BOT_TOKEN="${TELEGRAM_BOT_TOKEN:-YOUR_BOT_TOKEN}"
BOT_API_URL="${TELEGRAM_BOT_API_URL:-https://api.telegram.org}"
CHAT_ID="${TELEGRAM_CHAT_ID:-YOUR_CHAT_ID}"

echo "🤖 Telegram Bot API - curl Examples"
echo "===================================="

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

# Check if required variables are set
if [ "$BOT_TOKEN" = "YOUR_BOT_TOKEN" ]; then
    print_error "Please set TELEGRAM_BOT_TOKEN environment variable"
    exit 1
fi

if [ "$CHAT_ID" = "YOUR_CHAT_ID" ]; then
    print_error "Please set TELEGRAM_CHAT_ID environment variable"
    exit 1
fi

# Test 1: Get Bot Information
print_step "Testing bot information endpoint"
curl -s -X GET "${BOT_API_URL}/bot${BOT_TOKEN}/getMe" | jq '.' || print_error "Bot info request failed"
echo ""

# Test 2: Get Updates
print_step "Testing getUpdates endpoint"
curl -s -X GET "${BOT_API_URL}/bot${BOT_TOKEN}/getUpdates" | jq '.result | length' || print_error "Get updates failed"
echo ""

# Test 3: Send Text Message
print_step "Testing sendMessage endpoint"
curl -s -X POST "${BOT_API_URL}/bot${BOT_TOKEN}/sendMessage" \
  -H "Content-Type: application/json" \
  -d "{
    \"chat_id\": \"${CHAT_ID}\",
    \"text\": \"🤖 Test message from curl script\",
    \"parse_mode\": \"Markdown\"
  }" | jq '.ok' || print_error "Send message failed"
echo ""

# Test 4: Send Document (if test file exists)
if [ -f "test_cv.pdf" ]; then
    print_step "Testing sendDocument endpoint"
    curl -s -X POST "${BOT_API_URL}/bot${BOT_TOKEN}/sendDocument" \
      -F "chat_id=${CHAT_ID}" \
      -F "document=@test_cv.pdf" \
      -F "caption=Test CV upload from curl" | jq '.ok' || print_error "Send document failed"
    echo ""
else
    print_warning "test_cv.pdf not found, skipping document upload test"
fi

# Test 5: Get File Info (if file_id is available)
if [ ! -z "$FILE_ID" ]; then
    print_step "Testing getFile endpoint"
    curl -s -X GET "${BOT_API_URL}/bot${BOT_TOKEN}/getFile?file_id=${FILE_ID}" | jq '.' || print_error "Get file info failed"
    echo ""
else
    print_warning "FILE_ID not set, skipping getFile test"
fi

# Test 6: Local Bot API (if configured)
if [ "$TELEGRAM_USE_LOCAL_BOT_API" = "true" ]; then
    print_step "Testing Local Bot API"
    LOCAL_API_URL="${TELEGRAM_BOT_API_URL:-http://localhost:8081}"
    
    curl -s -X GET "${LOCAL_API_URL}/bot${BOT_TOKEN}/getMe" | jq '.' || print_error "Local Bot API test failed"
    echo ""
    
    print_step "Testing Local Bot API file limits"
    echo "Local Bot API can handle files up to 2GB"
    echo "Standard Bot API limit: 20MB"
    echo ""
fi

# Test 7: Bot Commands
print_step "Testing bot commands via sendMessage"

commands=(
    "/start"
    "/help"
    "/upload_cv"
    "/status"
)

for cmd in "${commands[@]}"; do
    echo "Sending command: $cmd"
    curl -s -X POST "${BOT_API_URL}/bot${BOT_TOKEN}/sendMessage" \
      -H "Content-Type: application/json" \
      -d "{
        \"chat_id\": \"${CHAT_ID}\",
        \"text\": \"$cmd\"
      }" | jq -r '.ok' || print_error "Command $cmd failed"
    sleep 1  # Rate limiting
done
echo ""

# Test 8: File Size Limits
print_step "Testing file size limit information"
echo "Standard Bot API limits:"
echo "  • Maximum file size: 20MB"
echo "  • Download timeout: 60 seconds"
echo "  • Rate limit: 30 requests/second"
echo ""
echo "Local Bot API benefits:"
echo "  • Maximum file size: 2GB"
echo "  • No rate limits"
echo "  • Faster downloads"
echo "  • Better reliability"
echo ""

# Test 9: Error Handling
print_step "Testing error handling"
echo "Testing invalid bot token..."
curl -s -X GET "${BOT_API_URL}/botINVALID_TOKEN/getMe" | jq '.ok' || print_success "Error handling works correctly"
echo ""

# Test 10: Webhook vs Polling
print_step "Testing webhook vs polling configuration"
echo "Current setup uses polling (getUpdates)"
echo "For production, consider using webhooks:"
echo "  curl -X POST \"${BOT_API_URL}/bot${BOT_TOKEN}/setWebhook\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"url\": \"https://your-domain.com/webhook\"}'"
echo ""

print_success "All curl examples completed!"
echo ""
echo "📝 Usage Notes:"
echo "  - Set TELEGRAM_BOT_TOKEN environment variable"
echo "  - Set TELEGRAM_CHAT_ID for testing"
echo "  - Use 'jq' for pretty JSON output"
echo "  - For Local Bot API: set TELEGRAM_USE_LOCAL_BOT_API=true"
echo ""
echo "🔧 Environment Variables:"
echo "  TELEGRAM_BOT_TOKEN     - Your bot token from @BotFather"
echo "  TELEGRAM_CHAT_ID       - Chat ID for testing"
echo "  TELEGRAM_USE_LOCAL_BOT_API - true/false"
echo "  TELEGRAM_BOT_API_URL   - Local Bot API URL (if using local)"
echo ""
echo "💡 File Size Handling:"
echo "  • Standard Bot API: 20MB limit"
echo "  • Local Bot API: 2GB limit"
echo "  • Bot provides intelligent warnings"
echo "  • Alternative solutions suggested"
echo ""
echo "🚀 Next Steps:"
echo "  1. Start the bot: python main.py"
echo "  2. Test with real files in Telegram"
echo "  3. Monitor logs for errors"
echo "  4. Configure Local Bot API for large files"
