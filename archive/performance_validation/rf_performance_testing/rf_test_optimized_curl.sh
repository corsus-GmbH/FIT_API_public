#!/bin/bash
# Test script for optimized endpoint using curl

echo "FIT API Optimized Endpoint Testing"
echo "============================================================"
echo "Comparing /calculate-recipe/ vs /calculate-recipe-optimized/"
echo "============================================================"

# Test data for single item
TEST_DATA_SINGLE='{
  "items": {
    "10001-FRA": 0.1
  },
  "weighting_scheme_name": "delphi_r0110"
}'

echo ""
echo "TESTING: Single Item Recipe"
echo "------------------------------------------------------------"

# Test original endpoint
echo "[ORIGINAL] /calculate-recipe/"
echo "Testing endpoint..."
START_TIME=$(date +%s.%N)
RESPONSE_ORIGINAL=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA_SINGLE" \
  http://localhost:8081/calculate-recipe/)
END_TIME=$(date +%s.%N)
ORIGINAL_TIME=$(echo "$END_TIME - $START_TIME" | bc -l)

HTTP_STATUS_ORIGINAL=$(echo $RESPONSE_ORIGINAL | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
RESPONSE_BODY_ORIGINAL=$(echo $RESPONSE_ORIGINAL | sed -E 's/HTTPSTATUS:[0-9]{3}$//')

if [ "$HTTP_STATUS_ORIGINAL" = "200" ]; then
    ORIGINAL_SCORE=$(echo $RESPONSE_BODY_ORIGINAL | python3 -c "
import sys, json
try:
    data=json.load(sys.stdin)
    print(data['recipe_scores']['single_score'])
except:
    print('ERROR_PARSING')
")
    ORIGINAL_ITEMS=$(echo $RESPONSE_BODY_ORIGINAL | python3 -c "
import sys, json
try:
    data=json.load(sys.stdin)
    print(len(data['graded_lcia_results']))
except:
    print('ERROR_PARSING')
")
    echo "✅ SUCCESS"
    echo "   Response time: ${ORIGINAL_TIME} seconds"
    echo "   Recipe single score: $ORIGINAL_SCORE"
    echo "   Items in response: $ORIGINAL_ITEMS"
else
    echo "❌ FAILED - Status: $HTTP_STATUS_ORIGINAL"
    echo "   Error response (first 500 chars): $(echo $RESPONSE_BODY_ORIGINAL | head -c 500)"
    ORIGINAL_SCORE="ERROR"
    ORIGINAL_ITEMS="ERROR"
fi

echo ""
echo "[OPTIMIZED] /calculate-recipe-optimized/"
echo "Testing endpoint..."
START_TIME=$(date +%s.%N)
RESPONSE_OPTIMIZED=$(curl -s -w "HTTPSTATUS:%{http_code}" -X POST \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA_SINGLE" \
  http://localhost:8081/calculate-recipe-optimized/)
END_TIME=$(date +%s.%N)
OPTIMIZED_TIME=$(echo "$END_TIME - $START_TIME" | bc -l)

HTTP_STATUS_OPTIMIZED=$(echo $RESPONSE_OPTIMIZED | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
RESPONSE_BODY_OPTIMIZED=$(echo $RESPONSE_OPTIMIZED | sed -E 's/HTTPSTATUS:[0-9]{3}$//')

if [ "$HTTP_STATUS_OPTIMIZED" = "200" ]; then
    OPTIMIZED_SCORE=$(echo $RESPONSE_BODY_OPTIMIZED | python3 -c "
import sys, json
try:
    data=json.load(sys.stdin)
    print(data['recipe_scores']['single_score'])
except:
    print('ERROR_PARSING')
")
    OPTIMIZED_ITEMS=$(echo $RESPONSE_BODY_OPTIMIZED | python3 -c "
import sys, json
try:
    data=json.load(sys.stdin)
    print(len(data['graded_lcia_results']))
except:
    print('ERROR_PARSING')
")
    echo "✅ SUCCESS"
    echo "   Response time: ${OPTIMIZED_TIME} seconds"
    echo "   Recipe single score: $OPTIMIZED_SCORE"
    echo "   Items in response: $OPTIMIZED_ITEMS"
else
    echo "❌ FAILED - Status: $HTTP_STATUS_OPTIMIZED"
    echo "   Error response (first 500 chars): $(echo $RESPONSE_BODY_OPTIMIZED | head -c 500)"
    echo "   Comparing with original response status: $HTTP_STATUS_ORIGINAL"
    OPTIMIZED_SCORE="ERROR"
    OPTIMIZED_ITEMS="ERROR"
fi

echo ""
echo "📊 COMPARISON:"
echo "   Original time:  ${ORIGINAL_TIME}s"
echo "   Optimized time: ${OPTIMIZED_TIME}s"

# Calculate performance improvement/regression
SPEEDUP=$(echo "scale=1; $ORIGINAL_TIME / $OPTIMIZED_TIME" | bc -l)
if (( $(echo "$OPTIMIZED_TIME < $ORIGINAL_TIME" | bc -l) )); then
    echo "   Improvement: ${SPEEDUP}x faster"
else
    echo "   Regression: ${SPEEDUP}x slower"
fi

# Check mathematical consistency
if [ "$ORIGINAL_SCORE" = "ERROR" ] || [ "$OPTIMIZED_SCORE" = "ERROR" ] || [ "$ORIGINAL_SCORE" = "ERROR_PARSING" ] || [ "$OPTIMIZED_SCORE" = "ERROR_PARSING" ]; then
    echo "   ⚠️  CANNOT COMPARE - One or both endpoints failed"
    echo "      Original:  $ORIGINAL_SCORE (Status: $HTTP_STATUS_ORIGINAL)"
    echo "      Optimized: $OPTIMIZED_SCORE (Status: $HTTP_STATUS_OPTIMIZED)"
else
    SCORE_DIFF=$(echo "scale=15; $ORIGINAL_SCORE - $OPTIMIZED_SCORE" | bc -l | sed 's/^-//')
    if (( $(echo "$SCORE_DIFF < 0.000000000000001" | bc -l) )); then
        echo "   ✅ IDENTICAL RESULTS - Mathematical consistency verified"
    else
        echo "   ❌ DIFFERENT RESULTS!"
        echo "      Original:  $ORIGINAL_SCORE"
        echo "      Optimized: $OPTIMIZED_SCORE"
        echo "      Difference: $SCORE_DIFF"
    fi
fi

echo ""
echo "🏁 SINGLE ITEM TEST COMPLETED"
echo "============================================================"