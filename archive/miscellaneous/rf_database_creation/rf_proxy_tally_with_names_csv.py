import sqlite3
import pandas as pd
from collections import defaultdict

def create_proxy_tally_csv():
    # Connect to both databases
    old_db = sqlite3.connect('../rf_db_backups/FIT_eeb3795.db')
    new_db = sqlite3.connect('rf_FIT_full_database.db')
    
    print('=== CREATING PROXY TALLY CSV WITH ITEM NAMES ===\n')
    
    old_cursor = old_db.cursor()
    new_cursor = new_db.cursor()
    
    # Get proxy tallies with names for old database
    old_cursor.execute("""
        SELECT item_id, name_lci, proxy_flag, COUNT(*) as count
        FROM metadata 
        GROUP BY item_id, name_lci, proxy_flag
        ORDER BY item_id, proxy_flag
    """)
    old_data = old_cursor.fetchall()
    
    # Get proxy tallies with names for new database
    new_cursor.execute("""
        SELECT item_id, name_lci, proxy_flag, COUNT(*) as count
        FROM metadata 
        GROUP BY item_id, name_lci, proxy_flag
        ORDER BY item_id, proxy_flag
    """)
    new_data = new_cursor.fetchall()
    
    # Organize data by item_id
    old_items = {}
    new_items = {}
    
    # Process old database data
    for item_id, name_lci, proxy_flag, count in old_data:
        if item_id not in old_items:
            old_items[item_id] = {'name_lci': name_lci, 'non_proxy': 0, 'proxy': 0}
        
        if proxy_flag == 0:
            old_items[item_id]['non_proxy'] = count
        else:
            old_items[item_id]['proxy'] = count
    
    # Process new database data  
    for item_id, name_lci, proxy_flag, count in new_data:
        if item_id not in new_items:
            new_items[item_id] = {'name_lci': name_lci, 'non_proxy': 0, 'proxy': 0}
        
        if proxy_flag == '0':  # String in new database
            new_items[item_id]['non_proxy'] = count
        else:
            new_items[item_id]['proxy'] = count
    
    # Get all unique item_ids
    all_items = sorted(set(old_items.keys()) | set(new_items.keys()))
    
    # Prepare data for CSV
    csv_data = []
    
    for item_id in all_items:
        old_data = old_items.get(item_id, {'name_lci': '', 'non_proxy': 0, 'proxy': 0})
        new_data = new_items.get(item_id, {'name_lci': '', 'non_proxy': 0, 'proxy': 0})
        
        # Use name from new database if available, otherwise from old
        name_lci = new_data['name_lci'] if new_data['name_lci'] else old_data['name_lci']
        
        # Determine pattern change
        old_pattern_desc = []
        if old_data['non_proxy'] > 0: old_pattern_desc.append(f"NP:{old_data['non_proxy']}")
        if old_data['proxy'] > 0: old_pattern_desc.append(f"P:{old_data['proxy']}")
        old_pattern = ','.join(old_pattern_desc) if old_pattern_desc else "None"
        
        new_pattern_desc = []
        if new_data['non_proxy'] > 0: new_pattern_desc.append(f"NP:{new_data['non_proxy']}")
        if new_data['proxy'] > 0: new_pattern_desc.append(f"P:{new_data['proxy']}")
        new_pattern = ','.join(new_pattern_desc) if new_pattern_desc else "None"
        
        # Determine change type
        change_type = "No Change"
        if item_id in old_items and item_id not in new_items:
            change_type = "Removed from New"
        elif item_id not in old_items and item_id in new_items:
            change_type = "Added to New"
        elif (old_data['non_proxy'] > 0 and old_data['proxy'] == 0 and
              new_data['non_proxy'] > 0 and new_data['proxy'] > 0):
            change_type = "Gained Proxy Versions"
        elif (old_data['non_proxy'] > 0 and old_data['proxy'] == 0 and
              new_data['non_proxy'] == 0 and new_data['proxy'] > 0):
            change_type = "Non-proxy to Proxy Only"
        elif (old_data['non_proxy'] == 0 and old_data['proxy'] > 0 and
              new_data['non_proxy'] > 0 and new_data['proxy'] == 0):
            change_type = "Proxy to Non-proxy"
        
        csv_data.append({
            'item_id': item_id,
            'name_lci': name_lci,
            'old_non_proxy_count': old_data['non_proxy'],
            'old_proxy_count': old_data['proxy'],
            'new_non_proxy_count': new_data['non_proxy'],
            'new_proxy_count': new_data['proxy'],
            'old_pattern': old_pattern,
            'new_pattern': new_pattern,
            'change_type': change_type,
            'old_total_records': old_data['non_proxy'] + old_data['proxy'],
            'new_total_records': new_data['non_proxy'] + new_data['proxy'],
            'record_count_change': (new_data['non_proxy'] + new_data['proxy']) - (old_data['non_proxy'] + old_data['proxy'])
        })
    
    # Create DataFrame and save to CSV
    df = pd.DataFrame(csv_data)
    
    # Sort by item_id
    df = df.sort_values('item_id')
    
    # Export to CSV
    csv_filename = 'rf_proxy_tally_comparison.csv'
    df.to_csv(csv_filename, index=False)
    
    print(f"CSV exported to: {csv_filename}")
    print(f"Total items in CSV: {len(df):,}")
    
    # Show summary statistics
    print('\nSummary Statistics:')
    print(f"Items in old database only: {len(df[df['change_type'] == 'Removed from New']):,}")
    print(f"Items in new database only: {len(df[df['change_type'] == 'Added to New']):,}")
    print(f"Items that gained proxy versions: {len(df[df['change_type'] == 'Gained Proxy Versions']):,}")
    print(f"Items with no change: {len(df[df['change_type'] == 'No Change']):,}")
    
    # Show first few rows as preview
    print('\nFirst 10 rows preview:')
    print(df[['item_id', 'name_lci', 'old_pattern', 'new_pattern', 'change_type']].head(10).to_string(index=False))
    
    old_db.close()
    new_db.close()
    
    return csv_filename

if __name__ == "__main__":
    csv_file = create_proxy_tally_csv()
    print(f"\nCSV file created: {csv_file}")