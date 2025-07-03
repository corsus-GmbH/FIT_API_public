#!/usr/bin/env python3
"""
Quick performance comparison for new database containers.
Tests limited scenarios to avoid timeouts while demonstrating optimization impact.
"""

import json
import time
import requests

def test_items_performance():
    """Test GET /items/ with different limits"""
    print("=== GET /items/ Performance Test ===")
    
    test_cases = [
        {"name": "5 items", "params": "?limit=5"},
        {"name": "50 items", "params": "?limit=50"},
        {"name": "100 items", "params": "?limit=100"},
    ]
    
    results = {}
    
    for case in test_cases:
        print(f"\nTesting {case['name']}:")
        case_results = {"original": [], "optimized": []}
        
        # Test original (port 8082) - only 1 run due to slowness
        start = time.time()
        try:
            response = requests.get(f"http://localhost:8082/items/{case['params']}", timeout=30)
            end = time.time()
            if response.status_code == 200:
                case_results["original"].append(end - start)
                print(f"  Original: {end - start:.3f}s")
            else:
                print(f"  Original: ERROR {response.status_code}")
        except requests.Timeout:
            print(f"  Original: TIMEOUT (>30s)")
        except Exception as e:
            print(f"  Original: EXCEPTION {e}")
        
        # Test optimized (port 8083) - 3 runs for average
        for run in range(3):
            start = time.time()
            try:
                response = requests.get(f"http://localhost:8083/items/{case['params']}", timeout=10)
                end = time.time()
                if response.status_code == 200:
                    case_results["optimized"].append(end - start)
                    print(f"  Optimized run {run+1}: {end - start:.3f}s")
                else:
                    print(f"  Optimized run {run+1}: ERROR {response.status_code}")
            except Exception as e:
                print(f"  Optimized run {run+1}: EXCEPTION {e}")
        
        # Calculate improvement
        if case_results["original"] and case_results["optimized"]:
            orig_avg = sum(case_results["original"]) / len(case_results["original"])
            opt_avg = sum(case_results["optimized"]) / len(case_results["optimized"])
            improvement = orig_avg / opt_avg if opt_avg > 0 else 0
            print(f"  Improvement: {improvement:.1f}x faster")
            case_results["improvement"] = improvement
            
        results[case["name"]] = case_results
    
    return results

