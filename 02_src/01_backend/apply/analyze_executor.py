def run_apply_analyze(table, model):
    estimated = model({"dummy": True})
    print(f"Applying ANALYZE with estimated sample size {estimated}")
