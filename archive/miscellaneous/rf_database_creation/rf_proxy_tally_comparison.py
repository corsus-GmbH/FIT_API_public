import sqlite3
from collections import defaultdict

def analyze_proxy_patterns():
    # Connect to both databases
    old_db = sqlite3.connect('../rf_db_backups/FIT_eeb3795.db')
    new_db = sqlite3.connect('rf_FIT_full_database.db')
    
    print('=== PROXY PATTERN ANALYSIS BY ITEM_ID ===\n')
    
    old_cursor = old_db.cursor()
    new_cursor = new_db.cursor()
    
    # Get proxy tallies for old database
    old_cursor.execute("""
        SELECT item_id, proxy_flag, COUNT(*) as count
        FROM metadata 
        GROUP BY item_id, proxy_flag
        ORDER BY item_id, proxy_flag
    """)
    old_data = old_cursor.fetchall()
    
    # Get proxy tallies for new database
    new_cursor.execute("""
        SELECT item_id, proxy_flag, COUNT(*) as count
        FROM metadata 
        GROUP BY item_id, proxy_flag
        ORDER BY item_id, proxy_flag
    """)
    new_data = new_cursor.fetchall()
    
    # Organize data by item_id
    old_items = defaultdict(lambda: {'non_proxy': 0, 'proxy': 0})
    new_items = defaultdict(lambda: {'non_proxy': 0, 'proxy': 0})
    
    # Process old database data
    for item_id, proxy_flag, count in old_data:
        if proxy_flag == 0:
            old_items[item_id]['non_proxy'] = count
        else:
            old_items[item_id]['proxy'] = count
    
    # Process new database data  
    for item_id, proxy_flag, count in new_data:
        if proxy_flag == '0':  # String in new database
            new_items[item_id]['non_proxy'] = count
        else:
            new_items[item_id]['proxy'] = count
    
    # Get all unique item_ids
    all_items = sorted(set(old_items.keys()) | set(new_items.keys()))
    
    print('1. SUMMARY STATISTICS')
    print('=' * 50)
    
    # Count patterns in old database
    old_non_proxy_only = sum(1 for item_id in old_items if old_items[item_id]['non_proxy'] > 0 and old_items[item_id]['proxy'] == 0)
    old_proxy_only = sum(1 for item_id in old_items if old_items[item_id]['non_proxy'] == 0 and old_items[item_id]['proxy'] > 0)
    old_both = sum(1 for item_id in old_items if old_items[item_id]['non_proxy'] > 0 and old_items[item_id]['proxy'] > 0)
    
    # Count patterns in new database
    new_non_proxy_only = sum(1 for item_id in new_items if new_items[item_id]['non_proxy'] > 0 and new_items[item_id]['proxy'] == 0)
    new_proxy_only = sum(1 for item_id in new_items if new_items[item_id]['non_proxy'] == 0 and new_items[item_id]['proxy'] > 0)
    new_both = sum(1 for item_id in new_items if new_items[item_id]['non_proxy'] > 0 and new_items[item_id]['proxy'] > 0)
    
    print(f"{'Pattern':<20} {'Old DB':<8} {'New DB':<8} {'Change':<8}")
    print('-' * 50)
    print(f"{'Non-proxy only':<20} {old_non_proxy_only:<8} {new_non_proxy_only:<8} {new_non_proxy_only-old_non_proxy_only:+d}")
    print(f"{'Proxy only':<20} {old_proxy_only:<8} {new_proxy_only:<8} {new_proxy_only-old_proxy_only:+d}")
    print(f"{'Both versions':<20} {old_both:<8} {new_both:<8} {new_both-old_both:+d}")
    print(f"{'Total items':<20} {len(old_items):<8} {len(new_items):<8} {len(new_items)-len(old_items):+d}")
    
    print('\n2. PATTERN CHANGES - ITEMS THAT CHANGED PROXY STATUS')
    print('=' * 80)
    
    # Find items that changed from non-proxy to proxy-only
    non_proxy_to_proxy = []
    for item_id in all_items:
        old_pattern = old_items[item_id]
        new_pattern = new_items[item_id]
        
        # Was non-proxy only in old, now proxy only in new
        if (old_pattern['non_proxy'] > 0 and old_pattern['proxy'] == 0 and
            new_pattern['non_proxy'] == 0 and new_pattern['proxy'] > 0):
            non_proxy_to_proxy.append(item_id)
    
    # Find items that changed from proxy to non-proxy
    proxy_to_non_proxy = []
    for item_id in all_items:
        old_pattern = old_items[item_id]
        new_pattern = new_items[item_id]
        
        # Was proxy only in old, now non-proxy only in new
        if (old_pattern['non_proxy'] == 0 and old_pattern['proxy'] > 0 and
            new_pattern['non_proxy'] > 0 and new_pattern['proxy'] == 0):
            proxy_to_non_proxy.append(item_id)
    
    # Find items that gained proxy versions (but kept non-proxy)
    gained_proxy = []
    for item_id in all_items:
        old_pattern = old_items[item_id]
        new_pattern = new_items[item_id]
        
        # Had non-proxy only in old, now has both in new
        if (old_pattern['non_proxy'] > 0 and old_pattern['proxy'] == 0 and
            new_pattern['non_proxy'] > 0 and new_pattern['proxy'] > 0):
            gained_proxy.append(item_id)
    
    print(f"Items changed from non-proxy to proxy-only: {len(non_proxy_to_proxy)}")
    if non_proxy_to_proxy and len(non_proxy_to_proxy) <= 20:
        print("Examples:", ', '.join(non_proxy_to_proxy))
    
    print(f"\nItems changed from proxy to non-proxy: {len(proxy_to_non_proxy)}")
    if proxy_to_non_proxy and len(proxy_to_non_proxy) <= 20:
        print("Examples:", ', '.join(proxy_to_non_proxy))
    
    print(f"\nItems that gained proxy versions (kept non-proxy): {len(gained_proxy)}")
    if gained_proxy and len(gained_proxy) <= 20:
        print("Examples:", ', '.join(gained_proxy))
    
    print('\n3. DETAILED TALLY FOR SAMPLE ITEMS')
    print('=' * 100)
    print(f"{'Item ID':<10} {'Old Non-Proxy':<12} {'Old Proxy':<10} {'New Non-Proxy':<12} {'New Proxy':<10} {'Pattern Change'}")
    print('-' * 100)
    
    # Show sample of items with interesting patterns
    sample_items = []
    
    # Include some items that changed patterns
    sample_items.extend(non_proxy_to_proxy[:5])
    sample_items.extend(proxy_to_non_proxy[:5])
    sample_items.extend(gained_proxy[:5])
    
    # Add some random items for comparison
    remaining_items = [item for item in all_items[:20] if item not in sample_items]
    sample_items.extend(remaining_items[:10])
    
    for item_id in sorted(set(sample_items))[:25]:  # Show max 25 items
        old = old_items[item_id]
        new = new_items[item_id]
        
        # Determine pattern change
        old_desc = []
        if old['non_proxy'] > 0: old_desc.append(f"NP:{old['non_proxy']}")
        if old['proxy'] > 0: old_desc.append(f"P:{old['proxy']}")
        old_pattern = ','.join(old_desc) if old_desc else "None"
        
        new_desc = []
        if new['non_proxy'] > 0: new_desc.append(f"NP:{new['non_proxy']}")
        if new['proxy'] > 0: new_desc.append(f"P:{new['proxy']}")
        new_pattern = ','.join(new_desc) if new_desc else "None"
        
        change = f"{old_pattern} → {new_pattern}"
        
        print(f"{item_id:<10} {old['non_proxy']:<12} {old['proxy']:<10} {new['non_proxy']:<12} {new['proxy']:<10} {change}")
    
    # Show items only in one database
    only_in_old = set(old_items.keys()) - set(new_items.keys())
    only_in_new = set(new_items.keys()) - set(old_items.keys())
    
    print(f'\n4. ITEMS UNIQUE TO EACH DATABASE')
    print('=' * 50)
    print(f"Items only in old database: {len(only_in_old)}")
    if only_in_old and len(only_in_old) <= 15:
        print(f"Examples: {', '.join(sorted(only_in_old))}")
    
    print(f"\nItems only in new database: {len(only_in_new)}")
    if only_in_new and len(only_in_new) <= 15:
        print(f"Examples: {', '.join(sorted(only_in_new))}")
    
    old_db.close()
    new_db.close()

if __name__ == "__main__":
    analyze_proxy_patterns()