# Table of Contents

1. [Functional Requirements](#1-functional-requirements)


📘 **For terminology and technical background used in this document, please refer to the [Reference and Glossary](./03_reference.md#prerequisites).**

---

# 1. Functional Requirements

The following are the functional requirements that this tool must satisfy:

### 1. Estimation of Sampling Row Counts
- For each table, estimate the optimal number of sampling rows based on past execution logs and statistical information.
- In the initial phase, use rule-based logic or regression models, with potential future support for reinforcement learning.

### 2. Metrics Collection

In its initial implementation, the tool will collect the following statistical and metadata from PostgreSQL:

- System catalogs used:
  - `pg_stat_all_tables`
  - `pg_stat_user_indexes`
  - `pg_class`
  - `pg_attribute`
  - `pg_stats`

- Key metrics collected:
  - Number of rows in each table (`reltuples`)
  - Free space and fragmentation (`n_dead_tup`)
  - Column-level statistics such as cardinality, correlation, and `n_distinct`

Additional internal views or statistics may be considered in future implementations or performance evaluations, such as `pg_stat_progress_analyze`, `pg_stat_io`, and extended statistics.

### 3. Control of ANALYZE Execution
- Dynamically execute `ANALYZE` based on the estimated sampling row count.
- Consider partitioned tables and partial indexes to issue `ANALYZE` at the appropriate scope.
- Exclude unsupported targets (e.g., foreign tables).

### 4. Logging and Anomaly Detection
- Record execution results (estimates, execution time, update status, etc.) to logs.
- In case of errors, output logs appropriately and implement retry or skip mechanisms.

### 5. Configuration and Parameter Control
- Allow users to define target schemas, excluded tables, thresholds, etc., via configuration files.
- Enable switching between dry-run mode and execution mode.

### 6. Integration with Schedulers and CI/CD (Future Functionality)
- Batch execution capabilities assuming integration with cron or job schedulers.
- Framework for automation in conjunction with CI/CD tools.
