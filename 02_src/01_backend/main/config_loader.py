import yaml
import os

def load_config(path="02_src/05_config/config.yaml"):
    with open(path, 'r') as f:
        return yaml.safe_load(f)
