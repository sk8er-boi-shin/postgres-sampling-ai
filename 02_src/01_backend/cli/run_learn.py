from learn.flow_controller import LearnFlowController

def main():
    tables = ["sales", "products", "users"]
    flow = LearnFlowController(tables)
    flow.run()
