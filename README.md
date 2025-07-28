## ⚠️ Note: This branch is a work in progress (WIP)

- Initial class scaffolding has been completed.
- Database connectivity and execution with PostgreSQL have **not** been tested yet.
- Please refrain from merging into `main` until the implementation is stable.

# postgres-sampling-ai

A Python-based tool to **automatically determine optimal sampling rates** for PostgreSQL's statistics collection,  
based on **data distribution analysis and machine learning**.

This helps DBAs and performance engineers shorten `ANALYZE` time without sacrificing accuracy, especially on large tables.

---

## 🚀 Features

- Analyze **column-level uniqueness, distribution, and index presence**
- Suggest **appropriate sampling rates** to improve `ANALYZE` efficiency
- Works with **scikit-learn**, **pandas**, and standard PostgreSQL statistics
- Supports **declarative partitioned tables** (PostgreSQL 10+)

---

## 🎯 Target Users

- PostgreSQL **DBAs** facing long ANALYZE time
- **Performance tuning engineers** optimizing large or complex queries
- Engineers working with **big data tables** or limited maintenance windows

---

## ⚠️ Limitations

- ❌ **INHERITS-based legacy tables are not supported**
- ✅ Works only with **standard or declarative partitioned tables** (PostgreSQL 10+)
- Designed for environments where **`ANALYZE` is executed via standard PostgreSQL mechanisms**

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
