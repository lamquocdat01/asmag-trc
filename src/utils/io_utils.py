import os
import json
from pathlib import Path

def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(path)

def save_json(obj, path):
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
