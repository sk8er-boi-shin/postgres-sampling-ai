# Table of Contents

1. [Introduction](#1-introduction)
2. [Background and Purpose](#2-background-and-purpose)
3. [Scope](#3-scope)
4. [System Structure](#4-system-structure)
5. [Processing Overview](#5-processing-overview)
6. [Processing Flow and Logic Overview](#6-processing-flow-and-logic-overview)


📘 **For terminology and technical background used in this document, please refer to the [Reference and Glossary](./03_reference.md#prerequisites).**

---

# 1. Introduction

This document outlines the basic design of a tool that improves the efficiency of statistics update processing in PostgreSQL by automatically determining the optimal number of sampling rows using AI.

In PostgreSQL, statistics are used for query optimization, but updating them requires executing `ANALYZE`. The processing time and accuracy can vary significantly depending on the size and characteristics of the target tables. This project aims to design a mechanism to address the following challenges:

- Long execution times of `ANALYZE` on large tables  
- Suboptimal execution plans caused by outdated or inconsistent statistics  
- Lack of adaptive sampling strategies based on update frequency and data characteristics  
- Handling of partitioned or fragmented tables  
- Variability due to delayed updates or estimates in `pg_stat` system views  

This design document details the system architecture, processing flow, input/output specifications, and the logic used to dynamically calculate sampling row counts using AI.

The tool will begin as a locally executable script for proof-of-concept (PoC) purposes, with future plans to support scalable execution in cloud environments and potential integration with a web-based UI.


---

# 2. Background and Purpose

In PostgreSQL, table-level statistics are used to generate optimal query execution plans.

However, these statistics must be collected either manually or automatically by running `ANALYZE`.  
During this process, statistics are gathered from a randomly sampled subset of rows from the entire table.

The number of sampled rows is internally calculated by PostgreSQL, and by default, it selects enough rows to match the `default_statistics_target` value (default is 100) for each column.

This value can be customized per column, allowing a balance between accuracy and processing overhead.  
However, depending on the size and structure of the table, even sampling may involve significant load or execution time.

Additionally, PostgreSQL’s auto-ANALYZE relies on trigger conditions (such as update ratios and timing), which can lead to the following problems in actual production environments:

- No adaptive sampling strategy exists based on update frequency or data characteristics  
- There is no clear guideline for when to use full scan versus sampling  
- The decision to run ANALYZE is often left to individual users or administrators, leading to inconsistency

Furthermore, in partitioned or fragmented tables, inconsistent statistics are more likely to occur, which can result in poor execution plan choices.

To address these issues, this project aims to develop a mechanism that uses AI to dynamically analyze table-specific characteristics (such as row count, update rate, cardinality, and uniqueness) and automatically calculate the optimal number of rows to sample.

This tool is designed to provide the following value:

- Reduce the time required to collect statistics and improve the efficiency of ANALYZE operations  
- Estimate realistic sampling row counts based on actual data to improve execution plan accuracy  
- Automate statistics management and reduce the need for manual tuning and trial-and-error

This design document describes the system architecture, execution logic, AI-based estimation approach, and key technical considerations to solve the above challenges.

---

# 3. Scope

The scope of this design is defined as follows:

### Included Scope

- Statistics update processing (`ANALYZE`) for PostgreSQL databases  
- Optimization of the sampling row count based on `default_statistics_target`  
- Design of a script that dynamically calculates the optimal sampling row count for each target table and executes `ANALYZE`  
- Statistics updates for both regular local tables and partitioned tables  

### Excluded Scope

- Handling of foreign tables or tables accessed via FDW (Foreign Data Wrapper)  
- Support for RDBMS other than PostgreSQL (e.g., MySQL, Oracle, SQL Server)  
  ※ Currently limited to PostgreSQL, but expansion to other major RDBMS may be considered in the future if this approach proves stable and effective.  
- Modifying PostgreSQL's built-in automatic statistics update behavior or directly controlling server parameters  
- Visualization features such as web UIs or dashboards (considered for future expansion)

### Assumed Environment

- Targeting PostgreSQL version 13 and above
- Development and execution environment assumed to be a local PC or lightweight VPS  
- Deployment to production environments will be considered based on the results of future PoC evaluations

---

# 4. System Structure

This tool aims to improve the performance of statistics updates in PostgreSQL by using AI to estimate the optimal number of sampling rows and executing `ANALYZE` based on those estimates.

The initial phase assumes a local execution environment, with future possibilities of cloud deployment and integration with a web UI.

The system consists of the following two phases:

- **Learning Phase**: Collects statistics and execution plans before and after queries, and trains an AI model to estimate optimal sampling row counts
- **Application Phase**: Uses the trained model to estimate sampling row counts and applies `ANALYZE` in production environments

## Overview of the Learning and Application Phases


```
[Learning Phase: Executed in development or PoC environments]  
↓  
1. Specify a target query  
↓  
2. For each included table, repeat the following:  
   - Collect statistical metrics (e.g., from pg_stat)  
   - Estimate the sampling row count using AI  
   - Execute ANALYZE based on the estimated value  
   - Retrieve the execution plan and record the processing time  
↓  
3. Retrain the AI model using the execution plan and collected statistics  
↓  
4. Save the trained model to a file (e.g., best_model.pkl)  

↓

[Application Phase: Executed in production environments]  
↓  
1. Specify a target query  
↓  
2. Collect only the metrics of the involved tables  
↓  
3. Estimate the sampling row count using the trained model  
↓  
4. Execute ANALYZE based on the estimated value  
   (or output logs in dry-run mode)  

```

## Component Structure

The following outlines the module composition supporting both the learning and application phases:

### Components in the Learning Phase

#### 1. Sampling Optimization Engine (AI Logic)
- Estimates optimal sampling row counts for each table based on past execution logs and statistics
- Initially uses a simple rule-based or regression model; future expansions may include reinforcement learning or clustering
- The trained model is saved as a file (e.g., Pickle format) and reused in the application phase

#### 2. Metrics Collection Module
- Collects statistical and structural information from system catalogs such as `pg_stat_all_tables`, `pg_stat_user_indexes`, and `pg_class`
- Targets include `reltuples`, `n_dead_tup`, cardinality, correlation coefficients, etc.
- Applies to all tables included in the query

#### 3. Statistics Update & Execution Plan Logging Module
- Executes `ANALYZE` based on the estimated sampling row count to update statistics
- Then runs the target query and records its execution plan and duration
- Results are stored in a history table or log file for reuse in learning

### Components in the Application Phase

#### 4. Trained Model Application Module
- Loads the trained model file and estimates sampling row counts for target tables
- Implements a fallback mechanism to default values if model-feature inconsistencies are detected (fail-safe design)

#### 5. Sampling Execution & Statistics Update Module (Production)
- Applies `ANALYZE` based on the estimated sampling row count
- Targets only the tables included in the specified query
- Post-statistics update, the system proceeds with production processing without retrieving execution plans

### Common Components

#### 6. Logging and Error Handling Mechanism
- Outputs logs for execution results and anomaly detection
- Includes retry processing, target exclusion, and feedback into the learning phase in case of errors

#### 7. (Planned) Web UI / API Integration Module
- Visualizes query patterns and prediction models  
- Provides analysis dashboards for sampling accuracy and effectiveness  
- Explores integration with CI/CD pipelines via backend APIs

---

# 5. Processing Overview

This tool aims to optimize the performance of statistics updates in PostgreSQL.  
It uses AI to estimate an appropriate number of sampling rows for each table and applies that to the `ANALYZE` process, reducing update time and improving efficiency.

The tool operates in two distinct phases:

- **Learning Phase (PoC or development environment)**  
  Collects statistical information and execution plans, then trains an AI model to estimate optimal sampling row counts.

- **Application Phase (production environment)**  
  Uses the trained model to estimate sampling row counts and applies them to `ANALYZE`.

```

[Learning Phase]  
↓  
1. Specify the target query  
↓  
2. For each table included in the query, perform the following:  
   - Retrieve statistical information  
   - Estimate the sampling row count using AI  
   - Execute ANALYZE and update statistics  
   - Retrieve and record the execution plan and execution time  
↓  
3. Retrain the model based on the results and save it as a file  

↓

[Application Phase]  
↓  
1. Specify the target query  
↓  
2. Collect metrics for each table  
↓  
3. Estimate sampling row counts using the trained model  
↓  
4. Execute ANALYZE based on the estimated values  

```

※ For detailed module structure, see [System Structure](#4-system-structure).

---


# 6. Processing Flow and Logic Overview

This section describes the processing flow and core logic of each phase defined in the previous chapter, **System Structure**—specifically, the **Learning Phase** and the **Application Phase**.



### Learning Phase: Flow and Logic Overview

The learning phase assumes a development or PoC environment and performs a series of operations to allow AI to learn the optimal sampling row count.

#### Processing Flow

1. Specify the target query  
2. Extract the tables used in the query  
3. For each table, repeat the following steps:  
   - Retrieve statistical and structural data from system catalogs (e.g., `pg_stat_all_tables`, `pg_class`)  
   - Estimate the sampling row count using AI  
   - Execute `ANALYZE` using the estimated row count  
   - Record the execution plan and processing time of the target query  
4. Retrain the AI model based on the results  
5. Save the trained model (e.g., `best_model.pkl`)

#### Logic Overview

- Uses features such as `reltuples`, `n_dead_tup`, cardinality, and correlation coefficients  
- Applies a simple regression model or rule-based logic (with plans to extend to reinforcement learning, etc.)  
- Implements outlier removal and minimum/maximum sampling row limits to ensure safety  
- Records the feature schema along with the model to prevent inconsistencies during loading


### Application Phase: Flow and Logic Overview

In the application phase, the trained model is used in a production environment to apply `ANALYZE` to the appropriate tables referenced in a given query.

#### Processing Flow

1. Specify the target query  
2. Extract the tables used in the query  
3. For each table, perform the following:  
   - Collect metrics (statistical and structural information)  
   - Estimate the sampling row count using the trained model  
   - Execute `ANALYZE` using the estimated value  
     ※ In dry-run mode, only logs are output

#### Logic Overview

- If there is a mismatch between the loaded model and the feature schema, fallback to safe default values  
- Supports parallel execution for multiple tables (with configurable concurrency limit)  
- Logs the estimated results, and in dry-run mode, outputs them in JSON or CSV format  
- In production environments, execution plans are not retrieved—only `ANALYZE` is executed to minimize impact


### Common Functions and Notes

- **Logging and Error Handling**: Logs the results, errors, and anomaly detections of each step. Logs can also be used to feed back into the learning phase  
- **Threshold Management**: Applies thresholds for minimum and maximum sampling row counts to automatically adjust extreme estimates  
- **Extensibility**:
  - Future plans include operating via a web UI and visualizing results  
  - CI/CD integration and automated model evaluation may also be considered


---