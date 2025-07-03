# Database Creation System

This directory contains the production-ready database creation system for the FIT API.

## Directory Structure

```
database_creation/
├── input/                    # Drop fresh CSV files here
├── output/                   # Generated database outputs here
├── create_full_database.py   # Main database creation script
├── sqlmodel_classes.py       # SQLModel class definitions
├── table_csv_mapping.json    # CSV file mapping configuration
└── column_mapping_edits.json # Column name mappings
```

## Usage

### 1. Prepare CSV Files
Place CSV files generated via [FIT_scripts](github.com/corsus-GmbH/FIT_scripts_public) in the `input/` directory. The required files have these naming patterns:
- `dbout_geographies_*.csv`
- `dbout_groups_*.csv`
- `dbout_impactcategories_*.csv`
- `dbout_impactcategoryweights_*.csv`
- `dbout_lifecyclestages_*.csv`
- `dbout_metadata_*.csv`
- `dbout_normalizedlciavalues_*.csv`
- `dbout_singlescores_*.csv`
- `dbout_subgroups_*.csv`
- `dbout_weightedresults_*.csv`
- `dbout_weightingschemes_*.csv`

### 2. Run Database Creation
```bash
cd database_creation/
python3 create_full_database.py
```

### 3. Retrieve Generated Database
The new database will be created at: `output/FIT_full_database.db`

## Safety Features

- **Input isolation**: CSV files in `input/` don't interfere with archived data
- **Output isolation**: Generated database in `output/` doesn't overwrite `../data/FIT.db`
- **Clean separation**: Production files vs. analysis scripts clearly separated

## Production Deployment

To deploy the new database:
1. Verify the generated database: `output/FIT_full_database.db`
2. Replace production database: `cp output/FIT_full_database.db ../data/FIT.db`
3. Restart API containers to pick up the new database

## Files Overview
- `create_full_database.py` - Main script, creates database from CSVs
- `sqlmodel_classes.py` - Database schema definitions
- `table_csv_mapping.json` - Maps table names to CSV file patterns
- `column_mapping_edits.json` - Column name mapping configuration
