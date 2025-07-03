#!/usr/bin/env python3
"""
Enhanced performance testing script for the POST /calculate-recipe/ endpoint
Tests with different recipe sizes to better demonstrate N+1 query impact
"""

import time
import json
import urllib.request
import urllib.error
from datetime import datetime
import sys

# Larger set of valid item IDs for testing
VALID_ITEMS = [
    "25541-FRA",  # Lamb on skewer
    "25505-FRA",  # Beef on skewer
    "42200-FRA",  # Soy lecithin
    "9643-IND",   # Rice bran
    "11010-BRA",  # Baker's yeast, compressed
    "9200-PER",   # Corn or maize grain, raw
    "9360-FRA",   # Sorghum, whole, raw
    "9010-FRA",   # Wheat, whole, raw
    "9612-FRA",   # Mix of cereals and legumes, raw
    "18902-FRA",  # Soy drink, flavoured, with sugar
    "18903-FRA",  # Soy drink, flavoured, enriched in calcium
    "18901-FRA",  # Soy drink, plain, fortified with calcium
    "18900-FRA",  # Soy drink, plain, prepacked
    "18020-LKA",  # Tea, brewed, without sugar
    "18154-LKA",  # Black tea, brewed, without sugar
    "18156-LKA",  # Oolong tea, brewed, without sugar
    "18155-LKA",  # Green tea, brewed, without sugar
    "18022-LKA",  # Infusion, brewed, without sugar
    "20282-FRA",  # Asparagus, white or purple, peeled, raw
    "20279-FRA",  # Asparagus, green, raw
]

