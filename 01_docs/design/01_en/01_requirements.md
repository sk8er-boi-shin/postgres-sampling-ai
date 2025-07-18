# Table of Contents

1. [Functional Requirements](#1-functional-requirements)
2. [Non-functional Requirements](#2-non-functional-requirements)
3. [Technology Stack (Libraries and Runtime Environment)](#3-technology-stack-libraries-and-runtime-environment)


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

---

# 2. Non-functional Requirements

The non-functional requirements of this tool are defined with a focus on execution efficiency, maintainability, operability, and extensibility.  
Additionally, initial threshold values and constraints required during the basic design phase will be set, serving as the basis for future automation and optimization.

### 1. Performance

- Aims to complete statistics collection and updates within a few minutes, even for large tables.
- Assumes fast statistics collection using sampling, with optional comparison against full scans.
- Monitors memory usage and CPU load at runtime to avoid excessive resource consumption.

#### Initial Thresholds (Performance-related)

| Item | Description | Initial Value (Example) |
|------|-------------|--------------------------|
| Max execution time (ANALYZE) | Upper time limit per table; logs warnings if exceeded but continues processing. *Note 1 | 60 seconds |
| Memory usage limit | Limit per process | 1GB |
| Parallel execution count | Number of concurrent ANALYZE operations | 1–4 threads |

*Note 1: In the future, support for cancellation or error-level escalation may be considered as options.


### 2. Availability & Stability

- Implements a mechanism to log errors and safely terminate or skip processing when failures occur.
- Includes fail-safe mechanisms to prevent unexpected crashes.

#### Initial Thresholds (Anomaly Detection & Retry)

| Item | Description | Initial Value (Example) |
|------|-------------|--------------------------|
| Retry count | Retries for temporary failures | Max 3 times |
| Handling on statistics collection failure | If invalid stats are returned | Skip + Log output |


### 3. Maintainability

- Modular structure to allow easy modifications.
- Logs and error details should be clear and facilitate troubleshooting.
- *Note: Additional notes on module structure, interface separation, and use of DI will be provided in the detailed design.


### 4. Extensibility

- Designed to allow future support for other RDBMS and additional statistics.
- Considers modular separation to support future integration with Web UI and external APIs.
- *Note: Abstract design and interface definitions for future expansion will be covered in the detailed design.


### 5. Runtime Environment & Compatibility

- The initial release assumes local execution on PostgreSQL 15 series + Linux.
- Future compatibility with cloud platforms (e.g., AWS RDS, GCP Cloud SQL) is also envisioned.


### 6. Security

| Item | Content | Notes |
|------|---------|-------|
| SQL injection prevention | Use bind variables for all queries. Prohibit SQL construction using string concatenation. | Especially important when GUI is implemented. Enforce via common API layer. |
| Server parameter restrictions | Restrict session-level parameter changes via `SET` statements. | Controlled by user permissions; also disabled via GUI. |
| Dangerous command control | Restrict commands such as `COPY`, `DO`, `EXECUTE`. | Validate commands received from the frontend on the backend. |
| Long-running query prevention | Use `statement_timeout` to prevent runaway queries. | Also enforced during GUI-based executions. |

* As GUI functionality is planned for the future, risks from invalid inputs or unexpected operations will increase. Therefore, security policies will be clearly defined from the beginning, with restrictions implemented at the backend. During GUI development, these policies will be reinforced with input validation, API authorization, and role-based controls.


### 7. Logging & Auditing

- Logs execution results, target objects, execution time, estimated sampling values, etc.
- CSV output for post-analysis and performance evaluation is also under consideration.

#### Initial Thresholds (Logging)

| Item | Description | Initial Value (Example) |
|------|-------------|--------------------------|
| Logging condition | Based on query execution time | Only log if execution time exceeds 5 seconds (*Note 1) |

*Note 1: Initially defines 5 seconds as the slow query threshold. Logs only those exceeding it. Future plans include dynamic thresholds based on average response time. Regardless of time, the following will always be logged:
- When an error occurs during query execution
- When degradation in statistical accuracy is detected (e.g., unexpected switch from `Index Scan` to `Seq Scan` or `Bitmap Heap Scan`, or a sharp increase in estimated cost)

#### ▼ Examples of Statistical Degradation Detection:
- **Change in scan method**  
  e.g., `Index Scan` → `Seq Scan` or `Bitmap Heap Scan`
- **Sudden increase in estimated cost**  
  e.g., Total cost doubling compared to historical values
- **Mismatch in estimated vs. actual row count**  
  e.g., Estimated `rows=10` but actual result contains `10000 rows`
- **Significant increase in execution time**  
  e.g., Query becomes much slower without query change


### 8. Table Selection & Sampling Settings

- Determine target tables based on row count, schema, and type.
- Initial sampling rates and exclusion criteria are set, but AI-driven dynamic adjustment is planned.

#### Initial Thresholds (Selection & Sampling)

| Item | Description | Initial Value (Example) |
|------|-------------|--------------------------|
| Minimum row count threshold | Minimum row count to include in processing | Not set (*Note 1) |
| Excluded schemas | Excluded from processing | `pg_catalog`, `information_schema` |
| Foreign table exclusion | Determined by table attributes (*Note 2) | Excluded |
| Sampling row count | Number of samples used for ANALYZE | Automatically adjusted based on PostgreSQL settings (*Note 3) |
| default_statistics_target | Column-level statistics granularity | 100 (PostgreSQL default) |
| Statistics update frequency limit | Avoid frequent re-execution | Configurable by hour or day (*Note 4) |

*Note 1: No fixed lower limit is set initially to allow updates when row counts drop significantly (e.g., from 10,000 to 5,000). Future plans include AI-based dynamic logic based on data variation.

*Note 2: In PostgreSQL, if `pg_class.relkind = 'f'`, the table is defined as a foreign table. These are excluded as they connect to external sources via FDW.

*Note 3: PostgreSQL internally calculates the required sample count for `ANALYZE` based on `default_statistics_target`, column count, and stat type. This tool respects that and may adjust as needed. Future plans include AI-based tuning.

*Note 4: In the future, the tool may monitor `pg_stat_xxx` or query performance continuously and use AI to automatically control timing for updating statistics.


### Notes and Remarks

- All thresholds mentioned above are **initial values**, designed to support **future AI-driven dynamic optimization**.
- Since values may vary depending on version and environment (on-premises or cloud), **support for overrides via environment variables or config files is recommended**.

---


# 3. Technology Stack (Libraries and Runtime Environment)

The following factors were considered when selecting technologies for implementing this tool:

- Balance between execution efficiency and learning cost
- Availability of libraries for data analysis and model building
- Compatibility with PostgreSQL and ease of SQL integration
- Future potential for web UI or cloud deployment

### Technologies Used

| Category | Technology | Purpose / Reason |
|----------|------------|------------------|
| Language | Python 3.9+ | Enables unified implementation for data handling, AI modeling, and DB access. Offers both low learning cost and rich libraries. ※1 |
| Data Analysis | pandas / numpy | Used for processing and analyzing statistical info and logs. Chosen for lightweight use cases. ※2 |
| Machine Learning | scikit-learn | Used to build lightweight regression models to estimate sampling row counts. Simple, well-suited for small to mid-scale data, and easy to maintain. ※3 |
| Data Visualization (optional) | matplotlib / seaborn | Used during PoC phase to visualize model accuracy and feature distributions. ※4 |
| DB Access | psycopg2 | Secure and efficient PostgreSQL driver. |
| Logging | logging | For recording execution results and errors. Also used to accumulate data for training. |

※1: R and Julia excel at statistical analysis but lack seamless DB integration. Java and C# are better suited for business systems, but less favorable for AI/ML due to higher learning cost and library usability. Python offers balanced support for ML, data analysis, and database operations.

※2: Since the workload per query is small (approx. 100 rows max), pandas/numpy were selected for fast startup and rich ecosystems. High-performance libraries like Dask or Polars are more suited for large-scale data and parallel processing, which would cause overhead in this case.

※3: This tool handles relatively small feature sets (tens of columns) and small to mid-sized data (a few thousand rows) per query. scikit-learn is fast, lightweight, and integrates well with pandas/numpy. `.fit()` / `.predict()` are simple to use, and model persistence is easy. XGBoost and LightGBM offer high accuracy but are overkill for this context. Deep learning frameworks like TensorFlow or PyTorch are not ideal due to complexity and low interpretability.

※4: matplotlib/seaborn were chosen for lightweight, mature visualizations. They integrate well with pandas and scikit-learn and are sufficient for PoC needs. More complex tools like Plotly, Altair, or Dash were excluded as overkill.


### Runtime Environment

| Category | Details |
|----------|---------|
| OS | Linux (Ubuntu 22.04) is assumed. Provides a lightweight and stable environment for batch processing and data analysis. Also compatible with PostgreSQL and cloud migration. macOS is also supported. |
| Python Version | Python 3.9 or later (to ensure compatibility and maintainability) ※1 |
| PostgreSQL Version | PostgreSQL 13 or later (for improved ANALYZE and statistics features) |
| Execution Mode | Local script (CLI-based). Can be scheduled with cron. |
| Required Permissions | Must have database access with ANALYZE privileges. |
| Extensibility | Future plans may include Dockerization and deployment via cloud services (e.g., AWS Batch or Lambda). |

※1: Python 3.8 and earlier are no longer supported and are not suitable for long-term use. Python 3.9+ introduces useful features like the dictionary merge operator `|`, improving readability and maintainability.


### Future Expansion Plans

- Consider adopting **MLflow** or **DVC** for model management.
- Web UI integration is envisioned through REST API, allowing frontend frameworks (e.g., React, Next.js).
- Integration with **CI/CD pipelines** for model auto-updating and notifications.
