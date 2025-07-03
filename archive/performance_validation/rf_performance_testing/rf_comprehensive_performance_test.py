#!/usr/bin/env python3
"""
Comprehensive performance test suite for POST /calculate-recipe/ optimization.

Tests extensive performance comparison between original and optimized endpoints
with varying recipe sizes, including large recipe sets to validate bulk query benefits.
"""

import json
import time
import random
import statistics
from typing import List, Dict, Tuple, Any
import requests

class PerformanceTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8081"
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
            # Additional items for larger recipes
            "11001-FRA",  # Additional test items
            "11002-FRA", 
            "11003-FRA",
            "11004-FRA",
            "11005-FRA",
            "11006-FRA",
            "11007-FRA",
            "11008-FRA",
            "11009-FRA",
            "11010-FRA",
            "11011-FRA",
            "11012-FRA",
            "11013-FRA",
            "11014-FRA"
        ]
        self.results = []
        
    def generate_recipe(self, size: int) -> Dict[str, float]:
        """Generate a recipe with specified number of items."""
        # Use first 'size' items to ensure consistency
        selected_items = self.test_items[:min(size, len(self.test_items))]
        recipe = {}
        for item in selected_items:
            # Random amounts between 0.05kg and 0.5kg
            amount = round(random.uniform(0.05, 0.5), 3)
            recipe[item] = amount
        return recipe
    
    def test_endpoint(self, endpoint: str, recipe_data: Dict[str, Any], test_name: str) -> Tuple[bool, float, Dict[str, Any]]:
        """Test a single endpoint with given recipe data."""
        start_time = time.time()
        try:
            response = requests.post(
                f"{self.base_url}{endpoint}",
                json=recipe_data,
                timeout=60  # Increased timeout for large recipes
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return True, response_time, data
            else:
                print(f"❌ {test_name} FAILED - Status: {response.status_code}")
                print(f"   Error: {response.text[:200]}...")
                return False, response_time, {}
                
        except Exception as e:
            response_time = time.time() - start_time
            print(f"❌ {test_name} FAILED - Exception: {e}")
            return False, response_time, {}
    
    def compare_results(self, orig_data: Dict[str, Any], opt_data: Dict[str, Any]) -> Tuple[bool, float]:
        """Compare mathematical results between original and optimized endpoints."""
        try:
            orig_score = orig_data["Recipe Info"]["Single Score"]["Single Score"]
            opt_score = opt_data["Recipe Info"]["Single Score"]["Single Score"]
            difference = abs(orig_score - opt_score)
            return difference < 1e-12, difference
        except Exception as e:
            print(f"❌ Error comparing results: {e}")
            return False, float('inf')
    
    def run_performance_test(self, recipe_size: int, iterations: int = 3) -> Dict[str, Any]:
        """Run performance test for a specific recipe size with multiple iterations."""
        print(f"\n{'='*80}")
        print(f"TESTING RECIPE SIZE: {recipe_size} ITEMS ({iterations} iterations)")
        print(f"{'='*80}")
        
        # Generate consistent recipe for all iterations
        recipe_items = self.generate_recipe(recipe_size)
        recipe_data = {
            "items": recipe_items,
            "weighting_scheme_name": "delphi_r0110"
        }
        
        print(f"Recipe contains {len(recipe_items)} items")
        print(f"Total mass: {sum(recipe_items.values()):.3f} kg")
        
        orig_times = []
        opt_times = []
        consistency_checks = []
        
        for iteration in range(iterations):
            print(f"\n--- Iteration {iteration + 1}/{iterations} ---")
            
            # Test original endpoint
            orig_success, orig_time, orig_data = self.test_endpoint(
                "/calculate-recipe/", recipe_data, f"Original (iteration {iteration + 1})"
            )
            
            if not orig_success:
                return {"status": "failed", "reason": "Original endpoint failed"}
            
            orig_times.append(orig_time)
            
            # Test optimized endpoint
            opt_success, opt_time, opt_data = self.test_endpoint(
                "/calculate-recipe-optimized/", recipe_data, f"Optimized (iteration {iteration + 1})"
            )
            
            if not opt_success:
                return {"status": "failed", "reason": "Optimized endpoint failed"}
            
            opt_times.append(opt_time)
            
            # Compare results
            consistent, difference = self.compare_results(orig_data, opt_data)
            consistency_checks.append(consistent)
            
            print(f"   Original time:  {orig_time:.3f}s")
            print(f"   Optimized time: {opt_time:.3f}s")
            print(f"   Speedup: {orig_time/opt_time:.1f}x")
            print(f"   Consistent: {'✅' if consistent else '❌'} (diff: {difference:.2e})")
        
        # Calculate statistics
        orig_avg = statistics.mean(orig_times)
        opt_avg = statistics.mean(opt_times)
        orig_std = statistics.stdev(orig_times) if len(orig_times) > 1 else 0
        opt_std = statistics.stdev(opt_times) if len(opt_times) > 1 else 0
        
        result = {
            "status": "success",
            "recipe_size": recipe_size,
            "iterations": iterations,
            "original": {
                "times": orig_times,
                "avg_time": orig_avg,
                "std_time": orig_std,
                "min_time": min(orig_times),
                "max_time": max(orig_times)
            },
            "optimized": {
                "times": opt_times,
                "avg_time": opt_avg,
                "std_time": opt_std,
                "min_time": min(opt_times),
                "max_time": max(opt_times)
            },
            "performance": {
                "avg_speedup": orig_avg / opt_avg,
                "min_speedup": min(orig_times) / max(opt_times),
                "max_speedup": max(orig_times) / min(opt_times)
            },
            "consistency": {
                "all_consistent": all(consistency_checks),
                "consistent_count": sum(consistency_checks),
                "total_checks": len(consistency_checks)
            }
        }
        
        print(f"\n📊 SUMMARY FOR {recipe_size} ITEMS:")
        print(f"   Original avg:  {orig_avg:.3f}s (±{orig_std:.3f}s)")
        print(f"   Optimized avg: {opt_avg:.3f}s (±{opt_std:.3f}s)")
        print(f"   Average speedup: {result['performance']['avg_speedup']:.1f}x")
        print(f"   Consistency: {result['consistency']['consistent_count']}/{result['consistency']['total_checks']} ✅")
        
        return result
    
    def run_comprehensive_test_suite(self):
        """Run comprehensive performance test suite with various recipe sizes."""
        print("FIT API Comprehensive Performance Test Suite")
        print("=" * 80)
        print("Testing /calculate-recipe/ vs /calculate-recipe-optimized/")
        print("=" * 80)
        
        # Test various recipe sizes to demonstrate scaling benefits  
        test_sizes = [1, 3, 5, 10, 15, 20, 25, 30]  # Large sizes to show bulk query benefits
        iterations = 3  # Multiple iterations for statistical significance
        
        print(f"Test plan: {len(test_sizes)} recipe sizes, {iterations} iterations each")
        print(f"Recipe sizes: {test_sizes}")
        
        overall_results = []
        
        for size in test_sizes:
            if size > len(self.test_items):
                print(f"\n⚠️  Skipping size {size} - not enough test items ({len(self.test_items)} available)")
                continue
                
            result = self.run_performance_test(size, iterations)
            if result["status"] == "success":
                overall_results.append(result)
            else:
                print(f"❌ Test failed for size {size}: {result['reason']}")
                break
        
        # Generate comprehensive report
        self.generate_final_report(overall_results)
        
        return overall_results
    
    def generate_final_report(self, results: List[Dict[str, Any]]):
        """Generate comprehensive final report."""
        print(f"\n{'='*80}")
        print("COMPREHENSIVE PERFORMANCE TEST RESULTS")
        print(f"{'='*80}")
        
        if not results:
            print("❌ No successful test results to report")
            return
        
        print(f"{'Size':<6} {'Original (avg)':<15} {'Optimized (avg)':<16} {'Speedup':<10} {'Consistent':<12}")
        print("-" * 80)
        
        total_speedup = 0
        total_consistent = 0
        total_tests = 0
        
        for result in results:
            size = result["recipe_size"]
            orig_avg = result["original"]["avg_time"]
            opt_avg = result["optimized"]["avg_time"]  
            speedup = result["performance"]["avg_speedup"]
            consistent = result["consistency"]["all_consistent"]
            
            total_speedup += speedup
            total_consistent += 1 if consistent else 0
            total_tests += 1
            
            print(f"{size:<6} {orig_avg:<15.3f} {opt_avg:<16.3f} {speedup:<10.1f}x {'✅' if consistent else '❌':<12}")
        
        avg_speedup = total_speedup / total_tests if total_tests > 0 else 0
        consistency_rate = (total_consistent / total_tests * 100) if total_tests > 0 else 0
        
        print("-" * 80)
        print(f"OVERALL RESULTS:")
        print(f"  Tests completed: {total_tests}/{len(results)}")
        print(f"  Average speedup: {avg_speedup:.1f}x")
        print(f"  Consistency rate: {consistency_rate:.1f}% ({total_consistent}/{total_tests})")
        
        # Scaling analysis
        if len(results) >= 3:
            print(f"\nSCALING ANALYSIS:")
            small_recipes = [r for r in results if r["recipe_size"] <= 5]
            large_recipes = [r for r in results if r["recipe_size"] >= 15]
            
            if small_recipes and large_recipes:
                small_avg_speedup = statistics.mean([r["performance"]["avg_speedup"] for r in small_recipes])
                large_avg_speedup = statistics.mean([r["performance"]["avg_speedup"] for r in large_recipes])
                
                print(f"  Small recipes (≤5 items): {small_avg_speedup:.1f}x average speedup")
                print(f"  Large recipes (≥15 items): {large_avg_speedup:.1f}x average speedup")
                print(f"  Bulk query benefit: {large_avg_speedup/small_avg_speedup:.1f}x better scaling")
        
        # Final recommendation
        print(f"\n🎯 RECOMMENDATION:")
        if consistency_rate >= 99 and avg_speedup >= 1.2:
            print("✅ READY FOR PRODUCTION DEPLOYMENT")
            print("   - Mathematical consistency verified")
            print("   - Significant performance improvement achieved")
            print("   - Safe to replace original endpoint")
        elif consistency_rate >= 99:
            print("⚠️  MATHEMATICALLY CONSISTENT BUT LIMITED PERFORMANCE GAINS")
            print("   - Results are identical but performance improvement is modest")
        else:
            print("❌ NOT READY FOR DEPLOYMENT")
            print("   - Mathematical inconsistencies detected")
            print("   - Further investigation required")
        
        print(f"{'='*80}")

def main():
    """Main function to run comprehensive performance tests."""
    # Set random seed for reproducible recipe generation
    random.seed(42)
    
    test_suite = PerformanceTestSuite()
    results = test_suite.run_comprehensive_test_suite()
    
    # Save results to file for future reference
    with open("/home/marius/projects/FIT_API_public/rf_performance_testing/rf_comprehensive_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: rf_comprehensive_test_results.json")

if __name__ == "__main__":
    main()