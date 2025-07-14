# Table of Contents

1. [Input/Output Specifications](#1-inputoutput-specifications)
2. [Module Structure](#2-module-structure)
3. [Data Structures and Specifications to Consider](#3-data-structures-and-specifications-to-consider)


📘 **For terminology and technical background used in this document, please refer to the [Reference and Glossary](./03_reference.md#prerequisites).**

---

# 1. Input/Output Specifications

This section outlines the main input and output specifications of the tool.  
It assumes execution as a CLI tool and includes settings files, DB connection info, AI inference I/O, logs, etc.

### Input Specifications

| Category           | Description                                        | Format / Example                            | Notes |
|--------------------|----------------------------------------------------|---------------------------------------------|-------|
| Query              | Target SQL query (common to learning and apply phases) | `SELECT * FROM sales WHERE amount > 1000;`  | Specified in config file or script (flexible) ※1 |
| Target DB Info     | DB connection details (host, port, user, dbname, etc.) | JSON or .env                               | Plaintext storage not recommended for security |
| Sampling Criteria  | Settings for target tables to be sampled          | YAML / JSON format                           | Includes exclusion schemas and thresholds |
| Trained Model      | Model file used during apply phase                | `best_model.pkl`                             | Generated after learning phase |
| Metrics            | Stats from PostgreSQL system catalogs             | `pg_stat_all_tables`, `pg_stats`, etc.       | Retrieved automatically; no manual input required |
| Execution Mode     | Mode to control execution behavior (e.g., normal) | `--mode run`                                 | dry-run mode considered for future support ※2 |

※1: To ensure reproducibility and accuracy, query input methods should be flexible depending on the context.  
Execution environment and conditions are omitted in this document for simplicity.

※2: Currently, execution is fully controlled by the Python logic.  
Full prevention of stats updates via dry-run is partially limited.  
Future enhancements may include modes limited to `EXPLAIN` or outputting logs only.


### Output Specifications

| Category            | Description                                         | Format / Example                           | Notes |
|---------------------|-----------------------------------------------------|--------------------------------------------|-------|
| Execution Logs      | Logs of results, estimated row counts, etc.         | `execution_20240624.log`                    | Log rotation/compression planned |
| Estimated Results   | Estimated sampling row count per table              | CSV or JSON                                | Format: `table_name,estimated_rows` |
| ANALYZE Results     | Success/failure of ANALYZE, execution time, etc.    | JSON or embedded in log                    | Example: `{"status":"success","time":2.13}` |
| EXPLAIN/Stats History | EXPLAIN results for executed queries              | CSV or DB table                            | Used in model retraining |
| Error Output        | Error information during processing                 | stderr or log file                         | Includes retry-eligible flag |
| Model File          | Trained regression model, etc.                      | `best_model.pkl`                            | Expected formats: joblib/pickle via scikit-learn |


### Notes

- All input/output files use UTF-8 encoding.
- Output destinations for model files and statistics can be changed via `config.yaml` or CLI options.
- For future cloud integration (e.g., S3), output destinations like `s3://` URIs will be supported.


---

# 2. module structure

This section describes the module structure that supports the main processing phases (learning phase / application phase) of this tool.  
Each module is clearly separated by responsibility, aiming for an architecture that allows easy future extensions or replacements.



### Learning Phase (PoC / Development Environment)

| Module Name            | Role                                                                 |
|------------------------|----------------------------------------------------------------------|
| `metrics_collector.py` | Collects table statistics (e.g., from pg_stat, pg_class) used in the query |
| `sampling_estimator.py`| Estimates sampling row counts using AI (regression model) based on collected stats |
| `analyze_executor.py`  | Executes `ANALYZE` using the estimated value to update statistics     |
| `plan_logger.py`       | Retrieves and logs the execution plan and elapsed time after query execution |
| `model_trainer.py`     | Trains a regression model using the results and saves it as a `.pkl` file |



### Application Phase (Production or Operational Use)

| Module Name            | Role                                                                 |
|------------------------|----------------------------------------------------------------------|
| `metrics_collector.py` | Collects metrics (same as in the learning phase)                     |
| `model_loader.py`      | Loads the trained model and performs estimation                      |
| `analyze_executor.py`  | Executes `ANALYZE` with estimated rows (dry-run mode also considered) |



### Common / Supporting Modules

| Module Name            | Role                                                                 |
|------------------------|----------------------------------------------------------------------|
| `logger.py`            | Outputs logs for execution results, errors, and estimation values    |
| `config_loader.py`     | Loads configuration files (YAML/JSON) and manages common parameters  |
| `query_parser.py`      | Extracts target tables from a given SQL query                        |
| `error_handler.py`     | Handles errors (retry, skip, notify, etc.)                           |
| `constants.py`         | Manages threshold values and constants centrally                     |



### Planned Extensions (Future Vision)

| Tentative Module Name  | Role                                                                 |
|------------------------|----------------------------------------------------------------------|
| `api_server.py`        | REST API server for requests from Web UI or external tools           |
| `ui_adapter.py`        | Converts model results and stats for visual representation           |
| `job_scheduler.py`     | Manages scheduled/batch jobs (cron or CI/CD integration)             |


> Responsibilities of each module will be further refined in the detailed design phase.  
> Python package structure (e.g., `/modules/`, `/utils/`) and dependency design will also be addressed during implementation.

---

# 3. Data Structures and Specifications to Consider

This section outlines the internal structures of PostgreSQL, column characteristics, and data specifications that should be considered when collecting, estimating, and applying statistical information, as well as the features required for AI-based row estimation.



### 1. PostgreSQL Structures Related to Statistics

| Table / View            | Description                     | Key Columns Used                                              |
|-------------------------|----------------------------------|---------------------------------------------------------------|
| `pg_class`              | Basic table information          | `reltuples`, `relpages`, `relkind`                            |
| `pg_stat_all_tables`    | Per-table statistics             | `n_tup_ins`, `n_tup_upd`, `n_tup_del`, `n_live_tup`, `n_dead_tup` |
| `pg_stat_user_indexes`  | Index usage statistics           | `idx_scan`, `idx_tup_read`                                   |
| `pg_attribute`          | Column definitions               | `attname`, `attnum`, `attstattarget`                         |
| `pg_stats`              | Per-column statistics (view)     | `null_frac`, `n_distinct`, `most_common_vals`, `histogram_bounds`, `correlation` |



### 2. Features for AI Model Training (Feature Vectors)

The AI estimates the sampling row count based on the following expected features:

- **Table size indicators**  
  - `reltuples` (estimated number of rows)  
  - `relpages` (table size in pages)

- **Column statistical characteristics**  
  - `n_distinct` (uniqueness)  
  - `correlation` (correlation coefficient)  
  - `null_frac` (NULL ratio)  
  - Number of columns (used for feature dimensionality)

- **Update frequency and data volatility**  
  - `n_tup_upd`, `n_tup_ins`, `n_tup_del`  
  - `n_dead_tup` (degree of fragmentation)

- **Other metadata (design stage)**  
  - Whether the table is partitioned  
  - Whether partial indexes exist  
  - Schema/table name patterns (for exclusion filtering)



### 3. Specifications and Constraints to Consider

| Item                      | Description                                          | Notes                                                        |
|---------------------------|------------------------------------------------------|--------------------------------------------------------------|
| Handling of foreign tables | Tables with `pg_class.relkind = 'f'` are excluded    | ANALYZE is not supported on FDW tables                       |
| Partitioning structure    | Target of ANALYZE differs depending on parent-child  | Caution required whether `ANALYZE parent_table` includes children |
| Granularity of statistics | PostgreSQL manages stats at column level             | Tunable via `default_statistics_target`                      |
| Extended statistics       | Multi-column stats from PostgreSQL 10+               | Currently out of scope but may be included in future         |
| Accuracy of `reltuples`   | May differ from actual row count                     | Can be unreliable unless recently ANALYZEd                   |
| Delay in `pg_stat_xxx`    | May lag behind buffer cache updates                  | Especially right after updates or inserts                    |
| `INHERITS` tables         | Legacy table inheritance mechanism                   | Not recommended; may be confused with partitions             |



### 4. Assumed Data Structures for Future Expansion

- **Execution log structure (CSV or DB table)**  
  - `query_id`, `table_name`, `estimated_rows`, `actual_duration`, `plan_type`, `timestamp`

- **Feature cache mechanism**  
  - To skip redundant computation for unchanged table structures

- **Training data structure for model retraining**  
  - Logs combining input features and target label (optimal sample count)



*During implementation, the above specifications will be reorganized into SQL views or Python DataFrame structures.  
Additionally, differences in PostgreSQL versions and handling of extended statistics will be evaluated through testing before adoption.*

---