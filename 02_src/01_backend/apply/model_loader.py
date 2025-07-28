def load_model(model_path):
    print(f"Loading model from {model_path}")
    return lambda metrics: 1000  # ダミー推定器
