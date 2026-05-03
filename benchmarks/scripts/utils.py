import json
from pathlib import Path
from datetime import datetime


def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def save_json(path: str, data):
    ensure_dir(str(Path(path).parent))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def timestamp():
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")