# postgres-sampling-ai

A Python-based tool to automatically determine optimal sampling rates for PostgreSQL statistics collection, based on data distribution analysis and machine learning.

## Features

- Analyze column-level uniqueness and distribution
- Suggest appropriate sampling rates for ANALYZE
- Uses scikit-learn, pandas

## Target

- PostgreSQL DBAs
- Performance tuning engineers

## Limitations

- This tool does **not support legacy inheritance-based tables** defined using `INHERITS`.
- It is designed for standard PostgreSQL tables and declarative partitioning (available since PostgreSQL 10 and later).
- Make sure to run this tool only on tables where statistics are collected using standard `ANALYZE` behavior.