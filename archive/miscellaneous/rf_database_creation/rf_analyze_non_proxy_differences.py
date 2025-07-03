import sqlite3

def analyze_non_proxy_differences():
    # Connect to both databases
    old_db = sqlite3.connect('../rf_db_backups/FIT_eeb3795.db')
    new_db = sqlite3.connect('rf_FIT_full_database.db')
    
    print('=== NON-PROXY ITEMS ANALYSIS ===\n')
    
    old_cursor = old_db.cursor()
    new_cursor = new_db.cursor()
    
    # Get group and subgroup names for reference
    new_cursor.execute("SELECT group_id, group_name FROM groups ORDER BY group_id")
    groups = dict(new_cursor.fetchall())
    
    new_cursor.execute("SELECT subgroup_id, subgroup_name FROM subgroups ORDER BY subgroup_id")
    subgroups = dict(new_cursor.fetchall())
    
    # Get all unique non-proxy items from old database
    old_cursor.execute("""
        SELECT DISTINCT item_id, code_ciqual, name_lci, group_id, subgroup_id
        FROM metadata 
        WHERE proxy_flag = 0
        ORDER BY item_id
    """)
    old_items = {row[0]: row for row in old_cursor.fetchall()}
    
    # Get all unique non-proxy items from new database  
    # Note: new database has proxy_flag as VARCHAR, so check for '0'
    new_cursor.execute("""
        SELECT DISTINCT item_id, code_ciqual, name_lci, group_id, subgroup_id
        FROM metadata 
        WHERE proxy_flag = '0'
        ORDER BY item_id
    """)
    new_items = {row[0]: row for row in new_cursor.fetchall()}
    
    print(f"Old database non-proxy items: {len(old_items):,}")
    print(f"New database non-proxy items: {len(new_items):,}")
    print(f"Net difference: {len(new_items) - len(old_items):+,}\n")
    
    # Find items only in old database (missing from new)
    missing_in_new = set(old_items.keys()) - set(new_items.keys())
    
    # Find items only in new database (additional in new)
    additional_in_new = set(new_items.keys()) - set(old_items.keys())
    
    print('1. ITEMS MISSING IN NEW DATABASE (Non-proxy only)')
    print('=' * 80)
    print(f"Total missing: {len(missing_in_new)}")
    
    if missing_in_new:
        # Group missing items by subgroup
        missing_by_subgroup = {}
        for item_id in missing_in_new:
            item_data = old_items[item_id]
            _, _, name_lci, group_id, subgroup_id = item_data
            key = (group_id, subgroup_id)
            if key not in missing_by_subgroup:
                missing_by_subgroup[key] = []
            missing_by_subgroup[key].append((item_id, name_lci))
        
        print(f"\n{'Group':<20} {'Subgroup':<25} {'Count':<5} {'Sample Items'}")
        print('-' * 100)
        
        for (group_id, subgroup_id), items in sorted(missing_by_subgroup.items()):
            group_name = groups.get(group_id, 'Unknown')[:19]
            subgroup_name = subgroups.get(subgroup_id, 'Unknown')[:24]
            
            # Show first 3 items as sample
            sample_items = items[:3]
            sample_text = ', '.join([f"{item_id}({name[:20]})" for item_id, name in sample_items])
            if len(items) > 3:
                sample_text += f" ... (+{len(items)-3} more)"
            
            print(f"{group_name:<20} {subgroup_name:<25} {len(items):<5} {sample_text}")
    
    print('\n\n2. ADDITIONAL ITEMS IN NEW DATABASE (Non-proxy only)')
    print('=' * 80)
    print(f"Total additional: {len(additional_in_new)}")
    
    if additional_in_new:
        # Group additional items by subgroup
        additional_by_subgroup = {}
        for item_id in additional_in_new:
            item_data = new_items[item_id]
            _, _, name_lci, group_id, subgroup_id = item_data
            key = (group_id, subgroup_id)
            if key not in additional_by_subgroup:
                additional_by_subgroup[key] = []
            additional_by_subgroup[key].append((item_id, name_lci))
        
        print(f"\n{'Group':<20} {'Subgroup':<25} {'Count':<5} {'Sample Items'}")
        print('-' * 100)
        
        for (group_id, subgroup_id), items in sorted(additional_by_subgroup.items()):
            group_name = groups.get(group_id, 'Unknown')[:19]
            subgroup_name = subgroups.get(subgroup_id, 'Unknown')[:24]
            
            # Show first 3 items as sample
            sample_items = items[:3]
            sample_text = ', '.join([f"{item_id}({name[:20]})" for item_id, name in sample_items])
            if len(items) > 3:
                sample_text += f" ... (+{len(items)-3} more)"
            
            print(f"{group_name:<20} {subgroup_name:<25} {len(items):<5} {sample_text}")
    
    # Detailed analysis of specific missing categories
    if missing_in_new:
        print('\n\n3. DETAILED ANALYSIS OF MISSING ITEMS')
        print('=' * 60)
        
        # Focus on waters (subgroup 16) since that had -84 difference
        waters_missing = [item_id for item_id in missing_in_new 
                         if old_items[item_id][4] == 16]  # subgroup_id = 16
        
        if waters_missing:
            print(f"\nWaters (subgroup 16) - {len(waters_missing)} missing items:")
            for item_id in sorted(waters_missing)[:10]:  # Show first 10
                _, _, name_lci, _, _ = old_items[item_id]
                print(f"  {item_id}: {name_lci}")
            if len(waters_missing) > 10:
                print(f"  ... and {len(waters_missing)-10} more waters")
    
    # Check proxy flag distribution
    print('\n\n4. PROXY FLAG DISTRIBUTION')
    print('=' * 40)
    
    # Old database proxy distribution
    old_cursor.execute("SELECT proxy_flag, COUNT(*) FROM metadata GROUP BY proxy_flag")
    old_proxy_dist = dict(old_cursor.fetchall())
    
    # New database proxy distribution  
    new_cursor.execute("SELECT proxy_flag, COUNT(*) FROM metadata GROUP BY proxy_flag")
    new_proxy_dist = dict(new_cursor.fetchall())
    
    print("Old database:")
    for flag, count in sorted(old_proxy_dist.items()):
        flag_text = "Non-proxy" if flag == 0 else "Proxy"
        print(f"  {flag_text}: {count:,}")
    
    print("\nNew database:")
    for flag, count in sorted(new_proxy_dist.items()):
        flag_text = "Non-proxy" if flag == '0' else "Proxy"  
        print(f"  {flag_text}: {count:,}")
    
    old_db.close()
    new_db.close()

if __name__ == "__main__":
    analyze_non_proxy_differences()