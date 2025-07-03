#!/usr/bin/env python3
"""
Performance testing script for the GET /items/ endpoint
Tests the FIT API running in Docker container at localhost:8080
"""

import time
import json
import urllib.request
import urllib.error
from datetime import datetime
import sys

def test_items_endpoint(url="http://localhost:8080/items/"):
    """Test the GET /items/ endpoint and measure performance"""
    
    print(f"Testing endpoint: {url}")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 50)
    
    try:
        # Record start time
        start_time = time.time()
        
        # Make the request
        with urllib.request.urlopen(url) as response:
            response_data = response.read().decode('utf-8')
            
        # Record end time
        end_time = time.time()
        
        # Calculate duration
        duration = end_time - start_time
        
        # Parse response
        data = json.loads(response_data)
        item_count = len(data)
        
        # Display results
        print(f"✅ SUCCESS")
        print(f"Response time: {duration:.3f} seconds")
        print(f"Number of items: {item_count}")
        print(f"Response size: {len(response_data)} bytes")
        print(f"Items per second: {item_count/duration:.1f}")
        
        # Sample first few items
        print("\nFirst 3 items:")
        for i, (key, value) in enumerate(list(data.items())[:3]):
            print(f"  {i+1}. {key}: {value['product_name']} ({value['country']})")
        
        return {
            'success': True,
            'duration': duration,
            'item_count': item_count,
            'response_size': len(response_data),
            'items_per_second': item_count/duration
        }
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP ERROR")
        print(f"Status code: {e.code}")
        print(f"Response: {e.read().decode('utf-8')}")
        return {
            'success': False,
            'status_code': e.code,
            'error': e.read().decode('utf-8')
        }
        
    except urllib.error.URLError as e:
        print(f"❌ CONNECTION ERROR")
        print("Could not connect to http://localhost:8080")
        print("Make sure the Docker container is running with:")
        print("  docker run -d --name fit-api-container -p 8080:80 fit-api:latest")
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

def run_multiple_tests(num_tests=3, url="http://localhost:8080/items/"):
    """Run multiple tests and calculate average performance"""
    
    print(f"Running {num_tests} performance tests...")
    print("=" * 60)
    
    results = []
    
    for i in range(num_tests):
        print(f"\nTest {i+1}/{num_tests}:")
        result = test_items_endpoint(url)
        results.append(result)
        
        if not result['success']:
            print(f"Test {i+1} failed, stopping...")
            break
            
        # Wait between tests
        if i < num_tests - 1:
            time.sleep(1)
    
    # Calculate averages for successful tests
    successful_results = [r for r in results if r['success']]
    
    if successful_results:
        avg_duration = sum(r['duration'] for r in successful_results) / len(successful_results)
        avg_item_count = sum(r['item_count'] for r in successful_results) / len(successful_results)
        avg_items_per_second = sum(r['items_per_second'] for r in successful_results) / len(successful_results)
        
        print("\n" + "=" * 60)
        print("SUMMARY STATISTICS:")
        print(f"Successful tests: {len(successful_results)}/{num_tests}")
        print(f"Average response time: {avg_duration:.3f} seconds")
        print(f"Average items returned: {avg_item_count:.0f}")
        print(f"Average items per second: {avg_items_per_second:.1f}")
        
        # Performance assessment
        if avg_duration > 5:
            print("⚠️  PERFORMANCE WARNING: Response time > 5 seconds")
        elif avg_duration > 2:
            print("⚠️  PERFORMANCE NOTICE: Response time > 2 seconds")
        else:
            print("✅ PERFORMANCE OK: Response time < 2 seconds")
    
    return results

if __name__ == "__main__":
    # Default values
    url = "http://localhost:8080/items/"
    num_tests = 1
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        # First argument is URL
        url = sys.argv[1]
        
        # Second argument (optional) is number of tests
        if len(sys.argv) > 2:
            try:
                num_tests = int(sys.argv[2])
            except ValueError:
                print("Usage: python test_items_endpoint.py [url] [number_of_tests]")
                print("Example: python test_items_endpoint.py http://localhost:8081/items/ 3")
                sys.exit(1)
    
    # Add /items/ if not present in URL (but don't add if URL already has query parameters)
    if '/items' not in url:
        if '?' in url:
            # URL has query params but no /items/ - insert /items/ before the ?
            base_url, query = url.split('?', 1)
            if base_url.endswith('/'):
                url = f"{base_url}items/?{query}"
            else:
                url = f"{base_url}/items/?{query}"
        else:
            # No query params, add /items/
            if url.endswith('/'):
                url += 'items/'
            else:
                url += '/items/'
    
    print(f"Testing URL: {url}")
    if num_tests > 1:
        print(f"Number of tests: {num_tests}")
    
    if num_tests == 1:
        test_items_endpoint(url)
    else:
        run_multiple_tests(num_tests, url)