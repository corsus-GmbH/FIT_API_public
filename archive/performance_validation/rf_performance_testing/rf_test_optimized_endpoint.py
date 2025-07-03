#!/usr/bin/env python3
"""
Test script for the optimized /calculate-recipe-optimized/ endpoint.

Compares performance and mathematical consistency between:
- Original: /calculate-recipe/
- Optimized: /calculate-recipe-optimized/

Both endpoints should return identical results with improved performance.
"""

import json
import time
import requests
from typing import Dict, Any

def test_endpoint_comparison():
    """Test both endpoints with the same data and compare results."""
    
    print("FIT API Optimized Endpoint Testing")
    print("=" * 60)
    print("Comparing /calculate-recipe/ vs /calculate-recipe-optimized/")
    print("=" * 60)
    
    # Test data - single item recipe
    test_data_single = {
        "items": {
            "10001-FRA": 0.1  # 100g Lamb from France
        },
        "weighting_scheme_name": "delphi_r0110"
    }
    
    # Test data - multi-item recipe
    test_data_multi = {
        "items": {
            "10001-FRA": 0.1,    # 100g Lamb from France  
            "20001-FRA": 0.05,   # 50g Beef from France
            "30001-ESP": 0.2,    # 200g Tomatoes from Spain
            "40001-DEU": 0.15,   # 150g Bread from Germany
            "50001-ITA": 0.1     # 100g Cheese from Italy
        },
        "weighting_scheme_name": "delphi_r0110"
    }
    
    test_cases = [
        ("Single Item Recipe", test_data_single),
        ("Multi-Item Recipe (5 items)", test_data_multi)
    ]
    
    base_url_8081 = "http://localhost:8081"
    
    for test_name, test_data in test_cases:
        print(f"\n{test_name}")
        print("-" * 50)
        
        # Test original endpoint
        print(f"[ORIGINAL] /calculate-recipe/")
        start_time = time.time()
        try:
            response_original = requests.post(
                f"{base_url_8081}/calculate-recipe/",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            original_time = time.time() - start_time
            
            if response_original.status_code == 200:
                original_data = response_original.json()
                original_score = original_data["recipe_scores"]["single_score"]
                print(f"✅ SUCCESS")
                print(f"   Response time: {original_time:.3f} seconds")
                print(f"   Recipe single score: {original_score}")
                print(f"   Items in response: {len(original_data['graded_lcia_results'])}")
            else:
                print(f"❌ FAILED - Status: {response_original.status_code}")
                print(f"   Error: {response_original.text}")
                continue
                
        except Exception as e:
            print(f"❌ FAILED - Exception: {e}")
            continue
            
        # Test optimized endpoint
        print(f"\n[OPTIMIZED] /calculate-recipe-optimized/")
        start_time = time.time()
        try:
            response_optimized = requests.post(
                f"{base_url_8081}/calculate-recipe-optimized/",
                json=test_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            optimized_time = time.time() - start_time
            
            if response_optimized.status_code == 200:
                optimized_data = response_optimized.json()
                optimized_score = optimized_data["recipe_scores"]["single_score"]
                print(f"✅ SUCCESS")
                print(f"   Response time: {optimized_time:.3f} seconds")
                print(f"   Recipe single score: {optimized_score}")
                print(f"   Items in response: {len(optimized_data['graded_lcia_results'])}")
            else:
                print(f"❌ FAILED - Status: {response_optimized.status_code}")
                print(f"   Error: {response_optimized.text}")
                continue
                
        except Exception as e:
            print(f"❌ FAILED - Exception: {e}")
            continue
            
        # Compare results
        print(f"\n📊 COMPARISON:")
        print(f"   Original time:  {original_time:.3f}s")
        print(f"   Optimized time: {optimized_time:.3f}s")
        
        if optimized_time < original_time:
            speedup = original_time / optimized_time
            print(f"   Improvement: {speedup:.1f}x faster")
        else:
            slowdown = optimized_time / original_time  
            print(f"   Regression: {slowdown:.1f}x slower")
            
        # Mathematical consistency check
        if abs(original_score - optimized_score) < 1e-10:
            print(f"   ✅ IDENTICAL RESULTS - Mathematical consistency verified")
        else:
            print(f"   ❌ DIFFERENT RESULTS!")
            print(f"      Original:  {original_score}")
            print(f"      Optimized: {optimized_score}")
            print(f"      Difference: {abs(original_score - optimized_score)}")
            
        print("=" * 50)
    
    print(f"\n🏁 TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_endpoint_comparison()