def test_recipe_performance():
    """Test POST /calculate-recipe/ with small recipes"""
    print("\n=== POST /calculate-recipe/ Performance Test ===")
    
    recipes = [
        {
            "name": "1 item",
            "data": {
                "items": [{"item_id": "11032-FRA", "amount": 100}],
                "weighting_scheme_name": "delphi_r0110"
            }
        },
        {
            "name": "3 items", 
            "data": {
                "items": [
                    {"item_id": "11032-FRA", "amount": 100},
                    {"item_id": "12737-FRA", "amount": 150},
                    {"item_id": "20039-FRA", "amount": 75}
                ],
                "weighting_scheme_name": "delphi_r0110"
            }
        }
    ]
    
    results = {}
    
    for recipe in recipes:
        print(f"\nTesting {recipe['name']}:")
        recipe_results = {"original": [], "optimized": []}
        
        # Test original (port 8082) - 1 run due to potential slowness
        start = time.time()
        try:
            response = requests.post(
                "http://localhost:8082/calculate-recipe/",
                json=recipe["data"],
                headers={"Content-Type": "application/json"},
                timeout=60
            )
            end = time.time()
            if response.status_code == 200:
                recipe_results["original"].append(end - start)
                print(f"  Original: {end - start:.3f}s ✓")
            else:
                print(f"  Original: ERROR {response.status_code}")
                print(f"    Response: {response.text[:100]}")
        except requests.Timeout:
            print(f"  Original: TIMEOUT (>60s)")
        except Exception as e:
            print(f"  Original: EXCEPTION {e}")
        
        # Test optimized (port 8083) - 3 runs
        for run in range(3):
            start = time.time()
            try:
                response = requests.post(
                    "http://localhost:8083/calculate-recipe/",
                    json=recipe["data"],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                end = time.time()
                if response.status_code == 200:
                    recipe_results["optimized"].append(end - start)
                    print(f"  Optimized run {run+1}: {end - start:.3f}s ✓")
                else:
                    print(f"  Optimized run {run+1}: ERROR {response.status_code}")
            except Exception as e:
                print(f"  Optimized run {run+1}: EXCEPTION {e}")
        
        # Calculate improvement
        if recipe_results["original"] and recipe_results["optimized"]:
            orig_avg = sum(recipe_results["original"]) / len(recipe_results["original"])
            opt_avg = sum(recipe_results["optimized"]) / len(recipe_results["optimized"])
            improvement = orig_avg / opt_avg if opt_avg > 0 else 0
            print(f"  Improvement: {improvement:.1f}x faster")
            recipe_results["improvement"] = improvement
            
        results[recipe["name"]] = recipe_results
    
    return results

def test_consistency():
    """Test result consistency between containers"""
    print("\n=== Result Consistency Test ===")
    
    # Test small items set
    try:
        orig_items = requests.get("http://localhost:8082/items/?limit=3", timeout=30).json()
        opt_items = requests.get("http://localhost:8083/items/?limit=3", timeout=10).json()
        items_identical = orig_items == opt_items
        print(f"Items consistency (3 items): {'✅ IDENTICAL' if items_identical else '❌ DIFFERENT'}")
    except Exception as e:
        print(f"Items consistency test: ERROR {e}")
        items_identical = False
    
    # Test simple recipe
    recipe_data = {
        "items": [{"item_id": "11032-FRA", "amount": 100}],
        "weighting_scheme_name": "delphi_r0110"
    }
    
    try:
        orig_recipe = requests.post(
            "http://localhost:8082/calculate-recipe/",
            json=recipe_data,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        opt_recipe = requests.post(
            "http://localhost:8083/calculate-recipe/",
            json=recipe_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if orig_recipe.status_code == 200 and opt_recipe.status_code == 200:
            recipe_identical = orig_recipe.json() == opt_recipe.json()
            print(f"Recipe consistency (1 item): {'✅ IDENTICAL' if recipe_identical else '❌ DIFFERENT'}")
        else:
            print(f"Recipe consistency: ERROR - Original: {orig_recipe.status_code}, Optimized: {opt_recipe.status_code}")
            recipe_identical = False
            
    except Exception as e:
        print(f"Recipe consistency test: ERROR {e}")
        recipe_identical = False
    
    return {"items_identical": items_identical, "recipe_identical": recipe_identical}

def main():
    print("=" * 80)
    print("QUICK NEW DATABASE PERFORMANCE COMPARISON")
    print("=" * 80)
    print("Port 8082: Original code + New database")
    print("Port 8083: Optimized code + New database")
    print("=" * 80)
    
    # Run tests
    items_results = test_items_performance()
    recipe_results = test_recipe_performance()
    consistency_results = test_consistency()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    print("\n📊 GET /items/ Performance:")
    for test_name, data in items_results.items():
        if "improvement" in data:
            print(f"  {test_name:12s}: {data['improvement']:.1f}x improvement")
    
    print("\n⚡ POST /calculate-recipe/ Performance:")
    for test_name, data in recipe_results.items():
        if "improvement" in data:
            print(f"  {test_name:12s}: {data['improvement']:.1f}x improvement")
    
    print("\n🎯 Result Consistency:")
    if consistency_results["items_identical"]:
        print("  GET /items/:     ✅ IDENTICAL")
    else:
        print("  GET /items/:     ❌ DIFFERENT")
        
    if consistency_results["recipe_identical"]:
        print("  POST /calculate/: ✅ IDENTICAL")
    else:
        print("  POST /calculate/: ❌ DIFFERENT")
    
    # Save results
    all_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "items_tests": items_results,
        "recipe_tests": recipe_results,
        "consistency_tests": consistency_results
    }
    
    with open("rf_quick_new_db_comparison_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nResults saved to: rf_quick_new_db_comparison_results.json")

if __name__ == "__main__":
    main()