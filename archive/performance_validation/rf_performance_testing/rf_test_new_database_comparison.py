#!/usr/bin/env python3
"""
Comprehensive performance test suite for New Database comparison.

Tests performance and result consistency between:
- Port 8082: Original code + New database (truly original N+1 patterns)
- Port 8083: Optimized code + New database (bulk query optimizations)

This should demonstrate the full optimization impact with the new database.
"""

import json
import time
import statistics
from typing import List, Dict, Tuple, Any
import requests

class NewDatabaseComparisonTest:
    def __init__(self):
        self.original_url = "http://localhost:8082"  # Original code + New DB
        self.optimized_url = "http://localhost:8083"  # Optimized code + New DB
        
        # Test items from rf_test_20_items_summary.md
        self.test_items = [
            "11032-FRA",  # Basil, dried
            "11045-BRA",  # Baker's yeast, dehydrated  
            "11163-ESP",  # Sweet and sour sauce, prepacked
            "12737-FRA",  # Mimolette cheese, half-old
            "12834-FRA",  # Crottin de Chavignol cheese
            "13731-FRA",  # Peach, canned in light syrup
            "15006-FRA",  # Coconut, ripe kernel, fresh
            "19026-FRA",  # Condensed milk, without sugar
            "20039-FRA",  # Leek, raw
            "20904-FRA",  # Tofu, plain
            "25123-FRA",  # Moussaka
            "26091-FRA",  # Mullet, raw
            "26270-FRA",  # Pizza, tuna
            "31102-FRA",  # Cereal bar with chocolate
            "4020-FRA",   # Dauphine potato, frozen, raw
            "51510-FRA",  # Frik (crushed immature durum wheat)
            "7650-FRA",   # Croissant w almonds, from bakery
            "9380-FRA",   # Buckwheat, whole, raw
            "9621-FRA",   # Wheat bran
            "9640-FRA",   # Oat bran
        ]
        
        self.results = {
            "test_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "container_info": {
                "port_8082": "Original code + New database",
                "port_8083": "Optimized code + New database"
            },
            "get_items_tests": {},
            "calculate_recipe_tests": {},
            "consistency_tests": {}
        }

    def test_get_items_performance(self) -> Dict[str, Any]:
        """Test GET /items/ endpoint performance"""
        print("\n=== Testing GET /items/ Performance ===")
        
        # Test different pagination scenarios
        test_scenarios = [
            {"name": "full_items", "params": ""},
            {"name": "first_100", "params": "?limit=100"},
            {"name": "items_500_1000", "params": "?skip=500&limit=500"},
        ]
        
        results = {}
        
        for scenario in test_scenarios:
            print(f"\nTesting {scenario['name']}...")
            scenario_results = {
                "original": {"times": [], "response_size": 0, "item_count": 0},
                "optimized": {"times": [], "response_size": 0, "item_count": 0}
            }
            
            # Test original endpoint (port 8082)
            for run in range(3):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.original_url}/items/{scenario['params']}")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_time = end_time - start_time
                        scenario_results["original"]["times"].append(response_time)
                        if run == 0:  # Only count size once
                            data = response.json()
                            scenario_results["original"]["response_size"] = len(response.text)
                            scenario_results["original"]["item_count"] = len(data) if isinstance(data, dict) else 0
                        print(f"  Original run {run+1}: {response_time:.3f}s")
                    else:
                        print(f"  Original run {run+1}: ERROR {response.status_code}")
                except Exception as e:
                    print(f"  Original run {run+1}: EXCEPTION {e}")
            
            # Test optimized endpoint (port 8083)
            for run in range(3):
                start_time = time.time()
                try:
                    response = requests.get(f"{self.optimized_url}/items/{scenario['params']}")
                    end_time = time.time()
                    
                    if response.status_code == 200:
                        response_time = end_time - start_time
                        scenario_results["optimized"]["times"].append(response_time)
                        if run == 0:  # Only count size once
                            data = response.json()
                            scenario_results["optimized"]["response_size"] = len(response.text)
                            scenario_results["optimized"]["item_count"] = len(data) if isinstance(data, dict) else 0
                        print(f"  Optimized run {run+1}: {response_time:.3f}s")
                    else:
                        print(f"  Optimized run {run+1}: ERROR {response.status_code}")
                except Exception as e:
                    print(f"  Optimized run {run+1}: EXCEPTION {e}")
                    
            # Calculate averages
            if scenario_results["original"]["times"]:
                scenario_results["original"]["avg_time"] = statistics.mean(scenario_results["original"]["times"])
            if scenario_results["optimized"]["times"]:
                scenario_results["optimized"]["avg_time"] = statistics.mean(scenario_results["optimized"]["times"])
                
            # Calculate improvement ratio
            if (scenario_results["original"]["times"] and 
                scenario_results["optimized"]["times"] and
                scenario_results["optimized"]["avg_time"] > 0):
                scenario_results["improvement_ratio"] = (
                    scenario_results["original"]["avg_time"] / scenario_results["optimized"]["avg_time"]
                )
            
            results[scenario["name"]] = scenario_results
            
        return results

    def test_calculate_recipe_performance(self) -> Dict[str, Any]:
        """Test POST /calculate-recipe/ endpoint performance with different recipe sizes"""
        print("\n=== Testing POST /calculate-recipe/ Performance ===")
        
        test_recipes = [
            {
                "name": "single_item",
                "items": [{"item_id": "11032-FRA", "amount": 100}]
            },
            {
                "name": "small_recipe_5_items", 
                "items": [
                    {"item_id": item_id, "amount": 100 + i * 25} 
                    for i, item_id in enumerate(self.test_items[:5])
                ]
            },
            {
                "name": "medium_recipe_10_items",
                "items": [
                    {"item_id": item_id, "amount": 100 + i * 10}
                    for i, item_id in enumerate(self.test_items[:10])
                ]
            },
            {
                "name": "large_recipe_20_items",
                "items": [
                    {"item_id": item_id, "amount": 50 + i * 5}
                    for i, item_id in enumerate(self.test_items)
                ]
            }
        ]
        
        results = {}
        
        for recipe in test_recipes:
            print(f"\nTesting {recipe['name']} ({len(recipe['items'])} items)...")
            
            recipe_data = {
                "items": recipe["items"],
                "weighting_scheme_name": "delphi_r0110"
            }
            
            recipe_results = {
                "original": {"times": [], "success_count": 0},
                "optimized": {"times": [], "success_count": 0}
            }
            
            # Test original endpoint (port 8082)
            for run in range(5):
                start_time = time.time()
                try:
                    response = requests.post(
                        f"{self.original_url}/calculate-recipe/",
                        json=recipe_data,
                        headers={"Content-Type": "application/json"}
                    )
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    recipe_results["original"]["times"].append(response_time)
                    
                    if response.status_code == 200:
                        recipe_results["original"]["success_count"] += 1
                        print(f"  Original run {run+1}: {response_time:.3f}s ✓")
                    else:
                        print(f"  Original run {run+1}: {response_time:.3f}s ERROR {response.status_code}")
                        
                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    recipe_results["original"]["times"].append(response_time)
                    print(f"  Original run {run+1}: {response_time:.3f}s EXCEPTION")
            
            # Test optimized endpoint (port 8083)
            for run in range(5):
                start_time = time.time()
                try:
                    response = requests.post(
                        f"{self.optimized_url}/calculate-recipe/",
                        json=recipe_data,
                        headers={"Content-Type": "application/json"}
                    )
                    end_time = time.time()
                    
                    response_time = end_time - start_time
                    recipe_results["optimized"]["times"].append(response_time)
                    
                    if response.status_code == 200:
                        recipe_results["optimized"]["success_count"] += 1
                        print(f"  Optimized run {run+1}: {response_time:.3f}s ✓")
                    else:
                        print(f"  Optimized run {run+1}: {response_time:.3f}s ERROR {response.status_code}")
                        
                except Exception as e:
                    end_time = time.time()
                    response_time = end_time - start_time
                    recipe_results["optimized"]["times"].append(response_time)
                    print(f"  Optimized run {run+1}: {response_time:.3f}s EXCEPTION")
            
            # Calculate averages and improvement
            if recipe_results["original"]["times"]:
                recipe_results["original"]["avg_time"] = statistics.mean(recipe_results["original"]["times"])
            if recipe_results["optimized"]["times"]:
                recipe_results["optimized"]["avg_time"] = statistics.mean(recipe_results["optimized"]["times"])
                
            if (recipe_results["original"]["times"] and 
                recipe_results["optimized"]["times"] and
                recipe_results["optimized"]["avg_time"] > 0):
                recipe_results["improvement_ratio"] = (
                    recipe_results["original"]["avg_time"] / recipe_results["optimized"]["avg_time"]
                )
            
            results[recipe["name"]] = recipe_results
            
        return results

    def test_result_consistency(self) -> Dict[str, Any]:
        """Test that results are mathematically identical between containers"""
        print("\n=== Testing Result Consistency ===")
        
        # Test a simple recipe
        test_recipe = {
            "items": [
                {"item_id": "11032-FRA", "amount": 100},
                {"item_id": "12737-FRA", "amount": 150}
            ],
            "weighting_scheme_name": "delphi_r0110"
        }
        
        results = {"items_consistency": {}, "recipe_consistency": {}}
        
        # Test GET /items/ consistency (first 10 items)
        try:
            original_items = requests.get(f"{self.original_url}/items/?limit=10").json()
            optimized_items = requests.get(f"{self.optimized_url}/items/?limit=10").json()
            
            results["items_consistency"] = {
                "identical": original_items == optimized_items,
                "original_count": len(original_items) if isinstance(original_items, dict) else 0,
                "optimized_count": len(optimized_items) if isinstance(optimized_items, dict) else 0
            }
            
        except Exception as e:
            results["items_consistency"] = {"error": str(e)}
        
        # Test recipe calculation consistency
        try:
            original_response = requests.post(
                f"{self.original_url}/calculate-recipe/",
                json=test_recipe,
                headers={"Content-Type": "application/json"}
            )
            optimized_response = requests.post(
                f"{self.optimized_url}/calculate-recipe/",
                json=test_recipe,
                headers={"Content-Type": "application/json"}
            )
            
            original_success = original_response.status_code == 200
            optimized_success = optimized_response.status_code == 200
            
            if original_success and optimized_success:
                original_data = original_response.json()
                optimized_data = optimized_response.json()
                results["recipe_consistency"] = {
                    "both_successful": True,
                    "identical": original_data == optimized_data,
                    "original_status": original_response.status_code,
                    "optimized_status": optimized_response.status_code
                }
            else:
                results["recipe_consistency"] = {
                    "both_successful": False,
                    "original_status": original_response.status_code,
                    "optimized_status": optimized_response.status_code,
                    "original_error": original_response.text[:200] if not original_success else None,
                    "optimized_error": optimized_response.text[:200] if not optimized_success else None
                }
                
        except Exception as e:
            results["recipe_consistency"] = {"error": str(e)}
            
        return results

    def run_comprehensive_test(self) -> None:
        """Run all tests and generate comprehensive report"""
        print("=" * 80)
        print("NEW DATABASE PERFORMANCE COMPARISON TEST")
        print("=" * 80)
        print(f"Original Container (Port 8082): {self.results['container_info']['port_8082']}")
        print(f"Optimized Container (Port 8083): {self.results['container_info']['port_8083']}")
        print("=" * 80)
        
        # Run all tests
        self.results["get_items_tests"] = self.test_get_items_performance()
        self.results["calculate_recipe_tests"] = self.test_calculate_recipe_performance()
        self.results["consistency_tests"] = self.test_result_consistency()
        
        # Generate summary
        self.generate_summary_report()
        
        # Save results to file
        with open("rf_performance_testing/rf_new_database_comparison_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\nFull results saved to: rf_performance_testing/rf_new_database_comparison_results.json")

    def generate_summary_report(self) -> None:
        """Generate and print summary report"""
        print("\n" + "=" * 80)
        print("PERFORMANCE SUMMARY REPORT")
        print("=" * 80)
        
        # GET /items/ summary
        print("\n📊 GET /items/ Performance:")
        for scenario, data in self.results["get_items_tests"].items():
            if "avg_time" in data.get("original", {}) and "avg_time" in data.get("optimized", {}):
                orig_time = data["original"]["avg_time"]
                opt_time = data["optimized"]["avg_time"]
                improvement = data.get("improvement_ratio", 0)
                print(f"  {scenario:20s}: {orig_time:.3f}s → {opt_time:.3f}s ({improvement:.1f}x improvement)")
            
        # POST /calculate-recipe/ summary  
        print("\n⚡ POST /calculate-recipe/ Performance:")
        for recipe, data in self.results["calculate_recipe_tests"].items():
            if "avg_time" in data.get("original", {}) and "avg_time" in data.get("optimized", {}):
                orig_time = data["original"]["avg_time"]
                opt_time = data["optimized"]["avg_time"]
                improvement = data.get("improvement_ratio", 0)
                orig_success = data["original"]["success_count"]
                opt_success = data["optimized"]["success_count"]
                print(f"  {recipe:20s}: {orig_time:.3f}s → {opt_time:.3f}s ({improvement:.1f}x improvement)")
                print(f"  {'':20s}  Success: {orig_success}/5 → {opt_success}/5")
                
        # Consistency summary
        print("\n🎯 Result Consistency:")
        consistency = self.results["consistency_tests"]
        if "items_consistency" in consistency:
            items_check = consistency["items_consistency"]
            if "identical" in items_check:
                status = "✅ IDENTICAL" if items_check["identical"] else "❌ DIFFERENT"
                print(f"  GET /items/:        {status}")
                
        if "recipe_consistency" in consistency:
            recipe_check = consistency["recipe_consistency"]
            if "identical" in recipe_check:
                status = "✅ IDENTICAL" if recipe_check["identical"] else "❌ DIFFERENT"
                print(f"  POST /calculate/:   {status}")
            elif "both_successful" in recipe_check:
                if not recipe_check["both_successful"]:
                    print(f"  POST /calculate/:   ❌ ERRORS DETECTED")
                    print(f"                      Original: {recipe_check['original_status']}")
                    print(f"                      Optimized: {recipe_check['optimized_status']}")

if __name__ == "__main__":
    tester = NewDatabaseComparisonTest()
    tester.run_comprehensive_test()