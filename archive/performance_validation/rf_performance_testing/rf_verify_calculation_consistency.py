#!/usr/bin/env python3
"""
Verification script to ensure mathematical optimizations don't change calculation results
Compares detailed responses between original and optimized endpoints
"""

import json
import urllib.request
import urllib.error
from datetime import datetime
import sys

def fetch_calculation_result(url, payload):
    """Fetch calculation result from endpoint"""
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            
        return json.loads(response_data)
    except Exception as e:
        return {'error': str(e)}

def compare_float_values(val1, val2, tolerance=1e-10):
    """Compare floating point values with tolerance"""
    if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
        return abs(val1 - val2) < tolerance
    return val1 == val2

def deep_compare_results(result1, result2, path=""):
    """Recursively compare two result dictionaries"""
    differences = []
    
    if type(result1) != type(result2):
        differences.append(f"{path}: Type mismatch - {type(result1).__name__} vs {type(result2).__name__}")
        return differences
    
    if isinstance(result1, dict):
        # Compare all keys
        all_keys = set(result1.keys()) | set(result2.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key
            
            if key not in result1:
                differences.append(f"{new_path}: Missing in original")
            elif key not in result2:
                differences.append(f"{new_path}: Missing in optimized")
            else:
                differences.extend(deep_compare_results(result1[key], result2[key], new_path))
    
    elif isinstance(result1, list):
        if len(result1) != len(result2):
            differences.append(f"{path}: Length mismatch - {len(result1)} vs {len(result2)}")
        else:
            for i in range(len(result1)):
                differences.extend(deep_compare_results(result1[i], result2[i], f"{path}[{i}]"))
    
    elif isinstance(result1, (int, float)) and isinstance(result2, (int, float)):
        if not compare_float_values(result1, result2):
            differences.append(f"{path}: Value mismatch - {result1} vs {result2}")
    
    elif result1 != result2:
        differences.append(f"{path}: Value mismatch - {result1} vs {result2}")
    
    return differences

def verify_recipe_consistency(recipe_payload, recipe_name):
    """Verify that both endpoints return identical results for a recipe"""
    print(f"\n{'='*60}")
    print(f"VERIFYING: {recipe_name}")
    print(f"{'='*60}")
    
    # Fetch results from both endpoints
    original_result = fetch_calculation_result("http://localhost:8080/calculate-recipe/", recipe_payload)
    optimized_result = fetch_calculation_result("http://localhost:8081/calculate-recipe/", recipe_payload)
    
    # Check for errors
    if 'error' in original_result:
        print(f"❌ Original endpoint error: {original_result['error']}")
        return False
    
    if 'error' in optimized_result:
        print(f"❌ Optimized endpoint error: {optimized_result['error']}")
        return False
    
    # Compare results
    differences = deep_compare_results(original_result, optimized_result)
    
    if not differences:
        print("✅ IDENTICAL RESULTS")
        print(f"   Recipe single score: {original_result.get('Recipe Info', {}).get('Single Score', {}).get('Single Score', 'N/A')}")
        print(f"   Items in response: {len(original_result.get('Item Results', {}))}")
        return True
    else:
        print(f"❌ FOUND {len(differences)} DIFFERENCES:")
        for diff in differences[:10]:  # Show first 10 differences
            print(f"   • {diff}")
        if len(differences) > 10:
            print(f"   • ... and {len(differences) - 10} more differences")
        return False

def main():
    print("FIT API Calculation Consistency Verification")
    print("=" * 60)
    print("Comparing original (8080) vs optimized (8081) calculation results")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test cases with different recipe sizes
    test_cases = [
        {
            "name": "Single Item (Lamb)",
            "payload": {"items": {"25541-FRA": 0.1}}
        },
        {
            "name": "Two Items",
            "payload": {"items": {"25541-FRA": 0.1, "25505-FRA": 0.05}}
        },
        {
            "name": "Small Recipe (3 items)",
            "payload": {"items": {"25541-FRA": 0.15, "25505-FRA": 0.1, "42200-FRA": 0.02}}
        },
        {
            "name": "Medium Recipe (5 items)", 
            "payload": {"items": {
                "25541-FRA": 0.15,
                "25505-FRA": 0.1, 
                "42200-FRA": 0.02,
                "9643-IND": 0.05,
                "11010-BRA": 0.01
            }}
        },
        {
            "name": "Large Recipe (10 items)",
            "payload": {"items": {
                "25541-FRA": 0.15, "25505-FRA": 0.1, "42200-FRA": 0.02,
                "9643-IND": 0.05, "11010-BRA": 0.01, "9200-PER": 0.08,
                "9360-FRA": 0.04, "9010-FRA": 0.12, "9612-FRA": 0.06,
                "18902-FRA": 0.03
            }}
        },
    ]
    
    # Run verification for each test case
    all_passed = True
    passed_count = 0
    
    for test_case in test_cases:
        result = verify_recipe_consistency(test_case["payload"], test_case["name"])
        if result:
            passed_count += 1
        else:
            all_passed = False
    
    # Final summary
    print(f"\n{'='*60}")
    print("VERIFICATION SUMMARY")
    print(f"{'='*60}")
    print(f"Tests passed: {passed_count}/{len(test_cases)}")
    
    if all_passed:
        print("🎉 ALL TESTS PASSED - Mathematical optimizations preserve calculation accuracy!")
        print("✅ Original and optimized endpoints return identical results")
    else:
        print("⚠️  SOME TESTS FAILED - Calculation differences detected")
        print("❌ Mathematical optimizations may have introduced errors")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)