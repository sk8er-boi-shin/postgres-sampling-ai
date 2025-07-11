# Table of Contents

1. [Introduction](#1-introduction)
2. [Background and Purpose](#2-background-and-purpose)
3. [Scope](#3-scope)


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

