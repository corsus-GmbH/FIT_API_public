from sqlmodel import SQLModel, Field, create_engine, Session, select, func
from typing import Optional
import os
import pandas as pd
import json
import glob
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the auto-generated SQLModel classes
from sqlmodel_classes import (
    Geographies, Groups, Impactcategories, Impactcategoryweights,
    Lifecyclestages, Metadata, Normalizedlciavalues, Singlescores,
    Subgroups, Weightedresults, Weightingschemes
)

# Database setup with timestamp
timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
database_path = f"output/FIT_{timestamp}.db"
logger.info(f"Creating database: {database_path}")

if os.path.exists(database_path):
    logger.info(f"Removing existing database: {database_path}")
    os.remove(database_path)

engine = create_engine(f"sqlite:///{database_path}")
SQLModel.metadata.create_all(engine)

def load_csv_mapping():
    """Load the table-to-CSV mapping configuration"""
    with open('table_csv_mapping.json', 'r') as f:
        return json.load(f)

def find_csv_file(pattern):
    """Find CSV file matching the pattern"""
    # Pattern now points to input/ directory
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError(f"No CSV file found for pattern: {pattern}")
    if len(files) > 1:
        logger.warning(f"Multiple files found for {pattern}, using: {files[0]}")
    return files[0]

def get_column_mapping(table_name):
    """Get column name mapping from CSV headers to database columns"""
    mappings = {
        'geographies': {
            'alpha-2': 'geo_shorthand_2',
            'alpha-3': 'geo_shorthand_3', 
            'country-code': 'international_code',
            'name': 'country_name'
        },
        'groups': {
            'group_en': 'group_name'
        },
        'subgroups': {
            'subgroup_en': 'subgroup_name'
        },
        'impactcategories': {
            'normalisation_value': 'normalization_value',
            'normalisation_unit': 'normalization_unit'
        },
        'lifecyclestages': {
            'lcstage_shorthand': 'lc_stage_shorthand',
            'name': 'lc_name'
        },
        'impactcategoryweights': {
            'value': 'ic_weight'
        },
        'singlescores': {
            'single_scores': 'single_score'
        }
    }
    return mappings.get(table_name, {})

def clean_dataframe(df, table_name):
    """Clean DataFrame for database insertion"""
    # Remove any unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Apply column name mappings
    column_mapping = get_column_mapping(table_name)
    if column_mapping:
        df = df.rename(columns=column_mapping)
        logger.info(f"Applied column mapping for {table_name}: {column_mapping}")
    
    # Handle specific data fixes
    if table_name == 'geographies':
        # Fix missing alpha-2 code for Namibia
        namibia_mask = (df['country_name'] == 'Namibia') & (df['geo_shorthand_2'].isna())
        if namibia_mask.any():
            df.loc[namibia_mask, 'geo_shorthand_2'] = 'NA'
            logger.info("Fixed missing alpha-2 code for Namibia: set to 'NA'")
    
    # Replace NaN with None for proper NULL handling
    df = df.where(pd.notnull(df), None)
    
    logger.info(f"Cleaned {table_name}: {len(df)} records, {len(df.columns)} columns")
    logger.info(f"Columns: {list(df.columns)}")
    return df

def populate_table(table_class, csv_pattern, session):
    """Populate a single table from CSV with batch operations"""
    table_name = table_class.__tablename__
    logger.info(f"Populating {table_name}...")
    
    try:
        # Find and load CSV file
        csv_file = find_csv_file(csv_pattern)
        logger.info(f"Loading CSV: {csv_file}")
        
        # Read CSV with semicolon delimiter and skip first column (index)
        # Preventing `item_id` being incorrectly set as numeral
        df = pd.read_csv(csv_file, sep=';', index_col=0, encoding="utf-8", dtype={"item_id": str})
        df = clean_dataframe(df, table_name)
        
        if len(df) == 0:
            logger.warning(f"No data found in {csv_file}")
            return 0
        
        # Convert DataFrame to records for bulk insert
        records = df.to_dict('records')
        
        # Tables that might have duplicates - use merge instead of bulk insert
        tables_with_duplicates = set()  # metadata now has composite primary key
        
        if table_name in tables_with_duplicates:
            # Use merge for tables with potential duplicates
            total_inserted = 0
            for record in records:
                obj = table_class(**record)
                session.merge(obj)
                total_inserted += 1
                
                if total_inserted % 1000 == 0:
                    session.commit()
                    logger.info(f"  Processed {total_inserted}/{len(records)} records")
            
            session.commit()
        else:
            # Use bulk insert for tables without duplicates
            batch_size = 10000
            total_inserted = 0
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i+batch_size]
                session.bulk_insert_mappings(table_class, batch)
                session.commit()
                total_inserted += len(batch)
                
                if len(records) > batch_size:
                    logger.info(f"  Inserted batch {i//batch_size + 1}/{(len(records)-1)//batch_size + 1}")
        
        logger.info(f"{table_name}: {total_inserted} records inserted")
        return total_inserted
        
    except Exception as e:
        logger.error(f"Error populating {table_name}: {e}")
        session.rollback()
        return 0

def create_full_database():
    """Create the complete FIT database from CSV files"""
    logger.info("Starting full database creation...")
    start_time = time.time()
    
    # Load CSV mapping
    csv_mapping = load_csv_mapping()
    
    # Define table creation order (to handle dependencies)
    table_order = [
        (Geographies, 'geographies'),
        (Groups, 'groups'),
        (Subgroups, 'subgroups'),
        (Impactcategories, 'impactcategories'),
        (Lifecyclestages, 'lifecyclestages'),
        (Weightingschemes, 'weightingschemes'),
        (Metadata, 'metadata'),
        (Impactcategoryweights, 'impactcategoryweights'),
        (Normalizedlciavalues, 'normalizedlciavalues'),
        (Weightedresults, 'weightedresults'),
        (Singlescores, 'singlescores')
    ]
    
    total_records = 0
    
    with Session(engine) as session:
        for table_class, table_key in table_order:
            csv_pattern = csv_mapping[table_key]
            records_inserted = populate_table(table_class, csv_pattern, session)
            total_records += records_inserted
    
    end_time = time.time()
    logger.info(f"Database creation completed in {end_time - start_time:.2f} seconds")
    logger.info(f"Total records inserted: {total_records:,}")
    
    # Verify final database
    with Session(engine) as session:
        logger.info("\nFinal database summary:")
        for table_class, _ in table_order:
            # count = session.query(table_class).count()
            statement = select(func.count()).select_from(table_class)
            count = session.exec(statement).one()
            logger.info(f"  {table_class.__tablename__}: {count:,} records")

if __name__ == "__main__":
    try:
        create_full_database()
        logger.info(f"Database successfully created: {database_path}")
    except Exception as e:
        logger.error(f"Database creation failed: {e}")
        raise