#!/usr/bin/env python3
"""
Test mathematical consistency between original and optimized endpoints.

Tests /calculate-recipe/ vs /calculate-recipe-optimized/ for identical results.
"""

import json
import requests
import time

def test_optimized_consistency():
    """Test optimized endpoint against original for mathematical consistency."""
    
    print("FIT API Optimized Endpoint Consistency Testing")
    print("=" * 60)
    
    base_url = "http://localhost:8081"
    
    # Test cases from successful previous tests
    test_cases = [
        {
            "name": "Single Item (Basil)",
            "data": {
                "items": {"11032-FRA": 0.1},
                "weighting_scheme_name": "delphi_r0110"
            }
        },
        {
            "name": "Two Items",
            "data": {
                "items": {
                    "11032-FRA": 0.1,
                    "12737-FRA": 0.05
                },
                "weighting_scheme_name": "delphi_r0110"
            }
        },
        {
            "name": "Small Recipe (3 items)",
            "data": {
                "items": {
                    "11032-FRA": 0.1,
                    "12737-FRA": 0.05,
                    "13731-FRA": 0.2
                },
                "weighting_scheme_name": "delphi_r0110"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n{'='*60}")
        print(f"VERIFYING: {test_case['name']}")
        print(f"{'='*60}")
        
        # Test original endpoint
        print("[ORIGINAL] /calculate-recipe/")
        start_time = time.time()
        try:
            response_orig = requests.post(
                f"{base_url}/calculate-recipe/",
                json=test_case["data"],
                timeout=30
            )
            orig_time = time.time() - start_time
            
            if response_orig.status_code == 200:
                orig_data = response_orig.json()
                orig_score = orig_data["recipe_scores"]["single_score"]
                print(f"✅ SUCCESS")
                print(f"   Response time: {orig_time:.3f} seconds")
                print(f"   Recipe single score: {orig_score}")
                print(f"   Items in response: {len(orig_data['graded_lcia_results'])}")
            else:
                print(f"❌ FAILED - Status: {response_orig.status_code}")
                continue
                
        except Exception as e:
            print(f"❌ FAILED - Exception: {e}")
            continue
            
        # Test optimized endpoint
        print(f"\n[OPTIMIZED] /calculate-recipe-optimized/")
        start_time = time.time()
        try:
            response_opt = requests.post(
                f"{base_url}/calculate-recipe-optimized/",
                json=test_case["data"],
                timeout=30
            )
            opt_time = time.time() - start_time
            
            if response_opt.status_code == 200:
                opt_data = response_opt.json()
                opt_score = opt_data["recipe_scores"]["single_score"]
                print(f"✅ SUCCESS")
                print(f"   Response time: {opt_time:.3f} seconds")
                print(f"   Recipe single score: {opt_score}")
                print(f"   Items in response: {len(opt_data['graded_lcia_results'])}")
            else:
                print(f"❌ FAILED - Status: {response_opt.status_code}")
                continue
                
        except Exception as e:
            print(f"❌ FAILED - Exception: {e}")
            continue
            
        # Compare results
        print(f"\n📊 COMPARISON:")
        print(f"   Original time:  {orig_time:.3f}s")
        print(f"   Optimized time: {opt_time:.3f}s")
        
        if opt_time < orig_time:
            speedup = orig_time / opt_time
            print(f"   Performance: {speedup:.1f}x faster")
        else:
            slowdown = opt_time / orig_time
            print(f"   Performance: {slowdown:.1f}x slower")
            
        # Mathematical consistency check
        if abs(orig_score - opt_score) < 1e-12:
            print(f"   ✅ IDENTICAL RESULTS - Mathematical consistency verified")
        else:
            print(f"   ❌ DIFFERENT RESULTS!")
            print(f"      Original:  {orig_score}")
            print(f"      Optimized: {opt_score}")
            print(f"      Difference: {abs(orig_score - opt_score)}")
    
    print(f"\n🏁 CONSISTENCY TESTING COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    test_optimized_consistency()