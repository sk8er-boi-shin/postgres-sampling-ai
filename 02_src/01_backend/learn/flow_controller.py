# 02_src/01_backend/learn/flow_controller.py
from learn import metrics_collector, sampling_estimator, analyze_executor, plan_logger, model_trainer
from main.db_executor import DBExecutor

class LearnFlowController:
    def __init__(self, tables: list[str]):
        self.tables = tables
        self.db = DBExecutor()
        self.training_data = []

    def run(self):
        for table in self.tables:
            print(f"[INFO] Processing table: {table}")

            metrics = metrics_collector.collect_metrics(table)
            sample_size = sampling_estimator.estimate_sample_size(metrics)
            analyze_executor.run_analyze(table, sample_size)

            plan = plan_logger.log_execution_plan(f"SELECT * FROM {table} LIMIT 100;")  # 仮クエリ
            self.training_data.append({
                "metrics": metrics,
                "plan": plan
            })

        model_trainer.train_model(self.training_data)
        self.db.close()
