# FIT API Changelog

## v1.1.0 - 2025-07-28 - Performance & Database Optimization

### Performance Improvements
- **GET `/items/`**: dramatically faster after N+1 query elimination
- **POST `/calculate-recipe/`**: Up to 1.6x faster with 90% query reduction
- Added pagination support for `/items/` endpoint (`skip` and `limit` parameters)

### Database System
- New database creation pipeline in `database_creation/` with input/output structure
- Timestamped database generation (`FIT_YYYYMMDD-HHMMSS.db`)

### Technical Changes
- Bulk database query optimizations (`crud_optimizations.py`, `processors_optimized.py`)
- Optimized endpoint implementations integrated into main API

### No Breaking Changes
All API endpoints maintain identical input/output formats and behavior.

### Validation
- Mathematical consistency verified across all calculations
- Performance tested against original implementation