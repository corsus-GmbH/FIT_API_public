import sqlite3
import json
from collections import OrderedDict

# Connect to the backed up database
conn = sqlite3.connect('rf_db_backups/FIT_eeb3795.db')
cursor = conn.cursor()

# Get detailed schema information
schema_info = OrderedDict()

# Get all tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    # Get column information
    cursor.execute(f'PRAGMA table_info({table})')
    columns = cursor.fetchall()
    
    # Get foreign keys
    cursor.execute(f'PRAGMA foreign_key_list({table})')
    foreign_keys = cursor.fetchall()
    
    # Get record count
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    record_count = cursor.fetchone()[0]
    
    # Store structured info
    schema_info[table] = {
        'columns': [
            {
                'name': col[1],
                'type': col[2],
                'not_null': bool(col[3]),
                'default_value': col[4],
                'primary_key': bool(col[5])
            }
            for col in columns
        ],
        'foreign_keys': [
            {
                'column': fk[3],
                'references_table': fk[2],
                'references_column': fk[4]
            }
            for fk in foreign_keys
        ],
        'record_count': record_count
    }

# Save as JSON
with open('rf_db_backups/rf_schema_structure.json', 'w') as f:
    json.dump(schema_info, f, indent=2)

# Create Python class definitions
with open('rf_db_backups/rf_sqlmodel_classes.py', 'w') as f:
    f.write('from sqlmodel import SQLModel, Field, Relationship\n')
    f.write('from typing import Optional, List\n\n')
    f.write('# Auto-generated SQLModel classes from FIT_eeb3795.db schema\n')
    f.write('# Generated on: 2025-07-08\n\n')
    
    for table_name, table_info in schema_info.items():
        class_name = ''.join(word.capitalize() for word in table_name.split('_'))
        f.write(f'class {class_name}(SQLModel, table=True):\n')
        f.write(f'    __tablename__ = "{table_name}"\n')
        
        for col in table_info['columns']:
            python_type = {
                'INTEGER': 'int',
                'VARCHAR': 'str', 
                'FLOAT': 'float',
                'TEXT': 'str'
            }.get(col['type'], 'str')
            
            if not col['not_null'] and not col['primary_key']:
                python_type = f'Optional[{python_type}]'
            
            field_args = []
            if col['primary_key']:
                field_args.append('primary_key=True')
            if col['default_value'] is not None:
                field_args.append(f'default={repr(col["default_value"])}')
            elif not col['not_null']:
                field_args.append('default=None')
            
            field_str = f'Field({", ".join(field_args)})' if field_args else 'Field()'
            f.write(f'    {col["name"]}: {python_type} = {field_str}\n')
        
        f.write('\n')

# Create table mapping info
table_mapping = {
    'geographies': 'rf_csv_inputs/dbout_geographies_*.csv',
    'groups': 'rf_csv_inputs/dbout_groups_*.csv',
    'impactcategories': 'rf_csv_inputs/dbout_impactcategories_*.csv',
    'impactcategoryweights': 'rf_csv_inputs/dbout_impactcategoryweights_*.csv',
    'lifecyclestages': 'rf_csv_inputs/dbout_lifecyclestages_*.csv',
    'metadata': 'rf_csv_inputs/dbout_metadata_*.csv',
    'normalizedlciavalues': 'rf_csv_inputs/dbout_normalizedlciavalues_*.csv',
    'singlescores': 'rf_csv_inputs/dbout_singlescores_*.csv',
    'subgroups': 'rf_csv_inputs/dbout_subgroups_*.csv',
    'weightedresults': 'rf_csv_inputs/dbout_weightedresults_*.csv',
    'weightingschemes': 'rf_csv_inputs/dbout_weightingschemes_*.csv'
}

with open('rf_db_backups/rf_table_csv_mapping.json', 'w') as f:
    json.dump(table_mapping, f, indent=2)

conn.close()
print('Created structured schema files:')
print('- rf_schema_structure.json (detailed schema info)')
print('- rf_sqlmodel_classes.py (ready-to-use SQLModel classes)')
print('- rf_table_csv_mapping.json (table-to-CSV mapping)')