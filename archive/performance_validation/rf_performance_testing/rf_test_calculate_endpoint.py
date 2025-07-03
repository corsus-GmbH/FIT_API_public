#!/usr/bin/env python3
"""
Performance testing script for the POST /calculate-recipe/ endpoint
Tests both single item and multi-item recipe calculations
"""

import time
import json
import urllib.request
import urllib.error
from datetime import datetime
import sys

def test_calculate_endpoint(url, payload, test_name):
    """Test the POST /calculate-recipe/ endpoint and measure performance"""
    
    print(f"Testing: {test_name}")
    print(f"Endpoint: {url}")
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
        total_items = len(result.get('items', {}))
        has_recipe_totals = 'recipe' in result
        
        # Display results
        print(f"✅ SUCCESS")
        print(f"Response time: {duration:.3f} seconds")
        print(f"Items processed: {total_items}")
        print(f"Response size: {len(response_data)} bytes")
        print(f"Recipe totals included: {has_recipe_totals}")
        
        # Show sample data
        if 'items' in result and result['items']:
            first_item_key = list(result['items'].keys())[0]
            first_item = result['items'][first_item_key]
            print(f"Sample item: {first_item_key}")
            if 'single_score' in first_item:
                print(f"  Single score: {first_item['single_score']:.4f}")
        
        if has_recipe_totals and 'single_score' in result['recipe']:
            print(f"Recipe total single score: {result['recipe']['single_score']:.4f}")
        
        return {
            'success': True,
            'duration': duration,
            'items_processed': total_items,
            'response_size': len(response_data),
            'has_recipe_totals': has_recipe_totals
        }
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP ERROR")
        print(f"Status code: {e.code}")
        error_response = e.read().decode('utf-8')
        print(f"Response: {error_response}")
        return {
            'success': False,
            'status_code': e.code,
            'error': error_response
        }
        
    except urllib.error.URLError as e:
        print(f"❌ CONNECTION ERROR")
        print(f"Could not connect to {url}")
        print("Make sure the Docker container is running")
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

def compare_ports(payload, test_name):
    """Compare performance between port 8080 and 8081"""
    
    print(f"=" * 60)
    print(f"PERFORMANCE COMPARISON: {test_name}")
    print(f"=" * 60)
    
    # Test original (port 8080)
    print("\n[ORIGINAL] Port 8080:")
    result_8080 = test_calculate_endpoint("http://localhost:8080/calculate-recipe/", payload, test_name)
    
    print("\n" + "=" * 40)
    
    # Test refactored (port 8081)  
    print("\n[REFACTORED] Port 8081:")
    result_8081 = test_calculate_endpoint("http://localhost:8081/calculate-recipe/", payload, test_name)
    
    # Summary comparison
    if result_8080['success'] and result_8081['success']:
        print("\n" + "=" * 60)
        print("COMPARISON SUMMARY:")
        print(f"Original (8080):   {result_8080['duration']:.3f} seconds")
        print(f"Refactored (8081): {result_8081['duration']:.3f} seconds")
        
        if result_8081['duration'] > 0:
            improvement = result_8080['duration'] / result_8081['duration']
            if improvement > 1:
                print(f"Improvement: {improvement:.1f}x faster")
            elif improvement < 1:
                print(f"Regression: {1/improvement:.1f}x slower")
            else:
                print("Performance: Similar")
        
        print("=" * 60)
    
    return result_8080, result_8081

if __name__ == "__main__":
    
    # Test Case 1: Single item
    single_item_payload = {
        "items": {
            "25541-FRA": 0.1  # 100g of Lamb on skewer (France)
        }
    }
    
    # Test Case 2: Multi-item recipe (using valid item IDs)
    recipe_payload = {
        "items": {
            "25541-FRA": 0.15,   # 150g Lamb on skewer
            "25505-FRA": 0.1,    # 100g Beef on skewer  
            "42200-FRA": 0.02,   # 20g Soy lecithin
            "9643-IND": 0.05,    # 50g Rice bran
            "11010-BRA": 0.01    # 10g Baker's yeast
        }
    }
    
    print("FIT API /calculate-recipe/ Performance Testing")
    print("=" * 60)
    
    # Test single item
    compare_ports(single_item_payload, "Single Item (100g Lamb)")
    
    time.sleep(2)  # Brief pause between tests
    
    # Test recipe
    compare_ports(recipe_payload, "Multi-Item Recipe")