def test_calculate_endpoint(url, payload, test_name):
    """Test the POST /calculate-recipe/ endpoint and measure performance"""
    
    print(f"Testing: {test_name}")
    print(f"Endpoint: {url}")
    print(f"Items: {len(payload['items'])}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Prepare request
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        
        # Record start time
        start_time = time.time()
        
        # Make the request
        with urllib.request.urlopen(req) as response:
            response_data = response.read().decode('utf-8')
            
        # Record end time
        end_time = time.time()
        
        # Calculate duration
        duration = end_time - start_time
        
        # Parse response
        result = json.loads(response_data)
        
        # Extract key metrics
        has_recipe_totals = 'Recipe Info' in result
        recipe_items = len(payload['items'])
        
        # Display results
        print(f"✅ SUCCESS")
        print(f"Response time: {duration:.3f} seconds")
        print(f"Recipe items: {recipe_items}")
        print(f"Response size: {len(response_data):,} bytes")
        print(f"Items per second: {recipe_items/duration:.1f}")
        print(f"Recipe totals included: {has_recipe_totals}")
        
        # Show sample data if available
        if has_recipe_totals and 'Single Score' in result['Recipe Info']:
            single_score = result['Recipe Info']['Single Score'].get('Single Score', 'N/A')
            print(f"Recipe single score: {single_score}")
        
        return {
            'success': True,
            'duration': duration,
            'recipe_items': recipe_items,
            'response_size': len(response_data),
            'items_per_second': recipe_items/duration,
            'has_recipe_totals': has_recipe_totals
        }
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP ERROR")
        print(f"Status code: {e.code}")
        error_response = e.read().decode('utf-8')
        print(f"Response: {error_response[:500]}...")  # Truncate long errors
        return {
            'success': False,
            'status_code': e.code,
            'error': 'HTTP Error'
        }
        
    except urllib.error.URLError as e:
        print(f"❌ CONNECTION ERROR")
        print(f"Could not connect to {url}")
        return {
            'success': False,
            'error': 'Connection failed'
        }
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_recipe(num_items):
    """Generate recipe payload with specified number of items"""
    if num_items > len(VALID_ITEMS):
        raise ValueError(f"Cannot create recipe with {num_items} items. Only {len(VALID_ITEMS)} valid items available.")
    
    recipe = {}
    for i in range(num_items):
        # Vary amounts to make it realistic (20g to 500g)
        amount = 0.02 + (i * 0.024)  # 20g, 44g, 68g, etc.
        recipe[VALID_ITEMS[i]] = round(amount, 3)
    
    return {"items": recipe}

def compare_recipe_sizes():
    """Compare performance across different recipe sizes"""
    
    recipe_sizes = [1, 3, 5, 10, 15, 20]
    
    print("=" * 80)
    print("RECIPE SIZE PERFORMANCE ANALYSIS")
    print("=" * 80)
    
    results = {
        'original': {},
        'optimized': {}
    }
    
    for size in recipe_sizes:
        print(f"\n{'='*60}")
        print(f"TESTING RECIPE SIZE: {size} ITEMS")
        print(f"{'='*60}")
        
        # Generate recipe
        recipe_payload = generate_recipe(size)
        
        # Test original (port 8080)
        print(f"\n[ORIGINAL] Port 8080 - {size} items:")
        result_original = test_calculate_endpoint(
            "http://localhost:8080/calculate-recipe/", 
            recipe_payload, 
            f"{size}-Item Recipe (Original)"
        )
        results['original'][size] = result_original
        
        print("\n" + "-" * 40)
        
        # Test optimized (port 8081)
        print(f"\n[OPTIMIZED] Port 8081 - {size} items:")
        result_optimized = test_calculate_endpoint(
            "http://localhost:8081/calculate-recipe/", 
            recipe_payload, 
            f"{size}-Item Recipe (Optimized)"
        )
        results['optimized'][size] = result_optimized
        
        # Comparison for this size
        if result_original['success'] and result_optimized['success']:
            improvement = result_original['duration'] / result_optimized['duration']
            print(f"\n📊 COMPARISON FOR {size} ITEMS:")
            print(f"Original:  {result_original['duration']:.3f}s")
            print(f"Optimized: {result_optimized['duration']:.3f}s")
            if improvement > 1:
                print(f"Improvement: {improvement:.1f}x faster")
            else:
                print(f"Regression: {1/improvement:.1f}x slower")
        
        # Add delay between recipe sizes
        time.sleep(1)
    
    # Final summary
    print("\n" + "=" * 80)
    print("FINAL PERFORMANCE SUMMARY")
    print("=" * 80)
    print(f"{'Size':<6} {'Original':<12} {'Optimized':<12} {'Improvement':<12} {'Status'}")
    print("-" * 60)
    
    for size in recipe_sizes:
        orig = results['original'][size]
        opt = results['optimized'][size]
        
        if orig['success'] and opt['success']:
            improvement = orig['duration'] / opt['duration']
            status = f"{improvement:.1f}x" if improvement > 1 else f"{1/improvement:.1f}x slower"
            print(f"{size:<6} {orig['duration']:<12.3f} {opt['duration']:<12.3f} {improvement:<12.1f} {status}")
        else:
            print(f"{size:<6} {'ERROR':<12} {'ERROR':<12} {'N/A':<12} {'FAILED'}")
    
    return results

if __name__ == "__main__":
    print("FIT API /calculate-recipe/ Performance Testing - Multiple Recipe Sizes")
    print("Testing recipe sizes from 1 to 20 items to demonstrate N+1 query impact")
    
    try:
        results = compare_recipe_sizes()
        
        # Calculate average improvement
        successful_comparisons = []
        for size in [1, 3, 5, 10, 15, 20]:
            orig = results['original'][size]
            opt = results['optimized'][size]
            if orig['success'] and opt['success']:
                improvement = orig['duration'] / opt['duration']
                successful_comparisons.append(improvement)
        
        if successful_comparisons:
            avg_improvement = sum(successful_comparisons) / len(successful_comparisons)
            print(f"\n🎯 AVERAGE IMPROVEMENT: {avg_improvement:.1f}x faster")
            print(f"📈 SCALING ANALYSIS: {len(successful_comparisons)}/{len([1, 3, 5, 10, 15, 20])} recipe sizes tested successfully")
        
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
    except Exception as e:
        print(f"\nUnexpected error: {e}")