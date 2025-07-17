# Table of Contents

1. [References and Glossary](#1-references-and-glossary)
2. [Future Expansion Plans](#2-future-expansion-plans)

---


# 1. References and Glossary

### 1. References

| Title | Description / Purpose | URL |
|-------|------------------------|-----|
| PostgreSQL Japanese Official Site | Used to research PostgreSQL specifications, behavior of ANALYZE, and system catalog structures. | https://www.postgresql.jp/ |
| PostgreSQL Official Documentation (English) | Technical reference for statistics collection methods, `default_statistics_target`, partitioning, etc. | https://www.postgresql.org/docs/ |
| scikit-learn Official Documentation | Guidelines on regression models and feature engineering. | https://scikit-learn.org/stable/ |

### 2. Glossary (PostgreSQL System Views & Tables)

| Term | Description |
|------|-------------|
| pg_class | System catalog holding basic information about tables and indexes. Stores row counts (`reltuples`) and page counts (`relpages`). |
| pg_stat_all_tables | View containing access statistics for each table, including insert/update/delete counts, live/dead tuples. |
| pg_stat_user_indexes | View providing statistics for user-defined indexes, such as scan counts and tuple reads. |
| pg_stats | View showing column-level statistics collected via ANALYZE. Includes `n_distinct`, `null_frac`, `correlation`, etc. |
| pg_attribute | System catalog storing metadata on table/view columns: names, order, statistics targets. |
| pg_namespace | Catalog managing schema (namespace) information including schema names and IDs. |
| pg_stat_progress_analyze | View showing progress of currently running ANALYZE operations. Visualizes blocks processed, current phase, etc. |
| pg_stat_io | Available from PostgreSQL 16. New view providing detailed I/O statistics including block reads/writes. |

### 3. Other Terms & Abbreviations

| Term / Abbreviation | Description |
|---------------------|-------------|
| ANALYZE | Command in PostgreSQL used to collect and update statistics. Essential for accurate query planning. |
| default_statistics_target | PostgreSQL parameter controlling the granularity of column statistics. Default is 100. |
| reltuples | Estimated row count in a table, stored in `pg_class`. Updated after ANALYZE. |
| n_distinct | Estimated number of unique values in a column. Used in selectivity estimation. |
| correlation | Correlation between column values and physical row order (-1 to 1). Affects index efficiency. |
| null_frac | Ratio of NULL values in a column. Used in selectivity calculations. |
| FDW (Foreign Data Wrapper) | Mechanism to map external data sources into PostgreSQL. FDW tables are not compatible with ANALYZE. |
| PoC (Proof of Concept) | Preliminary implementation to validate feasibility of a concept or feature. |
| dry-run | Mode where actual operations are skipped, and only behavior or results are observed for verification. |
| Regression Model | AI method used to predict numerical values. Utilized here to estimate sampling row counts. |
| relkind | Column in `pg_class` indicating the object type (table, index, view, etc.). |


---

# 2. Future Expansion Plans

This section outlines features and improvements that are not currently implemented but are being considered for future enhancement.

### 1. Web UI Integration

- Visualization of training and application results (e.g., sampling row count, prediction basis, execution time)
- GUI-based control for specifying queries, selecting models, and executing dry-run operations
- Dashboard to track the time-series transition of statistical information

### 2. Continuous Model Learning and Evaluation

- Automatic retraining based on accumulated execution logs (predicted values and actual performance)
- Periodic model evaluation and automatic replacement
- Integration with CI/CD pipelines to prevent deployment of underperforming models

### 3. Multi-node / Cluster Support

- Extension of model application logic for PostgreSQL cluster environments
- Support for statistical discrepancies depending on the query routing destination

### 4. Flexible Configuration via Files or Environment Variables

- Configuration management using `.yaml` or `.toml` files
- Externalization of rules for max/min sample rows and table exclusions

### 5. Enhanced Security and Operational Reliability

- Log encryption and tamper detection
- JWT authentication and RBAC implementation for API integrations
- Scheduling support using cron or Airflow

### 6. Expansion of Supported RDBMS (Mid to Long Term)

- Although the tool currently supports only PostgreSQL, the following RDBMS are also under consideration:
  - Amazon Aurora PostgreSQL
  - Greenplum / YugabyteDB
  - MySQL family (requires redesign due to different sampling mechanisms)

> Note: The above items are conceptual and their implementation priorities will be determined based on PoC results, user feedback, and operational outcomes.
