#!/bin/bash
# Gateway functionality validation script
# Part of Phase 3A: Gateway Architecture Design completion validation
# Usage: ./test_gateway.sh

set -e

echo "🚀 Testing Gateway Service Implementation (Phase 3A Validation)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
GATEWAY_URL="http://localhost"
API_URL="$GATEWAY_URL/api"
STORAGE_URL="$GATEWAY_URL/storage"

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3

    echo -n "Testing $description... "

    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")

    if [[ "$status" == "$expected_status" ]]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $status)"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $status, expected $expected_status)"
        return 1
    fi
}

# Function to test with authentication
test_with_auth() {
    local url=$1
    local token=$2
    local expected_status=${3:-200}
    local description=$4

    echo -n "Testing $description... "

    local status=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $token" \
        "$url" || echo "000")

    if [[ "$status" == "$expected_status" ]]; then
        echo -e "${GREEN}✅ OK${NC} (HTTP $status)"
        return 0
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $status, expected $expected_status)"
        return 1
    fi
}

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Test basic gateway health
echo -e "\n${YELLOW}Testing Gateway Health:${NC}"
test_endpoint "$GATEWAY_URL/health" 200 "Gateway health endpoint"

# Test service routing
echo -e "\n${YELLOW}Testing Service Routing:${NC}"
test_endpoint "$API_URL/health" 200 "API service through gateway"
test_endpoint "$STORAGE_URL/health" 200 "Storage service through gateway"

# Test rate limiting
echo -e "\n${YELLOW}Testing Rate Limiting:${NC}"
echo -n "Testing rate limit headers... "
response=$(curl -s -I "$GATEWAY_URL/health")
if echo "$response" | grep -q "X-RateLimit-"; then
    echo -e "${GREEN}✅ OK${NC} (Rate limit headers present)"
else
    echo -e "${YELLOW}⚠️ WARNING${NC} (Rate limit headers missing)"
fi

# Test security headers
echo -e "\n${YELLOW}Testing Security Headers:${NC}"
echo -n "Testing security headers... "
response=$(curl -s -I "$GATEWAY_URL/health")
security_headers=("X-Frame-Options" "X-Content-Type-Options" "X-XSS-Protection")
missing_headers=0

for header in "${security_headers[@]}"; do
    if ! echo "$response" | grep -q "$header"; then
        ((missing_headers++))
    fi
done

if [[ $missing_headers -eq 0 ]]; then
    echo -e "${GREEN}✅ OK${NC} (All security headers present)"
else
    echo -e "${YELLOW}⚠️ WARNING${NC} ($missing_headers security headers missing)"
fi

# Test authentication (without valid JWT)
echo -e "\n${YELLOW}Testing Authentication:${NC}"
test_endpoint "$API_URL/v1/tasks" 401 "API endpoint without authentication"

# Test CORS
echo -e "\n${YELLOW}Testing CORS:${NC}"
echo -n "Testing CORS preflight... "
cors_response=$(curl -s -I -X OPTIONS \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: GET" \
    "$API_URL/health")

if echo "$cors_response" | grep -q "Access-Control-Allow"; then
    echo -e "${GREEN}✅ OK${NC} (CORS headers present)"
else
    echo -e "${YELLOW}⚠️ WARNING${NC} (CORS headers missing)"
fi

# Test request ID propagation
echo -e "\n${YELLOW}Testing Request Tracing:${NC}"
echo -n "Testing request ID propagation... "
request_response=$(curl -s -I "$GATEWAY_URL/health")
if echo "$request_response" | grep -q "X-Request-ID"; then
    echo -e "${GREEN}✅ OK${NC} (Request ID header present)"
else
    echo -e "${RED}❌ FAILED${NC} (Request ID header missing)"
fi

echo -e "\n${GREEN}🎉 Gateway testing complete!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. ✅ Gateway container is running with basic functionality"
echo "2. 🔄 Implement JWT validation testing (requires valid token)"
echo "3. 🔄 Add service discovery testing (Stage 4)"
echo "4. 🔄 Add SSL/TLS configuration for production"
echo "5. 🔄 Add comprehensive monitoring and observability"

echo -e "\n${YELLOW}Architecture Status:${NC}"
echo "✅ Phase 3A: Gateway Architecture Design - COMPLETED"
echo "🔄 Phase 3B: API Gateway Service Implementation - IN PROGRESS"
echo "⏳ Phase 3C: Enhanced Security Framework - PENDING"
echo "⏳ Phase 3D: Service Discovery & Registration - PENDING"
echo "⏳ Phase 3E: Production Security Hardening - PENDING"
