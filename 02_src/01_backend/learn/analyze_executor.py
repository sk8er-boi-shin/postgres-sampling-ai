from main.db_executor import DBExecutor

def run_analyze(table_name):
    db = DBExecutor()
    db.run_analyze(table_name)
    db.close()
