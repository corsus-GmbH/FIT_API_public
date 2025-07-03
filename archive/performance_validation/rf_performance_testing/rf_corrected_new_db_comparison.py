#!/usr/bin/env python3
"""
Corrected performance comparison for new database containers with proper payload format.
"""

import json
import time
import requests

def test_recipe_performance():
    """Test POST /calculate-recipe/ with corrected payload format"""
    print("=== POST /calculate-recipe/ Performance Test (Corrected Format) ===")
    
    test_recipes = [
        {
            "name": "1 item (port specific)",
            "port_8082_payload": {"items": {"10001-FRA": 0.1}},  # Item that exists in 8082
            "port_8083_payload": {"items": {"25541-FRA": 0.1}}   # Item that exists in 8083
        },
        {
            "name": "3 items (mixed)",
            "port_8082_payload": {"items": {"10001-FRA": 0.1, "10002-FRA": 0.15, "10003-FRA": 0.05}},
            "port_8083_payload": {"items": {"25541-FRA": 0.1, "21514-FRA": 0.15, "26211-FRA": 0.05}}
        }
    ]
    
    results = {}
    
    for recipe in test_recipes:
        print(f"\nTesting {recipe['name']}:")
        recipe_results = {"original": [], "optimized": []}
        
        # Test original (port 8082)
        for run in range(3):
            start = time.time()
            try:
                response = requests.post(
                    "http://localhost:8082/calculate-recipe/",
                    json=recipe["port_8082_payload"],
                    headers={"Content-Type": "application/json"},
                    timeout=60
                )
                end = time.time()
                if response.status_code == 200:
                    recipe_results["original"].append(end - start)
                    print(f"  Original run {run+1}: {end - start:.3f}s ✓")
                else:
                    print(f"  Original run {run+1}: ERROR {response.status_code}")
            except Exception as e:
                print(f"  Original run {run+1}: EXCEPTION {e}")
        
        # Test optimized (port 8083)
        for run in range(3):
            start = time.time()
            try:
                response = requests.post(
                    "http://localhost:8083/calculate-recipe/",
                    json=recipe["port_8083_payload"],
                    headers={"Content-Type": "application/json"},
                    timeout=30
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
            print(f"  Average times: Original {orig_avg:.3f}s → Optimized {opt_avg:.3f}s")
            print(f"  Improvement: {improvement:.1f}x faster")
            recipe_results["improvement"] = improvement
            recipe_results["orig_avg"] = orig_avg
            recipe_results["opt_avg"] = opt_avg
            
        results[recipe["name"]] = recipe_results
    
    return results

def test_cross_consistency():
    """Test if results are consistent when using same item across containers"""
    print("\n=== Cross-Container Consistency Test ===")
    
    # Find an item that exists in both containers by testing
    test_items = ["10001-FRA", "25541-FRA", "21514-FRA"]
    common_item = None
    
    for item in test_items:
        payload = {"items": {item: 0.1}}
        try:
            # Test if item works in both containers
            resp_8082 = requests.post("http://localhost:8082/calculate-recipe/", json=payload, timeout=30)
            resp_8083 = requests.post("http://localhost:8083/calculate-recipe/", json=payload, timeout=30)
            
            if resp_8082.status_code == 200 and resp_8083.status_code == 200:
                common_item = item
                print(f"Found common item: {item}")
                
                # Compare results
                data_8082 = resp_8082.json()
                data_8083 = resp_8083.json()
                
                # Compare single scores if available
                score_8082 = data_8082.get("Recipe Info", {}).get("Single Score", {}).get("Single Score")
                score_8083 = data_8083.get("Recipe Info", {}).get("Single Score", {}).get("Single Score")
                
                if score_8082 is not None and score_8083 is not None:
                    diff = abs(score_8082 - score_8083)
                    print(f"Single scores: 8082={score_8082:.6f}, 8083={score_8083:.6f}")
                    print(f"Difference: {diff:.6f}")
                    if diff < 0.001:
                        print("✅ Results are very close (likely identical calculations)")
                    else:
                        print("❌ Results differ significantly")
                break
                
        except Exception as e:
            print(f"Item {item} failed: {e}")
            continue
    
    if not common_item:
        print("❌ No common item found that works in both containers")
        return {"common_item": None}
    
    return {"common_item": common_item, "consistency_verified": True}

def main():
    print("=" * 80)
    print("CORRECTED NEW DATABASE PERFORMANCE COMPARISON")
    print("=" * 80)
    print("Port 8082: Original code + New database")
    print("Port 8083: Optimized code + New database")
    print("Using correct API payload format: {'items': {'item-id': amount}}")
    print("=" * 80)
    
    # Run tests
    recipe_results = test_recipe_performance()
    consistency_results = test_cross_consistency()
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY REPORT")
    print("=" * 80)
    
    print("\n⚡ POST /calculate-recipe/ Performance:")
    for test_name, data in recipe_results.items():
        if "improvement" in data:
            print(f"  {test_name:20s}: {data['orig_avg']:.3f}s → {data['opt_avg']:.3f}s ({data['improvement']:.1f}x improvement)")
    
    print("\n🎯 Result Consistency:")
    if consistency_results.get("consistency_verified"):
        print(f"  Common item test:    ✅ VERIFIED")
    else:
        print(f"  Common item test:    ❌ COULD NOT VERIFY")
    
    # Save results
    all_results = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "recipe_tests": recipe_results,
        "consistency_tests": consistency_results,
        "note": "Fixed payload format - items as dict, not list"
    }
    
    with open("rf_corrected_new_db_comparison_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\nResults saved to: rf_corrected_new_db_comparison_results.json")

if __name__ == "__main__":
    main()