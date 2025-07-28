from apply import model_loader, analyze_executor

def main():
    model = model_loader.load_model("02_src/03_models/best_model.pkl")
    analyze_executor.run_apply_analyze("my_table", model)

if __name__ == "__main__":
    main()
