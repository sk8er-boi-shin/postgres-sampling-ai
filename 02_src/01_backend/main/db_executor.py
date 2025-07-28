# 02_src/01_backend/main/db_executor.py
import psycopg2
from main.config_loader import load_config

class DBExecutor:
    def __init__(self):
        config = load_config()
        self.conn = psycopg2.connect(
            host=config["db"]["host"],
            port=config["db"]["port"],
            user=config["db"]["user"],
            password=config["db"]["password"],
            dbname=config["db"]["dbname"]
        )
        self.conn.autocommit = True

    def run_query(self, sql: str):
        with self.conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchall()

    def run_explain(self, sql: str):
        explain_sql = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql}"
        with self.conn.cursor() as cur:
            cur.execute(explain_sql)
            return cur.fetchone()[0]  # JSON形式で返される

    def run_analyze(self, table_name: str):
        with self.conn.cursor() as cur:
            cur.execute(f"ANALYZE {table_name}")

    def close(self):
        self.conn.close()
