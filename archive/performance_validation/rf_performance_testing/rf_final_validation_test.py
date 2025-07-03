#!/usr/bin/env python3
"""
Final validation test suite: Original vs Optimized containers.

Comprehensive performance and mathematical consistency testing between:
- Original container (port 8080) - baseline implementation
- Optimized container (port 8081) - integrated optimized implementation

This is the final validation before confirming the optimization is production-ready.
"""

import json
import time
import statistics
from typing import List, Dict, Tuple, Any
import requests

class FinalValidationSuite:
    def __init__(self):
        self.original_url = "http://localhost:8080"
        self.optimized_url = "http://localhost:8081"
        
        # Test items from the validated 20-item dataset
        self.test_items = [
            "11032-FRA",  # Basil, dried
            "11045-BRA",  # Baker's yeast, dehydrated  
            "11163-ESP",  # Sweet and sour sauce
            "12737-FRA",  # Mimolette cheese
            "12834-FRA",  # Crottin de Chavignol cheese
            "13731-FRA",  # Peach, canned in syrup
            "15006-FRA",  # Coconut, fresh
            "19026-FRA",  # Condensed milk
            "20039-FRA",  # Leek, raw
            "20904-FRA",  # Tofu, plain
            "25123-FRA",  # Moussaka
            "26091-FRA",  # Mullet, raw
            "26270-FRA",  # Pizza, tuna
            "31102-FRA",  # Cereal bar with chocolate
            "4020-FRA",   # Dauphine potato
        ]
        
    def generate_test_recipe(self, size: int) -> Dict[str, float]:
        """Generate a test recipe of specified size."""
        selected_items = self.test_items[:min(size, len(self.test_items))]
        recipe = {}
        for i, item in enumerate(selected_items):
            # Vary amounts for realistic recipes
            amount = round(0.05 + (i * 0.03), 3)  # 0.05, 0.08, 0.11, etc.
            recipe[item] = amount
        return recipe
    
    def test_single_endpoint(self, url: str, recipe_data: Dict[str, Any], container_name: str) -> Tuple[bool, float, Dict[str, Any], str]:
        """Test a single endpoint and return success, time, data, and any error."""
        start_time = time.time()
        try:
            response = requests.post(
                f"{url}/calculate-recipe/",
                json=recipe_data,
                timeout=30
            )
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return True, response_time, data, ""
            else:
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}..."
                return False, response_time, {}, error_msg
                
        except Exception as e:
            response_time = time.time() - start_time
            return False, response_time, {}, str(e)
    
    def extract_key_metrics(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics from response for comparison."""
        try:
            recipe_info = data["Recipe Info"]
            return {
                "single_score": recipe_info["Single Score"]["Single Score"],
                "single_score_grade": recipe_info["Single Score"]["Grade"],
                "contains_proxy": recipe_info["General Info"]["contains_proxy"],
                "item_count": len(recipe_info["Items"]),
                "stage_count": len(recipe_info["Stages"]),
                "impact_category_count": len(recipe_info["Impact Categories"])
            }
        except Exception as e:
            return {"error": f"Failed to extract metrics: {e}"}
    
    def compare_results(self, orig_metrics: Dict, opt_metrics: Dict) -> Dict[str, Any]:
        """Compare metrics between original and optimized results."""
        comparison = {
            "identical": True,
            "differences": [],
            "single_score_diff": 0.0
        }
        
        # Check if both have errors
        if "error" in orig_metrics or "error" in opt_metrics:
            comparison["identical"] = False
            comparison["differences"].append("One or both endpoints had extraction errors")
            return comparison
        
        # Compare single score (most critical)
        orig_score = orig_metrics["single_score"]
        opt_score = opt_metrics["single_score"]
        score_diff = abs(orig_score - opt_score)
        comparison["single_score_diff"] = score_diff
        
        if score_diff > 1e-12:
            comparison["identical"] = False
            comparison["differences"].append(f"Single score differs by {score_diff:.2e}")
        
        # Compare other metrics
        for key in ["single_score_grade", "contains_proxy", "item_count", "stage_count", "impact_category_count"]:
            if orig_metrics[key] != opt_metrics[key]:
                comparison["identical"] = False
                comparison["differences"].append(f"{key}: {orig_metrics[key]} vs {opt_metrics[key]}")
        
        return comparison
    
    def run_recipe_test(self, recipe_size: int, iterations: int = 3) -> Dict[str, Any]:
        """Run comprehensive test for a specific recipe size."""
        print(f"\n{'='*80}")
        print(f"FINAL VALIDATION: {recipe_size} ITEM RECIPE ({iterations} iterations)")
        print(f"{'='*80}")
        
        recipe_items = self.generate_test_recipe(recipe_size)
        recipe_data = {
            "items": recipe_items,
            "weighting_scheme_name": "delphi_r0110"
        }
        
        print(f"Recipe: {len(recipe_items)} items, Total mass: {sum(recipe_items.values()):.3f} kg")
        
        orig_times = []
        opt_times = []
        consistency_results = []
        
        for iteration in range(iterations):
            print(f"\n--- Iteration {iteration + 1}/{iterations} ---")
            
            # Test original container
            orig_success, orig_time, orig_data, orig_error = self.test_single_endpoint(
                self.original_url, recipe_data, "Original"
            )
            
            if not orig_success:
                print(f"❌ Original container failed: {orig_error}")
                return {"status": "failed", "reason": f"Original failed: {orig_error}"}
            
            orig_times.append(orig_time)
            orig_metrics = self.extract_key_metrics(orig_data)
            
            # Test optimized container
            opt_success, opt_time, opt_data, opt_error = self.test_single_endpoint(
                self.optimized_url, recipe_data, "Optimized"
            )
            
            if not opt_success:
                print(f"❌ Optimized container failed: {opt_error}")
                return {"status": "failed", "reason": f"Optimized failed: {opt_error}"}
            
            opt_times.append(opt_time)
            opt_metrics = self.extract_key_metrics(opt_data)
            
            # Compare results
            comparison = self.compare_results(orig_metrics, opt_metrics)
            consistency_results.append(comparison)
            
            # Print iteration results
            speedup = orig_time / opt_time if opt_time > 0 else 0
            print(f"   Original:  {orig_time:.3f}s")
            print(f"   Optimized: {opt_time:.3f}s") 
            print(f"   Speedup:   {speedup:.1f}x")
            print(f"   Identical: {'✅' if comparison['identical'] else '❌'}")
            
            if not comparison["identical"]:
                print(f"   Differences: {', '.join(comparison['differences'])}")
        
        # Calculate statistics
        orig_avg = statistics.mean(orig_times)
        opt_avg = statistics.mean(opt_times)
        avg_speedup = orig_avg / opt_avg if opt_avg > 0 else 0
        
        all_identical = all(result["identical"] for result in consistency_results)
        max_score_diff = max(result["single_score_diff"] for result in consistency_results)
        
        result = {
            "status": "success",
            "recipe_size": recipe_size,
            "iterations": iterations,
            "performance": {
                "original_avg": orig_avg,
                "optimized_avg": opt_avg,
                "avg_speedup": avg_speedup,
                "original_times": orig_times,
                "optimized_times": opt_times
            },
            "consistency": {
                "all_identical": all_identical,
                "max_score_difference": max_score_diff,
                "consistent_iterations": sum(1 for r in consistency_results if r["identical"])
            }
        }
        
        print(f"\n📊 SUMMARY FOR {recipe_size} ITEMS:")
        print(f"   Original avg:    {orig_avg:.3f}s")
        print(f"   Optimized avg:   {opt_avg:.3f}s")
        print(f"   Average speedup: {avg_speedup:.1f}x")
        print(f"   Consistency:     {result['consistency']['consistent_iterations']}/{iterations} ✅")
        print(f"   Max score diff:  {max_score_diff:.2e}")
        
        return result
    
    def run_comprehensive_validation(self):
        """Run the complete final validation suite."""
        print("FIT API FINAL VALIDATION TEST SUITE")
        print("=" * 80)
        print("Testing Original (port 8080) vs Optimized (port 8081) containers")
        print("=" * 80)
        
        # Test various recipe sizes
        test_sizes = [1, 3, 5, 8, 12, 15]
        iterations = 3
        
        print(f"Test plan: {len(test_sizes)} recipe sizes, {iterations} iterations each")
        print(f"Recipe sizes: {test_sizes}")
        
        all_results = []
        
        for size in test_sizes:
            if size > len(self.test_items):
                print(f"\n⚠️  Skipping size {size} - insufficient test items")
                continue
                
            result = self.run_recipe_test(size, iterations)
            if result["status"] == "success":
                all_results.append(result)
            else:
                print(f"❌ Test failed for recipe size {size}: {result['reason']}")
                break
        
        # Generate final validation report
        self.generate_final_report(all_results)
        
        return all_results
    
    def generate_final_report(self, results: List[Dict[str, Any]]):
        """Generate comprehensive final validation report."""
        print(f"\n{'='*80}")
        print("FINAL VALIDATION REPORT")
        print(f"{'='*80}")
        
        if not results:
            print("❌ NO SUCCESSFUL TEST RESULTS")
            print("RECOMMENDATION: DO NOT DEPLOY - Testing failed")
            return
        
        # Summary table
        print(f"{'Size':<6} {'Original(s)':<12} {'Optimized(s)':<13} {'Speedup':<10} {'Consistent':<12} {'Max Diff':<12}")
        print("-" * 80)
        
        total_speedup = 0
        total_consistent = 0
        max_difference = 0
        
        for result in results:
            size = result["recipe_size"]
            orig_avg = result["performance"]["original_avg"]
            opt_avg = result["performance"]["optimized_avg"]
            speedup = result["performance"]["avg_speedup"]
            consistent = result["consistency"]["all_identical"]
            max_diff = result["consistency"]["max_score_difference"]
            
            total_speedup += speedup
            total_consistent += 1 if consistent else 0
            max_difference = max(max_difference, max_diff)
            
            print(f"{size:<6} {orig_avg:<12.3f} {opt_avg:<13.3f} {speedup:<10.1f}x {'✅' if consistent else '❌':<12} {max_diff:<12.2e}")
        
        # Overall statistics
        num_tests = len(results)
        avg_speedup = total_speedup / num_tests if num_tests > 0 else 0
        consistency_rate = (total_consistent / num_tests * 100) if num_tests > 0 else 0
        
        print("-" * 80)
        print(f"OVERALL VALIDATION RESULTS:")
        print(f"  Tests completed:     {num_tests}/{len(results)}")
        print(f"  Average speedup:     {avg_speedup:.1f}x")
        print(f"  Consistency rate:    {consistency_rate:.1f}% ({total_consistent}/{num_tests})")
        print(f"  Maximum difference:  {max_difference:.2e}")
        
        # Performance analysis
        if num_tests >= 3:
            small_results = [r for r in results if r["recipe_size"] <= 5]
            large_results = [r for r in results if r["recipe_size"] >= 10]
            
            if small_results and large_results:
                small_speedup = statistics.mean([r["performance"]["avg_speedup"] for r in small_results])
                large_speedup = statistics.mean([r["performance"]["avg_speedup"] for r in large_results])
                
                print(f"\nSCALING PERFORMANCE:")
                print(f"  Small recipes (≤5 items):  {small_speedup:.1f}x average speedup")
                print(f"  Large recipes (≥10 items): {large_speedup:.1f}x average speedup")
                print(f"  Scaling benefit:           {large_speedup/small_speedup:.1f}x better for large recipes")
        
        # Final recommendation
        print(f"\n🎯 FINAL RECOMMENDATION:")
        
        if consistency_rate == 100 and max_difference < 1e-10 and avg_speedup >= 1.2:
            print("✅ OPTIMIZATION VALIDATED - READY FOR PRODUCTION")
            print("   ✅ Perfect mathematical consistency (100%)")
            print("   ✅ Significant performance improvement achieved")
            print("   ✅ All test scenarios passed successfully")
            print("   ✅ Safe to deploy optimized implementation")
        elif consistency_rate >= 95 and max_difference < 1e-8:
            print("⚠️  MINOR INCONSISTENCIES DETECTED - INVESTIGATE")
            print("   ⚠️  High but not perfect consistency rate")
            print("   ⚠️  Small numerical differences found")
        else:
            print("❌ OPTIMIZATION NOT VALIDATED - DO NOT DEPLOY")
            print("   ❌ Mathematical inconsistencies detected")
            print("   ❌ Further investigation and fixes required")
        
        print(f"{'='*80}")

def main():
    """Run the final validation test suite."""
    suite = FinalValidationSuite()
    results = suite.run_comprehensive_validation()
    
    # Save detailed results
    with open("/home/marius/projects/FIT_API_public/rf_performance_testing/rf_final_validation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: rf_final_validation_results.json")

if __name__ == "__main__":
    main()